# -*- coding: utf8 -*-
import base64
import hashlib
import hmac
import time
import threading
import json
import urllib,urllib2,httplib
import MySQLdb
import platform
import inspect
import ConfigParser
import sys
import re
import os
import xml.etree.ElementTree as Element
# from xml.etree.ElementTree import tostring
# import md5 as md5Self
import hashlib as md5Self


'''
' 发送消息给用户
' @param clientId int 景区ID
' @param userId string 用户的OPEN ID
' @param time int 时间戳
' @param textMessage string 消息内容
'''
def sendMessageToUser(clientId, userId, time, textMessage):
    time = str(time)
    sign = md5(str(clientId) + userId + time + 'oBlCMjoCEAPoBlCMjmHMDN3GXoBlCMjqn3LZYGkVhy7GQCpd3wiRIurBL2uaSfZ1164IJOPB8mASw7PIfHlQ')
    textMessage = textMessage.replace("\n", '//n').replace(' ', '%20')
    url = 'http://pwx.weijingtong.net/index.php?m=Api&c=SendMessageToUser&a=sendText&clientId=%d&userId=%s&time=%s&sign=%s&content=%s' % (clientId, userId, time, sign, textMessage)
    # print url
    return httpPost(url)


'''
' 配置获取方法
' @param f string 配置的大类
' @param i string 配置的key
'''
def md51(s):
    md5Obj = md5Self.new()
    md5Obj.update(s.encode("utf8"))
    return md5Obj.hexdigest()

def md5(s):
    m = md5Self.md5(s.encode("utf8"))
    return m.hexdigest()

'''
' 获取配置的本站门票id
' @param config json 配置信息
' @param type string ticket/ mall 返回门票id，还是商城门票id
' @return set
'''
def getTicketIds(config , type = 'ticket'):
    mallTicketIds = set()
    ticketIds = set()

    for tmpTicketId in config:
        m = re.match(r'\w+_(\d+)', tmpTicketId)
        # 是否匹配到 id
        if m:
            tmpId = int(m.group(1))

            #是商城门票还是门票
            if tmpTicketId.lower().find('mall') >= 0:
                # 商城门票
                mallTicketIds.add(tmpId)
            else:
                # 门票
                ticketIds.add(tmpId)

    if type== 'ticket':
        return ticketIds
    else:
        return mallTicketIds
'''
' 配置获取方法
' @param f string 配置的大类
' @param i string 配置的key
'''
def confGet(f, i):
    conf = ConfigParser.ConfigParser()
    conf.read("%s/config/config.ini" % sys.path[0])
    # print "%s/config/config.ini" % sys.path[0]
    return conf.get(f, i)

'''
' http get方法
' @param url string 要抓取的url
'''
def httpPost(url, data = None, headers = None) :
    #设置要请求的头，让服务器不会以为你是机器人
    if not headers:
        headers = {}
    headers['UserAgent'] = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

    #post方式时候要发送的数据
    if isinstance(data, dict):
        data = urllib.urlencode(data)
    # print data
    # getLog(data)
    #发送一个http请求
    request = urllib2.Request(url, headers = headers, data = data)

    #获得回送的数据
    response = urllib2.urlopen(request)

    return response.read()

'''
' http get方法
' @param url string 要抓取的url
'''
def httpGet(url) :
    # print url
    return urllib2.urlopen(url).read()

