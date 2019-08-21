#coding=UTF-8

import time
import threading
import string
import json
import urllib,urllib2,httplib
import MySQLdb
import util.helper as helper #工具集
import sys
from pyDes import *

from binascii import b2a_hex, a2b_hex
import base64



def runService():
    t1 = helper.thisTime()
    re = urllib2.urlopen('http://192.168.1.119/testhtml/test/test.php').read()
    t2 = helper.thisTime()
    re = re + ' -- ' + str(t1) + ' -- ' + str(t2) + ' -- ' + str( t2 - t1 )
    helper.getLog(re)

# 获取用户ids
def serviceInit():
    ts = []
    i = 0;
    while i < 200 :
        t = threading.Thread(target = runService, args=())
        t.start()
        # t.join()

        i += 1

if __name__ == "__main__":
    #serviceInit()

    print "sa'df'".replace("'", '"');exit();

    print 's'
    data = '{"pageIndex":1,"pageSize":100}' # 1/F4jrg9alyN0uDgJNlEaCLroiTtH9LhlljImdztF8Y=
    KEY = "45643149"    #密钥
    IV = "45643149"     #偏转向量
    # 使用DES对称加密算法的CBC模式加密
    k = des(KEY, ECB, IV, pad=None, padmode=PAD_PKCS5)
    d = k.encrypt(data)
    # print base64.encodestring(b2a_hex(d))
    print base64.encodestring(d)
    print "Decrypted: %r" % k.decrypt(d)


    # str = '一二三四1五六七八九十百千万';
    # print str[0:30]

    print 'end'







