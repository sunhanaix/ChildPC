import xmlrpc.client
import hashlib,time,socket
import os,sys,re,json
#################################################
#本程序用于手工更新目标机器上的ChildGuard.py脚本#
#################################################
def rf(fname):
	f=open(fname,'rb')
	ss=f.read()
	f.close()
	return ss

def wf(fname,data,opt='w'): 
	f=open(file=fname,mode=opt)
	f.write(data)
	f.close

def md5sum(fname):
	f=open(fname,'rb')
	m=hashlib.md5(f.read())
	f.close()
	return m.hexdigest()

def ts(ts=None):
	 return time.strftime("%Y%m%d_%H%M%S", time.localtime(ts))	

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
				 
def main():
	global cfg
	cfg_file='ChildControl.ini'
	cfg=load_cfg(cfg_file)
	print("cfg=%s" % json.dumps(cfg,indent=2))
	socket.setdefaulttimeout(cfg['timeout']) #每次socket连接，默认最长多久超时
	resUri=selectHost(cfg['hosts'])
	if resUri:
		uri='http://%s:%s' % (resUri[0],resUri[1])
		print("try to %s" % uri)
		s = xmlrpc.client.ServerProxy(uri)
	else:
		print("all in cfg['hosts'] can not to conenct!:%s" % str(cfg['hosts']))
		sys.exit(1)
	app_path=s.get_path()['app_path']
	fnames=['ChildGuard.py','MyTTS.py']
	remote_fnames=[]
	for fname in fnames:
		ss=rf(fname)
		local_md5=md5sum(fname)
		data=xmlrpc.client.Binary(ss)
		remote_fname=app_path+'\\'+fname+ts()
		res=s.wf(remote_fname,data,'wb')
		print("remote:%s,local:%s,lmd5=%s,rmd5=%s" % (remote_fname,fname,local_md5,res))
		cmdline="copy /y %s %s.org" % (app_path+"\\"+fname,app_path+"\\"+fname)
		print(cmdline)
		res=s.my_exec(cmdline)
		print("stdout=%s\nsterr=%s" % (res['stdout'],res['stderr']) )
		cmdline="copy /y %s %s" % (remote_fname,app_path+"\\"+fname)
		print(cmdline)
		res=s.my_exec(cmdline)
		print("stdout=%s\nsterr=%s" % (res['stdout'],res['stderr']) )
		remote_fnames.append(remote_fname)
	cmdline="dir %s %s" % (" ".join([app_path+"\\"+item for item in fnames]),",".join(remote_fnames)) 
	print(cmdline)
	res=s.my_exec(cmdline)
	print("stdout=%s\nsterr=%s" % (res['stdout'],res['stderr']) )
	cmdline="findstr VERSION %s\\*.py" % app_path
	print(cmdline)
	res=s.my_exec(cmdline)
	print("stdout=%s\nsterr=%s" % (res['stdout'],res['stderr']) )
	
	
if __name__=='__main__':
	main()