'''
' webservice
' @param url string 要抓取的url
'''
def webservice(host, port, path, data, SOAPAction, debug = 0) :

    webservice = httplib.HTTPConnection(host, port, timeout = 50)
    webservice.set_debuglevel(debug)

    # print response.getheaders() #获取头信息
    #连接到服务器后的第一个调用。它发送由request字符串到到服务器
    webservice.putrequest("POST", path)
    # webservice.putrequest("POST", "/service.asmx/OrderOccupies")
    # webservice.putheader("Accept-Encoding", "text")
    # webservice.putheader("Host", "123.11.226.80")
    webservice.putheader("User-Agent", "WeijingtongService-python")
    webservice.putheader("Content-Type", "text/xml; charset=utf-8")
    # webservice.putheader("Content-Type", 'application/x-www-form-urlencoded')
    # webservice.putheader("Connection", "Keep-Alive")
    webservice.putheader("Content-Length", "%d" % len(data))
    # webservice.putheader("SOAPAction", '"http://localhost/WebSell/OrderOccupies"')
    webservice.putheader("SOAPAction", '"'+ SOAPAction +'"')
    # webservice.putheader("SOAPAction", '"http://123.11.226.80/OrderOccupies"')
    #发送空行到服务器，指示header的结束
    webservice.endheaders()
    #发送报文数据到服务器
    webservice.send(data)
    #获取返回HTTP 响应信息
    response = webservice.getresponse()
    responseBody = response.read()
    # print 'response:'
    # print response.read()
    # exit()
    res = []
    res.append('ReHttpStatus:' + str( response.status ))
    res.append('ReHttpReason:' + response.reason)
    res.append('ReHttpBody:' + responseBody)
    head = []
    for header in response.getheaders():
        head.append('%s: %s' % ( header[0], header[1] ))

    head = "\n".join(head)
    res.append('ReHttpHeader:' + head) #获取头信息
    # print res
    # exit()
    re = "\n".join(res)
    # re = re.decode('gb2312').encode('utf-8')
    webservice.close() #关闭链接
    return [responseBody, re]

'''
' 截取字符粗
' @param str string 要截取的字符串
' @param startStr string 开始的字符串
' @param endStr string 结束的字符串
' @return string'''
def subStr(str, startStr, endStr):
    if startStr == '':
        start = 0
    else:
        start = str.find(startStr) + len(startStr)
    if endStr == '':
        end = len(str)
    else:
        end = str.find(endStr)
    return str[start : end]


# 解析xml，对于soap返回格式有问题
def xml2dict(xml, node = 'root'):
    tree = Element.fromstring(xml)
    # root = tree.getroot()
    print xml
    print node
    i = 0
    # for ele in tree.findall(node):
    for ele in tree.iter(node):
        # for v in ele:
            # print i,v
            # i += 1
        print ele.tag, ele.attrib, ele.text


def dict2xml(tag, d, attr = ''):
    parts = ['<'+ tag +' '+ attr +'>']
    for i, v in enumerate(d) :
        # print v
        for k in v:
            val = d[i][k]
        # print 'key:' + k
        parts.append("<%s>%s</%s>\n" % (k, str(val), k))
    parts.append("</%s>\n" % tag)
    return ''.join(parts)

def dict2url(d):
    parts = []
    for i, v in enumerate(d) :
        # print v
        for k in v:
            val = d[i][k]
        # print 'key:' + k
        parts.append("%s=%s&" % (k, str(val)))

    return ''.join(parts)

def now(t = 0, format = '%Y-%m-%d %H:%M:%S'):
    # return time.strftime(format, time.localtime(time.time()))
    return time.strftime(format, time.localtime(float(int(time.time()) + int(t))))

#
#return time : 1520492870.57
def thisTime():
    # return time.strftime(format, time.localtime(time.time()))
    return time.time()

def getLog(c, fileName = ''):
    if fileName == '':
        fileName = inspect.stack()[1][3] + '.temp.log'
    sysInfo = platform.system()
    date = str(time.strftime('%Y-%m-%d', time.localtime(time.time())))
    if( sysInfo == "Windows" ):
        dirPath = 'C:/logs/python/' + date
        #fileName = 'H:/python/log/' +  fileName
    else :
        dirPath = '/logs/python/' + date
    if not os.path.isdir(dirPath):
        os.mkdir(dirPath)
    # print inspect.stack()
    fileName = dirPath + '/' + fileName
    try:
        f = open(fileName, 'a')
        f.write( "%s -- %s\n" % (now(), c) )
        f.close()
    except Exception, e:
        print 'Write file error:' + str(Exception) + ':' + str(e) + ' Content:' + c
        pass

def getHmacSha256(message, secret):
    message = bytes(message).encode('utf-8')
    secret = bytes(secret).encode('utf-8')
    signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
    return signature

