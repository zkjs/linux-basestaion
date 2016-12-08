#-*- encoding=utf-8 -*-
#/usr/bin/python
import Queue, threading, signal, traceback, os
import time, sys, datetime
import paho.mqtt.client as mqtt
import json
import socket
#from struct import *
#from bluepy.btle import Scanner,DefaultDelegate
#from hskcd_checksum import checksum

#initial global states
INIT_TS = int(time.time()) #the begin ts of the script
LAST_MQTT_RESP = 0 #the last mqtt response time;
LAST_BLE_RESP = 0 #the last bluetooth signal time;
#default setting
host = '192.168.43.150'
port = 8555
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#socket creater
def do_connect():
#    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        sock.setblocking(0)
    except socket.error as msg:
        print(msg)

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
    b = bytearray([0])
    n = cc[-1]
#    b[1]= n & 0xFF
#    n >>= 8
    b[0]= n & 0xFF
    return b

#bytes to short
def bytesToShort(b, offset):
    n = (b[offset+0]<<8) + b[offset+1]
    return n
#plain script init
do_connect()

#LOOP4EVER: main
#sample 0xfefe 01 111213141516 14131211
flag = '01' # 01 heartbeat position, 02 alarm, 03 off wrist
bc_mac = '010000000000'
bc_ip = ''.join(('{:02x}'.format(01,'x'), '{:02x}'.format(0,'x'), '{:02x}'.format(00, 'x'), '{:02x}'.format(00,'x'))) 
bs_mac = '010000000000'
rssi = '01' #-44 measured rssi
battery = '01' #percent 
temp = '01' 
for i in range(1,3):
#    main_process()
#    generate data
    key=bytearray.fromhex('fefe%s%s%s%s%s%s%s' % (flag, bc_mac, bc_ip, bs_mac, rssi, battery, temp))
    print('len %s and end: %s' % (len(key), key[-1]))
    key += checksum(key) #typeerro: concat bytearray int not allowed;
    #key = pack('hhb', key, checksum(key))
    print('len %s and end: %s' % (len(key), key[-1]))
    print('sending %s' % key)
    arrs = []
    for e in key:
        arrs.append(str(e))
    print('-'.join(arrs))
    try:
        sock.send(key)
    except socket.error as msg:
        print(msg)

#data = sock.recv(1024)
#print('res: %s' % data)
