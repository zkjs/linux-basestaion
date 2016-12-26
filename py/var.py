#! /usr/bin/python

import ConfigParser
import os,sys
def cur_file_dir():
     path = sys.path[0]
     if os.path.isdir(path):
         return path
     elif os.path.isfile(path):
         return os.path.dirname(path)
conf = ConfigParser.ConfigParser()
conf.read('%s/%s'% (cur_file_dir(),'t.cnf'))

POSITIONTITLE = conf.get("MQTT","position_t")
CMDTITLE = conf.get("MQTT","cmd_t")
CALLTITLE = conf.get("MQTT","call_t")
COMMONTITLE = conf.get("MQTT","common_t")
PositionQueueLength = int(conf.get("queue",'position_l'))
CommandQueueLength = int(conf.get("queue",'cmd_l'))
CallQueueLength = int(conf.get("queue","call_l"))
global MQTTserver
global MQTTPort
MQTTServer = conf.get('MQTT','server')
if conf.has_option('MQTT','port'):
	MQTTPort = int(conf.get('MQTT','port'))
else:
	MQTTPort = 1883

stationAlias=conf.get('station','alias')
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

#upload data configs,
#SEND MODE = SJ=socket json, SB=socket Binary, MJ=mqtt json