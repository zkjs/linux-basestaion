#! /usr/bin/python
import paho.mqtt.client as mqtt
import json
global n
n = 0
def defined(n):
	try:
		type(eval(n))
	except:
		return False
	else:
		return True
def on_message(client,userdata,msg):
	if msg.topic == 'position':
		#print (msg.topic+" " +str(msg.payload))
		t = json.loads(msg.payload)
		global n
		if n == 0:
			n = t['num']	
			print "Init %s \033[1;32;40m%s %s\033[0m" % (n,msg.topic,str(msg.payload))
		else:
			n+=1
			if n != t['num']:
		
				print "\033[1;31;40m[%s/%s]\033[1;32;40m%s %s\033[0m" % (n,t['num'],msg.topic,str(msg.payload))
				#n=t['num']
			else:
				print "[%s/%s]\033[1;32;40m%s %s\033[0m" % (n,t['num'],msg.topic,str(msg.payload))
	elif msg.topic =='nursecall':
		#print (msg.topic+" " +str(msg.payload))
		print "\033[1;31;40m%s %s\033[0m" % (msg.topic,str(msg.payload))

def on_connect(client,userdata,flags,rc):
	print("Connected with result code " + str(rc))
	client.subscribe("position")
	client.subscribe("nursecall")

client = mqtt.Client()
client.on_connect= on_connect
client.on_message = on_message
client.connect("192.168.1.199",1883,60)
client.loop_forever()

client.on_message = on_message
