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
#from six.moves import input
#from ftplib import FTP
from func import *
from var import *

global stationAlias
global reconnect_count
global lastDiscoveryTime
global stationMac 

threads=[]
threadID=1
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

class ScanDelegate(DefaultDelegate):
        def __init__(self):
                DefaultDelegate.__init__(self)
	def handleDiscovery(self, dev, isNewDev, isNewData):
		global stationAlias,stationMac
		data = {}
		timestamp = time.time()
		global lastDiscoveryTime
		global s
		try:
			for (adtype,desc,value) in dev.getScanData():
				data[desc]=value
		except UnicodeDecodeError,e:
			pass
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
		local_ip = get_ip_address('wlan0')
		hex_ip = ''.join([hex(int(i)).lstrip('0x').rjust(2,'0') for i in local_ip.split('.')])
		temp = 50
	
		newdata = 'fefe%s%s%s%s%s%s%s' % (flag,stationMac,hex_ip,dev.addr.replace(':',''),hex(dev.rssi*(-1)).lstrip('0x').rjust(2,'0'),electricity,hex(temp).lstrip('0x').rjust(2,'0'))
		BinData = bytearray.fromhex(newdata)
		newBinData= BinData+checksum(BinData)
		arrs=[]
                for e in newBinData:
                    arrs.append(str(e))
                    #arrs.append(str(struct.unpack('B', e[0])[0]))
                #print('-'.join(arrs))
                #newBinData = base64.b16decode(newdata)
		#print "send bin data: %s, last %s" % (newBinData,checksum(BinData))
		#send to where
                try:
                    #re-use present socket link;
                    #rather than close and open a new socket;
                    #this is only happen every 50 fails 
                    #s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    #s.connect((socketHost, socketPort))
                    s.sendall(newBinData)
                    print('-'.join(arrs))
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
	print "[get] topic %s , payload:%s " % (msg.topic, str(msg.payload))
	if msg.topic == CMDTITLE:
		commandQ.put(str(msg.payload))
		print "[get] %s " % (str(msg.payload),)

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
		print('exec ... ' + self.name)
		runcmd(self.name,self.q)

def senddata(threadName,title,q,sleeptime):
	while True:
		while not q.empty():
			data = q.get()
			client.publish(title,data)
			print "sended %s " % (data,)
		if sleeptime > 0:
			time.sleep(sleeptime)

def runcmd(threadName,q):
	
	print "\033[0;32;40m runcmd  \033[0m" 
	global MQTTServer,MQTTPort
	while True:
		print "\033[0;32;40m looping in runcmd %s while \033[0m"  % (q,)
		if not q.empty():
			data= q.get()
			print "\033[0;32;40m get %s\033[0m"  % (data,)
			if data.startswith('update'):
				print "\033[0;32;40mget cmd as %s \033[0m" % (data,)
				#parse args update -f[filename]* -m[md5_sum]* -i[ip/domain] -p[port]*  -r[random range] -v[version]*
				ArgsDict = parseArgs2Dict(data.lstrip('update'))
				if (not ArgsDict.has_key('f')) or (ArgsDict.has_key('i') and (not ArgsDict.has_key('p'))) or (not ArgsDict.has_key('v')) or (not ArgsDict.has_key('m')):
					#shoule rase Exception ,return and exit
					print "Error: lack some para"
					return 
				try:
					if float(ArgsDict['v']) > version:
						print "\033[0;32;40m new version upgrade command received \033[0m"
						if not ArgsDict.has_key('i'):
							ArgsDict['i'] = MQTTServer
						if not ArgsDict.has_key('p'):
							ArgsDict['p'] = MQTTPort
						if not ArgsDict.has_key('r'):
							ArgsDict['r'] = 600
						update_self(ArgsDict['f'],ArgsDict['m'],ArgsDict['v'],ArgsDict['i'],ArgsDict['p'],int(ArgsDict['r']))	
					else:
						#should log sth
						print "033[0;32;40m current version : %f, order version :%f\033[0m " % (version,ArgsDict['v'])
						pass	
				except Exception,e:
					print "\033[0;32;40m get %s:%s\033[0m"  % (Exception,e)
					pass
		time.sleep(10.0)

#def update_self(ip=MQTTServer,port=8000,ran=600,filename,md5_sum,version):
def update_self(filename,md5_sum,version,ip=MQTTServer,port=8000,ran=600):
	try:
		rdl = download(filename,md5_sum,ip,port,ran)
	except Exception,e:
		print Exception,e
		
	if rdl['status'] == 'OK':
		print "\033[0;32;40mDownload %s Successfully...\033[0m" % (filename,)
		rdp = deploy(filename)
		if rdp['status'] == 'OK':
			print "\033[0;32;40mDeploy Successfully...\nPreparing to remove the %s restart the program...\033[0m" % (filename,)
			if os.path.exist(filename):
				os.remove(filename)
			restart_program()
		else:
			#TODO
			#log sth
			pass
	else:
		#log sth
		#TODO
		pass

        #waittime = random.randrange(0,ran)
        #count = 5
	#suc = False
	##print "sleep %f seconds " % (waittime,)
        #time.sleep(waittime)
	##print "sleep done "
        #while not suc and count >= 0:
        #        try :
	#		#print "downloading..."
	#		url = 'http://%s:%s/%s' % (ip,port,filename)
        #                urllib.urlretrieve(url,filename)
	#		#print "set suc to True"
	#		suc = True
        #        except Exception,e:
        #                count-=1
	#		#print "Fail, sleep 10s and retry remain %d times" % (count,)			
	#		time.sleep(10)
	#if suc:			
	#	restart_program()
	#else:
	#	#log sth
	#	pass
			


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

		
if __name__=='__main__':
	Watcher()
	client = mqtt.Client(client_id=stationAlias,clean_session=False)
	thread1 = MqttClient(1,'thread1',on_connect,on_message,on_disconnect,MQTTServer,MQTTPort,mqttClientKeepAliveTime,mqttClientLoopSleepTime,mqttClientLoopTimeout)
	thread1.start()
	thread2 = MqttListener(2,'command',commandQ)
	thread2.start()
	thread3 = MqttSender(3,'thread3',POSITIONTITLE,positionQ,positionSenderSleeptime)
	thread3.start()
	#listen to zeroconf to check if mqtt server change

	# just for debug
	zeroconf = Zeroconf()
	listener = MyListener()
	browser = ServiceBrowser(zeroconf,"_mqtt._tcp.local.", listener)

	global lastDiscoveryTime
	global s
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
