# -*- coding: utf-8 -*-
#/usr/bin/python
import Queue,threading,signal,traceback,os
import time,sys,datetime
import paho.mqtt.client as mqtt
import json
from bluepy.btle import Scanner,DefaultDelegate
import uuid
import ConfigParser
import socket
import fcntl
import struct

conf = ConfigParser.ConfigParser()
conf.read('t.cnf')

POSITIONTITLE = conf.get("MQTT","position_t")
CMDTITLE = conf.get("MQTT","cmd_t")
CALLTITLE = conf.get("MQTT","call_t")
COMMONTITLE = conf.get("MQTT","common_t")
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
global stationAlias
global reconnect_count

stationAlias=conf.get('station','alias')
threads=[]
threadID=1
global lastDiscoveryTime
def get_mac_address(): 
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:] 
    return "".join([mac[e:e+2] for e in range(0,11,2)])
global stationMac 
stationMac = get_mac_address()
base = [str(x) for x in range(10)] + [ chr(x) for x in range(ord('A'),ord('A')+6)]
def hex2bin(string_num):
	dec = int(string_num.upper(),16)
	mid = []
	while True:
		if dec == 0: break
		dec,rem = divmod(dec, 2)
		mid.append(base[rem])
	return ''.join([str(x) for x in mid[::-1]])
	
	
def checksum_old(string):
	sum = 0
	tmp = bytearray.fromhex(string)
	for e in tmp:
		sum += e
	r = bytearray.fromhex('{:04x}',format(sum))
	return cc[-1]
#checksum based on RFC 
def checksum(b):
    sum = 0
    for e in b:
        sum += e
    cc = bytearray.fromhex('{:04x}'.format(sum))
    b = bytearray([0])
    n = cc[-1]
#    b[1]= n & 0xFF
#    n >>= 8
    b[0]= n & 0xFF
    return b

def defined(x):
	try :
		type(eval(x))
	except:
		return False
	else:
		return True
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #try to avoid net drop exceptions
    try: 
        res = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
    except:
        res = '127.0.0.1'
    return res

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
		#00ff121382 normal／  00ff126682 call
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
	
		#newdata = '%s%s%s%s%s%s' % (data['bcid'],stationAlias,stationMac,dev.addr,flag, electricity)
		#那拼数据，从包头到温度，ip转十六进制，然后整一串儿倒二进制，最后末端插一位校验和，就成了
		newdata = 'fefe%s%s%s%s%s%s%s' % (flag,stationMac,hex_ip,dev.addr.replace(':',''),hex(dev.rssi*(-1)).lstrip('0x').rjust(2,'0'),electricity,hex(temp).lstrip('0x').rjust(2,'0'))
		#print "stationMac: %s local_ip: %s(%s) bcid:%s ,rssi:%s, electricity:%s, temp:%s" % (stationMac,hex_ip,local_ip,dev.addr.replace(':',''),hex(dev.rssi*(-1)),electricity,hex(temp))
		#print "assem data: %s " % (newdata,)
		BinData = bytearray.fromhex(newdata)
		#print "after to bin:%s" % (BinData,)
		newBinData= BinData+checksum(BinData)
		arrs=[]
                for e in newBinData:
                    arrs.append(str(e))
                    #arrs.append(str(struct.unpack('B', e[0])[0]))
                print('-'.join(arrs))
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
		#print json.dumps(data)
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
		client.on_connect = on_connect
		client.on_message = on_message
		client.connect(self.server,self.port,self.alivetime)
		while True:
			client.loop(timeout=self.timeout)
			time.sleep(self.sleeptime)
#		client.loop_forever(timeout=self.timeout)

		
		
Watcher()
mqttClientKeepAliveTime = int(conf.get('time','thread_mqtt_keepalive_time'))
mqttClientLoopSleepTime = float(conf.get('time','thread_mqtt_loop_sleeptime'))
mqttClientLoopTimeout = float(conf.get('time','thread_mqtt_loop_timeout'))
cmdSleepTime = float(conf.get('time','thread_cmd_sleep_time'))
positionSenderSleeptime = float(conf.get('time','thread_mqtt_sender_position_sleeptime'))
scannerScanTime = float(conf.get('time','main_scanner_scantime'))
callFlag= conf.get('BLE','call_manufacturer_flag')
braceletFlag= conf.get('BLE','bracetlet_flag')
outbodyFlag = conf.get('BLE','outbody_manufacturer_flag')
positionFlag= conf.get('BLE','position_manufacturer_flag')
socketHost = conf.get('SOCKET','host')
socketPort = int(conf.get('SOCKET','port'))

client = mqtt.Client(client_id=stationAlias,clean_session=False)
thread1 = MqttClient(1,'thread1',on_connect,on_message,on_disconnect,MQTTServer,MQTTPort,mqttClientKeepAliveTime,mqttClientLoopSleepTime,mqttClientLoopTimeout)
thread1.start()
thread2 = MqttListener(2,'thread2',commandQ)
thread2.start()
thread3 = MqttSender(3,'thread3',POSITIONTITLE,positionQ,positionSenderSleeptime)
thread3.start()

if __name__=='__main__':
	global lastDiscoveryTime
	global s
	s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            s.connect((socketHost,socketPort))
            s.setblocking(0)
        except socket.error as msg:
            print(msg)
        reconnect_count = 0

	lastDiscoveryTime=0
	callscanner = Scanner().withDelegate(ScanDelegate())
	count =0
	
	while True:
		devices = callscanner.scan(scannerScanTime)
		now = time.time()
		if now - lastDiscoveryTime  > 30 :
			result={"status":0,"bsid":stationAlias,"timestamp":now}
			print "send common: %s " % (json.dumps(result),)
			client.publish(COMMONTITLE,json.dumps(result))
			lastDiscoveryTime = now
