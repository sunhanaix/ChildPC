import os,sys,re,json,time
import collections,jieba,wordcloud
import numpy as np
from PIL import ImageGrab,Image,ImageDraw,ImageFont  #pip install Pillow
import matplotlib.pyplot as plt
log_file='ChildControl.log'
mon_apps=['WeChat.exe','QQLive.exe']
ignore_list=['微信','图片查看','腾讯视频','CNewFeedsPlayerCtrlWnd','PlayerPluginWnd','ChatContactMenu']
remove_words = [u'的', u'也', u'他', u'，',u'和', u'是',u'自己',u'有', u'随着', u'对于', u'对',u'等',
	u'能',u'都',u'。',u' ',u'、',u'中',u'在',u'了',u'通常',u'如果',u'我们',u'需要',
	u'？',u'我',u'你',u'！',u'：',u'被',u'第',u'就',u'“',u'”',u'还'] # 自定义去除词库

def checkApps(ss):
	for mon_app in mon_apps:
		if ss.lower().find('name='+mon_app.lower())>-1:
			return True
	return False

def strTime2TS(ss): #给定"2020-05-18 11:45:01"这样的字符串，返回unix时间戳
	return int(time.mktime(time.strptime(ss,"%Y-%m-%d %H:%M:%S")))
 
def rf(fname,recentDays=5): #日期范围内的日志内容关键字分析
	f=open(fname,'r',encoding='utf8')
	texts=[]
	for line in f:
		if checkApps(line):
			res=re.findall(r'(\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2})\s+.+text=(.+)\s+name',line)
			if not type(res)==list :
				continue
			if len(res)<1:
				continue
			if not type(res[0])==tuple:
				continue
			if len(res[0]) <2:
				continue
			date,text=res[0]
			if text in ignore_list:
				continue
			texts.append({'date':date,'text':text})
	f.close()
	last_time=texts[-1]['date']
	print("last_time=%s" % last_time)
	ts_last_time=strTime2TS(last_time)
	ts_begin_time=ts_last_time-3600*24*int(recentDays)
	res=[]
	for t in texts:
		if strTime2TS(t['date']) >ts_begin_time:
			res.append(t)
	return res

def wf(fname,data,opt='w'):  #给定data，写到指定文件
	f=open(file=fname,mode=opt,encoding='utf8')
	f.write(data)
	f.close

def markText(pic_name,text): #给一个图片上，打上文字，默认把文字放 底下&中间
	try:
		setFont = ImageFont.truetype('arial.ttf', 16) ##选择文字字体和大小
	except Exception as e:
		print(e)
		setFont=None
	fillColor = "#FF0000"   #红色
	try:
		image = Image.open(pic_name)
	except Exception as e:
		print(e)
		print("can not Image.open: %s" % pic_name)
		return None
	width,height=image.size
	draw = ImageDraw.Draw(image)
	#image.show()
	draw.text((int(width/2)-160,height-40),text,font=setFont,fill=fillColor,direction=None)
	#image.show()
	try:
		image.save(pic_name)
		image.close()
	except Exception as e:
		print(e)

	
def deal_text(string_data): #给定字符串，返回词频统计数据
	pattern = re.compile(u'\t|\n|\.|-|:|;|\)|\(|\?|"') # 定义正则表达式匹配模式
	string_data = re.sub(pattern, '', string_data) # 将符合模式的字符去除
	seg_list_exact = jieba.cut(string_data, cut_all = False) # 精确模式分词
	object_list = []

	for word in seg_list_exact: # 循环读出每个分词
		if word not in remove_words: # 如果不在去除词库中
			object_list.append(word) # 分词追加到列表
	# 词频统计
	word_counts = collections.Counter(object_list) # 对分词做词频统计
	word_counts_top = word_counts.most_common(20) # 获取前n个最高频的词
	print (word_counts_top) # 输出检查
	return word_counts

def gen_pic(word_counts,x_axis_label,bg='butterfly.jpg',tgt_pic='res.jpg'):
	img=Image.open(bg)
	img_array=np.array(img)
	wc=wordcloud.WordCloud(
		font_path='c:/windows/fonts/simhei.ttf',
		background_color='white',
		mask=img_array,
		width=302,
		height=324,
	)
	wc.generate_from_frequencies(word_counts) # 从字典生成词云
	image_colors=wordcloud.ImageColorGenerator(img_array) # 从背景图建立颜色方案
	wc.recolor(color_func=image_colors) #将词云颜色设置为背景图方案
	plt.imshow(wc)
	plt.axis('off')
	plt.savefig(tgt_pic)
	markText(tgt_pic,x_axis_label)
	#plt.show()
	

def main():
	if len(sys.argv)>1 :
		recentDays=int(sys.argv[1])
	else:
		recentDays=5
	print("Reading recent %d days log from the file:%s..." % (recentDays,log_file))
	texts=rf(log_file,recentDays=recentDays)  #读最近n天的日志
	x_axis_label=texts[0]['date']+'-->'+texts[-1]['date']
	print("x_axis_label=%s" % x_axis_label)
	wf('res.txt',json.dumps(texts,indent=2,ensure_ascii=False))
	ss=''
	for t in texts:
		ss+=t['text']
	print("word counting...")
	word_counts=deal_text(ss)
	print("generating word cloud")
	tgt_pic=x_axis_label.replace(':','_').replace('>','')
	tgt_pic+='.jpg'
	gen_pic(word_counts,tgt_pic=tgt_pic,x_axis_label=x_axis_label)
	print("tgt_pic=%s" % tgt_pic)
if __name__=='__main__':
	main()
	