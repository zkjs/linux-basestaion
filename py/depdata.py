#! /usr/bin/python
# -*- coding: utf-8 -*-

import uuid, time, socket, fcntl
#for json type data use : inbetween
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

def rawdata_translate(rawbin):
    #this is 4 raw data collect and return a expected data prot
    #as demanded type
    

    return resdict

def gen_bin_data(datadict, bcmanu):
    #this generate same bin data type 4 two bc adv version

    return bin

def gen_json_data(datadict, bcmanu):
    #this generate same json data type 4 two bc adv version

    return json

def manu_filter(manudatabin):
    ##

    return True #if matches

    return False #if not matches supported bc adv packet

