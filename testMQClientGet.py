#coding=UTF-8

import os   #Python的标准库中的os模块包含普遍的操作系统功能
import re   #引入正则表达式对象
import urllib   #用于对URL进行编解码
import util.db as db #db操作类
import time
import json
from urlparse import urlparse
import socket
import socket
import sys
import util.helper as helper #工具集
import util.db as db #db操作类

HOST, PORT = "192.168.1.119", 9999
# Create a socket (SOCK_STREAM means a TCP socket)

try:
    while True:
        data = ",".join(['get', 'client1'])
        # print data
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(bytes(data + "\n"))

        # Receive data from the server and shut down
        received = str(sock.recv(1024))
        if len(received) > 1:
            print("Sent:     {}".format(data))
            print("Received: {}".format(received))
            for v in eval(received):
                helper.getLog(str(v), 'mq.client.get1.txt')

        time.sleep(0.1)
finally:
    sock.close()




