# -*- coding: utf-8 -*-   
#! /usr/bin/python
import Queue
import threading
import time
import paho.mqtt.client as mqtt
import json
from bluepy.btle import Scanner,DefaultDelegate

POSITIONTITLE='position'
CMDTITLE='cmd'
queueLock = threading.Lock()
positionQ= Queue.Queue(100)
commandQ = Queue.Queue(100)
threads=[]
threadID=1

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
			print('get ...' + data )
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
	def __init__(self,threadID,name,q):
		threading.Thread.__init__(self)
		self.threadID=threadID
		self.name = name
		self.q = q
	def run(self):
		scanBLE(self.name,self.q)
		print ('Scanning ... ')

def scanBLE(threadName,q):
	scanner = Scanner().withDelegate(ScanDelegate())
	while True:	
		devices = scanner.scan(10.0)
		bracelet_data=[]
		result={}
		for dev in devices:
			data={}
			data['addr']=dev.addr
			data['rssi']=dev.rssi
			for (adtype,desc,value) in dev.getScanData():
				data[desc]=value
			bracelet_data.append(data)
		result[dev.addr]=bracelet_data
		queueLock.acquire()
		q.put(json.dumps(result))
		queueLock.release()
		time.sleep(5)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('192.168.1.100',1883,60)

thread1 = MqttListener(1,'thread1',commandQ)
thread1.start()
thread2 = MqttSender(2,'thread2',positionQ)
thread2.start()
thread3 = BLEScanner(3,'thread3',positionQ)
thread3.start()
threads.append(thread1)
threads.append(thread2)
threads.append(thread3)

client.loop()
time.sleep(10.0)
for i in threads :
	i.join()
