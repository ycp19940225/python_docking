#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 游宝星4.0 （酉阳桃花源在用）
# date: 2019-3-27
# code: YBX
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


def test():
    print 'test'
    return 'hhh'


def ServiceYBX(config, ticketBoughtList):
    # print config.keys();exit()
    # print ticketBoughtList;exit()
    if len(ticketBoughtList) < 1:
        return

    # 循环检查门票
    ts = []  # 同步门票到第三方系统的线程列表
    for ticketBought in ticketBoughtList:
        # 同步门票
        for conf in config:
            try:
                if conf == 'ProductID_' + str(ticketBought['ticket_id']) and config[conf] != '':
                    # print ticketBought['id']
                    # print config, config[conf] + ':nTicketType_' + str(ticketBought['ticket_id'])
                    # 给第三方增加门票
                    helper.getLog(str(ticketBought['order_detail_id']) + '------------',
                                  'addTicketToOuterYBX.recordOrderId.log')
                    t = threading.Thread(target=addTicketToOuterYBX, args=(config, ticketBought,))
                    t.start()
                    ts.append(t)
                    break

                # print '========='
            except:
                # print '========='
                pass

    for t in ts:
        t.join()

    return True
    # re = dbObj.update("update t_client set phone = %s where id = %s", ('13200002222', '2'))
    # print re
    # exit()


# 同步门票到第三方系统的线程列表
def addTicketToOuterYBX(config, ticketBought):
    # global dbObj
    # dbObj = globalVar.getDbObj()
    dbObj = db.db()

    # 查询游客信息
    # userInfo = ''
    userInfo = dbObj.select(
        "select user_id, name, mobile, id_number from t_user_identity_info where id = %d" % ticketBought[
            'identity_info_id'])
    # userInfo = []
    # userInfo.append({
    # 'name': '微景通',
    # 'mobile' : '18523876001'
    # })
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


    orderInfo = {}
    orderInfo['mobile'] = visitorMobile
    orderInfo['identificationnumber'] = str(userInfo['id_number'])
    orderInfo['effectdate'] = str(ticketBought['plan_time'])[0:10]
    orderInfo['effectdate'] = orderInfo['effectdate'].replace('-', '', 3)
    orderInfo['otheruserid'] = int(ticketBought['identity_info_id'])  # 其他用户ID号，指用户在第三方系统的用户账号，主要用于官方网站和官方微信的对接，第三方OTA不能使用。
    orderInfo['senderid'] = str(ticketBought['order_detail_id'])  # 被接口方的业务单据ID，示例：同程网接口调用，此值表示同程网业务系统内对应的订单的单据号，此值在接口方系统内应为唯一值。不提供此参数时，系统将不会执行回调通知。提供这个参数还可以防止订单的重复提交。
    orderInfo['servicecode'] = ""
    orderInfo['timespanindex'] = 0
    orderInfo['tripbillcode'] = ""
    orderInfo['guidernumber'] = ""
    orderInfo['marketareaid'] = ""

    orderdetails = {}
    # orderdetails['productid'] = ticketBought['id']
    orderdetails['productid'] = config['ProductID_' + str(ticketBought['ticket_id'])]
    orderdetails['amount'] = ticketBought['count']
    orderdetails['identificationnumber'] = str(userInfo['id_number'])
    orderdetails['fullname'] = visitorName
    if (orderInfo['identificationnumber'] != ''):
        orderdetails['identificationtype'] = "1"  # 证件类型（'1'身份证，‘2’ 军官证(士兵证)，‘3’护照，‘4’其他）
    else:
        orderdetails['identificationtype'] = "4"  # 证件类型（'1'身份证，‘2’ 军官证(士兵证)，‘3’护照，‘4’其他）
    orderdetails['mobile'] = visitorMobile  # 手机号码，当过闸模式的值为“B”时，此项必填，且必须是一个合法的手机号
    orderdetails['gateinmode'] = 'B'  # 过闸模式 分别为"I"二代证，“B”手机条码，“T”前台或自助机取票。“T”是默认值。

    orderdetailInfo = [orderdetails]

    payInfo = {}
    payInfo['orderid'] = str(ticketBought['order_detail_id'])
    payInfo['paypassword'] = getPayPassword(config)

    orderInfo['orderdetails'] = orderdetailInfo
    orderData = {}
    orderData['orderinfo'] = orderInfo
    orderData['payinfo'] = payInfo
    postData = json.dumps(orderData)
    # print data;
    # exit();
    processOuterYBX(config, ticketBought, postData, 1)


