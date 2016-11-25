# -*- coding: utf-8 -*-
#/usr/bin/python
import Queue,threading,signal,traceback,os
import time,sys,datetime
import paho.mqtt.client as mqtt
import json
from bluepy.btle import Scanner,DefaultDelegate
import uuid
import ConfigParser

conf = ConfigParser.ConfigParser()
conf.read('t.cnf')

POSITIONTITLE = conf.get("MQTT","position_t")
CMDTITLE = conf.get("MQTT","cmd_t")
CALLTITLE = conf.get("MQTT","call_t")
PositionQueueLength = int(conf.get("queue",'position_l'))
CommandQueueLength = int(conf.get("queue",'cmd_l'))
CallQueueLength = int(conf.get("queue","call_l"))
MQTTServer = conf.get('MQTT','server')
if conf.has_option('MQTT','port'):
	MQTTPort = int(conf.get('MQTT','port'))
else:
	MQTTPort = 1883

positionQ= Queue.Queue(PositionQueueLength)
commandQ = Queue.Queue(CommandQueueLength)
callQ = Queue.Queue(CallQueueLength)
stationAlias=conf.get('station','alias')
threads=[]
threadID=1
def get_mac_address(): 
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:] 
    return ":".join([mac[e:e+2] for e in range(0,11,2)])
stationMac = get_mac_address()
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
	client.subscribe(CMDTITLE)
	print("Connected with resut code " + str(rc))

def on_message(client,userdata,msg):
	if msg.topic == CMD_TITLE:
		commandQ.put(str(msg.payload))

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
		if sleeptime > 0:
			time.sleep(sleeptime)

def runcmd(threadName,q):
	while True:
		if not q.empty():
			data= q.get()
			print ("run cmd here " + data)
		time.sleep(10.0)

class MqttClient(threading.Thread):
	def __init__(self,threadID,name,on_connect,on_message,server,port,alivetime,sleeptime):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.on_message = on_message
		self.on_connect = on_connect
		self.server = server
		self.port = port
		self.alivetime= alivetime 
		self.sleeptime = sleeptime
	def run(self):
		client.on_connect = on_connect
		client.on_message = on_message
		client.connect(self.server,self.port,self.alivetime)
		while True:
			client.loop()
			time.sleep(self.sleeptime)

		
		
Watcher()
mqttClientKeepAliveTime = int(conf.get('time','thread_mqtt_keepalive_time'))
mqttClientLoopSleepTime = float(conf.get('time','thread_mqtt_loop_sleeptime'))
cmdSleepTime = float(conf.get('time','thread_cmd_sleep_time'))
positionSenderSleeptime = float(conf.get('time','thread_mqtt_sender_position_sleeptime'))
scannerScanTime = float(conf.get('time','main_scanner_scantime'))
callPrefix = conf.get('BLE','call_manufacturer_prefix')
braceletPrefix = conf.get('BLE','bracetlet_prefix')

client = mqtt.Client(stationAlias)
thread1 = MqttClient(1,'thread1',on_connect,on_message,MQTTServer,MQTTPort,mqttClientKeepAliveTime,mqttClientLoopSleepTime)
thread1.start()
thread2 = MqttListener(2,'thread2',commandQ)
thread2.start()
thread3 = MqttSender(3,'thread3',POSITIONTITLE,positionQ,positionSenderSleeptime)
thread3.start()


if __name__=='__main__':
	callscanner = Scanner().withDelegate(ScanDelegate())
	highestL = 0 
	count =0
	while True:
		devices = callscanner.scan(scannerScanTime)
		bracelet_data = []
		result = {}
		count +=1
		for dev in devices:
			data={}		
			try:
				for (adtype,desc,value) in dev.getScanData():
					data[desc]=value
			except UnicodeDecodeError,e:
				pass
			#00ff121382 normal／  00ff126682 call
			if (not data.has_key('Manufacturer')) or ( not data['Manufacturer'].startswith(braceletPrefix)):
				continue
			data['addr'] = dev.addr
			data['rssi'] = dev.rssi
			
			if data['Manufacturer'].startswith(callPrefix):
				#send to callQ now
				callData=data
				callData['time']=str(datetime.datetime.now())
				callData['station']=stationAlias
				callData['stationMac']=stationMac
				print "\033[1;31;40m%s\033[0m" % (json.dumps(callData,))
				client.publish(CALLTITLE,json.dumps(callData))
			bracelet_data.append(data)
			
		result['BraceletResult']=bracelet_data
		result['time'] = str(datetime.datetime.now())
		result['station'] = stationAlias
		result['stationMac'] = stationMac
		result['num']=count
		print json.dumps(result)
		positionQ.put(json.dumps(result))
