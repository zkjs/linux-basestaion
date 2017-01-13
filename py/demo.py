#/usr/bin/python
# -*- coding: utf-8 -*-
import Queue,threading,signal,traceback,os
import time,sys,datetime
import paho.mqtt.client as mqtt
import random
import json
from bluepy.btle import Scanner,DefaultDelegate
import uuid
import socket
import fcntl
import struct
from zeroconf import ServiceBrowser, Zeroconf
import urllib 
import urllib2 
import requests
import picamera
import json
import re

try:
	from var import *
	from func import *
	from depdata import *
	from depconfig import *
except Exception,e:
	#logger.critical("\033[1;31;40mCannot import:%s,%s\033[0m" % (Exception,e))
	print "\033[1;31;40mCannot import neccessary file:%s,%s\033[0m" % (Exception,e)
	quit()

import logging
from logging.handlers import TimedRotatingFileHandler

#console_formatter = logging.Formatter('%(name)-5s: %(levelname)-8s %(message)s')
#Rthandler = RotatingFileHandler('demo.log',maxBytes=10*1024*1024,backupCount=5)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d %(name)s] - %(message)s')
#console_formatter = logging.Formatter(console_format)
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d %(name)s] - %(message)s [%(process)d,%(thread)d:%(threadName)s]')
#file_formatter = logging.Formatter(file_format)
console.setFormatter(console_formatter)
#logger = logging.getLogger('demo')
logger = logging.getLogger('demo')
logger.addHandler(console)
Trthandler = TimedRotatingFileHandler(filename=cur_file_dir()+'/'+log_name,when=file_handler_when,interval=file_handler_interval,backupCount=file_handler_backupcount)
#Trthandler.suffix = "%Y%m%d.log"
Trthandler.suffix = log_suffix
Trthandler.extMatch = r"^\d{4}-\d{2}-\d{2}.log$"

Trthandler.setLevel(logging.INFO)
Trthandler.setFormatter(file_formatter)
logger.addHandler(Trthandler)
logger.setLevel(logging.DEBUG)

global stationAlias
global reconnect_count
global reconnect_count_mqtt
global lastDiscoveryTime
global stationMac 
global cameraReviewed 
global dataddd
global ifname
#global alarm_cache
#alarm_cache = {}
dataddd={}
cameraReviewed = False
threads=[]
threadID=1
ifname = get_ifname(MacFilter)
stationMac = get_mac_address(MacFilter,':')
positionQ= Queue.Queue(PositionQueueLength)
commandQ = Queue.Queue(CommandQueueLength)
callQ = Queue.Queue(CallQueueLength)

def reconnect():
    #count reconnect counts, if bigger than 200, do reconn
    global reconnect_count
    global s
    reconnect_count += 1
    if reconnect_count>= 3:
        reconnect_count = 0
        try:
            s.close()
        except socket.error as msg:
            #print"socket reconnect:close error : %s " % (msg,)
            logger.warning("[reconnect]\033[1;33;40msocket reconnect:close error : %s\033[0m " % (msg,))
	    #logger.debug('
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect((depHost,depPort))
        except socket.error as msg:
            #print"socket reconnect error : %s " % (msg,)
            logger.warning("[reconnect\033[1;33;40m]socket reconnect:connect error %s,%s: %s \033[0m" % (depHost,depPort,msg))

def reconnect_mqtt():
	global reconnect_count_mqtt
	#global client
	global MQTTServer,MQTTPort,mqttClientKeepAliveTime
	reconnect_count_mqtt += 1
	if reconnect_count_mqtt >=3:
		reconnect_count_mqtt = 0
		try:
			client.disconnect()
		except Exception,e:
			#print "mqtt reconnect:disconnect error :%s,%s " % (Exception,e)
			logger.warning("[reconnect_mqtt]\033[1;33;40mmqtt reconnect:close error : %s\033[0m" % (msg,))
		try:
			client.connect(MQTTServer,MQTTPort,mqttClientKeepAliveTime)
		except Exception,e:
			#print "mqtt reconnect error :%s,%s " % (Exception,e)
			logger.warning("[reconnect_mqtt]\033[1;33;40mmqtt reconnect:connect error : %s \033[0m" % (msg,))
			return False
		else:
			return True

