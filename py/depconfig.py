#! /usr/bin/python
#ganben rewrite 27.12.2016
import ConfigParser
import os,sys
from func import cur_file_dir

depconf = ConfigParser.ConfigParser()
depconf.read('%s/%s'% (cur_file_dir(),'dep.cnf'))

#Socket IP
depHost = depconf.get('SOCKET','host')
#Socket Port
depPort = int(depconf.get('SOCKET','port'))
#MAC TYPE=wlan0/eth0
depMac = depconf.get('SOCKET', 'mac')
#PROT MODE = B/J binary/json
depProt = depconf.get('DATA', 'type')
#SENT MODE = S/M socket/mqtt
depNet = depconf.get('DATA', 'netmode')

