#!/usr/bin/python3
import xmlrpc.client
import pickle,hashlib
import os,sys,re,json,time
import inspect
import socket

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
	
#调用RPC
def main():
	global cfg
	cfg_file='ChildControl.ini'
	cfg=load_cfg(cfg_file)
	print("cfg=%s" % json.dumps(cfg,indent=2))
	socket.setdefaulttimeout(cfg['timeout']) #每次socket连接，默认最长多久超时
	resUri=selectHost(cfg['hosts'])
	uri='http://%s:%s' % (resUri[0],resUri[1])
	s = xmlrpc.client.ServerProxy(uri)
	while True:
		print("%s>" % uri,flush=True,end='')
		#cmdline=input()
		cmdline=''
		while True:
			c=sys.stdin.read(1)
			if c=="\n":
				break
			if c=="\4":
				sys.exit()
			cmdline+=c
		if cmdline.lower()=='exit' or cmdline.lower()=='quit':
			sys.exit()
		if cmdline=="":
			print()
			continue
		if cmdline.lower().find('uri=')>-1:
			match=re.findall(r'uri=(\S+\:\d+)',cmdline,re.IGNORECASE)
			uri=str(match[0])
			print(uri)
			if uri.lower().find('http://')>-1:
				pass
			else:
				uri='http://'+uri
			s = xmlrpc.client.ServerProxy(uri)
			continue
		if cmdline.find('(')>-1:
			func=cmdline
			try:
				para=re.findall(r'\((.+)\)',func)[0] 
				para_list=['"%s"' % item for item in para.split(',')] 
				print('para=%s' % para)
				func=func.replace(para,",".join(para_list)) 
				func='s.'+func
			except Exception as e:
				print(e)
		else:
			func='s.'+cmdline+'()'
		print("func=%s" % func)
		try:
			res=eval(func)
			print(str(res).replace("\\n","\n"))
		except Exception as e:
			print(e)


if __name__=='__main__':
	main()