def getQrcode(config, ticketcode, orderid):
    url = config['url']
    urlInfo = urlparse.urlparse(url)
    sanitizedHost = str(urlInfo.netloc)
    # url = 'http://' + sanitizedHost + "/api/Ticket/Resource/" + str(ticketcode)
    # url = 'http://' + sanitizedHost + "/api/Ticket/Resource/String/" + str(ticketcode)
    url = 'http://' + sanitizedHost + "/api/Ticket/Barcode/String/" + str(orderid) + '/' + str(ticketcode)
    headers = hawkAuth(url, config, 'get')
    try:
        response = requests.get(url, headers=headers)
        # helper.getLog(response, 'addTicketToOuterYBX.getQrcode.log')
        return response.json()
    except requests.exceptions:
        helper.getLog(requests.exceptions, 'addTicketToOuterYBX.addOrder.log')


# def getQrcodeFile(config, ticketcode, orderId):
#     url = config['url']
#     urlInfo = urlparse.urlparse(url)
#     sanitizedHost = str(urlInfo.netloc)
#     url = 'http://' + sanitizedHost + "/api/Order/QueryWJM?" + 'orderid=' + orderId + '&ticketid=' + str(ticketcode) + '&dwid='+config['dwid']+'&dwlx='+config['dwlx']
#     # url = 'http://' + sanitizedHost + "/api/Order/QueryWJM?" + 'orderid=' + orderId + '&ticketid=' + str(ticketcode) + '&dwid=bd0f291c-4d40-4f90-b3e8-924f77de9997&dwlx=1'
#     headers = hawkAuth(url, config, 'get')
#     try:
#         response = requests.get(url, headers=headers)
#         helper.getLog(response, 'addTicketToOuterYBX.getQrcode.log')
#         return response.json()
#     except requests.exceptions:
#         helper.getLog(requests.exceptions, 'addTicketToOuterYBX.addOrder.log')


