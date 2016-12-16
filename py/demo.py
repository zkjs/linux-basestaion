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
#<<<<<<< littlepinkyl
from zeroconf import ServiceBrowser, Zeroconf
import urllib 
import urllib2 
import requests
#from six.moves import input
#from ftplib import FTP
from func import *
from var import *

#=======
from protobuilder import outputbuilder

#conf = ConfigParser.ConfigParser()
#conf.read('t.cnf')
#SEND MODE = SJ=socket json, SB=socket Binary, MJ=mqtt json
SENDMODE = conf.get("DATA","MODE")
#POSITIONTITLE = conf.get("MQTT","position_t")
#CMDTITLE = conf.get("MQTT","cmd_t")

#CALLTITLE = conf.get("MQTT","call_t")
#COMMONTITLE = conf.get("MQTT","common_t")
#PositionQueueLength = int(conf.get("queue",'position_l'))
#CommandQueueLength = int(conf.get("queue",'cmd_l'))
#CallQueueLength = int(conf.get("queue","call_l"))
#MQTTServer = conf.get('MQTT','server')
#if conf.has_option('MQTT','port'):#
#	MQTTPort = int(conf.get('MQTT','port'))
#else:
#	MQTTPort = 1883

#positionQ= Queue.Queue(PositionQueueLength)
#commandQ = Queue.Queue(CommandQueueLength)
#callQ = Queue.Queue(CallQueueLength)
#>>>>>>> master
global stationAlias
global reconnect_count
global lastDiscoveryTime
global stationMac 

threads=[]
threadID=1
#<<<<<<< littlepinkyl
#=======
global lastDiscoveryTime
#pure mac without :
#def get_mac_address(): 
#    mac=uuid.UUID(int = uuid.getnode()).hex[-12:] 
#    return "".join([mac[e:e+2] for e in range(0,11,2)])
#full mac with :
def get_mac_address_full():
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ':'.join([mac[e:e+2] for e in range(0,11,2)])

#global stationMac 
#>>>>>>> master
stationMac = get_mac_address()
positionQ= Queue.Queue(PositionQueueLength)
commandQ = Queue.Queue(CommandQueueLength)
callQ = Queue.Queue(CallQueueLength)

class Watcher:
    """this class solves two problems with multithreaded 
    programs in Python, (1) a signal might be delivered 
    to any thread (which is just a malfeature) and (2) if 
    the thread that gets the signal is waiting, the signal 
    is ignored (which is a bug). 
 
    The watcher is a concurrent process (not thread) that 
    waits for a signal and the process that contains the 
    threads.  See Appendix A of The Little Book of Semaphores. 
    http://greenteapress.com/semaphores/ """

    def __init__(self):
        """ Creates a child thread, which returns.  The parent 
            thread waits for a KeyboardInterrupt and then kills 
            the child thread. 
        """
        self.child = os.fork()
        if self.child == 0:
            return
        else:
            self.watch()

    def watch(self):
        try:
            os.wait()
        except KeyboardInterrupt:
            # I put the capital B in KeyBoardInterrupt so I can  
            # tell when the Watcher gets the SIGINT  
            print 'KeyBoardInterrupt'
            self.kill()
        sys.exit()

    def kill(self):
        try:
            os.kill(self.child, signal.SIGKILL)
        except OSError: pass


def reconnect():
    #count reconnect counts, if bigger than 200, do reconn
    global reconnect_count
    global s
    reconnect_count += 1
    if reconnect_count>= 2:
        reconnect_count = 0
        try:
            s.close()
        except socket.error as msg:
            print(msg)
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect((socketHost,socketPort))
        except socket.error as msg:
            print(msg)
def alarm_update(bcid, flag):
    global alarm_cache
    global position_cache
    #position cache for time, alarm cache for counts for each bcid
    bc = str(bcid)
    f=str(flag)
    if f == '13':
        alarm_cache[bc]=0
        return False
    elif f == '66' and alarm_cache[bc] >=7 :
        alarm_cache[bc]=0
        return True
    elif f == '66' and alarm_cache[bc] < 7:
        alarm_cache[bc] += 1
        print('alarmtimes=%s' % alarm_cache[bc])
        return False


