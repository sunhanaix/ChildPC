import os,sys,subprocess,re,json,time
from PIL import ImageGrab,Image
import glob,shutil
import cv2
import numpy as np
######################################################################
#检查给定目录下的截图的图片文件，分析哪些是笔记本电脑屏幕合上来的情况#
#把对应的图片，存在check.txt里面，用于后续的处理                     #
######################################################################
def getPicFiles(snapDir,res):
	#对snapDir目录进行深度优先遍历
	files = os.listdir(snapDir)
	for fname in files:
		if os.path.isdir(os.path.join(snapDir,fname)):
			getPicFiles(os.path.join(snapDir,fname), res)
		else:
			match=re.findall(r'snap[a-zA-Z]+(\d+)_(\d+)\.png',fname)
			if match:
				res.append(os.path.join(snapDir,fname))
	
def checkDarkCam(fname): #给定一个2080*900的图像，取右上角的640*480的图像部分，判断是否为全黑
	im=cv2.imread(fname)
	#print(im.shape)
	#im的格式是：im[startRow:endRow, startCol:endCol]
	#也即是y1:y2,x1:x2的格式
	bname=os.path.basename(fname)
	if bname.find("snapMerge")>-1: #有屏幕截图和摄像头拍照合并一起的图片
		camPic=im[130:430,2080-640+150:2080-80]  #430x640的地方，是摄像头拍的椅子上部的位置
	elif bname.find("snapCam")>-1: #只有摄像头拍照的图片
		camPic=im[130:430,150:600] #(x1,y1):(x2,y2)=(150,130):(600,430)的地方，是大概人头部分的位置
	else:
		camPic=im[130:430,2080-640+150:2080-80]  #430x640的地方，是摄像头拍的椅子上部的位置
	#cv2.imshow("test",camPic)
	#cv2.waitKey(0)
	#print(camPic.shape)
	gray_img = cv2.cvtColor(camPic,cv2.COLOR_BGR2GRAY)
	#获取灰度图矩阵的行数和列数
	r,c = gray_img.shape[:2]
	dark_sum=0;	#偏暗的像素 初始化为0个
	dark_prop=0;	#偏暗像素所占比例初始化为0
	piexs_sum=r*c;	#整个弧度图的像素个数为r*c
	i=0
	avg=0
	sumT=0 #总灰度数值
	for row in gray_img:
		for colum in row:
			sumT+=colum
			if colum<40:	#人为设置的超参数,表示0~39的灰度值为暗
				dark_sum+=1;
	avg=sumT/piexs_sum  #平均灰度数值，0=黑，255为白
	#print("avg=%.2f" % avg)
	#print(gray_img[2,2])
	dark_prop=dark_sum/(piexs_sum);
	#print("dark_sum:"+str(dark_sum));
	#print("dark_prop=dark_sum/piexs_sum:"+str(dark_prop));
	#平均灰度值接近0的，是电脑关屏了
	#平均灰度值是90左右的，是人在电脑前面
	#平均灰度值是118左右的，是人离开了
	return avg

def wf(fname,data,opt='a+'):  #给定data，写到指定文件
	data=str(data)
	print(data)
	f=open(file=fname,mode=opt)
	f.write(data+"\n")
	f.close

def now(ts=None): #返回当前日期
	 return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
	
if __name__=='__main__'	:
	snapDir='g:\\Stanley\\snap\\20200406'
	snapDir='x:\\snap'
	stime=time.time()
	fnames=[]
	print(now())
	getPicFiles(snapDir,fnames)
	etime1=time.time()
	print(now())
	N=len(fnames)
	print("found %d files in %s,consumed %.2f s" % (N,snapDir,etime1-stime))
	#fnames=['live.png']
	#fnames=['g:\\Stanley\\snap\\snapCam20200404_223837.png']
	for fname in fnames:
		try:
			print("trying to check %s" % fname)
			avg=checkDarkCam(fname)
		except:
			continue
		try:
			wf("check.txt","%s=%.2f" % (fname,avg))
		except:
			pass
		if avg<10:
			try:
				print("try to delete %s" % fname)
				os.unlink(fname)
			except:
				pass
	etime=time.time()
	wf("consumed %.2f" % (etime-stime))