class ScanDelegate(DefaultDelegate):
	def __init__(self):
		DefaultDelegate.__init__(self)
	def handleDiscovery(self, dev, isNewDev, isNewData):
		global stationAlias,stationMac
		data = {}
		timestamp = time.time()
		global lastDiscoveryTime
		global s
		global dataddd  #assemble all data before the loop
		try:
			for (adtype,desc,value) in dev.getScanData():
				data[desc]=value
		except UnicodeDecodeError,e:
			pass
		##::here is new processing using depdata.py codes;
		if (data.has_key('Manufacturer')) and ( manu_filter(data.get('Manufacturer')) ):
			#if match the manufilter then start new processing:
			#u just want update minimum fresh data here
			try:
				#s.send(bytearray.fromhex('01ab02ab'))
				dataddd['keyflag']=rawdata_translate(data['Manufacturer'])
			#    if alarm_update(dev.addr.replace(':',''), dataddd['keyflag']):
			#        dataddd['keyflag'] = KEY_BINDING
			#ip need update
			except Exception,e:
				print('dev+1 %s' % dev.addr )
				logger.warning("[ScanDelegate.handleDiscovery]\033[1;33;40mrawdata_translate %s get exception:%s,%s\033[0m" % (dev.addr,Exception,e))
			if alarm_update(dev.addr.replace(':',''), dataddd['keyflag']):
				dataddd['keyflag'] = KEY_BINDING
			#local_ip = get_ip_address(depIfip) #dataddd['ip'] = str(local_ip) #dataddd['hexip'] = ''.join([hex(int(i)).lstrip('0x').rjust(2,'0') for i in local_ip.split('.')])
			dataddd['bcaddr'] = dev.addr
			dataddd['bcmac'] = dev.addr.replace(':','')
			dataddd['rssi'] = hex(dev.rssi*(-1)).lstrip('0x').rjust(2,'0')
			dataddd['srssi'] = dev.rssi*(-1)
			## data type 
			if depProt == 'B':
			#print('%s' % dataddd)
				load = gen_bin_data(dataddd)
			#print('%s' % dataddd)
			else:
				load = gen_json_data(dataddd)
			## send type
			#if depNet == 'S':
			try:
				s.send(load)
				#print('all xxx sent %s' % load)
			except socket.error as msg:
				logger.warning("[ScanDelegate.handleDiscovery]\033[1;33;40msocket error:%s\033[0m" % (msg,))
				#print('socket error %s' % msg)
				reconnect()
			else:
				logger.info("[ScanDelegate.handleDiscovery]socket send %s " % (load,))
			##Mqtt not processed

			## below is old codes
		#print "%s，%s" % (data['Manufacturer'],braceletFlag)
		if (not data.has_key('Manufacturer')) or ( not data['Manufacturer'].startswith(braceletFlag)):
			return 0
		data['addr'] = dev.addr
		data['rssi'] = dev.rssi
		data['bsid'] = stationAlias
		data['stationMac'] = stationMac
		data['timestamp'] = timestamp
		data['bcid'] = int(data['Manufacturer'][8:16],16)
		data['data'] = data['Manufacturer'][4:]
		#battery+station ip
		#electricity = data['Manufacturer'][16:18]
		electricity = '64' #fixed
		flag = data['Manufacturer'][6:8]
		local_ip = get_ip_address(ifname)
		hex_ip = ''.join([hex(int(i)).lstrip('0x').rjust(2,'0') for i in local_ip.split('.')])
		temp = 50
	
		if data['Manufacturer'].startswith(callFlag,6):
			callData=data
			callData['nursecall'] = True
			logger.info("[ScanDelegate.handleDiscovery]Call data get:%s" % (json.dumps(callData),))
			#print "\033[1;31;40m%s\033[0m" % (json.dumps(callData,))
			try:
				client.publish(CALLTITLE,json.dumps(callData))
			except Exception,e:
				#print "\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e)
				logger.warning("[ScanDelegate.handleDiscovery]\033[1;33;40msending call data %s to %s get %s:%s\033[0m and trying to reconnect" % (json.dumps(callData),CALLTITLE,Exception,e))
				reconnect_mqtt()
			else:
				logger.info("[ScanDelegate.handleDiscovery]\033[1;32;40mCall\033[0m data sended to %s(%s:%s):%s" % (CALLTITLE,MQTTServer,MQTTPort,json.dumps(callData)))
			#lastDiscoveryTime = time.time()
		elif data['Manufacturer'].startswith(outbodyFlag,6):
			outbodyData = data
			logger.info("[ScanDelegate.handleDiscovery]Outbody data get:%s" % (json.dumps(outbodyData),))
			try:
				client.publish(OUTBODYTITLE,json.dumps(outbodyData))
			except Exception,e:
				#print "\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e)
				logger.warning("[ScanDelegate.handleDiscovery]\033[1;33;40msending outbody data %s get %s:%s\033[0m and trying to reconnect" % (json.dumps(outbodyData),Exception,e))
				reconnect_mqtt()
			else:
				logger.info("[ScanDelegate.handleDiscovery]\033[1;32;40mOutbody\033[0m data sended to %s(%s:%s):%s" % (OUTBODYTITLE,MQTTServer,MQTTPort,json.dumps(outbodyData)))
			#lastDiscoveryTime = time.time()
		#change to send to mqtt immidiately
		#positionQ.put(json.dumps(data))
		else:
			logger.info("[ScanDelegate.handleDiscovery]Position data get:%s" % (json.dumps(data),))
			#logger.info("[ScanDelegate.handleDiscovery]Position data sended %s,%s:%s" % (MQTTServer,MQTTPort,json.dumps(data)))
			try:
				client.publish(POSITIONTITLE,json.dumps(data))
			except Exception,e:
				#print "\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e)
				logger.warning("[ScanDelegate.handleDiscovery]\033[1;33;40msending position data %s get %s:%s\033[0m and trying to reconnect" % (json.dumps(data),Exception,e))
				reconnect_mqtt()
			#print "%s,%s:%s" % (MQTTServer,MQTTPort,json.dumps(data))
			else:
				logger.info("[ScanDelegate.handleDiscovery]\033[1;32;40mPosition\033[0m data sended to %s(%s:%s)%s" % (POSITIONTITLE,MQTTServer,MQTTPort,json.dumps(data)))
			#lastDiscoveryTime = time.time()

