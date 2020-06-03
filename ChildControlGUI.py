import os,sys,shutil,json,time,re
import ctypes
from PyQt5.QtWidgets import QMessageBox,QMainWindow,QApplication,QFileDialog,QMenu,QAction,QGraphicsPixmapItem,QGraphicsScene,QTextBrowser
from PyQt5.QtGui import QIcon,QIntValidator,QTextCursor,QCursor,QColor,QPixmap
from PyQt5.QtCore import Qt,QVariant,QThread,pyqtSignal,QStringListModel,QPoint,QModelIndex,QItemSelectionModel,QAbstractTableModel,QRect,QTimer
from functools import partial
from ControlMenu_ui import Ui_MainWindow
import winreg,win32gui
import ChildControl
VERSION='v0.9.0.20200519'

app_path=os.path.dirname(os.path.abspath(sys.argv[0]))
cfg_file=os.path.join(app_path,'ChildControl.ini')
log_file=os.path.join(app_path,'ChildControl.log')
global cfg,lstSelect
cfg={}  #全局变量，存放配置信息
lstSelect={}  #全局变量，存放用于标记选择了那个QlistView里面的那个Item
def hideSelf(w):
	#获得dos console句柄方式隐藏dos窗口，这个daemon可以正常运行
	#直接改.py为.pyw虽然可以运行，但client访问时，总是报http.client.BadStatusLine
	whnd = ctypes.windll.kernel32.GetConsoleWindow() 
	if whnd != 0:
		ctypes.windll.user32.ShowWindow(whnd, 0)
		ctypes.windll.kernel32.CloseHandle(whnd)
	#w.MainWindow.setVisible(False)
	w.hide()
def log_pos(log_file): #获得当前log文件指针的位置
	try:
		f=open(log_file,'r')
		f.seek(0,2)
		n=f.tell()
		f.close()
	except Exception as e:
		n=0
	return n
def read_fr_pos(log_file,pos=0): #从给定指针位置开始读取，读取到末尾处
	try:
		f=open(log_file,'r',encoding='utf8')
		f.seek(pos)
		ss=f.read()
		f.close()
	except Exception as e:
		ss=''
	return ss
def get_files(): #处理exe当前运行程序的路径（%tmp%下的某个路径）
	if getattr(sys, 'frozen', False):
		#要是运行在pyInstaller环境中，sys的frozen属性会被标记为True，解压的临时路径通过sys._MEIPASS来获得
		app_path = sys._MEIPASS
		app_path=app_path+"/"+"src"
		icon_file=app_path+"/"+'c.ico'
		QRCodePic_file=app_path+"/"+'QRCode.jpg'
	else:
		cdir=os.path.dirname(sys.argv[0])
		icon_file=cdir+'/'+'c.ico'
		QRCodePic_file=cdir+"/"+'QRCode.jpg'
	return icon_file,QRCodePic_file

def checkIfAutoStart(name='ChildControlGui'): #给定名字，检查是否在自动启动项里面
	key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
		r"Software\Microsoft\Windows\CurrentVersion\Run")
	try:
		value,type=winreg.QueryValueEx(key, name)
		print(name,value,type)
	except Exception as e:
		return False
	return True

def setAutoStart(name='ChildControlGui'): #把sys.argv[0]内容加双引号，然后添加到自动启动项里面
	#默认OpenKey用KEY_READ权限打开，查询value时是够用；但这里面要赋值，添加项目，就不够用了
	key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
		r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_ALL_ACCESS)
	try:
		print(sys.argv[0])
		res=winreg.SetValueEx(key,name,None,winreg.REG_SZ,'"%s"' % os.path.abspath(sys.argv[0]))
		print('res=',res)
	except Exception as e:
		print('ChildControlGui:',e)
		return False
	return True

def delAutoStart(name='ChildControlGui'): #给定名字，删除自动启动项目
	#默认OpenKey用KEY_READ权限打开，查询value时是够用；但这里面要赋值，添加项目，就不够用了
	key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
		r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_ALL_ACCESS)
	try:
		print(sys.argv[0])
		res=winreg.DeleteValue(key,name)
		print('res=',res)
	except Exception as e:
		print('ChildControlGui:',e)
		return False
	return True

class RunControl(QThread)	:
	def __init__(self, parent=None):
		super(RunControl, self).__init__(parent)
		self.running=False
		self.num=0
	def __del__(self)	:
		self.running=False
		self.wait()
	def run(self):
		if not self.running:
			self.running=True
			ChildControl.main()
		else: #已经在运行状态了
			pass
			
