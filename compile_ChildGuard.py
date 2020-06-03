# -*- coding: utf-8 -*-
import os,shutil,sys,re,time
from PyInstaller.__main__ import run
# -F:打包成一个EXE文件 
# -w:不带console输出控制台，window窗体格式 
# --paths：依赖包路径 
# --icon：图标 
# --noupx：不用upx压缩 
# --clean：清理掉临时文件

def getVersion(fname): #给定脚本名字，取得里面的VERSION信息
	with open(fname,'r',encoding='utf-8') as f:
		while True:
			line=f.readline() 
			if not line:
				break
			match=re.findall(r'VERSION=(.*)',line)
			if match:
				version=match[0].replace("\'",'').replace('"','')
				break
		f.close()
		return version

def gen_ver_file(version):
	res_file='ver.txt'
	ss="""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=%s,
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'by sunbeat'),
        StringStruct(u'FileDescription', u'ChildGuard to monitor and control Child PC'),
        StringStruct(u'InternalName', u'ChildGuard.exe'),
        StringStruct(u'LegalCopyright', u'by sunbeat. All rights reserved.'),
        StringStruct(u'OriginalFilename', u'ChildGuard.exe'),
        StringStruct(u'ProductName', u'ChildGuard Server Daemon'),
        StringStruct(u'ProductVersion', '%s')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
	version=version.replace('v','')
	filevers=version.split('.')
	filevers[-1]='0'  #版本的最后一位似乎用20200513的数字不行，自动给变成1516的数了，因此这里直接赋值0好了
	str_filevers="(%s)" % ','.join(filevers)
	ss=ss % (str_filevers,version)
	f=open(res_file,'w')
	f.write(ss)
	f.close()
	return res_file		
if __name__ == '__main__':
	scriptName='ChildGuard.py'
	srcName=os.path.splitext(scriptName)[0]+'.exe'
	version=getVersion(scriptName)
	res_file=gen_ver_file(version)
	tgtName=os.path.splitext(scriptName)[0]+'_'+version+'.exe'
	opts = ['-F',
			'--icon', 'guard.ico', 
			'--add-binary',"readme.txt;src",
			'--add-binary',"dist/WatchDog.exe;src",
			'--version-file',res_file,
#			'-n',tgtName, #加这个或者下面的参数直接给新名字的话，会莫名其妙造成文件从33MB突进到68MB
#			'--name',tgtName,
			scriptName
			]
	cmds="pyinstaller "+" ".join(opts)
	print(cmds)
	#os.system(cmds)
	run(opts)
	#shutil.move("dist/"+srcName,"dist/"+tgtName)