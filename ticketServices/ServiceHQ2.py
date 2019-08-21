#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 环企票务2.0
# date: 2019-4-30
# code: HQ2
import base64
import hashlib
import httplib
import json
import threading
import urllib
import urlparse
import uuid
from StringIO import StringIO

import pyDes
import requests
import time

from pyDes import des, ECB, PAD_PKCS5

import util.db as db
import util.helper as helper


def ServiceHQ2(config, ticketBoughtList):
    if len(ticketBoughtList) < 1:
        return

    # 循环检查门票
    ts = []  # 同步门票到第三方系统的线程列表 使用Thread类创建线程
    for ticketBought in ticketBoughtList:
        helper.getLog(str(ticketBought['ticket_id']), 'responseOutCode.HQ2.log')
        # 同步门票
        for conf in config:
            try:
                if conf == 'productId_' + str(ticketBought['ticket_id']) and config[conf] != '':
                    # 给第三方增加门票
                    t = threading.Thread(target=addTicketToOuterHQ2, args=(config, ticketBought))
                    t.start()
                    ts.append(t)
                    break
                    # addTicketToOuterHQ2(config, ticketBought)
                    # break
                # print '========='
            except:
                # print '========='
                pass

    for t in ts:
        t.join()

    return True


# 同步门票到第三方系统的线程列表
def addTicketToOuterHQ2(config, ticketBought):
    # print ticketBought
    # helper.getLog('访问addTicketToOuterHQ2了！！！', 'responseOutCode.HQ2.log')
    # helper.getLog(ticketBought['id'], 'responseOutCode.HQ2.log')
    dbObj = db.db()
    # 查询游客信息
    userInfo = dbObj.select(
        "select user_id, name, mobile, id_number from t_user_identity_info where id = %d" % ticketBought['identity_info_id'])
    if userInfo == False or len(userInfo) < 1:
        visitorName = '散客'
        visitorMobile = '18523876001'
    else:
        userInfo = userInfo[0]
        visitorMobile = userInfo['mobile']
        visitorName = userInfo['name']
    if len(userInfo['mobile']) < 1:
        visitorMobile = '18523876001'
    if len(userInfo['name']) < 1:
        visitorName = '散客'
    timeNow =  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  #调用日期yyyy-MM-dd HH:mm:ss
    #构造环企票务所需要的订单信息
    postOrder = {} #回传订单及明细json数据
    postOrder['Ptime'] = timeNow
    postOrder['Type'] = '00' #订单类型 00门票 03剧场票

    order = {} #order信息
    order['OrderNO'] = ticketBought['order_detail_id'] #Ota订单号
    order['LinkName'] = visitorName #下单人姓名
    order['LinkPhone'] = visitorMobile #下单人电话
    order['CreateTime'] = timeNow #下单时间
    detail = {} #Details信息 List<Detail>
    detail['OrderNO'] = ticketBought['order_detail_id'] #Ota订单号
    detail['ItemID'] = ticketBought['order_detail_id'] #订单明细ID
    detail['ProductCode'] = config['productId_' + str(ticketBought['ticket_id'])]#门票编码
    detail['ProductPrice'] = str(ticketBought['price']) #门票单价
    detail['ProductCount'] = ticketBought['count'] #门票数量
    # 时间格式转换
    time_str = time.mktime(time.strptime(str(ticketBought['plan_time']), '%Y-%m-%d %H:%M:%S'))
    time_array = time.localtime(time_str)
    detail['productSDate'] = time.strftime("%Y-%m-%d", time_array) #游玩日期开始 yyyy-MM-dd
    detail['ProductEDate'] = time.strftime("%Y-%m-%d", time_array)  #游玩日期结束
    postOrder['Order'] = json.dumps(order)
    postOrder['Details'] = '[' + json.dumps(detail) + ']'
    postOrder['parkCode'] = config['parkCode']
    # helper.getLog(postOrder['Order'], 'responseOutCode.HQ2.log')
    # helper.getLog(postOrder['Details'], 'responseOutCode.HQ2.log')
    processOuterHQ2(config, ticketBought, postOrder, 1)

