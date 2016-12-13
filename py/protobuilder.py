# -*- coding: utf-8 -*-
#/usr/bin/python
import time,sys,datetime
import json

def outputbuilder(bccommand,bsmac,bcmac,battery,bsip,rssi):
    data={}
    #data builder
    #bsmac=basestation socket/wlan/ethernet mac
    #bcmac=bracelet bt mac
    #rssi=scanned rssi
    #bsip=basestation socket/ip
    #temp no input
    #battery until next bc version
    #bccommand = key, 13, 66, 68 etc;
    #bccommand = value, 2004, 2001, 2002, etc
    cmdict = {'13': 2004, '66': 2001, '68':2002}
    cm = cmdict.get(bccommand, False)
    if cm:
        data['Command'] = cm
    else:
        data['Command'] = 2004
    #mac 
    if not bsmac == None:# and len(bsmac) == 12:           
        data['APMac']=bsmac
    else:
        data['APMac']='0a:0a:0a:01:01:01'
    
    if not bcmac == None:# and len(bcmac) == 12:
        data['DevMac']=bcmac
    else:
        data['DevMac']='a0:a1:a3:01:02:03'
    #ip
    if not bsip == None:
        data['APAddress'] = bsip
    #generated battery 100, empty temp and port, rssi
    data['Power'] = battery
    data['Temperature'] = 0
    data['APPort']=0
    data['RSSI']=rssi
    #finally parse exception
    try:
        res = json.dumps(data)
    except:
        res = None
    
    return res+'\n'      #according to requirements, the json end with \n