def on_connect(client,userdata,flags,rc):
	client.subscribe(CMDTITLE)
	#print("Connected with resut code " + str(rc))
	logger.info("[MqttClient.on_connect] Mqtt Connected with resut code " + str(rc))

def on_disconnect(client, userdata, rc):      
	#print "Mqtt Disconnected..."
	logger.info("[MqttClient.on_disconnect]Mqtt Disconnected...")

def on_message(client,userdata,msg):
	#print "\033[1;31;40m[get] topic %s , payload:%s\033[0m" % (msg.topic, str(msg.payload))
	logger.debug("[MqttClient.on_message]get topic \033[1;32;40m%s\033[0m,payload:%s" % (msg.topic, str(msg.payload)))
	if msg.topic == CMDTITLE:
		#print "\033[1;31;40m[get] %s \033[0m" % (str(msg.payload),)
		logger.debug("[MqttClient.on_message]runcmd2 going to deal with %s" % (str(msg.payload),))
		runcmd2(str(msg.payload))

class MyListener(object):
	def add_service(self, zeroconf, type, name):
		global MQTTServer,MQTTPort,client
		info = zeroconf.get_service_info(type, name)
		logger.debug("[MyListerner.add_service]Service \033[1;32;40m%s\033[0m added, service info: \033[1;32;40m%s\033[0m" % (name, info))
		if info.server 	!= MQTTServer or info.port != MQTTPort:
			#print "\033[1;31;40m received new address from zeroconf so need to change to new mqtt server : %s:%s\033[0m" % (info.server,info.port)
			logger.info("[MyListener.add_service]received new address from zeroconf so need to change to new mqtt server : %s:%s\033[0m" % (info.server,info.port))
			MQTTServer = info.server
			MQTTPort = info.port
			res = reconnect_mqtt()
			if res:
				logger.info('[MyListener.add_service]change to new mqtt server suc.')
				try:
					write_conf('MQTT','server',MQTTServer)
					write_conf('MQTT','port',MQTTPort)
				except Exception,e:
					logger.warning('[Mylistener.add_service]\033[1;33;40mFailed to write mqtt new address back to conf file:%s,%s\033[0m' % (MQTTServer,MQTTPort))
					#print "\033[1;31;40m failed to write back new mqtt server : %s:%s\033[0m" % (Exception,e)
			else:
				logger.warning('[MyListener.add_service]\033[1;33;40mFailed to reconnect to new mqtt server:%s,%s\033[0m'% (MQTTServer,MQTTPort))
				#print "\033[1;31;40m failed to reconnect to new mqtt server : %s:%s\033[0m" % (Exception,e)
			
