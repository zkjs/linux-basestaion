#! /usr/bin/python
# -*- coding: utf-8 -*-

import uuid, time, socket, fcntl
from protobuilder import outputbuilder
from func import *
from depconfig import *
#for json type data use : inbetween
#::predefined values::
BCTYPE00 = 'b00' 
BCTYPE01 = 'b01'
#static value of bracelet type
KEY_HEARTBEAT = '01'
KEY_ALARM = '02'
KEY_BINDING = '03'
KEY_LOST = '04'
#static value 4 bracelet state, from proto document
def get_empty_datadict():
    #datadict={keyflag, bsmac, hexip, bcmac, rssi, battery, temp, reserve}
    datadict={}
    datadict['keyflag'] = KEY_HEARTBEAT
    datadict['bsmac'] = get_mac_address()
    datadict['ip'] = get_ip_address(depIfip)
    local_ip = get_ip_address(depIfip)
    datadict['hexip'] = ''.join([hex(int(i)).lstrip('0x').rjust(2,'0') for i in local_ip.split('.')])
    datadict['bcmac'] = '010000000000'  #null bc mac;
    datadict['rssi'] = '63' #-99 predefined
    datadict['battery'] = '64' #battery level=100
    datadict['temp']= '50' #hex temp
    datadict['reserved'] = '010001000100' #predefined fixed reserved bytes
    datadict['bsmacfull'] = get_mac_address_full()
    datadict['bcaddr'] = '01:00:00:00:00:00' #predefined null bcaddr for json
    print('datadict built %s' % datadict )
    return datadict

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
        elif keyflag == '66':
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
    else:
        
        return '01'
    #the alarm update count in later phase
    print('raw translate %s' % flagdict['key'])
    return flagdict['key'] #use plain value

def gen_bin_data(datadict):
    #this generate same bin data type 4 two bc adv version
    #datadict={keyflag, bsmac, hexip, bcmac, rssi, battery, temp, reserve}
    #return 0xfefe____________________________ (checksum)
    #return bytearray.fromhex('ffff01ff01ff')
    try:
        hexdata = 'fefe%s%s%s%s%s%s%s%s' % (datadict['keyflag'], datadict['bsmac'], datadict['hexip'], datadict['bcmac'], datadict['rssi'], datadict['battery'], datadict['temp'], datadict['reserved'])
        bindata = bytearray.fromhex(hexdata)
    except:
        print('bindata = %s' % datadict)
        return bytearray.fromhex('ab01ab33')
    return bindata  + checksum(bindata[2::])

def gen_json_data(datadict):
    #this generate same json data type 4 two bc adv version
    ssdata = outputbuilder(datadict.keyflag, datadict.bsmacfull, datadict.bcaddr, 100, datadict.ip, datadict.srssi)

    return ssdata

def manu_filter(manudatabin):
    ##filter only start with 00ff12 4#bc1.0
    ##filter only start with 01ff12 4#sbc1.21
    if manudatabin == None:
        return False

    if manudatabin.startswith('00ff12'):
        return BCTYPE00
    #if matches, return bcmanu = b00/b01
    elif manudatabin.startswith('01ff12'):
        return BCTYPE01
    else:
        return False #if not matches supported bc adv packet

