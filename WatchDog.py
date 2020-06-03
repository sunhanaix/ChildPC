import os,sys,subprocess,re,json,time
import threading
import win32com.client as win32com
import win32process,win32security
import win32api,win32con
#import ctypes
import pythoncom,win32file
import win32serviceutil ,win32ts,win32profile
import win32service ,psutil
import win32event , winerror
import win32timezone #不import这个，虽然可以编译成exe，但执行时会报错，找这个东西
import servicemanager
import shlex
VERSION='v0.9.2.20200512'


##进程守护程序daemon控制service##
'''
1. 读取配置文件WatchDog.ini
2. 按照指定间隔interval进行轮询，尝试启动cmd指定的命令行
3. 本身作为windows的service服务进行启动运行
'''

app_path=os.path.dirname(os.path.abspath(sys.argv[0]))
cfg_file=os.path.join(app_path,'WatchDog.ini')

def now():
	 return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	 
def mylog(ss,log=app_path+'/WatchDog.log'):
	ss=str(ss)
	print(now()+'  '+ss)
	f=open(log,'a+',encoding='utf8')
	f.write(now()+'  '+ss+"\n")
	f.close()

def get_path():
	return {'app_path':app_path,'cwd':os.getcwd()}

def load_cfg(cfg_file):
	cfg1={'interval':30, #间隔轮询程序是否启动的时间间隔（s）
		'appname':wherePython(), #python程序的位置.
		'cmdline': '"%s" port=8888' % os.path.join(app_path,'ChildGuard.py'),
		'key_word':'port=8888' , #service每个一段时间，检测后台进程，用哪个关键字，来判断进程活着
		'debug':0,   #是否以debug模式启动（会多print一些log）
		}
	cfg2={'interval':30, #间隔轮询程序是否启动的时间间隔（s）
		'appname':os.path.join(app_path,'ChildGuard.exe'), #要启动的程序.
		'cmdline': 'port=8888', 
		'key_word':'port=8888' ,#service每个一段时间，检测后台进程，用哪个关键字，来判断进程活着
		'debug':0,   #是否以debug模式启动（会多print一些log）
		}
	#看下当前目录下是否有.py的源码文件，有的话，优先用这个，否则用.exe的
	if os.path.isfile(os.path.join(app_path,'ChildGuard.py')):
		cfg=cfg1
	else:
		cfg=cfg2
	cfg['cmdline']='"%s" %s' % (cfg['appname'],cfg['cmdline'])
	#要是配置文件不存在，则用默认参数创建一个
	if not os.path.isfile(cfg_file):
		try:
			f=open(cfg_file,'w')
			f.write(json.dumps(cfg,indent=2))
			f.close()
		except Exception as e:
			print(e)
	#要是配置文件存在，尝试载入配置文件，返回其设置的参数值
	try:
		f=open(cfg_file,'r')
		cfg=json.loads(f.read())
		f.close()
	except Exception as e:
		mylog(e)
		mylog('WARRNING: will use default config')
	cfg['cmd']=cfg['cmdline']
	return cfg		

def wherePython(): #在用户环境变量PATH里面遍历，找到第一个python.exe的绝对路径
	for p in os.environ['PATH'].split(';'):
		check_fname=os.path.join(p,'python.exe')
		if os.path.isfile(check_fname):
			return check_fname
	return None

def getPrivs(htoken): #给定某个进程的token，返回其所拥有的权限
	privs = win32security.GetTokenInformation(htoken, win32security.TokenPrivileges)
	res=[]
	for privtuple in privs:
		res.append(win32security.LookupPrivilegeName(None, privtuple[0]))
	return res
	