def processOuterHQ2(config, ticketBought, data, processCount):
    # helper.getLog('访问processOuterHQ2！！！', 'responseOutCode.HQ2.log')
    dbObj = db.db()
    orderInfo = {}
    orderInfo['merchantCode'] = config['account'] #获取环企票务的编码
    orderInfo['postOrder'] = json.dumps(data).replace(' ','')
    tempOrder =  config['account'] + config['privateKey'] + orderInfo['postOrder']
    orderInfo['signature'] = base64.encodestring(helper.md5(tempOrder.strip()).upper()).strip()
    try:
        # 发起同步
        response = sendDataToOuterHQ2(config, orderInfo)
        # # 防止同时发起请求造成唯一ID插入错误
        # 成功同步
        if '00' == response['ResultCode']:
            # 获取订单详细信息
            orderNo = ticketBought['order_detail_id']
            orderDetail = getOrderDetail(config, str(orderNo))
            # 获取订单信息成功
            if orderDetail['ResultCode'] == '00':
                result = json.loads(orderDetail['ResultJson'].replace('[', '').replace(']', ''))
                for item in result:
                    if 'ECode' == item:
                        qrcodeData = result[item]
                        break
                qrcodeImgUrl = 'http://pwx.weijingtong.net/index.php/Api/Qrcode/?data=' + qrcodeData
                # 替换二维码 、订单号 、门票编码
                sql = "update t_ticket_bought set out_app_code = 'HQ2', temp_receiving_code = '%s', receiving_code = '%s', dimen_code_path='%s', remark2='%s' where id = %d" % (
                    ticketBought['receiving_code'], qrcodeData, qrcodeImgUrl,  qrcodeData, ticketBought['id'])
                try:
                    re = dbObj.update(sql)
                    if not True == re:
                        helper.getLog(sql, 'addTicketToOuterHQ2.UpdateTicketboughtlistErr.log')
                    else:
                        re = "%s \npostdata:%s" % (response, orderInfo)
                except Exception, e:
                    re = "%s " % e
            # 获取订单信息不成功
            else:
                re = "%s \n %s \n postdata:%s" % ('获取订单详情失败,订单已占用', orderDetail, orderInfo)
        else:
                re = "%s \npostdata:%s" % (response, orderInfo)
    except Exception, e:
        re = str(Exception) + ":" + str(e)
        re = "%s \nPostData:%s" % (re, data)
    # 保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
           values ('%d', '%d', '%d', '%d', '%s', '%s', '%s') "
    values = (
        ticketBought['client_id'], ticketBought['order_id'], ticketBought['order_detail_id'], 1, 'HQ2', re,
        helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToOuterHQ2.SqlErr.log')

# 订单同步
def sendDataToOuterHQ2(config, data):
    helper.getLog('访问sendDataToOuterHQ2！！！', 'responseOutCode.HQ2.log')
    url = config['url'] + '?op=OrderOccupies'

    headers = hawkAuth(url)
    data = '''<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
               <OrderOccupies xmlns="http://tempuri.org/">
                   <merchantCode>%s</merchantCode>
                   <postOrder>%s</postOrder>
                   <signature>%s</signature>
                </OrderOccupies>
            </soap:Body>
        </soap:Envelope>
       ''' % (
        data['merchantCode'], data['postOrder'], data['signature']
    )
    res = helper.httpPost(url, data, headers)
    resBody = json.loads(helper.subStr(res, '<OrderOccupiesResult>', '</OrderOccupiesResult>'))
    return resBody


# 获取订单详细信息  (订单完成接口）
def getOrderDetail(config, orderNo):
    helper.getLog('访问getOrderDetail！！！', 'responseOutCode.HQ2.log')
    url = config['url'] + '?op=OrderFinish'
    headers = hawkAuth(url)
    data = {}
    data['otaCode'] = config['account']
    data['otaOrderNO'] = orderNo
    data['platformSend'] = 0
    parameters = {}
    parameters['type'] = '00'
    parameters['parkCode'] = config['parkCode']
    data['parameters'] = json.dumps(parameters).replace(' ', '')
    sign_str = config['account'] + config['privateKey'] + orderNo + '0' + data['parameters']
    data['sign'] = base64.encodestring(helper.md5(sign_str.strip()).upper()).strip()
    postData = '''<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                   <OrderFinish xmlns="http://tempuri.org/">
                      <otaCode>%s</otaCode>
                      <otaOrderNO>%s</otaOrderNO>
                      <platformSend>%s</platformSend>
                      <parameters>%s</parameters>
                      <signature>%s</signature>
                    </OrderFinish>
                </soap:Body>
            </soap:Envelope>
       ''' % (
        config['account'], orderNo, 0, data['parameters'] ,data['sign']
    )
    res = helper.httpPost(url, postData, headers)
    resBody = json.loads(helper.subStr(res, '<OrderFinishResult>', '</OrderFinishResult>'))
    return resBody


# 计算hawk认证中的mac
def calculateMac(method, url, ext, ts, nonce, credential, type, payloadHash=None):
    urlInfo = urlparse.urlparse(url)
    sanitizedHost = str(urlInfo.hostname)
    port = str(urlInfo.port)
    path = str(urlInfo.path)
    if (str(urlInfo.query) != ''):
        path += "?" + str(urlInfo.query)
    normalized = "hawk.1." + type + "\n" + ts + "\n" + nonce + "\n" + method.upper() + "\n" + path + "\n" + sanitizedHost + "\n" + port + "\n\n\n"

    # print "mac加密前{%s},秘钥为{%s}" % (normalized, credential['authKey'])
    mac = helper.getHmacSha256(normalized, credential['authKey'])
    # print "mac加密后为%s " % mac
    return mac


# hawk认证
def hawkAuth(url, methond='post'):
    urlInfo = urlparse.urlparse(url)
    headers = {
        'Host': str(urlInfo.netloc),
        'Vary': "Accept - Encoding",
        'Content-Type': "text/xml",
    }
    if (methond == 'post'):
        headers['POST'] = str(urlInfo.path)
    return headers