class ScanDelegate(DefaultDelegate):
        def __init__(self):
                DefaultDelegate.__init__(self)
	def handleDiscovery(self, dev, isNewDev, isNewData):
		global stationAlias,stationMac
		data = {}
		timestamp = time.time()
		global lastDiscoveryTime
		global s
                #global alarm_cache
                #global position_cache
		try:
			for (adtype,desc,value) in dev.getScanData():
				data[desc]=value
		except UnicodeDecodeError,e:
			pass
#<<<<<<< littlepinkyl
		#print "%s，%s" % (data['Manufacturer'],braceletFlag)
		if (not data.has_key('Manufacturer')) or ( not data['Manufacturer'].startswith(braceletFlag)):
#=======
		#00ff121382 normal／  00ff126682 call
#                if (not data.has_key('Manufacturer')) or ( not data['Manufacturer'].startswith(braceletFlag)): #and (not data['Manufacturer'].startswith(braceletFlag2)) and (not data['Manufacturer'].startswith(braceletFlag3)):
#>>>>>>> master
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
		local_ip = get_ip_address('eth0')    #swap for wlan0 for convenience
		hex_ip = ''.join([hex(int(i)).lstrip('0x').rjust(2,'0') for i in local_ip.split('.')])
		temp = 50
                reserved = '010001000100' #fixed reserved bytes
	
#<<<<<<< littlepinkyl#
#		newdata = 'fefe%s%s%s%s%s%s%s' % (flag,stationMac,hex_ip,dev.addr.replace(':',''),hex(dev.rssi*(-1)).lstrip('0x').rjust(2,'0'),electricity,hex(temp).lstrip('0x').rjust(2,'0'))
#		BinData = bytearray.fromhex(newdata)
#		newBinData= BinData+checksum(BinData)
#		arrs=[]
#                for e in newBinData:
#                    arrs.append(str(e))
#=======
		#newdata = '%s%s%s%s%s%s' % (data['bcid'],stationAlias,stationMac,dev.addr,flag, electricity)
		#那拼数据，从包头到温度，ip转十六进制，然后整一串儿倒二进制，最后末端插一位校验和，就成了
		newdata = 'fefe%s%s%s%s%s%s%s%s' % (flag,stationMac,hex_ip,dev.addr.replace(':',''),hex(dev.rssi*(-1)).lstrip('0x').rjust(2,'0'),electricity,hex(temp).lstrip('0x').rjust(2,'0'), reserved)
		#print "stationMac: %s local_ip: %s(%s) bcid:%s ,rssi:%s, electricity:%s, temp:%s" % (stationMac,hex_ip,local_ip,dev.addr.replace(':',''),hex(dev.rssi*(-1)),electricity,hex(temp))
		#print "assem data: %s " % (newdata,)
		BinData = bytearray.fromhex(newdata)
		#print "after to bin:%s" % (BinData,)
                newBinData= BinData+checksum(BinData[2::])
		#arrs=[]
                #for e in newBinData:
                #    arrs.append(str(e))