def CreateProc(appname,cmdline=None):
	global cfg
	#找到winlogon.exe的进程信息，然后复制它的token，再赋权新的token，用新token创建的新进程，就有前台交互权限了
	p=getProcess(caption='winlogon.exe')[0]
	pid=p['pid']
	if cfg['debug']:
		mylog("pid=%d,type=%s" % (pid,type(pid)))
	#通过winlogon.exe的pid打开进程，获得它的句柄
	handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
	#通过winlogon.exe的句柄，获得它的令牌(经测试，admin权限运行的程序，只能用TOKEN_QUERY方式打开，service方式运行的程序，有全部权限)
	token_handle=win32security.OpenProcessToken(handle, win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY |win32con.TOKEN_DUPLICATE)
	if cfg['debug']:
		print("winlogon.exe's handle=%s,token=%s" % (handle,token_handle))
	res=None
	#通过winlogon.exe的令牌，复制一个新令牌(经测试，admin权限运行的程序，权限不足，service方式运行的程序，有全部权限)
	dup_th=win32security.DuplicateTokenEx(token_handle,
			win32security.SecurityImpersonation,
			win32security.TOKEN_ALL_ACCESS,
			win32security.TokenPrimary,
			)
	#通过winlogon.exe的pid，获得它的session id（经测试，admin权限运行的程序，没TCB权限，需要service方式运行的程序，有全部权限）
	curr_session_id = win32ts.ProcessIdToSessionId(pid)
	if cfg['debug']:
		print("dup_th=%s" % dup_th)
	#获得系统默认的程序启动信息（初始化程序所需的，标准输出、桌面选择等信息）
	startup = win32process.STARTUPINFO()
	if cfg['debug']:
		print(startup)
	#下面的这个win32con.CREATE_NEW_CONSOLE权限必须给，要不后面CreateProcessAsUser时看到执行了，然后程序就没了
	priority = win32con.NORMAL_PRIORITY_CLASS | win32con.CREATE_NEW_CONSOLE
	if cfg['debug']:
		mylog("in CreateProc(),appname=%s,cmdline=%s" % (appname,cmdline))
	(hProcess, hThread, dwProcessId, dwThreadId)=(None,None,None,None)
	#通过winlogon.exe的session id获得它的console令牌
	console_user_token = win32ts.WTSQueryUserToken(curr_session_id)
	#通过winlogon.exe的console令牌，获得它的环境profile设置信息
	environment = win32profile.CreateEnvironmentBlock(console_user_token, False)
	#给复制出来的token，绑定对应的session id，使之基于和winlogon.exe一样的会话
	win32security.SetTokenInformation(dup_th, win32security.TokenSessionId, curr_session_id)
	#设置调整权限的flag权限
	flags = win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
	#设置权限1：找到SE_DEBUG_NAME的权限的id，给p1
	p1 = win32security.LookupPrivilegeValue(None, win32con.SE_DEBUG_NAME)
	newPrivileges = [(p1, win32con.SE_PRIVILEGE_ENABLED)]
	#把复制出来的winlogon.exe的token，增加新权限（也即是SE_DEBUG_NAME权限）
	win32security.AdjustTokenPrivileges(dup_th, False, newPrivileges)
	if cfg['debug']:
		privs=getPrivs(dup_th)
		mylog("privs=%s" % "\n".join(privs))
	#下面准备启动程序需要的重定向的标准输出和标准错误输出的文件句柄，但目前似乎没有重定向成功:(
	fh_stdout = win32file.CreateFile(os.path.join(app_path,"watchdog.stdout"), win32file.GENERIC_WRITE,
		win32file.FILE_SHARE_READ|win32file.FILE_SHARE_WRITE, None,
		win32file.OPEN_ALWAYS, win32file.FILE_FLAG_SEQUENTIAL_SCAN , 0)
	fh_stderr = win32file.CreateFile(os.path.join(app_path,"watchdog.stderr"), win32file.GENERIC_WRITE,
		win32file.FILE_SHARE_READ|win32file.FILE_SHARE_WRITE, None,
		win32file.OPEN_ALWAYS, win32file.FILE_FLAG_SEQUENTIAL_SCAN , 0)
	startup.hStdOutput = fh_stdout
	startup.hStdError = fh_stderr
	
	#下面开始尝试用复制好的token：dup_th，并也给了足够的权限的token，然后来启动指定程序
	try:
		 (hProcess, hThread, dwProcessId, dwThreadId)=win32process.CreateProcessAsUser(dup_th, appname, cmdline, None, None, True, priority, None, None, startup)
	except Exception as e:
		mylog("in CreateProc(),return False,ERROR:%s" % str(e))
		return False
	mylog("%s,%s,%s,%s" % (hProcess, hThread, dwProcessId, dwThreadId))
	if dwProcessId==None:
		#创建进程失败
		mylog("Can not get dwProcessId from win32process.CreateProcessAsUser()")
		return False
	try:
		time.sleep(2)
		mylog("dwProcessId=%s" % dwProcessId)
		process = psutil.Process(dwProcessId)
	except Exception as e:
		mylog("CreateProc(),try to psutil.Process(),ERROR:%s" % str(e))
	mylog("process:%s" % process)
	return_code=None
	try:
		return_code = process.wait(10)
	except Exception as e:
		mylog("CreateProc(),try to process.wait(),ERROR:%s" % str(e))
		mylog("Maybe Child process Running already , but not quit")
	mylog("CreateProc return code=%s" % str(return_code))