def runcmd2(data):
	#print "\033[0;32;40m runcmd2  \033[0m" 
	global MQTTServer,MQTTPort
	global cameraReviewed 
	global hasCamera
	#print "\033[0;32;40m looping in runcmd %s while \033[0m"  % (q,)
	#print "\033[0;32;40m runcmd2 get %s \033[0m"  % (data,)
	if data.startswith('update'):
		#print "\033[0;32;40mget cmd as %s \033[0m" % (data,)
		logger.info("[runcmd2]get cmd \033[1;32;40m%s \033[0m" % (data,))
		#parse args update -f[filename]* -m[md5_sum]* -i[ip/domain] -p[port]*  -r[random range] -v[version]*
		ArgsDict = parseArgs2Dict(data.lstrip('update'))
		if (not ArgsDict.has_key('f')) or (ArgsDict.has_key('i') and (not ArgsDict.has_key('p'))) or (not ArgsDict.has_key('v')) or (not ArgsDict.has_key('m')):
			#shoule rase Exception ,return and exit
			#print "Error: lack some para"
			logger.warning('[runcmd2]\033[1;33;40mupdate cmd lack some para: %s\033[0m' % (data,))
			return 
		try:
			if float(ArgsDict['v']) > version:
				#print "\033[0;32;40m new version upgrade command received \033[0m"
				logger.info("[runcmd2]new version upgrade command received")
				if not ArgsDict.has_key('i'):
					ArgsDict['i'] = MQTTServer
				if not ArgsDict.has_key('p'):
					ArgsDict['p'] = 8000 
				if not ArgsDict.has_key('r'):
					ArgsDict['r'] = 600
				update_self(ArgsDict['f'],ArgsDict['m'],ArgsDict['v'],ArgsDict['i'],ArgsDict['p'],int(ArgsDict['r']))	
			else:
				logger.warning("[runcmd2]\033[1;33;40m current version : %f, order version :%f\033[0m " % (version,float(ArgsDict['v'])))
		except Exception,e:
			#print "\033[0;32;40m runcmd2 judging params get %s:%s\033[0m"  % (Exception,e)
			logger.warning('[runcmd2]\033[1;33;40mjudging params get %s:%s\033[0m' % (Exception,e))
	else :
		try:
			cmd = json.loads(data)
		except Exception,e:
			#print "\033[0;32;40m runcmd2 cannot cover cmd %s to json\033[0m" % (data,)
			logger.warning('[runcmd2]\033[1;33;40mcannot loads cmd to json:%s\033[0m' % (data,))

		if cmd['cmd'] == 'capture' :
			#print "\033[0;32;40m runcmd2 capture cmd2 received\033[0m"
			logger.info('[runcmd2]received capture cmd:%s' % (data,))
			#get photo
			if cmd['ap'] == stationAlias :
				#print "\033[0;32;40m capture cmd2 received and going to capture\033[0m"
				logger.info('[rumcmd2]demanded to capture')
				#print "\033[0;32;40m H:%s, %s ; V:%s, %s\033[0m" % (picResolutionH,type(picResolutionH),picResolutionV,type(picResolutionV))
				logger.debug("[runcmd2]capture resolution:\033[1;32;40m H:%s, %s ; V:%s, %s\033[0m" % (picResolutionH,type(picResolutionH),picResolutionV,type(picResolutionV)))
				now = int(time.time())
				filename = '%s_%s.jpg' % (cmd['bracelet'],now)
				#take_photo(filename,picUploadDir,picResolutionV,picResolutionH,cameraReviewed,hottime)
				#send_photo(filename,picUploadDir,picUploadServer,picUploadPort,cmd['ap'],cmd['bracelet'],now)
				#if not cameraReviewed:
				#	cameraReviewed = True
				if hasCamera:
					#print "\033[0;32;40m has Camera and going to capture:\033[0m"
					try:
						take_photo(filename,picUploadDir,picResolutionV,picResolutionH,cameraReviewed,hottime)
						#print "\033[0;32;40m Capture ? %s " % (re,)
					except Exception,e:
						#print "\033[0;32;40m Capture get Exception:%s:%s\033[0m" % (Exception,e)
						logger.error("[runcm2]\033[1;31;40mCapture get Exception:%s:%s\033[0m" % (Exception,e))
					else:
						#print "\033[0;32;40m Capture ? %s " % (re,)
						#if re:
						logger.info("[runcmd2]take photo suc")
						if cmd.has_key('url'):
							logger.debug("[runcmd2]going to call send_photo_url")
							try:
								res = send_photo_url(filename,picUploadDir,cmd['url'],now)	
							except Exception,e:
								logger.error("[runcmd2]\033[1;31;40msend_photo_url:%s,%s,%s,%s meet %s,%s\033[0m" % (filename,picUploadDir,cmd['url'],now,Exception,e))
							if res:
								logger.info("[send_photo_url]suc")
							else:
								logger.warning("[send_photo_url]\033[1;33;40mFailed\033[0m")
						else:
							logger.debug("[runcmd2]going to call send_photo for no url, cmd:\033[1;31;40n%s\033[0m" % (json.dumps(cmd),))
							res = send_photo(filename,picUploadDir,picUploadServer,picUploadPort,cmd['ap'],cmd['bracelet'],now)
							if res:
								logger.info("[send_photo]suc")
							else:
								logger.warning("[send_photo]\033[1;33;40mFailed\033[0m")
							
						#print "\033[0;32;40msend_photo done\033[0m"
						if not cameraReviewed:
							cameraReviewed = True
				else:
					#print "\033[0;32;40m no camera and ignore capture \033[0m"
					logger.warning("[rumcmd2]\033[1;33;40m capture cmd got but I did't have a camera!\033[0m")
					#return sth to server?

