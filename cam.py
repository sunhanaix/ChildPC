import os,sys,re,json,time
import cv2
from PIL import Image,ImageDraw, ImageFont
import numpy as np
import warnings

##调用笔记本电脑的摄像头，按ESC退出，按空格拍照
warnings.filterwarnings('ignore') #opencv会有些warrning，显示不友好，忽略它

def ts(ts=None):
	 return time.strftime("%Y-%m-%d_%H%M%S", time.localtime(ts))

def getCamera():
	N=5 #默认最多只尝试前N个摄像头
	Cameras=[]
	for i in range(N):
		try:
			ret = cv2.VideoCapture(i).open(i) #取第i个摄像头准备拍照
		except Exception as e:
			continue
		if ret:
			Cameras.append(i)
	return Cameras

def selectCamera():
	cams=getCamera()
	if len(cams) <1:
		print("这台电脑上找不到摄像头!")
		time.sleep(2)
		quit()
	elif len(cams)==1:
		print("本电脑只有一个摄像头，就用它了")
		return cams[0]
	print("这台电脑上有如下摄像头，请选择使用哪一个？")
	for i in cams:
		print("%d). 摄像头%d" % (i,i))
	print("你的选择:",end='')
	ai=input()
	if int(ai) in cams:
		return int(ai)
	else:
		print("无效的输入, 将使用默认值：0")
		time.sleep(1)
		return 0
	 
def getCamPic(capIndex=0):
	desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
	fname=os.path.join(desktop,"照相机抓拍%s.jpg" % ts() )
	#fname="Stanley%s.png" % ts()
	res=''
	cap = cv2.VideoCapture(capIndex) #取第0个摄像头准备拍照
	#https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html#videocapture-get
	#取得当前的分辨率：宽度和高度
	w=cap.get(3)
	h=cap.get(4)
	#print(w,h)
	#设置新的摄像头分辨率：宽度和高度
	#cap.set(cv2.CAP_PROP_AUTOFOCUS, 0) #关闭自动对焦试试
	cap.set(3,1920)
	cap.set(4,1080)
	#txtTitle=u"按ESC键退出，按空格键拍照"
	txtTitle="Pres <ESC> to quit, press <SPACE> to save picture and analyze"
	while True:
		f, img = cap.read()#此刻拍照
		#cv2_im = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		#pil_im = Image.fromarray(cv2_im)
		#draw = ImageDraw.Draw(pil_im) # 括号中为需要打印的canvas，这里就是在图片上直接打印
		#font = ImageFont.truetype("simhei.ttf", 20, encoding='utf-8') # 第一个参数为字体文件路径，第二个为字体大小
		#draw.text((0, 0), txtTitle, (0, 0, 255), font=font) # 第一个参数为打印的坐标，第二个为打印的文本，第三个为字体颜色，第四个为字体
		#cv2_text_im = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)
		#cv2.imshow("Video", cv2_text_im)
		cv2.namedWindow(txtTitle,cv2.WINDOW_NORMAL);
		cv2.imshow(txtTitle, img)
		k=cv2.waitKey(1)
		if k == 27:
			cv2.destroyAllWindows()
			cap.release()
			return None
		elif k==ord(" "):
			#res=cv2.imwrite(fname,img) #直接用imwrite不支持中文path，中文的文件名
			res=cv2.imencode('.jpg',img)[1].tofile(fname)
			print(res)
			cv2.destroyAllWindows()
			break
	cap.release()# 关闭调用的摄像头
	return fname
	

print("正在查看本机有哪些摄像头……")
capIndex=selectCamera()
#capIndex=1
print("正在尝试打开摄像头%d，记得退出时按ESC，拍照按空格键……" % capIndex)
camPic=getCamPic(capIndex)
print(camPic)