def getProcess(pid=None,caption=None):
	#获得当前后台所有程序，或给定pid的程序
	#取进程 id，失败返回 None
	global cfg
	pythoncom.CoInitialize() #默认win32com是非线程安全的，要在线程中安全使用，要在开始时CoInitialize，在结束时CoUninitialize
	if cfg['debug']:
		mylog("in getProcess(),pid=%s" % str(pid))
	wmi = win32com.GetObject('winmgmts:')
	if not pid==None:
		wql="SELECT * FROM Win32_Process where ProcessId=%s" % str(pid)
	elif not caption==None: #WQL是忽略大小写的，可以不用再转小写了
		wql="SELECT * FROM Win32_Process where Caption='%s'" % caption
	else:
		wql="SELECT * FROM Win32_Process "
	procs = wmi.ExecQuery(wql)
	if cfg['debug']:
		mylog("wql=%s" % wql)
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

def check_alive(cfg_keyword): #给定配置文件中的key_word字符串，判断是否已经在运行了
	procs=getProcess()
	#print(procs)
	for proc in procs:
		if not proc['name'] or not proc['cmd']:
			continue
		if proc['name'].lower()==cfg_keyword.lower():
			return True
		#有可能是py.exe，也可能是python.exe届时.py脚本
		elif proc['cmd'].lower().find(cfg_keyword.lower()) >-1:
			return True
		else:
			#print("cfg_keyword=%s,proc_name=%s" % (cfg_keyword,proc['name']))
			pass
	return False	
			
def main():
	#username=psutil.Process().username()
	pid=os.getpid()
	mylog("trying to run WatchDog Version=%s,pid=%s" % (VERSION,pid))
	global cfg
	cfg=load_cfg(cfg_file)
	mylog("cfg=%s" % json.dumps(cfg,indent=2,ensure_ascii=False))
	while True:
		users=psutil.users()
		num_users=len(users)
		if cfg['debug']:
			mylog("users=%s" % (str(users)))
		if num_users<1: #要是用户还没有登录windows，num_users=0，则继续等待，直到用户logon
			time.sleep(cfg['interval'])
			continue
		#检查是否存在对应的命令行程序
		if check_alive(cfg['key_word']):
			mylog("key_word=%s is alive\n" % cfg['key_word'])
			pass
		else: #如果没有启动，则拉它起来
			mylog("trying to start cmd=%s\n" % cfg['cmd'])
			try:
				CreateProc(cfg['appname'],cfg['cmdline'])
			except Exception as e:
				mylog("WatchDog trying to CreateProc():%s" % str(e))
		time.sleep(cfg['interval'])
	
class WatchDog(win32serviceutil.ServiceFramework): 
	#服务名叫WatchDogC，以避免和系统可能存在的WatchDog服务冲突
	_svc_name_ = "WatchDogC"
	_svc_display_name_ = "WatchDogC"
	_svc_description_="WatchDogC for ChildGuard app to monitor it"
	def __init__(self, args): 
		win32serviceutil.ServiceFramework.__init__(self, args) 
		self.stop_event  = win32event.CreateEvent(None, 0, 0, None) 
		self.run=True

	def SvcDoRun(self): 
		# 等待服务被停止 
		main()

	def SvcStop(self): 
		# 先告诉SCM停止这个过程 
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING) 
		# 设置事件 
		win32event.SetEvent(self.stop_event)
		self.ReportServiceStatus(win32service.SERVICE_STOPPED)
		self.run = False

if __name__=='__main__': 
	if len(sys.argv) > 1 and sys.argv[1]=='nohide':
		#如果执行WatchDog.exe nohide，则执行main()，不隐藏起来
		main()
	elif len(sys.argv)==1: #如果只是执行程序WatchDog.exe情况
		try:
			evtsrc_dll = os.path.abspath(servicemanager.__file__)
			servicemanager.PrepareToHostSingle(WatchDog)
			servicemanager.Initialize('WatchDogC', evtsrc_dll)
			servicemanager.StartServiceCtrlDispatcher()
		except win32service.error as details:
			mylog("except:%s" % str(details))
			win32serviceutil.usage()
	else: #如果执行WatchDog.exe install等命令的情况
		win32serviceutil.HandleCommandLine(WatchDog)
		#获得dos console句柄方式隐藏dos窗口，可以这个daemon正常运行
		#直接改.py为.pyw虽然可以运行，但client访问时，总是报http.client.BadStatusLine
		#whnd = ctypes.windll.kernel32.GetConsoleWindow() 
			#if whnd != 0:
			#	ctypes.windll.user32.ShowWindow(whnd, 0)
			#	ctypes.windll.kernel32.CloseHandle(whnd)
		