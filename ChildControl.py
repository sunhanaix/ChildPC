#!/usr/bin/python3
import xmlrpc.client
import os,sys,re,json,time,socket
import ctypes
VERSION='0.9.0.20200423'

def wf(fname,data,opt='w'): 
	f=open(file=fname,mode=opt)
	f.write(data)
	f.close
	
def now():
	 return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def check_keywords(ss,keywords):
	#在ss字符串中，找是否含有数组keywords里面指定的关键字，任意找到一个，则返回True，都没找到返回False
	for keyword in keywords:
		if ss.lower().find(keyword.lower())>-1:
			return True
	return False
	
def load_cfg(cfg_file): 	#载入配置文件，设置相关的参数
	#下面是默认参数配置
	res={'hosts':['10.10.20.59:8888','10.10.20.59:7777'],  #默认要监控的主机列表
		'interval':30,  #默认轮询间隔秒数
		'timeout':30, #设置socket默认超时，从而影响xmlrpc.client的连接超时
		'black_list':['360game.exe','qqlive.exe'], #进程黑名单，强制全部小写比对
		'browsers':['chrome.exe', #谷歌chrome浏览器
					'360se.exe', #360浏览器
					'iexplore.exe',  #老ie浏览器
					'MicrosoftEdge.exe', #微软Edge
					'MicrosoftEdgeCP.exe', #微软Edge
					'ApplicationFrameHost.exe', #微软Edge
					'firefox.exe',  #火狐浏览器
					'sogouexplorer.exe',  #搜狗浏览器
					'qqbrowser.exe',  #qq浏览器
					'wechatweb.exe'   #微信内置浏览器
					], #哪些浏览器被关注，强制小写比对
		'browser_keywords':['游戏','game'], #浏览器敏感词识别
		'do_kill':1, #满足black_list、condition_browser相关条件，是否kill
		'seconds':10, #默认每次录音多少秒
		'allow_periods':[{'p':'12:15-13:30','w':'1-5'}, #周一至周五，12:15-13:30可以玩，不kill
									{'p':'12:15-14:30','w':'6'},  #周六，12:15-14:30可以玩，不kill
									{'p':'17:45-19:30','w':'6,7'}, #周六日，17:45-19:30可以玩，不kill
									{'p':'12:00-13:20','w':'7'}, #周日，12:00-13:20可以玩，不kill
			], #哪些时间段可以
		'snap_dir':'snap/',  #抓取的截图和录音，放置的目录位置
		'hide':0, #是否隐藏自己
			}
	#要是配置文件不存在，则新建一个配置文件，用默认参数值
	if not os.path.isfile(cfg_file):
		try:
			f=open(cfg_file,'w')
			f.write(json.dumps(res,indent=2))
			f.close()
		except Exception as e:
			print(e)
		return res
	#要是配置文件存在，尝试载入配置文件，返回其设置的参数值
	try:
		f=open(cfg_file,'r')
		res=json.loads(f.read())
		f.close()
	except Exception as e:
		print("ERROR:"+str(e))
		print('will use default config')
	return res

def check_cfg_mtime(cfg_file): #检查cfg_file的时间戳，判断是否被修改过，返回修改的时间（epoch）
	mtime=os.stat(cfg_file).st_mtime
	return int(mtime)

def get_weeks_fr_str(w):  #给定周几的字符串定义，类似w='1-3,5,6-7' ，返回一个含有所有周几数组（int类型）
	week=[]
	if w.find(',')>-1:
		for d in w.split(','):
			if d.find('-')>-1:
				(d1,d2)=d.split('-')
				d1=int(d1)
				d2=int(d2)
				for i in range(d1,d2+1):
					week.append(i)
			else:
				week.append(int(d))
	elif w.find('-')>-1:
		(d1,d2)=w.split('-')
		d1=int(d1)
		d2=int(d2)		
		for i in range(d1,d2+1):
			week.append(i)
	else:
		week.append(int(w))
	return week

def get_hour_minute(p) : #给定起止时间，类似p='11:50-12:30'，返回起始的hour、minute
	(stime,etime)=p.split('-')
	(sh,sm)=stime.split(':')
	(eh,em)=etime.split(':')
	shour=int(sh)
	sminute=int(sm)
	ehour=int(eh)
	eminute=int(em)
	return (shour,sminute,ehour,eminute)

def check_now_is_allow(allow_periods): #检测当前时间，是否是在允许的范围内
	if not allow_periods or type(allow_periods)!=list:
		return False
	current=time.localtime()
	for period in allow_periods:
		weeks=get_weeks_fr_str(period['w'])
		(shour,sminute,ehour,eminute)=get_hour_minute(period['p'])
		current_time=current.tm_hour*60+current.tm_min #把12:45这样的时间，换成12*60+45这样的数值，用它比较
		stime=shour*60+sminute
		etime=ehour*60+eminute
		if current.tm_wday+1 in weeks and current_time >=stime and current_time <=etime:
			return True
	return False
		
def mylog(ss,log='ChildControl.log'):
	ss=str(ss)
	print(now()+'  '+ss)
	f=open(log,'a+',encoding='utf8')
	f.write(now()+'  '+ss+"\n")
	f.close()	 

def portPing(host,port): #检测主机对应的端口是否活着
	port=int(port)
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print("checking host=%s,port=%s" % (host,port))
	s.settimeout(1)
	try:
		s.connect((host,port))
	except:
		return False
	return True
	