def processOuterYBX(config, ticketBought, data, processCount):
    dbObj = db.db()
    send_time = time.time()
    # 错误时 记录信息
    sql_error = "update t_ticket_bought set out_app_error='%s' where id = %d" % (1, ticketBought['id'])
    try:
        # 记录请求时间
        # 发起同步
        response = sendDataToOuterYBX(config, data)

        # 防止票务系统死锁
        if -2 == response['resultcode']:
            for i in range(1, 10):
                time.sleep(i)
                response = sendDataToOuterYBX(config, data)
                if response != -2:
                    break
        # 成功同步
        if 0 == response['resultcode']:
            # 获取订单详细信息
            orderId = response['orderid']
            orderDetail = getOrderDetail(config, orderId)
            # 门票唯一ID
            ticketId = orderDetail[0]['ticketinnernumber']
            # 获取filecode
            # cQrCodeFile = getQrcodeFile(config, ticketId, orderId)
            # 获取二维码
            cQrCodeInfo = getQrcode(config, ticketId, orderId)
            # cQrCode = base64.b64decode(cQrCodeInfo['imagebase64'])
            # 获取二维码成功
            if cQrCodeInfo['errcode'] == 0:
                cQrCode = cQrCodeInfo['imagebase64']
                cQrCode = base64.b64encode(cQrCode)
                qrcodeImgUrl = 'http://pwx.weijingtong.net/index.php/Api/Qrcode/getQrCode?data=' + cQrCode
                # 替换二维码 、订单号 、门票编码
                sql = "update t_ticket_bought set out_app_code = 'YBX', temp_receiving_code = '%s', receiving_code = '%s', dimen_code_path='%s', remark2='%s', out_app_error='%s' where id = %d" % (
                    ticketBought['receiving_code'], ticketId, qrcodeImgUrl, orderId, 2, ticketBought['id'])
                try:
                    re = dbObj.update(sql)
                    if not True == re:
                        helper.getLog(sql, 'addTicketToOuterYBX.UpdateTicketboughtlistErr.log')
                    else:
                        re = "%s \npostdata:%s" % (response, data)
                except Exception, e:
                    dbObj.update(sql_error)
                    re = "%s " % e
            # 获取二维码不成功
            else:
                dbObj.update(sql_error)
                re = "%s \n %s \n postdata:%s" % ('获取二维码失败,订单已同步', cQrCodeInfo, data)
        else:
                dbObj.update(sql_error)
                re = "%s \npostdata:%s" % (response, data)
    except Exception, e:
        dbObj.update(sql_error)
        re = str(Exception) + ":" + str(e)
        re = "%s \nPostData:%s" % (re, data)
    # re = re.replace("'", '"')
    # print re;exit()
    # 记录请求结束时间
    helper.getLog(str(ticketBought['order_detail_id']) + '------------' + str((time.time() - send_time)), 'addTicketToOuterYBX.recordEndTime.log')
    # 保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
           values ('%d', '%d', '%d', '%d', '%s', '%s', '%s')"
    values = (
        ticketBought['client_id'], ticketBought['order_id'], ticketBought['order_detail_id'], 1, 'YBX', re,
        helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # 记录存数据库的时间
    # helper.getLog(helper.now(), 'addTicketToOuterYBX.recordSqlTime.log')
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToOuterYBX.SqlErr.log')


# 订单同步
def sendDataToOuterYBX(config, data):
    url = config['url']
    payload = data
    headers = hawkAuth(url, config)
    response = requests.request("POST", url, data=payload, headers=headers)
    return response.json()


# 获取订单详细信息
def getOrderDetail(config, orderId):
    url = config['url']
    urlInfo = urlparse.urlparse(url)
    sanitizedHost = str(urlInfo.netloc)
    url = 'http://' + sanitizedHost + "/api/Order/Query/Detail/" + str(orderId)
    headers = hawkAuth(url, config, 'get')
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except requests.exceptions:
        helper.getLog(requests.exceptions, 'addTicketToOuterYBX.addOrder.log')


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
def hawkAuth(url, config, methond='post'):
    urlInfo = urlparse.urlparse(url)
    hawkId = config['user']
    key = config['privateKey']
    hawkAuthKey = key + helper.md5(config['password']).upper()
    ts = str(time.time())[0:10]
    credential = {}
    credential['user'] = hawkId
    credential['algorithm'] = 'sha256'  # 验证方式
    credential['authKey'] = hawkAuthKey  # 密码
    nonce = uuid.uuid1()
    nonce = str(nonce)[0:32]
    mac = calculateMac(methond, url, '', ts, nonce, credential, "header")
    auth = 'Hawk id="%s", ts="%s", nonce="%s", mac="%s"' % (hawkId, ts, nonce, mac)
    headers = {
        'Host': str(urlInfo.netloc),
        'Content-Type': "application/json",
        'Authorization': auth
    }
    if (methond == 'post'):
        headers['POST'] = str(urlInfo.path)
    return headers
# 支付密码加密
def getPayPassword(config):
    # 会话秘钥
    sIV = "hellocxp"
    # 通信的key
    sha256key = config['privateKey'] + helper.md5(config['password']).upper()

    KEY = hashlib.sha256(sha256key.encode('utf8'))
    KEY = KEY.digest()
    KEY = KEY[0:24]
    #
    # KEY = str(KEY2)  # 密钥
    IV = sIV  # 偏转向量

    desObj = pyDes.triple_des(KEY, ECB, IV, pad=None, padmode=PAD_PKCS5)  # 使用DES对称加密算法的CBC模式加密

    str = desObj.encrypt(helper.md5(config['payPassword']).upper(), padmode=PAD_PKCS5)

    return base64.b64encode(str)