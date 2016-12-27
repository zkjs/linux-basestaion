#! /usr/bin/python
# -*- coding: utf-8 -*-

import uuid, time, socket, fcntl
#for json type data use : inbetween
BCTYPE00 = 'b00' 
BCTYPE01 = 'b01'
#static value of bracelet type
KEY_HEARTBEAT = '01'
KEY_ALARM = '02'
KEY_BINDING = '03'
KEY_LOST = '04'
#static value 4 bracelet state, from proto document

def get_mac_address_full():
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ':'.join([mac[e:e+2] for e in range(0,11,2)])

#for bc1.0 count conseq alarm times4 binding flag
def alarm_update(bcid, flag):
    global alarm_cache
    global position_cache
    #position cache for time, alarm cache for counts for each bcid
    bc = str(bcid)
    f=str(flag)
    if f == '13':
        alarm_cache[bc]=0
        return False
    elif f == '66' and alarm_cache[bc] >=7 :
        alarm_cache[bc]=0
        return True
    elif f == '66' and alarm_cache[bc] < 7:
        alarm_cache[bc] += 1
        print('alarmtimes=%s' % alarm_cache[bc])
        return False

def rawdata_translate(manufdata):
    #this is 4 raw data collect and return a expected data prot
    #as demanded type
    flagdict = {}
    bctype = manu_filter(manufdata)
    if bctype == BCTYPE00:
        keyflag = manufdata[6:8]
        if keyflag == '13':
            flagdict['key'] = KEY_HEARTBEAT
        elif: keyflag == '66':
            flagdict['key'] = KEY_ALARM
        #the alarm update count in later 
    elif bctype == BCTYPE01:
        statflag = manufdata[6:8]
        keyflag = manufdata[8:10]
        if keyflag == '80':
            flagdict['key'] = KEY_ALARM
        elif keyflag == '00' and statflag == '14' :
            flagdict['key'] = KEY_LOST
        else:
            flagdict['key'] = KEY_HEARTBEAT            
        #the alarm update count in later phase

    return flagdict

def gen_bin_data(datadict, bcmanu):
    #this generate same bin data type 4 two bc adv version

    return bin

def gen_json_data(datadict, bcmanu):
    #this generate same json data type 4 two bc adv version

    return json

def manu_filter(manudatabin):
    ##filter only start with 00ff12 4#bc1.0
    ##filter only start with 01ff12 4#sbc1.21
    if manudatabin == None:
        return False

    if manudatabin.startswith(braceletFlag):
        return BCTYPE00
    #if matches, return bcmanu = b00/b01
    elif manudatabin.startswith('01ff12'):
        return BCTYPE01
    else:
        return False #if not matches supported bc adv packet

