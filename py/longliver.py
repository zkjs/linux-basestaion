#-*- encoding=utf-8 -*-
#/usr/bin/python
import Queue, threading, signal, traceback, os
import time, sys, datetime
import paho.mqtt.client as mqtt
import json
from bluepy.btle import Scanner,DefaultDelegate

#initial global states
INIT_TS = int(time.time()) #the begin ts of the script
LAST_MQTT_RESP = 0 #the last mqtt response time;
LAST_BLE_RESP = 0 #the last bluetooth signal time;

#states checker
def mqtt_checker():
    if int(time.time())>= LAST_MQTT_RESP + 75:  #re-initialise mqtt obj
        try:
            do_re_connect
        exception e:
            logger_sth
    return True

#LOOP4EVER in child threadings:
    while True:
        delay(INTERVAL)
        mqtt_checker()

#LOOP4EVER: main
while True:
    main_process
    key=base64.b16decode('%s%s%s%s%s' % (bcid, bsid, bs-mac, bc-mac, flag, battery))
    msg = new MqttMessage()
    msg.payload = key
    mqttclient.publish('t', msg)

