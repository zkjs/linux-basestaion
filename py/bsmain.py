# -*- coding: utf-8 -*-
#/usr/bin/python
#bsmain.py
#ganben: a rewriten main entrance for modulated parts
#other modules
from protobuilder import outputbuilder #who build the json data
from var import *
from func import *


#sys packages
from bluepy.btle import Scanner, DefaultDelegate
import socket, struct, time, sys, datetime, json, uuid



if __name__ == '__main__':
    
