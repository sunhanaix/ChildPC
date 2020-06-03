#!/usr/bin/python3
import os,time,sys
from aip import AipSpeech  #百度语音识别库，#pip install baidu-aip安装百度的AIP模块
import pyaudio             #麦克风声音采集库
import wave
import requests,json       #音乐搜索
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame              #mp3播放
from pydub import AudioSegment #用来做pcm/wav格式转换成mp3格式，调用的ffmpeg实现，要先下载ffmpeg，并把它放在PATH能够得着的地方
from subprocess import call
VERSION='v0.9.20200416'

APP_ID = 'xxxxx'  #这个需要自己到百度API去申请
API_KEY = 'xxxxx'
SECRET_KEY = 'xxxxxxxxxx'
baidu_aip_client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
CHUNK = 1024
FORMAT = pyaudio.paInt16 #16位采集
CHANNELS = 1             #单声道
RATE = 16000             #采样率
RECORD_SECONDS = 9       #采样时长 定义为9秒的录音
WAVE_OUTPUT_FILENAME = "myvoice.pcm"  #采集声音文件存储路径
audio_dir='tmp_audio'

def ts(ts=None):
	 return time.strftime("%Y%m%d_%H%M%S", time.localtime(ts))
	 
def play_audio(file):
	pygame.mixer.init() # #最后时刻再做文字到语音，然后播放，否则MyTTS里面会占用声卡
	#直接pygame.mixer.music.load(file_name)，然后pygame.mixer.quit()发现有较大概率不会释放文件占用句柄
	#改成给文件描述符，然后关pygame，关文件句柄方式，目前未发生不释放情况
	try:
		f=open(file,'rb')
	except Exception as e:
		print(e)
		return False
	pygame.mixer.music.load(f)#text文字转化的语音文件
	pygame.mixer.music.play(loops=0)
	while pygame.mixer.music.get_busy() == True:
		#print('waiting')
		pass
	pygame.mixer.quit()
	pygame.quit()
	try:
		f.close()
	except Exception as e:
		print(e)
	

def play(file):
	try:
		ext=os.path.splitext(file)[1]
	except Exception as e:
		print(e)
		ext=''
	#对不同扩展名的音频文件进行处理，这里面就不特别处理，调用百度TTS出来的MP3可以用pygame播放
	#如果还想播放.wmv .ra等音频文件，pygame就不行，需要用ffmpeg的ffplay等来播放
	play_audio(file)
	return True
	
def word_to_voice(text,n=1): #n为播放几次
	#print("word_to_voice(): trying to word to audio")
	#调用百度aip接口，把文字发过去，获得文字转音频的二进制内容
	# 发音人选择, 基础音库：0为度小美，1为度小宇，3为度逍遥，4为度丫丫，
	# 精品音库：5为度小娇，103为度米朵，106为度博文，110为度小童，111为度小萌，默认为度小美 
	PER = 111;
	#语速，取值0-9，默认为5中语速
	SPD = 5;
	#音调，取值0-9，默认为5中语调
	PIT = 6;
	#音量，取值0-9，默认为5中音量
	VOL = 5;

	result = baidu_aip_client.synthesis(text, 'zh', 1, 
		{'vol': VOL, 'spd': SPD, 'per': PER, 'pit':PIT} )
	try:
		os.mkdir(audio_dir)
	except Exception as e:
		pass			
	audio_file=audio_dir+'/'+ts()+'tts_audio.mp3'
	if not isinstance(result, dict):
		with open(audio_file, 'wb') as f:
			f.write(result)
			f.close()
	try:
		for i in range(n):
			play(audio_file)
	except Exception as e:
		print(e)
		print('erro in MyTTS.paly()')
	try:
		os.unlink(audio_file)
	except Exception as e:
		print(e)
		pass
	return

def  get_mic_voice_file(audio_output_file,RECORD_SECONDS=10,mp3=False): #从麦克风读声音，存成一个pcm格式的文件
	stime=time.time()
	p = pyaudio.PyAudio()
	stream = p.open(format=FORMAT,
		channels=CHANNELS,
		rate=RATE,
		input=True,
		frames_per_buffer=CHUNK)
	print("* recording for %d s" % RECORD_SECONDS)
	frames = []
	for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
		data = stream.read(CHUNK)
		frames.append(data)
	etime=time.time()
	print("* done recording for %.2f s" % (etime-stime))
	stream.stop_stream()
	stream.close()
	#p.terminate()#这里先不使用p.terminate(),否则 p = pyaudio.PyAudio()将失效，还得重新初始化。
	wf = wave.open(audio_output_file+'.pcm', 'wb')
	wf.setnchannels(CHANNELS)
	wf.setsampwidth(p.get_sample_size(FORMAT))
	wf.setframerate(RATE)
	wf.writeframes(b''.join(frames))
	wf.close()
	print('recording finished')
	if mp3:
		print("found mp3 tag,try to load pcm format audio")
		raw_audio = AudioSegment.from_file(audio_output_file+'.pcm', format="wav")
		print("try to pcm to mp3 converting")
		try:
			raw_audio.export(audio_output_file, format="mp3")
		except Exception as e:
			print(e)
		try:
			stats=os.stat(audio_output_file)
		except Exception as e:
			print(e)
			return None
		print("stats=%s" % str(stats))
		if stats.st_size==0:  #要是生成的mp3文件是0字节的话，
			print('stats.st_size=0')
			try:
				os.unlink(audio_outpu_file)
			except:
				pass
			res_name=audio_output_file.replace('.mp3','.wav')
			os.rename(audio_output_file+'.pcm',res_name)
			return res_name
		try:
			os.unlink(audio_output_file+'.pcm')
		except Exception as e:
			pass
	return audio_output_file
	
def vocie_to_word(audio_file):
	with open(audio_file, 'rb') as fp:
		ss=fp.read()
		fp.close()
	results = baidu_aip_client.asr(ss)  #asr模块，用于把二进制的语音文件内容，转成文字。语音文件，默认format为pcm
	print(results)
	return results['result'][0]
	#song_name=results['result'][0]
	#print(song_name)
	#return song_name
	
if __name__=='__main__'	:
	word_to_voice('这是个测试')
	quit()