#>>>>>>> master
                    #arrs.append(str(struct.unpack('B', e[0])[0]))
                #print('-'.join(arrs))
                #newBinData = base64.b16decode(newdata)
		#print "send bin data: %s, last %s" % (newBinData,checksum(BinData))
		#send to where
                #!the sent must count first, every 3 packet sent one position packet
                #!if shortly 10 + alarm count, then sent a regist count (flag=70);
                #!see the method: alarm_update()
                
                
                try:
                    #re-use present socket link;
                    #rather than close and open a new socket;
                    #this is only happen every 50 fails 
                    #s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    #s.connect((socketHost, socketPort))
                    if SENDMODE == 'SB':# and alarm_update(flag):
                        s.send(newBinData)
                    #s.sendall(newBinData) #this caused a flush on recv side
                    #print('-'.join(arrs))
                    elif SENDMODE == 'SJ':# and alarm_update(flag):
                        s.send(outputbuilder(flag,get_mac_address_full(),dev.addr,100,local_ip,dev.rssi))
                        if alarm_update(data['bcid'], flag):                        
                            s.send(outputbuilder('70',get_mac_address_full(),dev.addr,100,local_ip,dev.rssi))
                            print('sent 70xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
                    #s.close()
                except socket.error as msg:
                    #s.close()
                    global reconnect_count
                    print('%s(%s)' % (msg, reconnect_count))
                    reconnect()

		#rc = s.recv(1024)
		#print rc

		if data['Manufacturer'].startswith(callFlag,6):
			callData=data
			callData['nursecall'] = True
			print "\033[1;31;40m%s\033[0m" % (json.dumps(callData,))
			client.publish(CALLTITLE,json.dumps(callData))
			lastDiscoveryTime = time.time()
			return 0	
		elif data['Manufacturer'].startswith(outbodyFlag,6):
			outbodyData = data
			client.publish(COMMONTITLE,json.dumps(outbodyData))
			lastDiscoveryTime = time.time()
			return 0
		positionQ.put(json.dumps(data))
		print json.dumps(data)
		lastDiscoveryTime = time.time()

def on_connect(client,userdata,flags,rc):
	client.subscribe(CMDTITLE)
	print("Connected with resut code " + str(rc))

def on_disconnect(client, userdata, rc):      
	while rc != 0:
	 	sleep(2)
		print "Reconnecting..."
		rc = client.reconnect()

def on_message(client,userdata,msg):
	if msg.topic == CMD_TITLE:
		commandQ.put(str(msg.payload))

class MyListener(object):

    def remove_service(self, zeroconf, type, name):
	#TODO:?
        #print("Service %s removed" % (name,))
	pass

    def add_service(self, zeroconf, type, name):
	global MQTTServer,MQTTPort,client
        info = zeroconf.get_service_info(type, name)
        #print("Service %s added, service info: %s" % (name, info))
	if info.server 	!= MQTTServer or info.port != MQTTPort:
		MQTTServer = info.server
		MQTTPort = info.port
		client.disconnect()
		client.connect(MQTTServer,MQTTPort,mqttClientKeepAliveTime)

class MqttSender(threading.Thread):
	def __init__(self,threadID,name,title,q,sleeptime):
		threading.Thread.__init__(self)
		self.threadID=threadID
		self.name=name
		self.q=q
		self.title = title
		self.sleeptime = sleeptime	
		
	def run(self):
		senddata(self.name,self.title,self.q,self.sleeptime)

class MqttListener(threading.Thread):
	def __init__(self,threadID,name,q):
		threading.Thread.__init__(self)
		self.threadID=threadID
		self.name=name
		self.q=q

	def run(self):
		runcmd(self.name,self.q)
		print('exec ... ' + self.name)

def senddata(threadName,title,q,sleeptime):
	while True:
		while not q.empty():
			data = q.get()
			client.publish(title,data)
			print "sended %s " % (data,)
		if sleeptime > 0:
			time.sleep(sleeptime)

def runcmd(threadName,q):
	global MQTTServer,MQTTPort
	while True:
		if not q.empty():
			data= q.get()
			if data.startswith('update'):
				#parse args update -f[filename]* -i[ip/domain] -p[port]  -r[random range] -v[version] -P[path]
				ArgsDict = {}
				data = data.lstrip('update')
				ArgsArray = data.split(' ')
				for i in ArgsArray:
					if i.startswith('-'):
						if i[1] in ['i','p','f','r','P','v']:
							ArgsDict[i[1]] = i[2:]
						else:
							#i don't know how to react	
							pass
					else:
						#i don't know how to react
						pass
				if (not ArgsDict.has_key('f')) or (ArgsDict.has_key('i') and (not ArgsDict.has_key('p'))) or (not ArgDict.has_key('v'):
					#shoule rase Exception ,return and exit
					pass
				if type(ArgsDict['v']) != type('1.1'):
					f=ArgsDict['v']	
					try:
						ArgsDict['v'] = float(f)
					except Exception,e:
						#TODO
						pass
				if not ArgsDict.has_key('i'):
					ArgsDict['i'] = MQTTServer
				if not ArgsDict.has_key('p'):
					ArgsDict['p'] = 8000 
				if not ArgsDict.has_key('r'):
					ArgsDict['r'] = 600
				#call thd func
				if ArgsDict['v'] > version:
					update_self(ArgsDict['f'],ArgsDict['i'],ArgsDict['p'],ArgsDict['v'],ArgsDict['r'])	
				pass
			print ("run cmd here " + data)
		time.sleep(10.0)

def update_self(filename,ip,port,version,ran):
	
        waittime = random.randrange(0,ran)
        count = 5
	suc = False
	#print "sleep %f seconds " % (waittime,)
        time.sleep(waittime)
	#print "sleep done "
        url = 'http://%s:%s/%s' % (ip,port,filename)
        while not suc and count >= 0:
                try :
			#print "downloading..."
                        urllib.urlretrieve(url,filename)
			#print "set suc to True"
			suc = True
                except Exception,e:
                        count-=1
			#print "Fail, sleep 10s and retry remain %d times" % (count,)			
			time.sleep(10)
	if suc:			
		restart_program()
	else:
		#log sth
		pass
			
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
		client.connect(self.server,self.port,self.alivetime)
		while True:
			#if MQTTServer != self.server or MQTTPort != self.port:
			#	disconnect()
			#	self.server = MQTTServer
			#	self.port = MQTTPort
			#	client.connect(self.server,self.port,self.alivetime)
			client.loop(timeout=self.timeout)
			time.sleep(self.sleeptime)

		
#<<<<<<< littlepinkyl
#=======
		
#Watcher()
#mqttClientKeepAliveTime = int(conf.get('time','thread_mqtt_keepalive_time'))
#mqttClientLoopSleepTime = float(conf.get('time','thread_mqtt_loop_sleeptime'))
#mqttClientLoopTimeout = float(conf.get('time','thread_mqtt_loop_timeout'))
#cmdSleepTime = float(conf.get('time','thread_cmd_sleep_time'))
#positionSenderSleeptime = float(conf.get('time','thread_mqtt_sender_position_sleeptime'))
#scannerScanTime = float(conf.get('time','main_scanner_scantime'))
#callFlag= conf.get('BLE','call_manufacturer_flag')
#braceletFlag= conf.get('BLE','bracetlet_flag')
#braceletFlag2=conf.get('BLE','bracelet2_flag')
#braceletFlag3=conf.get('BLE','bracelet3_flag')
#outbodyFlag = conf.get('BLE','outbody_manufacturer_flag')
#positionFlag= conf.get('BLE','position_manufacturer_flag')
#socketHost = conf.get('SOCKET','host')
#socketPort = int(conf.get('SOCKET','port'))

#client = mqtt.Client(client_id=stationAlias,clean_session=False)
#thread1 = MqttClient(1,'thread1',on_connect,on_message,on_disconnect,MQTTServer,MQTTPort,mqttClientKeepAliveTime,mqttClientLoopSleepTime,mqttClientLoopTimeout)
#thread1.start()
#thread2 = MqttListener(2,'thread2',commandQ)
#thread2.start()
#thread3 = MqttSender(3,'thread3',POSITIONTITLE,positionQ,positionSenderSleeptime)
#thread3.start()

#>>>>>>> master
if __name__=='__main__':
	Watcher()
	client = mqtt.Client(client_id=stationAlias,clean_session=False)
	thread1 = MqttClient(1,'thread1',on_connect,on_message,on_disconnect,MQTTServer,MQTTPort,mqttClientKeepAliveTime,mqttClientLoopSleepTime,mqttClientLoopTimeout)
	thread1.start()
	thread2 = MqttListener(2,'thread2',commandQ)
	thread2.start()
	thread3 = MqttSender(3,'thread3',POSITIONTITLE,positionQ,positionSenderSleeptime)
	thread3.start()
	#listen to zeroconf to check if mqtt server change
	zeroconf = Zeroconf()
	listener = MyListener()
	browser = ServiceBrowser(zeroconf,"_mqtt._tcp.local.", listener)

	global lastDiscoveryTime
	global s
        global position_cache
        global alarm_cache
        position_cache = {}
        alarm_cache = {}
	s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            s.connect((socketHost,socketPort))
            s.setblocking(0)
        except socket.error as msg:
	    print "socket error:"
            print(msg)
        reconnect_count = 0

	lastDiscoveryTime=0
	callscanner = Scanner().withDelegate(ScanDelegate())
	count =0
	
	while True:
            try:
                devices = callscanner.scan(scannerScanTime)
		#now = time.time()
		#if now - lastDiscoveryTime  > 30 :
		#	result={"status":0,"bsid":stationAlias,"timestamp":now}
		#	print "send common: %s " % (json.dumps(result),)
		#	client.publish(COMMONTITLE,json.dumps(result))
		#	lastDiscoveryTime = now
            except:
		#print e
                time.sleep(5)