def update_self(filename,md5_sum,version,ip=MQTTServer,port=8000,ran=600):
	global stationAlias
	try:
		rdl = download(filename,md5_sum,ip,port,ran)
	except Exception,e:
		#print "download got error : %s, %s " % (Exception,e)
		logger.warning("[update_self]\033[1;33;40m Download file %s got error: %s,%s\033[0m" % (filename,Exception,e))
		#should report to server?
		
	if rdl['status'] == 'OK':
		#print "\033[0;32;40mDownload %s Successfully...\033[0m" % (filename,)
		logger.info("[update_self]Download file %s Successfully" % (filename,))
		rdp = deploy(filename)
		if rdp['status'] == 'OK':
			#print "\033[0;32;40mDeploy Successfully...\nPreparing to remove the %s restart the program...\033[0m" % (filename,)
			logger.info("[update_self]Deploy Successfully.")
			try:	
				if os.path.exists(filename):
					os.remove(filename)
			except Exception,e:
				logger.warning("[update_self]\033[1;33;40mException caught during reomove file%s:%s,%s\033[0m" % (filename,Exception,e))
			else:
				logger.info("[update_self]Removed file %s" % (filename,))
			#write back the alias ID
			try:
				write_conf('station','alias',stationAlias)
			except Exception,e:	
				logger.warning("[update_self]\033[1;33;40mcannot write stationAlias %s bakc to conf file \033[0m and going to restart raspi." % (stationAlias,))
			else:
				logger.info("[update_self]Wrote stationAlias %s back to conf file and going to call restart_raspi()" % (stationAlias,))
			restart_raspi()
			#restart_program()
		else:
			logger.warning("[update_self]\033[1;33;40mFailed to deploy file %s.\033[0m" % (filename,))
			#should report to server?
	else:
		#TODO
		logger.warning("[update_self]\033[1;33;40mFailed to download file %s.\033[0m" % (filename,))
		#should report to server?


class MqttClient(threading.Thread):
	def __init__(self,threadID,name,on_connect,on_message,on_disconnect,server,port,alivetime,sleeptime,timeout):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.on_message = on_message
		self.on_connect = on_connect
		self.on_disconnect = on_disconnect
		self.server = server
		self.port = port
		self.alivetime= alivetime 
		self.sleeptime = sleeptime
		self.timeout = timeout
	def run(self):
		global MQTTServer
		global MQTTPort
		client.on_connect = on_connect
		client.on_message = on_message
		try:
			client.connect(self.server,self.port,self.alivetime)
		except Exception,e:
			#print "\033[1;31;40mmqtt connect error (%s,%s) %s:%s\033[0m try reconnect" % (MQTTServer,MQTTPort,Exception,e)
			logger.warning("[MqttClient.run]\033[1;33;40m mqtt server %s:%s  connect error: %s,%s\033[0m and going to reconnect" % (MQTTServer,MQTTPort,Exception,e))
			reconnect_mqtt()
		while True:
			try:
				client.loop(timeout=self.timeout)
			except Exception,e:
				#print "\033[1;31;40mmqtt loop error (%s,%s) %s:%s\033[0m try reconnect" % (MQTTServer,MQTTPort,Exception,e)
				logger.warning("[MqttClient.run]\033[1;33;40mmqtt %s:%s loop error: %s,%s\033[0m and going to reconnect" % (MQTTServer,MQTTPort,Exception,e))
				reconnect_mqtt()

		