def selectHost(uriList): #给定一组host:port的列表，返回第一个能连通的
	for uri in uriList:
		(host,port)=uri.split(':')
		if portPing(host,port):
			return (host,port)

def hideSelf():
	#获得dos console句柄方式隐藏dos窗口，可以这个daemon正常运行
	#直接改.py为.pyw虽然可以运行，但client访问时，总是报http.client.BadStatusLine
	whnd = ctypes.windll.kernel32.GetConsoleWindow() 
	if whnd != 0:
		ctypes.windll.user32.ShowWindow(whnd, 0)
		ctypes.windll.kernel32.CloseHandle(whnd)	

def tts(msg,cfg_file='ChildControl.ini'):
	cfg=load_cfg(cfg_file)
	last_mtime=check_cfg_mtime(cfg_file)
	mylog("cfg=%s" % json.dumps(cfg,indent=2))	
	socket.setdefaulttimeout(cfg['timeout']) #每次socket连接，默认最长多久超时		
	resUri=selectHost(cfg['hosts'])
	if resUri:
		uri='http://%s:%s' % (resUri[0],resUri[1])
		mylog("try to %s" % uri)
		s = xmlrpc.client.ServerProxy(uri)
		s.tts(msg)
		
def main():
	#设置尝试往指定服务器连接
	global cfg
	cfg_file='ChildControl.ini'
	cfg=load_cfg(cfg_file)
	last_mtime=check_cfg_mtime(cfg_file)
	mylog("cfg=%s" % json.dumps(cfg,indent=2))
	if cfg['hide']: #要是设置了hide参数，则隐藏自己
		try:
			hideSelf()
		except Exception as e:
			print(e)
			sys.exit()
	socket.setdefaulttimeout(cfg['timeout']) #每次socket连接，默认最长多久超时
	while True: #死循环，每次获得当前获得进程的名字，如果进程名字含有关键字，做kill等动作
		mtime=check_cfg_mtime(cfg_file)
		if mtime > last_mtime:
			last_mtime=mtime
			cfg=load_cfg(cfg_file)
			mylog("cfg=%s" % json.dumps(cfg,indent=2))
		resUri=selectHost(cfg['hosts'])
		if resUri:
			uri='http://%s:%s' % (resUri[0],resUri[1])
			mylog("try to %s" % uri)
			s = xmlrpc.client.ServerProxy(uri)
		else:
			mylog("all in cfg['hosts'] can not to conenct!:%s" % str(cfg['hosts']))
			time.sleep(cfg['interval'])
			continue
		try:
			res=s.getActiveProcName()
		except Exception as e:
			mylog(str(e))
			res=False
		if not res:
			mylog("not get Active Proc name")
			res=False
		if res: #要是取得了当前进程信息的话，则对结果进行匹配，是否进行杀进程
			mylog("caption=%s pid=%s text=%s name=%s cmd=%s" % (res['caption'],res['pid'],res['text'],res['name'],res['cmd']))
			#打开了浏览器，网页标题有列表的关键字的话：
			condition_browser=(res['caption'].lower() in [item.lower() for item in cfg['browsers'] ] and check_keywords(res['text'],cfg['browser_keywords']) )
			#要是当前运行进程的名字在黑名单中，则进行下面的kill动作
			if (res['caption'].lower() in cfg['black_list'] or condition_browser) and cfg['do_kill'] and not check_now_is_allow(cfg['allow_periods']):
				mylog("Found not allow, kill it")
				pid=res['pid']
				try:
					s.killProcess(pid)
				except Exception as e:
					mylog("kill process pid=%s failed" % pid )
					mylog(str(e))
		if cfg['black_list'] and cfg['do_kill'] and not check_now_is_allow(cfg['allow_periods']): #要是存在黑名单，并且设置了要do_kill，那么找到它们，杀掉它们
				mylog("searching proc in black_list")
				black_procs=s.getProcess(0,cfg['black_list'])
				mylog(str(black_procs))
				if black_procs:
					mylog("Found %s,not allow, kill it" % str(black_procs))
					for black_proc in black_procs:
						try:
							s.killProcess(black_proc['pid'])
						except Exception as e:
							mylog(str(e))
			#注意的是，如果孩子pc上的ChildGuard运行在后台，调用get_hwnd_by_pids的GetWindowText是拿不到相关信息的
			#因此，这种情况下的浏览器标题信息抓不到，就不做处理了。
		#下面尝试抓屏和抓摄像头操作，并把图片拿回来。					
		try:
			os.mkdir(cfg['snap_dir'])
		except:
			pass
		try:
			res=s.snapMerge()
			fname=res['fname']
			data=res['data']
			wf(os.path.join(cfg['snap_dir'],fname),data.data,'wb')
			mylog("snapScreen: %s" % fname)
		except Exception as e:
			mylog("in snapScreen() "+str(e))
		try:
			res=s.snapAudio(cfg['seconds'])
			fname=res['fname']
			data=res['data']
			wf(os.path.join(cfg['snap_dir'],fname),data.data,'wb')
			mylog("snapAudio: %s for %d seconds" % (fname,cfg['seconds']))
		except Exception as e:
			mylog("in snapAudio(): "+str(e))
						
		#设置interval s执行一次大轮询
		time.sleep(cfg['interval'])

if __name__=='__main__':
	#抓取的屏幕和摄像头图片，放置当前目录的snap下面
	main()
