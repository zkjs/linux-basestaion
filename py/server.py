#-*- encoding=utf-8 -*-
#/usr/bin/python
# Echo server program
import socket
import sys
import time
import struct
#from SocketServer import *
import SocketServer
#import SocketServer.BaseRequestHandler
HOST = '0.0.0.0'               # Symbolic name meaning all available interfaces
PORT = 8555              # Arbitrary non-privileged port
#s = None
#for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC,
#                              socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
#    af, socktype, proto, canonname, sa = res
#    try:
#        s = socket.socket(af, socktype, proto)
#    except socket.error as msg:
#        s = None
#        continue
#    try:
#        s.bind(sa)
#        s.listen(10)
#    except socket.error as msg:
#        s.close()
#        s = None
#        continue
#    break
#if s is None:
#    print 'could not open socket'
#    sys.exit(1)
#global conn
#global addr
#def sserv():
#    try:
#        while True:
#            conn, addr = s.accept()
#            print 'Connected by', addr
#while 1:
           # while True:
#                data = conn.recv(1024)
    #if data:
#                if not data: break
    #conn.send(data)
#                arrs = []
#                for e in data:
#                    arrs.append(str(struct.unpack('B', e[0])[0]))
#                print('-'.join(arrs))
    #else:
#            conn.close()
    #conn, addr = s.accept()
#    except Exception,ex:
#        print ex
    #print('%s' % data)
#conn.close()
#SocketServer()i
class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        arrs = []
        for e in self.data:
            arrs.append(str(struct.unpack('B', e[0])[0]))
        print('-'.join(arrs))

if __name__ == "__main__":
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()
