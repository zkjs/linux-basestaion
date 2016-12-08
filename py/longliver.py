#-*- encoding=utf-8 -*-
#/usr/bin/python
import Queue, threading, signal, traceback, os
import time, sys, datetime
import paho.mqtt.client as mqtt
import json
import socket
#from bluepy.btle import Scanner,DefaultDelegate
#from hskcd_checksum import checksum

#initial global states
INIT_TS = int(time.time()) #the begin ts of the script
LAST_MQTT_RESP = 0 #the last mqtt response time;
LAST_BLE_RESP = 0 #the last bluetooth signal time;
#default setting
host = '47.88.15.107'
port = 8555

#socket creater
def do_connect():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.setblocking(0)

#states checker
def mqtt_checker():
    if int(time.time())>= LAST_MQTT_RESP + 75:  #re-initialise mqtt obj
        try:
            sock.close
            do_connect()
        except e:
            print('err %s' % e)
            return False

#LOOP4EVER in child threadings


#endian converse
def endian_reverse(b):
    reverse_b = []
    for e in b:
        reverse_b= [e] + reverse_b
    print('%s' % b)
    print('%s' % reverse_b)
    return reverse_b

#checksum based on RFC 
def checksum(b):
    sum = 0
    for e in b:
        sum += e
    cc = bytearray.fromhex('{:04x}'.format(sum))
    return cc[-1]

#plain script init
do_connect()

#LOOP4EVER: main
#sample 0xfefe 01 111213141516 14131211
flag = '01' # 01 heartbeat position, 02 alarm, 03 off wrist
bc_mac = 'aa2a3a4b5b6b'
bc_ip = ''.join(format(222,'x'), format(222,'x'), format(222, 'x'), format(222,'x')) 
bs_mac = '1b2b3b1a2a3a'
rssi = '44' #-44 measured rssi
battery = '99' #percent 
temp = '20' 
for i in range(1,3):
#    main_process()
#    generate data
    key=bytearray.fromhex('fefe%s%s%s%s%s%s%s' % (flag, bc_mac, bc_ip, bs_mac, rssi, battery, temp))
    key += chechsum(key)
    print('sending %s' % key)
    sock.send(key)
data = sock.recv(1024)
print('res: %s' % data)
