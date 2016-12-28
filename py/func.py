#! /usr/bin/python
# -*- coding: utf-8 -*-
#import uuid
import uuid
import fcntl 
import struct
import random
import socket
import hashlib,urllib
import os,sys,time
import tarfile
import picamera
import requests

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #try to avoid net drop exceptions
    try: 
        res = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
    except:
        res = '127.0.0.1'
    return res


def get_mac_address(): 
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:] 
    return "".join([mac[e:e+2] for e in range(0,11,2)])


def checksum(b):
    sum = 0
    for e in b:
        sum += e
    cc = bytearray.fromhex('{:04x}'.format(sum))
    b = bytearray([0])
    n = cc[-1]
#    b[1]= n & 0xFF
#    n >>= 8
    b[0]= n & 0xFF
    return b

def restart_program():  
    """Restarts the current program. 
    Note: this function does not return. Any cleanup action (like 
    saving data) must be done before calling this function."""  
    python = sys.executable  
    os.execl(python, python, * sys.argv)  

def md5sum(fname):
    """ 计算文件的MD5值
    """
    def read_chunks(fh):
        fh.seek(0)
        chunk = fh.read(8096)
        while chunk:
            yield chunk
            chunk = fh.read(8096)
        else: #最后要将游标放回文件开头
            fh.seek(0)
    m = hashlib.md5()
    if isinstance(fname, basestring) \
            and os.path.exists(fname):
        with open(fname, "rb") as fh:
            for chunk in read_chunks(fh):
                m.update(chunk)
    #上传的文件缓存 或 已打开的文件流
    elif fname.__class__.__name__ in ["StringIO", "StringO"] \
            or isinstance(fname, file):
        for chunk in read_chunks(fname):
            m.update(chunk)
    else:
        return ""
    return m.hexdigest()

def download(filename,md5_sum,ip,port,ran):
	waittime = random.randrange(0,ran)
	print "\033[0;32;40m sleep %ss\033[0m" % (waittime,)
	time.sleep(waittime)
	print "\033[0;32;40m sleep %ss done\033[0m" % (waittime,)
	try:
		url = 'http://%s:%s/%s' % (ip,port,filename)
		urllib.urlretrieve(url,filename)
		print "\033[0;32;40m download suc\033[0m "
	except Exception,e:
		print "\033[0;32;40m download ERROR %s:%s\033[0m" % (Exception,e)
		return {'status':'Error','Info':"cannot download file %s:%s,%s" % (filename,Exception,e)}
	md5OfFile = md5sum(filename)
	if md5OfFile == md5_sum:
		print "\033[0;32;40m download md5 check ok\033[0m "
		return {'status':'OK'}
	else:
		print "\033[0;32;40m download md5 check failure receive:%s file:%s\033[0m "% (md5_sum,md5OfFile)
		return {'status':'Error','Info': 'md5 of file:%s , md5 providd:%s, doesn\'t match.' % (md5OfFile,md5_sum)}
		
def extract(tar_path, target_path):
    try:
        tar = tarfile.open(tar_path, "r")
        file_names = tar.getnames()
        for file_name in file_names:
            tar.extract(file_name, target_path)
        tar.close()
    except Exception, e:
        raise Exception, e

def deploy(filename):
	try:
		extract(filename,cur_file_dir())		
	except Exception,e:
		pass
	return {'status':'OK'}

def parseArgs2Dict(cmd_line):
	args_array = cmd_line.split()
	args_hash = {}
	for i in args_array:
		if i.startswith('-'):
			args_hash[i[1]] = i[2:]
	return args_hash

def cur_file_dir():
     path = sys.path[0]
     if os.path.isdir(path):
         return path
     elif os.path.isfile(path):
         return os.path.dirname(path)

def take_photo(filename,filedir,picResolutionV,picResolutionH,cameraReviewed,hottime):
	camera = picamera.PiCamera()
	#print pic
	camera.resolution = (picResolutionH,picResolutionV)
	if not cameraReviewed:
		camera.start_preview()
		time.sleep(hottime)
		camera.capture('%s/%s/%s' % (cur_file_dir(),filedir,filename,))
		camera.stop_preview()
		#cameraReviewed = True
	else:
		camera.capture('%s/%s/%s' % (cur_file_dir(),filedir,filename,))
	camera.close()

def send_photo(filename,filedir,ip,port,bsid,bcid,now):
	pic = open('%s/%s/%s' % (cur_file_dir(),filedir,filename))
	url_path = 'http://%s:%s/photo/%s?bracelets=%s&time=%s' % (ip,port,bsid,bcid,now)
	print "\033[1;31;40mURL:%s\033[0m" % (url_path,)
	res = requests.post(url = url_path,
                    data=pic,
		    headers={'Content-Type': 'image/jpeg'})
	print "\033[1;31;40m%s \033[0m " % (res,)
	print "\033[1;31;40m%s \033[0m " % (res.status_code,)
	if res.status_code == 200 :
		os.remove('%s/%s/%s' % (cur_file_dir(),filedir,filename))
		return True
