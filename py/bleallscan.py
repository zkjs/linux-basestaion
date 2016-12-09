#! /usr/bin/python

from bluepy.btle import Scanner, DefaultDelegate
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        data={}
        if dev.addr.startswith('80:ea:ca:'):
#            print "new dev: ", dev.addr
            try:
                for (adtype, desc, value) in dev.getScanData():
                    data[desc]=value
            except UnicodeDecodeError,e:
                pass
            if not data.has_key('Manufacturer'):
                return 0
            print(' %s ' % data['Manufacturer'])
#        elif isNewData:
#            print "Recv from: ", dev.addr

scanner = Scanner().withDelegate(ScanDelegate())
while True:
    devices = scanner.scan(10.0)
    for dev in devices:
        if dev.addr.startswith('80:ea:ca:'):
            print "%s, %s" % (dev.addr, dev.getScanData())

