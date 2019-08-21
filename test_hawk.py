#!/usr/bin/python
# -*- coding: UTF-8 -*-
import base64
import hashlib
import hmac
import string
import urllib
import urllib2
import time
import random
import urlparse
import uuid

from util import helper


import requests

# url = "http://121.41.6.55:8601/api/OrderAndPay/WithPrepayment"
url = "http://121.41.6.55:8601/api/Order/QueryWJM?orderid=YD-2019-04-04-000033&ticketid=WLPAA190000000000101&dwid=bd0f291c-4d40-4f90-b3e8-924f77de9997&dwlx=1"

payload = "{\n    \"orderinfo\": {\n        \"orderdetails\": [\n            {\n                \"productid\": \"AC1CFCE6-A650-401F-BB98-A5F56597CD09\",\n                \"amount\": 1,\n                \"identificationnumber\": \"610124199609203934\",\n                \"fullname\": \"ycp\",\n                \"identificationtype\": \"1\",\n                \"mobile\": \"18518933040\",\n                \"gateinmode\": \"B\",\n                \"seatitems\": null\n            }\n        ],\n        \"mobile\": \"18518933040\",\n        \"otheruserid\": 0,\n        \"identificationnumber\": \"610124199609203934\",\n        \"effectdate\": \"20190421\",\n        \"needinvoice\": \"\",\n        \"invoicetitle\": \"\",\n        \"invoicecode\": \"\",\n        \"senderid\": \"\",\n        \"servicecode\": \"\",\n        \"timespanindex\": 0,\n        \"tripbillcode\": \"\",\n        \"guidernumber\": \"\",\n        \"marketareaid\": \"\"\n    },\n    \"payinfo\": {\n        \"orderid\": \"161843814545000000\",\n        \"paypassword\": \"QqXlcUJI+l454hJ1LKsZ7xCcwLKvHpo1u3gYr5QAwb39UeHA252gZQ==\"\n    }\n}"
hawkId = 'ybxkj'
key = '2b4747b3-788b-46ba-9ca4-c5d112a7c066'
hawkAuthKey = key + helper.md5('123456').upper()
ts = str(time.time())[0:10]

credential = {}
credential['user'] = hawkId
credential['algorithm'] = 'sha256'  # 验证方式
credential['authKey'] = hawkAuthKey  # 密码
nonce = uuid.uuid1()
nonce = str(nonce)[0:32]
def calculateMac(method, uri, ext, ts, nonce, credential, type, payloadHash = None):
    urlInfo = urlparse.urlparse(url)
    sanitizedHost = str(urlInfo.hostname)
    port = str(urlInfo.port)
    path = str(urlInfo.path) + "?" +str(urlInfo.query)
    normalized = "hawk.1." + type + "\n" + ts + "\n" + nonce + "\n" + method.upper() + "\n" + path + "\n" + sanitizedHost + "\n" + port + "\n\n\n"

    print "mac加密前{%s},秘钥为{%s}" % (normalized, credential['authKey'])
    mac = getHmacSha256(normalized, credential['authKey'])
    print "mac加密后为%s " % mac
    return mac

mac = calculateMac('get', url, '', ts, nonce, credential, "header")
auth = 'Hawk id="ybxkj", ts="%s", nonce="%s", mac="%s"' % (ts, nonce, mac)
headers = {
    # 'POST': '/api/OrderAndPay/WithPrepayment',
    'Host': '121.41.6.55:8601',
    'Content-Type': "application/json",
    'Authorization': auth
}
response = requests.request("GET", url, headers=headers)

print(response.text)

def getHmacSha256(message, secret):
    message = bytes(message).encode('utf-8')
    secret = bytes(secret).encode('utf-8')
    signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
    return signature
