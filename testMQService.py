#coding=UTF-8

import os   #Python的标准库中的os模块包含普遍的操作系统功能
import re   #引入正则表达式对象
import urllib   #用于对URL进行编解码
import util.db as db #db操作类
import json
from urlparse import urlparse
import socket
import random
import util.helper as helper #工具集

# address = ('127.0.0.1', 3333)

# s2 = socket.socket()
# s2.connect(address)
# s2.recv(1024, flag)
# s2.send('200 OK ok')
# s2.close();
import SocketServer

msg = []
clients = {}

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        global msg
        global clients
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        # print("{} wrote:".format(self.client_address[0]))
        # print(self.data)
        kv = self.data.split(',')

        if kv[0] == 'put':
            """
            put 数据格式如:put,somedata
            somedata会被追加到消息队列
            """
            msg.append(kv[1])
            # print(msg)
            # just send back the same data, but upper-cased
            # self.request.sendall(self.data.upper())
            self.request.sendall(str('200 OK'))
            if not int(random.random() * 1000) % 37:
                helper.getLog(str(msg), 'mq.server.msg.txt')
        elif kv[0] == 'get':
            """
            get 数据格式如:get,clientname
            根据clientname，返回最新的消息
            """
            try:
                msglen = len(msg)
                if not clients[kv[1]] == msglen:
                    self.request.sendall(str(msg[clients[kv[1]]: clients[kv[1]] + 20]))
                    clients[kv[1]] = msglen
                    # print msg[clients[kv[1]]:]
                # print clients[kv[1]]
                if msglen > 10000:
                    del msg[0: 50]
                    for k in clients:
                        clients[k] -= 50
                    print(clients)
            except:
                self.request.sendall(str(msg))
                clients[kv[1]] = len(msg)
                # print clients
        else:
            pass

if __name__ == "__main__":
    HOST, PORT = "192.168.1.119", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()

