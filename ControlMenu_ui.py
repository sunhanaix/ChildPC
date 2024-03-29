# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ControlMenu.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1193, 720)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.lstHosts = QtWidgets.QTableView(self.centralwidget)
        self.lstHosts.setGeometry(QtCore.QRect(10, 20, 321, 151))
        self.lstHosts.setDragEnabled(True)
        self.lstHosts.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.lstHosts.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.lstHosts.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.lstHosts.setObjectName("lstHosts")
        self.lstHosts.horizontalHeader().setDefaultSectionSize(157)
        self.btTTS = QtWidgets.QPushButton(self.centralwidget)
        self.btTTS.setGeometry(QtCore.QRect(540, 620, 81, 23))
        self.btTTS.setObjectName("btTTS")
        self.btCfgReset = QtWidgets.QPushButton(self.centralwidget)
        self.btCfgReset.setGeometry(QtCore.QRect(510, 500, 75, 23))
        self.btCfgReset.setObjectName("btCfgReset")
        self.radNotKill = QtWidgets.QRadioButton(self.centralwidget)
        self.radNotKill.setGeometry(QtCore.QRect(600, 120, 51, 16))
        self.radNotKill.setObjectName("radNotKill")
        self.txtTimeout = QtWidgets.QSpinBox(self.centralwidget)
        self.txtTimeout.setGeometry(QtCore.QRect(530, 40, 42, 22))
        self.txtTimeout.setMinimum(1)
        self.txtTimeout.setMaximum(300)
        self.txtTimeout.setProperty("value", 30)
        self.txtTimeout.setObjectName("txtTimeout")
        self.txtInterval = QtWidgets.QSpinBox(self.centralwidget)
        self.txtInterval.setGeometry(QtCore.QRect(530, 10, 42, 22))
        self.txtInterval.setMinimum(1)
        self.txtInterval.setMaximum(300)
        self.txtInterval.setProperty("value", 30)
        self.txtInterval.setObjectName("txtInterval")
        self.label_10 = QtWidgets.QLabel(self.centralwidget)
        self.label_10.setGeometry(QtCore.QRect(340, 160, 111, 21))
        self.label_10.setObjectName("label_10")
        self.txtSnapdir = QtWidgets.QLineEdit(self.centralwidget)
        self.txtSnapdir.setGeometry(QtCore.QRect(160, 500, 301, 21))
        self.txtSnapdir.setObjectName("txtSnapdir")
        self.btHide = QtWidgets.QPushButton(self.centralwidget)
        self.btHide.setGeometry(QtCore.QRect(260, 560, 75, 23))
        self.btHide.setObjectName("btHide")
        self.label_9 = QtWidgets.QLabel(self.centralwidget)
        self.label_9.setGeometry(QtCore.QRect(10, 340, 121, 21))
        self.label_9.setObjectName("label_9")
        self.btRun = QtWidgets.QPushButton(self.centralwidget)
        self.btRun.setGeometry(QtCore.QRect(160, 560, 75, 23))
        self.btRun.setObjectName("btRun")
        self.lstBrowsers = QtWidgets.QListView(self.centralwidget)
        self.lstBrowsers.setGeometry(QtCore.QRect(10, 360, 251, 121))
        self.lstBrowsers.setObjectName("lstBrowsers")
        self.btQuit = QtWidgets.QPushButton(self.centralwidget)
        self.btQuit.setGeometry(QtCore.QRect(370, 560, 75, 23))
        self.btQuit.setObjectName("btQuit")
        self.label_8 = QtWidgets.QLabel(self.centralwidget)
        self.label_8.setGeometry(QtCore.QRect(340, 340, 121, 21))
        self.label_8.setObjectName("label_8")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 0, 371, 21))
        self.label.setObjectName("label")
        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        self.label_7.setGeometry(QtCore.QRect(10, 500, 151, 21))
        self.label_7.setObjectName("label_7")
        self.btBrowse = QtWidgets.QPushButton(self.centralwidget)
        self.btBrowse.setGeometry(QtCore.QRect(460, 500, 41, 23))
        self.btBrowse.setObjectName("btBrowse")
        self.lstBlacklist = QtWidgets.QListView(self.centralwidget)
        self.lstBlacklist.setGeometry(QtCore.QRect(10, 200, 251, 121))
        self.lstBlacklist.setObjectName("lstBlacklist")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(420, 40, 101, 20))
        self.label_3.setObjectName("label_3")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(420, 10, 101, 20))
        self.label_2.setObjectName("label_2")
        self.txtSeconds = QtWidgets.QSpinBox(self.centralwidget)
        self.txtSeconds.setGeometry(QtCore.QRect(530, 70, 42, 22))
        self.txtSeconds.setMinimum(1)
        self.txtSeconds.setMaximum(300)
        self.txtSeconds.setProperty("value", 10)
        self.txtSeconds.setObjectName("txtSeconds")
        self.radKill = QtWidgets.QRadioButton(self.centralwidget)
        self.radKill.setGeometry(QtCore.QRect(600, 100, 41, 16))
        self.radKill.setChecked(True)
        self.radKill.setObjectName("radKill")
        self.gridGroupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.gridGroupBox.setGeometry(QtCore.QRect(-10, 590, 641, 81))
        self.gridGroupBox.setObjectName("gridGroupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.gridGroupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(360, 110, 241, 21))
        self.label_5.setObjectName("label_5")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(10, 180, 81, 21))
        self.label_4.setObjectName("label_4")
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(420, 70, 101, 20))
        self.label_6.setObjectName("label_6")
        self.lstKeywords = QtWidgets.QListView(self.centralwidget)
        self.lstKeywords.setGeometry(QtCore.QRect(340, 360, 291, 121))
        self.lstKeywords.setObjectName("lstKeywords")
        self.btUpdate = QtWidgets.QPushButton(self.centralwidget)
        self.btUpdate.setGeometry(QtCore.QRect(590, 500, 75, 23))
        self.btUpdate.setObjectName("btUpdate")
        self.ckAutoStart = QtWidgets.QCheckBox(self.centralwidget)
        self.ckAutoStart.setGeometry(QtCore.QRect(50, 560, 101, 16))
        self.ckAutoStart.setObjectName("ckAutoStart")
        self.txtMsg = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.txtMsg.setGeometry(QtCore.QRect(10, 600, 521, 61))
        self.txtMsg.setObjectName("txtMsg")
        self.lstPeriods = QtWidgets.QTableView(self.centralwidget)
        self.lstPeriods.setGeometry(QtCore.QRect(340, 180, 301, 151))
        self.lstPeriods.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.lstPeriods.setObjectName("lstPeriods")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(680, 20, 501, 651))
        self.groupBox.setObjectName("groupBox")
        self.txtStatus = QtWidgets.QTextEdit(self.groupBox)
        self.txtStatus.setGeometry(QtCore.QRect(10, 20, 481, 621))
        self.txtStatus.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.txtStatus.setReadOnly(True)
        self.txtStatus.setTabStopDistance(80.0)
        self.txtStatus.setObjectName("txtStatus")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1193, 23))
        self.menubar.setObjectName("menubar")
        self.menu_H = QtWidgets.QMenu(self.menubar)
        self.menu_H.setObjectName("menu_H")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.mnAbout = QtWidgets.QAction(MainWindow)
        self.mnAbout.setObjectName("mnAbout")
        self.mnFeedback = QtWidgets.QAction(MainWindow)
        self.mnFeedback.setObjectName("mnFeedback")
        self.menu_H.addAction(self.mnAbout)
        self.menubar.addAction(self.menu_H.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.btTTS.setText(_translate("MainWindow", "发消息给对方"))
        self.btCfgReset.setText(_translate("MainWindow", "重置配置"))
        self.radNotKill.setText(_translate("MainWindow", "不杀"))
        self.label_10.setText(_translate("MainWindow", "临时放开管控时段："))
        self.txtSnapdir.setText(_translate("MainWindow", "snap"))
        self.btHide.setText(_translate("MainWindow", "隐藏运行"))
        self.label_9.setText(_translate("MainWindow", "需要监控的浏览器："))
        self.btRun.setText(_translate("MainWindow", "开始"))
        self.btQuit.setText(_translate("MainWindow", "退出"))
        self.label_8.setText(_translate("MainWindow", "浏览器关键词黑名单："))
        self.label.setText(_translate("MainWindow", "管控电脑地址列表（会按照从上到下的顺序，找到第一个可以连通的）"))
        self.label_7.setText(_translate("MainWindow", "抓取图片和录音存放路径："))
        self.btBrowse.setText(_translate("MainWindow", "浏览"))
        self.label_3.setText(_translate("MainWindow", "超时设置（秒）："))
        self.label_2.setText(_translate("MainWindow", "轮询间隔（秒）："))
        self.radKill.setText(_translate("MainWindow", "杀"))
        self.label_5.setText(_translate("MainWindow", "发现黑名单程序和浏览违禁词时，是否杀掉："))
        self.label_4.setText(_translate("MainWindow", "程序黑名单："))
        self.label_6.setText(_translate("MainWindow", "录音时长（秒）："))
        self.btUpdate.setText(_translate("MainWindow", "更新配置"))
        self.ckAutoStart.setText(_translate("MainWindow", "开机自动启动"))
        self.groupBox.setTitle(_translate("MainWindow", "程序执行状态日志信息:"))
        self.menu_H.setTitle(_translate("MainWindow", "帮助(&H)"))
        self.mnAbout.setText(_translate("MainWindow", "关于(&A)"))
        self.mnFeedback.setText(_translate("MainWindow", "建议反馈(&F)"))