class MyTableModel(QAbstractTableModel): #实例化的QAbstractTableModel方法，用于被QTableView调用
	def __init__(self, datain, headerdata, parent=None, *args):
		print('datain=',datain,'headerdata=',headerdata,'parent=',parent,'args=',args)
		QAbstractTableModel.__init__(self, parent) 
		self.arraydata = datain  #存放QTableView里面二维表数据数组
		self.headerdata = headerdata  #存放QTableView里面的表头标题
		self.mdlName=args[0]
		self.handle=args[1]
		self.colorCells=[]  #存放[row,col]格式的二维数组，标记哪些单元格需要颜色上颜色
	def rowCount(self, parent): 
		return len(self.arraydata) 
	def columnCount(self, parent):
		return len(self.arraydata[0]) 
	def data(self, index, role=Qt.DisplayRole):  # 必须实现的接口方法，供视图调用，以获取用以显示的数据
		if (not index.isValid() or not (0 <= index.row() < len(self.arraydata))):  # 无效的数据请求
			return None 
		row,col = index.row(),index.column()
		data=self.arraydata[row]
		if role == Qt.DisplayRole or role==Qt.EditRole: #在显示状态，和在编辑状态，都显示原值
			#如果不单独制定EditRole的时候也返回原值，默认会clear掉当前cell的内容
			item = data[col]
			return item
		if role==Qt.ForegroundRole and [row,col] in self.colorCells: #判断是否显示前景色，并且当前单元格是需要上色的话
			return QColor(0,255,0)
		return None
	def headerData(self, col, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return QVariant(self.headerdata[col])
		return QVariant()
	def flags(self, index): # 必须实现的接口方法，不实现，则View中数据不可编辑（双击没反应）
		if not index.isValid():
			return Qt.ItemIsEnabled
		res_flags = super(self.__class__,self).flags(index)
		res_flags |= Qt.ItemIsEditable
		res_flags |= Qt.ItemIsSelectable
		res_flags |= Qt.ItemIsEnabled
		res_flags |= Qt.ItemIsDragEnabled
		res_flags |= Qt.ItemIsDropEnabled
		return res_flags
	def setData(self,index,value,role=Qt.EditRole): # 以下为编辑功能所必须实现的方法
		# 编辑后更新模型中的数据 View中编辑后，View会调用这个方法修改Model中的数据
		print(self.mdlName)
		if index.isValid() and 0 <= index.row() < len(self.arraydata) and value:
			col = index.column()
			print("in setData(),col=",col)
			if 0 <= col < len(self.headerdata):
				self.beginResetModel()
				org_value=self.arraydata[index.row()][col]
				if self.mdlName=='mdlHosts' and col==0:  #要是主机列表的第1列情况（主机地址）
					if not re.findall(r'^[a-zA-Z0-9\._\-]+$',value):
						self.handle.msg('主机地址："%s"看起来不是一个有效的主机名或者ip地址，有效的入："127.0.0.1",请重新填写' % value,"ERROR")
						return False
				if self.mdlName=='mdlHosts' and col==1:  #要是主机列表的第2列情况（端口）
					if not re.findall(r'^[1-9][0-9]+$',value):
						self.handle.msg('端口："%s"看起来不是一个有效的端口，有效的如："8888"，请重新填写' % value,"ERROR")
						return False
				if self.mdlName=='mdlPeriods' and col==0: #要是时间管控时段的第1列情况（周几）
					if not (re.findall(r'^[1-7]{1}$',value) or re.findall(r'^[1-7]{1}[,，-]{1}[1-7]{1}$',value) ):
						self.handle.msg('周几："%s"看起来不是一个有效的星期（1-7），请重新填写' % value,"ERROR")
						return False
					value=value.replace('，',',')
				if self.mdlName=='mdlPeriods' and col==1: #要是时间管控时段的第2列情况（时间段）
					print("mldName=%s,value=%s,col=%s" % (self.mdlName,value,col))
					if not re.findall(r'^\d+[:：]\d+\-\d+[:：]\d+$',value):
						self.handle.msg('允许时间："%s"看起来不是一个有效时间范围，有效的如："7:00-8:00"，请重新填写' % value,"ERROR")
						return False				
					print("value=%s" % value)
					value=value.replace("：",':')
					print("value=%s" % value)
				self.arraydata[index.row()][col] = value
				self.dirty = True
				self.endResetModel()
				if value !=org_value: #要是新传进来的数值和之前不同，认为是个新数值，则标记它颜色
					self.colorCells.append([index.row(),col])
				return True
		return False
	def stringList(self):
		return self.arraydata
	def setStringList(self,arrayData):
		#对其内数据进行修改前，要先beginResetModel，修改后，要endResetModel，否则QTableView里面表格刷新有问题
		self.beginResetModel()
		self.arraydata=arrayData
		self.dirty = True
		self.endResetModel()
		
		
class pkgWindow(Ui_MainWindow,QMainWindow): #封装designer做好的Ui_MainWindow内容到一个标准类中
	def __init__(self,parent=None):
		super(pkgWindow,self).__init__()
		self.setupUi(self)
		self.setAcceptDrops(True) #允许拖文件到这个QMainWindow上
		self.setWindowTitle('管控孩子电脑 '+VERSION)
		self.setWindowIcon(QIcon(get_files()[0]))
		self.btQuit.clicked.connect(self.Quit)
		self.btUpdate.clicked.connect(partial(self.UpdateCfg,True))
		self.btCfgReset.clicked.connect(self.loadCfgToGUI)
		self.btBrowse.clicked.connect(self.Browse)
		self.btRun.clicked.connect(self.Run)
		self.btHide.clicked.connect(self.Hide)
		self.btTTS.clicked.connect(self.TTS)
		self.radKill.clicked.connect(self.radioKill)
		self.radNotKill.clicked.connect(self.radioNotKill)
		self.ckAutoStart.clicked.connect(self.DealAutoStart)
		cfg=self.loadCfgToGUI()
		self.mnAbout.triggered.connect(self.MenuAbout)
		self.myrun=RunControl()
		self.pos=log_pos(log_file) #记录下当前log文件的指针位置
		#设置一个计时器，每200ms触发一次，检查log是否有更新，把内容同步到图形界面里面
		self.timerFlushStatus= QTimer(self)
		self.timerFlushStatus.start(200) #每200ms触发一次
		self.timerFlushStatus.timeout.connect(self.FlushStatus) 
		if checkIfAutoStart():  #要是检测到设置了开机就自动启动，那么初始化界面时，就执行监控程序
			self.myrun.start()
			self.btRun.setText("停止")
			if cfg['hide']:
				Hide(self)
	def loadCfgToGUI(self):
		global cfg
		cfg=ChildControl.load_cfg(cfg_file)
		self.txtInterval.setProperty("value", cfg['interval'])
		self.txtTimeout.setProperty("value", cfg['timeout'])
		self.txtSeconds.setProperty("value", cfg['seconds'])
		if cfg['do_kill']:
			self.radKill.setChecked(True)
			self.radNotKill.setChecked(False)
		else:
			self.radKill.setChecked(False)
			self.radNotKill.setChecked(True)
		if checkIfAutoStart():
			self.ckAutoStart.setChecked(True)
		else:
			self.ckAutoStart.setChecked(False)
		self.txtSnapdir.setText(cfg['snap_dir'])
		self.mdlHosts=MyTableModel([a.split(':') for a in cfg['hosts']], ['主机地址','端口'],None,'mdlHosts',self) 
		self.lstHosts.setModel(self.mdlHosts)
		self.lstHosts.setContextMenuPolicy(3) 
		self.lstHosts.customContextMenuRequested[QPoint].connect(partial(self.lstRightMenu,'mdlHosts'))
		self.lstHosts.clicked.connect(partial(self.ItemSelect,'mdlHosts'))
		self.mdlBlacklist=QStringListModel()
		self.mdlBlacklist.setStringList(cfg['black_list'])
		self.lstBlacklist.setModel(self.mdlBlacklist)
		self.lstBlacklist.setContextMenuPolicy(3) 
		self.lstBlacklist.customContextMenuRequested[QPoint].connect(partial(self.lstRightMenu,'mdlBlacklist'))
		self.lstBlacklist.clicked.connect(partial(self.ItemSelect,'mdlBlacklist'))
		self.mdlKeywords=QStringListModel()
		self.mdlKeywords.setStringList(cfg['browser_keywords'])
		self.lstKeywords.setModel(self.mdlKeywords)
		self.lstKeywords.setContextMenuPolicy(3) 
		self.lstKeywords.customContextMenuRequested[QPoint].connect(partial(self.lstRightMenu,'mdlKeywords'))
		self.lstKeywords.clicked.connect(partial(self.ItemSelect,'mdlKeywords'))
		self.mdlBrowsers=QStringListModel()
		self.mdlBrowsers.setStringList(cfg['browsers'])
		self.lstBrowsers.setModel(self.mdlBrowsers)
		self.lstBrowsers.setContextMenuPolicy(3) 
		self.lstBrowsers.customContextMenuRequested[QPoint].connect(partial(self.lstRightMenu,'mdlBrowsers'))		
		self.lstBrowsers.clicked.connect(partial(self.ItemSelect,'mdlBrowsers'))
		self.mdlPeriods=MyTableModel([ [a['w'],a['p']] for a in cfg['allow_periods'] ],['允许周几','允许时间'],None,'mdlPeriods',self)
		all_periods=[]
		#self.mdlPeriods.setStringList(["允许时间：%s，允许周几：%s" % (item['p'],item['w']) for item in cfg['allow_periods']])
		self.lstPeriods.setModel(self.mdlPeriods)
		self.lstPeriods.setContextMenuPolicy(3) 
		self.lstPeriods.customContextMenuRequested[QPoint].connect(partial(self.lstRightMenu,'mdlPeriods'))
		self.lstPeriods.clicked.connect(partial(self.ItemSelect,'mdlPeriods'))
		return cfg
	def MenuAbout(self,q):
		msgBox=QMessageBox()
		msgBox.setWindowIcon(QIcon(get_files()[0]))  #设置弹出关于对话框的左上角的图标
		msgBox.setIcon(QMessageBox.Information)  #设置弹出关于对话框内容区里面的那个蓝色(i)的那个图标
		msgBox.setTextFormat(Qt.RichText) #RichText模式才支持超链接
		msgBox.setWindowTitle('关于')
		ss='ChildControl&ChildGuard电脑管控程序（%s）,<br>\n' % VERSION
		ss+='Copyright by <a href="mailto:sun_beat@163.com">sun_beat@163.com</a><br>\n'
		ss+='QQ:67073118，欢迎提修改意见<br/>\n'
		ss+='官网地址：<a href="https://github.com/sunhanaix/ChildPC">https://github.com/sunhanaix/ChildPC</a><br/><p/>\n'
		ss+='编码不容易，一块两块也是肉，微信扫码支持下哈：<br>\n'
		ss+='<img src="%s"/>' % get_files()[1]
		msgBox.setText(ss)
		#msgBox.setText(u'<a href='"'mailto:sun_beat@163.com'"'>sun_beat@163.com</a>')
		msgBox.setStandardButtons(QMessageBox.Ok)
		msgBox.exec()
	def ItemSelect(self,model_name,index):
		global lstSelect
		lstSelect={'model_name':model_name,'index':index,'row':index.row(),'data':index.data()}
	def lstRightMenu(self,model_name,pos):  #显示右键选中QListView对象时的右键上下文弹出菜单
		popMenu = QMenu()
		popMenu.addAction(QAction(u'插入整行', self))
		popMenu.addAction(QAction(u'删除整行', self))
		popMenu.addAction(QAction(u'修改单元格', self))
		popMenu.triggered[QAction].connect(partial(self.RightMenuAction,model_name,pos))
		popMenu.exec_(QCursor.pos())
	def RightMenuAction(self,model_name,pos,q):  #处理点了右键菜单后的动作
		print(self,pos,model_name,q)
		ss='self.'+model_name+'.stringList()'  #先拿到当前数据列表
		model_list=eval(ss)
		print('model_list=',model_list)
		listView={'mdlHosts':'lstHosts','mdlBlacklist':'lstBlacklist',
						'mdlPeriods':'lstPeriods','mdlBrowsers':'lstBrowsers','mdlKeywords':'lstKeywords'
			}
		clv=listView[model_name]  #通过model name获得当前listView的名字
		ss = 'self.'+clv+'.selectionModel()'
		print(ss)
		sm=eval(ss)
		ss='self.'+clv+'.indexAt(pos)'  #通过鼠标点击位置传进来的坐标，获得当前焦点是选择在哪个条目上
		index=eval(ss)
		if q.text()=='插入整行':
			if model_name in ['mdlHosts','mdlPeriods']:
				model_list.insert(index.row(),['','']) #给这个数据列表，再增加一行
			else:
				model_list.insert(index.row(),'') #给这个数据列表，再增加一行
			sm.select(index.siblingAtRow(index.row()-2),QItemSelectionModel.Select)  #选定新增的这一行
		elif q.text()=='删除整行':
			model_list.pop(index.row())
		elif q.text()=='修改单元格':
			pass
		ss='self.'+model_name+'.setStringList(model_list)'
		print(ss)
		eval(ss) 
		print('model_list=',model_list)
		#ss='self.'+clv+'.setModel(self.'+model_name+')'
		ss='self.'+clv+'.setUpdatesEnabled(True)'
		#eval(ss)
		print(q.text())
	def radioKill(self):
		self.radNotKill.setChecked(False)
	def radioNotKill(self):
		self.radKill.setChecked(False)
	def DealAutoStart(self):
		if self.ckAutoStart.isChecked(): 
			setAutoStart()
		else:
			delAutoStart()
	def Quit(self): 
		sys.exit()
	def UpdateCfg(self,prompt):
		#保存当前配置，更新内容，并通知监控进程
		print(self,prompt)
		global cfg
		hosts=self.mdlHosts.stringList()
		cfg['hosts']=[]
		i=0
		while i < len(hosts):
			host=hosts[i]
			if not host[0] or not host[1]: #要是主机地址是空，或者端口是空，删掉这行
				hosts.pop(i)
				self.mdlHosts.setStringList(hosts)
				continue
			i+=1
			cfg['hosts'].append("%s:%s" % (host[0],host[1]) )
		cfg['browsers']=self.mdlBrowsers.stringList()
		cfg['browser_keywords']=self.mdlKeywords.stringList()
		cfg["allow_periods"]=[]
		periods=self.mdlPeriods.stringList()
		i=0
		while i< len(periods):
			period=periods[i]
			if not period[0] or not period[1]: #要是周几是空，或者时间段是空，删掉这行
				periods.pop(i)
				self.mdlPeriods.setStringList(periods)
				continue
			i+=1
			cfg["allow_periods"].append({'w':period[0],'p':period[1]})
		cfg['interval']=self.txtInterval.value()
		cfg['timeout']=self.txtTimeout.value()
		cfg['seconds']=self.txtSeconds.value()
		if self.radKill.isChecked():
			cfg['do_kill']=1
		else:
			cfg['do_kill']=0
		cfg['snap_dir']=self.txtSnapdir.text()
		try:
			f=open(cfg_file,'w')
			f.write(json.dumps(cfg,indent=2))
			f.close()
			if prompt:
				self.msg("配置文件已经更新")
		except Exception as e:
			print(e)
			if prompt:
				self.msg("配置文件更新失败："+str(e))
		print(json.dumps(cfg,indent=2))
	def Browse(self):
		dlg = QFileDialog()
		dlg.setFileMode(QFileDialog.Directory)
		if dlg.exec_():
			try:
				self.txtSnapdir.setText(dlg.selectedFiles()[0])
			except Exception as e:
				print(e)
	def Run(self):
		##判断当前是运行状态，还是停止状态，进行状态的切换
		print("do Run Button")
		self.UpdateCfg(prompt=False) #run之前，先把当前配置更新了
		print("status:%s" % self.myrun.isRunning())
		if self.myrun.isRunning():
			self.btRun.setText("开始")
			self.myrun.terminate()  #此方法强制结束，不是官方推荐方法；官方建议在Qthread.run方法里面，定义loop，检测某个flag，来判断是否终止
			self.myrun=RunControl()
		else:
			self.btRun.setText("停止")
			self.myrun.start()
	def FlushStatus(self): #刷新txtStatus里面的内容
		n=log_pos(log_file)
		cursor = self.txtStatus.textCursor()  
		cursor.movePosition(QTextCursor.End)
		if n==self.pos: #log文件没有变化
			pass
		elif n<self.pos: #要是log文件被重置了
			ss=read_fr_pos(log_file)
			cursor.insertText(ss)
		else:
			ss=read_fr_pos(log_file,self.pos) #从上次读的位置开始读到末尾
			cursor.insertText(ss)
		self.txtStatus.setTextCursor(cursor)  
		self.txtStatus.ensureCursorVisible()  
		self.pos=n
	def TTS(self):
		print("do TTS")
		msg=self.txtMsg.toPlainText()
		if not msg:
			return None
		print("msg=%s" % msg)
		ChildControl.tts(msg)
	def Hide(self):
		global cfg
		cfg['hide']=1
		self.UpdateCfg(prompt=False)
		if not self.myrun.isRunning():
			self.myrun.start()
		try:
			hideSelf(self)
		except Exception as e:
			self.msg(str(e))
	def msg(self,smsg,msgType='info'):
		whnd=0
		try:
			whnd=win32gui.GetForegroundWindow()
		except Exception as e:
			print("in msg(),Erro:%s" % str(e))
		if not whnd:
			whnd=0
		QMessageBox.information(self,msgType,smsg)

if __name__ == '__main__':
	app = QApplication(sys.argv)
	w=pkgWindow()
	w.show()
	sys.exit(app.exec_())