***************************************************************
**请将本程序用在合法用途，产生的一切后果，本程序概不负责***
***************************************************************

一、程序的组成
1.1 本程序server端
server的daemon端，也即是ChildGuard.exe，默认监听在8888端口。
运行时，会申请管理员身份运行，无管理权限会失败。
由于其申请会申请windows开机启动等一系列木马常用行为，会被360认为是木马之类。
需要让360放行，并添加信任。
如果不放心exe程序，请下载对应的源码，自行编译
由于其会尝试调用电脑摄像头抓拍，有时会被360拦截，有时不会（说明360这个功能不靠谱啊，真拦截时，拦不住）
请在360安全卫士，“设置”-->“安全防护中心”-->设置“免打扰模式”和去掉“魔法摄像头”
ChildGuard其会释放出WatchDog.exe程序，并将它注册成为一个开机自启动的WatchDogC的服务。
WatchDogC的服务，会根据WatchDog.ini里面的配置，来定期轮询启动的ChildGuard.exe是否活着，没有活着的话，尝试启动它。
这样可以保证ChildGuard.exe即使被杀，WatchDogC服务会自动再拉起一个ChildGuard.exe程序
执行完后，重启下电脑，重启后，netstat -ano|findstr 8888
验证确认ChildGuard.exe已经可以自动启动，监听在了8888端口
1.2 本程序的client端
客户端部分，有几个：
1.2.1 ChildControl.exe控制部分
这个程序放在家长电脑上运行，或者放置在孩子电脑上运行
放置在家长的电脑上运行，记得修改ChildControl.ini里面的孩子电脑ip地址
它负责死循环，每30s检查一下孩子pc的状态：
①获得当前运行的是什么程序，程序的标题是什么
②如果当前的前台程序在黑名单，那么kill它
③检查360浏览器的标题，含有相关关键字，kill它
④检查腾讯视频是否存在，kill它
⑤每30s抓拍一次电脑屏幕，以及摄像头抓拍一次
⑥每30s抓一端10s的麦克风录音
⑦黑名单的开启时间段：比如设置成晚上或者周末，可以使用黑名单的程序，其他时间可以
如果设置了启动时自动隐藏，下次想能够操作，请先修改ChildControl.ini里面的hide参数，设置为0

1.2.2 rpc_cmd.exe是命令行cli部分
这个可以放在我的电脑上运行：
>rpc_cmd.exe
checking host=stanleypc,port=8888
http://stanleypc:8888>help
func=s.help()
['now', 'md5sum', 'wf', 'rf', 'my_exec', 'killProcess', 'getProcess', 'getActiveProcName', 'cpu_usage', 'mem_usage', 'dimm_info', 'msg', 'msgImm', 'get_path', 'tts', 'net_info', 'is_admin', 'GetSystemPowerStatus', 'uptime', 'create_time', 'username', 'disk_c_usage', 'disk_io_counters', 'net_io_counters', 'snapScreen', 'snapCam', 'snapMerge', 'snapAudio', 'll', 'exit', 'help', 'version']
http://stanleypc:8888>version
func=s.version()
v0.8.6.20200410
http://stanleypc:8888>tts(别玩游戏啦，快做作业！)
tts这个用得多，主要是会在它屏幕上显示一个对话框，上面有你发过去的文字，然后会在他电脑上，语音播报一下这段文字

二、程序当前支持的功能：
now：取得当前孩子pc的时间
md5sum：给定文件名，返回对应的md5值（用于校验文件比对）
wf: 写data给到指定文件
rf: 读文件内容
my_exec : 执行指定的dos命令，返回标准输出的内容，和错误输出的内容
'killProcess', 给定pid，杀进程
'getProcess', 不加参数，返回所有进程信息；加pid返回pid进程信息；加caption信息，返回caption的进程信息
'getActiveProcName', 返回当前前台的进程信息
'cpu_usage', 返回当前cpu利用率
'mem_usage', 返回当前内存利用率
'dimm_info',返回当前物理内存条情况
'msg', 发指定的文本消息给孩子的电脑屏幕，并等待孩子点“确定”
'msgImm',发指定的文本消息给孩子的电脑屏幕，不等孩子点，直接返回
'get_path',获得当孩子pc上ChildGuard.exe运行所在目录
'tts',发指定的文本消息给孩子的电脑屏幕，并语音播报给消息内容
'net_info',返回孩子pc上的网络信息内容
'is_admin', 判断ChildGuard.exe是否是以管理员模式运行的
'GetSystemPowerStatus',判断电池电量等信息，方便今后的其他应急程序准备
'uptime', 获得电脑的运行时间
'create_time',获得ChildGuard.exe的运行时间
'username', 获得当前ChildGuard.exe是以哪个用户运行的
'disk_c_usage', 获得c盘的利用率
'disk_io_counters', 获得当前磁盘的io情况，建议间隔运行2次，取差值÷间隔时间，获得io流量
'net_io_counters', 获得网络io情况
'snapScreen',抓电脑屏幕
'snapCam', 抓摄像头拍照
'snapMerge', 抓电脑屏幕并抓摄像头拍照，然后把两者拼接到一个图片上
'snapAudio',抓电脑的麦克风录音一段指定时长（默认10s）
'll',类似linux的ls -l的输出信息


三、待完善支持功能
1、热更新
2、获得微信访问指定网址的内容。
目前GetForegroundWindow获得窗口句柄
再GetWindowText用窗口句柄获得标题，
用GetWindowThreadProcessId获得pid
用WMI接口用pid获得命令行信息
基本能覆盖各个浏览器标题内容，满足了大部分需求。
但如果用微信打开的网页链接，或者小程序之类的，这个标题text或者页面内容获得不到。
还在尝试别的思路，捕获这个信息
3、防被杀
目前孩子小，还不会任务管理器，将来可能就会了。
要考虑病毒方式双进程互动
4、目前用的是xmlrpc.server.SimpleXMLRPCServer，还没有身份验证机制，内网使用还好，不建议映射端口挂公网
……

四、补充下使用技巧
1、ChildControl.ini中的轮询间隔
设置为30s，目前来看是折中后，比较合适的。
性能和及时性上，都可以保障
2、snap的文件太多了，list会耗时太长，
这个需要定期清理下
写了这个archive_snap_pic.py程序，可以定期清理
3、snap后的照片分析
 analyze_pic.py程序
用孩子电脑摄像头抓拍了照片，可以用opencv简单判断下几个状态：
a、笔记本电脑合上了；b、孩子离开座位，没在电脑前；c、孩子坐在电脑前
目前还在研究opencv的玩法，大致只实现了上述的几个内容
4、源码方式执行：
需要依赖的几个包：
python.exe -m pip install pyinstaller PyQt5  opencv-python  pywin32  Pillow baidu-aip psutil pygame pydub
去网站：https://www.lfd.uci.edu/~gohlke/pythonlibs/
找到对应自己电脑版本的PyAudio模块，下载下来，然后安装它
python.exe -m pip install PyAudioxxxxx.whl
