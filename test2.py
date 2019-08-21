#coding=UTF-8

import time
import os
import sys
import threading
import string
import json
import urllib,urllib2,httplib
import MySQLdb
import random
import base64
import util.helper as helper
import util.db as db

msg = {}

def t(s):
    global msg
    msg[s] = s

if __name__ == "__main__":

    textMessage = '微景通验证码：722399640 \n票务验证码：722399640 \n购票张数：1'
    textMessage = repr(textMessage).replace(r'\x', '%').replace(' ', '%20')
    textMessage = textMessage[1:-1]
    print textMessage
    exit()

    ticketBought = {
        'receiving_code': 'aaaaaa',
        'count': 2,
        'client_id': 759,
        'user_id': 'oRAx7ju3yK19Ll0WEwxlMBeFcia4'
    }
    cQrCode = 'bbb'
    textMessage = "微景通验证码：%s \n票务验证码：%s \n购票张数：%d" % (ticketBought['receiving_code'], cQrCode, ticketBought['count'])
    textMessage = urllib.quote(textMessage)
    time = str(int(helper.thisTime()))
    sign = helper.md5(str(ticketBought['client_id']) + ticketBought['user_id'] + time + 'oBlCMjoCEAPoBlCMjmHMDN3GXoBlCMjqn3LZYGkVhy7GQCpd3wiRIurBL2uaSfZ1164IJOPB8mASw7PIfHlQ')
    url = 'http://pwx.weijingtong.net/index.php?m=Api&c=SendMessageToUser&a=sendText&clientId=%d&userId=%s&time=%s&content=%s&sign=%s' % (ticketBought['client_id'], ticketBought['user_id'], time, textMessage, sign)
    print helper.httpGet(url)

    exit()

    data = '<?xml version="1.0" encoding="UTF-8"?>    <request xsi:schemaLocation="http://piao.qunar.com/2013/QMenpiaoRequestSchema QMRequestDataSchema-2.0.1.xsd" xmlns="http://piao.qunar.com/2013/QMenpiaoRequestSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">        <header>            <application>Qunar.Menpiao.Agent</application>            <processor>SupplierDataExchangeProcessor</processor>            <version>v2.0.1</version>            <bodyType>CreateOrderForBeforePaySyncRequestBody</bodyType>            <createUser>SupplierSystemName</createUser>            <createTime>2017-12-28 11:22:18</createTime>            <supplierIdentity>27</supplierIdentity>        </header>        <body xsi:type="CreateOrderForBeforePaySyncRequestBody">            <orderInfo>                <orderId>595117</orderId>                <product>                    <resourceId>7425</resourceId>                    <productName>成人票</productName>                    <visitDate>2017-11-30 00:00:00</visitDate>                    <sellPrice>1</sellPrice>                    <cashBackMoney>0</cashBackMoney>                </product>                <contactPerson>                    <name>巫星星</name><namePinyin></namePinyin>                    <mobile>18223350508</mobile>                    <email></email>                    <address></address>                    <zipCode></zipCode>                </contactPerson>                <visitPerson>                    <person>                        <name></name><namePinyin></namePinyin>                        <credentials></credentials>                        <credentialsType></credentialsType>                        <defined1Value></defined1Value>                        <defined2Value></defined2Value>                    </person>                </visitPerson>                <orderQuantity>1</orderQuantity>                <orderPrice>1</orderPrice>                <orderCashBackMoney></orderCashBackMoney>                <orderStatus>CASHPAY_ORDER_INIT</orderStatus>                <orderRemark></orderRemark>                <orderSource></orderSource>                <eticketNo></eticketNo>            </orderInfo>        </body>    </request>    '

    print base64.encodestring(data)
    exit()

    # print sys.getsizeof(l) / 1024

    s1 = 1
    print sys.getsizeof(s1)

    s12 = 1111
    print sys.getsizeof(s12)

    s2 = 'a'
    print sys.getsizeof(s2)

    s3 = 'ab'
    print sys.getsizeof(s3)

    s4 = 'abcdef'
    print sys.getsizeof(s4)

    #print int(random.random() * 100) % 7

    # re = 'a,bbb'.split(',')
    # print re

    # re = os.system('/opt/lampp/bin/php /datas/www/php/common-service/cli.php  /SystemService/PosterScoreByPython/process/data/%7B%22id%22%3A%22629660%22%2C%22client_id%22%3A%2246%22%2C%22user_id%22%3A%22oNDNxt4VdZQjFHnl7O7enqAush-s%22%2C%22scene_id%22%3A%221474890528%22%2C%22status%22%3A%222%22%2C%22object_id%22%3A%22None%22%7D')
    # print re





