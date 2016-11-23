# -*- coding: utf-8 -*-   
#! /usr/bin/python
import Queue,threading,signal,traceback,os
import time,sys
import paho.mqtt.client as mqtt
import json
from bluepy.btle import Scanner,DefaultDelegate
import ConfigParser

queueLock = threading.Lock()
conf = ConfigParser.ConfigParser()
conf.read('t.cnf')
# if config not exists:


POSITIONTITLE = conf.get("MQTT","position_t")
CMDTITLE = conf.get("MQTT","cmd_t")
PositionQueueLength = conf.get("queue",'position_l')
CommandQueueLength = conf.get("queue",'cmd_l')
MQTTServer = conf.get('MQTT','server')
if conf.has_option('MQTT','port'):
	MQTTPort = conf.get('MQTT','port')
else:
	MQTTPort = 1883

positionQ= Queue.Queue(PositionQueueLength)
commandQ = Queue.Queue(CommandQueueLength)
threads=[]
threadID=1
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


class ScanDelegate(DefaultDelegate):
        def __init__(self):
                DefaultDelegate.__init__(self)
                def handleDiscovery(self, dev, isNewDev, isNewData):
                        if isNewDev:
                                print "Discovered device", dev.addr
                        elif isNewData:
                                print "Received new data from", dev.addr

def on_connect(client,userdata,flags,rc):
	client.subscribe(POSITIONTITLE)
	client.subscribe(CMDTITLE)
	print("Connected with resut code " + str(rc))

def on_message(client,userdata,msg):
	#if msg.topic ==  POSITION_TITLE:
	#	queueLock.acquire()
	#	positionQ.put(str(msg.payload))
	#	queueLock.release()

	if msg.topic == CMD_TITLE:
		queueLock.acquire()
		commandQ.put(str(msg.payload))
		queueLock.release()

class MqttSender(threading.Thread):
	def __init__(self,threadID,name,q):
		threading.Thread.__init__(self)
		self.threadID=threadID
		self.name=name
		self.q=q
	
	def run(self):
		senddata(self.name,self.q)
		print ('sending ... ' + self.name)

class MqttListener(threading.Thread):
	def __init__(self,threadID,name,q):
		threading.Thread.__init__(self)
		self.threadID=threadID
		self.name=name
		self.q=q

	def run(self):
		runcmd(self.name,self.q)
		print('exec ... ' + self.name)

def senddata(threadName,q):
	while True:
		queueLock.acquire()
		if not q.empty():
			data = q.get()
			#ok?
			client.publish(POSITIONTITLE,data)
			queueLock.release()
			print('get ...'+data )
		else:
			queueLock.release()
		time.sleep(5)

def runcmd(threadName,q):
	while True:
		queueLock.acquire()
		if not q.empty():
			data= q.get()
			print ("run cmd here " + data)
			queueLock.release()
		else:
			queueLock.release()
		time.sleep(5)


class BLEScanner(threading.Thread):
	def __init__(self,threadID,name,q,title,Mhead,sleeptime):
		threading.Thread.__init__(self)
		self.threadID=threadID
		self.name = name
		self.q = q
		self.title = title
		self.sleeptime = sleeptime
		self.Mhead = Mhead
	def run(self):
		scanBLE(self.name,self.q,self.title,self.Mhead,self.sleeptime)
		print ('Scanning ... ')

def scanBLE(threadName,q,title,Mhead,sleeptime):
	scanner = Scanner().withDelegate(ScanDelegate())
	while True:	
		devices = scanner.scan(10.0)
		bracelet_data=[]
		result={}
		for dev in devices:
			data={}
			data['addr']=dev.addr
			data['rssi']=dev.rssi
			try:
				for (adtype,desc,value) in dev.getScanData():
					data[desc]=value
			except UnicodeDecodeError,e:
				print 'get UnicodeDecodeError: %s ... Ignore' % (e,)
			if (not data.has_key('Manufacturer')) or ( not data['Manufacturer'].startswith(Mhead)):
				continue
			bracelet_data.append(data)
		result['BraceletResult']=bracelet_data
		queueLock.acquire()
		#q.put(json.dumps(result))
		client.publish(title,json.dumps(result))
		queueLock.release()
		time.sleep(sleeptime)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTTServer,MQTTPort,60)

Watcher()


thread1 = MqttListener(1,'thread1',commandQ)
thread1.start()
#thread2 = MqttSender(2,'thread2',positionQ)
#thread2.start()
thread3 = BLEScanner(3,'thread3',positionQ,POSITIONTITLE,'00ff',5)
thread3.start()
threads.append(thread1)
#threads.append(thread2)
threads.append(thread3)

client.loop()
time.sleep(10.0)
for i in threads :
	i.join()