class heartBeat(threading.Thread):
	def __init__(self,threadID,name,heartbeatSleeptime):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.heartbeatSleeptime = heartbeatSleeptime
	def run(self):
		global stationAlias
		global version
		global starttime
		global hasCamera
		if has_camera():
			hasCamera = True
			logger.debug("[heartBeat.run]I got a camera!")
		else:
			hasCamera =False
			logger.debug("[heartBeat.run]Oooops,I haven't got a camera")
		while True:
			nowtime = time.time()
			heartbeat = get_system_info()
			heartbeat['version'] = version
			heartbeat['bsid'] = stationAlias
			heartbeat['script_uptime'] = "%s mins" % (str(round((nowtime-starttime)/60.0,1)),)
			heartbeat['mac'] = stationMac
			heartbeat['ip'] =  get_ip_address(ifname)
			if not heartbeat.has_key('features'):
				heartbeat['features'] = []
			if hasCamera:
				heartbeat['features'].append('camera')
			try:
				client.publish(HEARTBEATTITLE,json.dumps(heartbeat))
				#print "\033[1;31;40mheartbeat  %s\033[0m" % (json.dumps(heartbeat),)
			except Exception,e:
				#print "\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e)
				logger.warning("[heartbeat]\033[1;31;40mMqtt Exception:%s,%s [%s]\033[0m" % (MQTTServer,MQTTPort,json.dumps(heartbeat)))
				reconnect_mqtt()
			else:
				logger.info("[heartbeat]\033[1;34;40m%s\033[0m"% (json.dumps(heartbeat)),)
			time.sleep(heartbeatSleeptime)
if __name__=='__main__':
	global starttime
	global hasCamera
	global reconnect_count_mqtt 

	reconnect_count_mqtt =0 
	#global mqttClientKeepAliveTime
	starttime=time.time()
	client = mqtt.Client(client_id=stationAlias,clean_session=False)
	thread1 = MqttClient(1,'thread1',on_connect,on_message,on_disconnect,MQTTServer,MQTTPort,mqttClientKeepAliveTime,mqttClientLoopSleepTime,mqttClientLoopTimeout)
	threads.append(thread1)
	thread4 = heartBeat(4,'thread4',heartbeatSleeptime)
	threads.append(thread4)
	for i in threads:
		i.setDaemon(True)
		i.start()
	#zeroconf : get new mqtt server if exists
	zeroconf = Zeroconf()
	listener = MyListener()
	browser = ServiceBrowser(zeroconf,"_mqtt._tcp.local.", listener)

	global lastDiscoveryTime
	global s

	dataddd = get_empty_datadict()
	s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	try:
		s.connect((depHost,depPort))
		s.setblocking(0)
	except socket.error as msg:
		#print "socket error:%s" % (msg,)
		logger.warning("[__main__]\033[1;33;40msocket error %s,%s:%s\033[0m" % (depHost,depPort,msg))
	reconnect_count = 0

	lastDiscoveryTime=0
	try:
		callscanner = Scanner().withDelegate(ScanDelegate())
	except Exception,e:
		#print "\033[0;32;40m main:BLEscanner init:%s,%s\033[0m"  % (Exception,e)
		logger.warning("[main]\033[1;33;40mBLEScan init error:%s,%s\033[0m" % (Exception,e))
	count =0
	
	while True:
		try:
			devices = callscanner.scan(scannerScanTime)
		except Exception,e:
			#print "\033[0;32;40m main:callscanner:scan %s,%s\033[0m and going to sleep 5s and scan again"  % (Exception,e)
			logger.warning("[main]\033[1;33;40mcallscanner:scan %s,%s and going to sleep 5s and scan again\033[0m" % (Exception,e))
			time.sleep(5)
