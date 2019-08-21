#coding=UTF-8

import os   #Python的标准库中的os模块包含普遍的操作系统功能
import re   #引入正则表达式对象
import urllib   #用于对URL进行编解码
import util.db as db #db操作类
import json
import time
from urlparse import urlparse
import socket
import socket
import sys
import random
import util.helper as helper #工具集
import util.db as db #db操作类

HOST, PORT = "192.168.1.119", 9999
# Create a socket (SOCK_STREAM means a TCP socket)

try:
    n = 0
    while True:
        for i in range(1, 5):
            n += 1
            data = ",".join(['put', 'b' + str(n) + '_' + str(i) + '_' + str(random.random())])
            print data
            # Connect to server and send data
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            sock.sendall(bytes(data + "\n"))

            # Receive data from the server and shut down
            received = str(sock.recv(1024))
            # print i
            # print("Sent:     {}".format(data))
            # print("Received: {}".format(received))
            helper.getLog(received + ' -- ' + data, 'mq.client.put2.txt')
        time.sleep(0.01)
finally:
    sock.close()
    pass




