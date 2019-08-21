#coding=UTF-8
#助销客票务系统 （衡水旅游在用）
#date: 2017-07-03
#code: ZXK

import time
import threading
import string
import json
import urllib,urllib2,httplib
import MySQLdb
import socket
import util.helper as helper
import util.db as db
import config.globalVar as globalVar #系统定义的全局变量

from pyDes import *
from binascii import b2a_hex, a2b_hex
import base64
import md5

def test():
    print 'test'
    return 'hhh'

def ServiceZXK(config, ticketBoughtList):
    # print config.keys();exit()
    # print ticketBoughtList;exit()
    if len(ticketBoughtList) < 1:
        return

    #循环检查门票
    ts = [] #同步门票到第三方系统的线程列表
    for ticketBought in ticketBoughtList:
        #同步门票
        for conf in config:
            try:
                if conf == 'productNo_' + str(ticketBought['ticket_id']) and config[conf] != '' :
                    # print ticketBought['id']
                    # print config, config[conf] + ':productNo_' + str(ticketBought['ticket_id'])
                    # 给第三方增加门票
                    t = threading.Thread(target = addTicketToOuterZXK, args=(config, ticketBought,))
                    t.start()
                    ts.append(t)
                    break

                # print '========='
            except:
                # print '========='
                pass

    for t in ts :
        t.join()

    return True
    # re = dbObj.update("update t_client set phone = %s where id = %s", ('13200002222', '2'))
    # print re
    # exit()

#同步门票到第三方系统的线程列表
def addTicketToOuterZXK(config, ticketBought):
    # global dbObj
    # dbObj = globalVar.getDbObj()
    dbObj = db.db()

    #查询游客信息
    # userInfo = ''
    userInfo = dbObj.select("select user_id, name, mobile, id_number from t_user_identity_info where id = %d" % ticketBought['identity_info_id'])
    # userInfo = []
    # userInfo.append({
        # 'name': '微景通',
        # 'mobile' : '18523876001'
    # })
    if userInfo == False or len(userInfo) < 1:
        visitorName = 'weijingtongVisitor'
        visitorMobile = '18523876001'
        visitorIdNumber = '110102198601018573'
    else:
        userInfo = userInfo[0]
        visitorMobile = userInfo['mobile']
        visitorIdNumber = userInfo['id_number']
##        visitorName = userInfo['user_id']
        visitorName = userInfo['name']
        visitorName = repr(visitorName.decode('UTF-8'))[2:-1]
##        visitorName = '\u5f20\u8001\u5927'
##        visitorName = urllib.urlencode({1:visitorName})[2:]

    # visitorName = 'wjtVisitor'
    # ticketName = dbObj.getValue("select name from t_ticket where id = %d" % ticketBought['ticket_id'], 'name')
    # ticketName = '成人票'
    # ticketName = repr(ticketName.decode('UTF-8'))[2:-1][0:48]
    # ticketName = 'test'
    visitPerson = '''[
        {    "name": "%s",
            "mobile": "%s",
            "idCard": "%s"
        }
    ]''' % ( visitorName[0:24], visitorMobile, visitorIdNumber )
    requestBody = '''{
        "orderSerialId": "%s",
        "productNo": "%s",
        "payType": 1,
        "tickets": %s,
        "price": %s,
        "contractPrice": %s,
        "bookName": "%s",
        "bookMobile": "%s",
        "idCard": "%s",
        "travelDate": "%s",
        "visitPerson": %s
    }''' % ( ticketBought["order_detail_id"], config["productNo_" + str(ticketBought["ticket_id"])], ticketBought["count"], int(ticketBought["price"]*100),
            int(ticketBought["price"]*100), visitorName[0:24], visitorMobile, visitorIdNumber, str(ticketBought["plan_time"])[0:10], visitPerson
            )

    # print requestBody;exit();
    # data = '{"pageIndex":1,"pageSize":100}' # 1/F4jrg9alyN0uDgJNlEaCLroiTtH9LhlljImdztF8Y=
    KEY = str(config['user_key'])    #密钥
    IV = str(config['user_key'])     #偏转向量
    desObj = des(KEY, ECB, IV, pad=None, padmode=PAD_PKCS5) # 使用DES对称加密算法的CBC模式加密
    # requestBody = 'adfasfaf'
    requestBody = str(requestBody)
    requestBodyFormat = requestBody
    # print helper.httpPost('http://123.56.105.30:5677/Tongcheng/Encrypt/', requestBody);exit(); #获取des密文
    # print (requestBody);
    # print (str(config['user_key']) );
    requestBody = desObj.encrypt(requestBody)
    # print base64.encodestring(b2a_hex(requestBody))
    requestBody = base64.encodestring(requestBody)
    # print requestBody;
    # print "Decrypted: %r" % desObj.decrypt(base64.decodestring(requestBody));exit()

    timestamp = str(time.time())[0:10]

    sign = config['user_id'] + 'CreateOrder' + str(timestamp) + 'v1.0' + requestBody + config['user_key']
    # print (sign);
    md5Obj = md5.new()
    md5Obj.update(sign)
    sign = md5Obj.hexdigest()

    requestHead = '''{
        "user_id": "%s",
        "method": "CreateOrder",
        "timestamp": %s,
        "version": "v1.0",
        "sign": "%s"
    }''' % (config["user_id"], timestamp, sign)
    data = '''{
        "requestHead": %s,
        "requestBody": "%s"
    }''' % (requestHead, requestBody)

    # print (data);
    # exit();

    try:
        re = helper.httpPost(config['url'], data)

        #成功同步
        res = json.loads(re)
        # print res;
        # print res['responseHead']['res_code'];
        # print json.loads(desObj.decrypt(base64.decodestring(res['responseBody'])))
        responseBody = desObj.decrypt(base64.decodestring(res['responseBody']))
        re = re + "\nResponseBodyFormat:" + responseBody
        responseBody = json.loads(responseBody)
        # exit();
        #成功同步
        if ('1000' == res['responseHead']['res_code'] or '2001' == res['responseHead']['res_code']) and (not responseBody['partnerCode'] is None):
            sql = "update t_ticket_bought set out_app_code='ZXK', temp_receiving_code='%s', receiving_code='%s', dimen_code_path='%s', remark2='%s' where id = %d" %  (ticketBought['receiving_code'], responseBody['partnerCode'], responseBody['partnerQRCodeAddress'], responseBody['partnerOrderId'], ticketBought['id'])
            # print sql
            if not True == dbObj.update(sql):
                helper.getLog(sql, 'addTicketToOuterZXK.UpdateTicketboughtlistErr.log')
        else:
            re = "%s \nPostData:%s\nRequestBodyFormat:%s" %(re, data, requestBodyFormat)
            pass
    except Exception, e:
        re = str(Exception) + ":" + str(e)
        re = "%s \nPostData:%s\nRequestBodyFormat:%s" %(re, data, requestBodyFormat)

    re =  re.replace("'", '"')
    # print re;exit()
    #保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
           values ('%d', '%d', '%d', '%d', '%s', '%s', '%s') "
    values = (ticketBought['client_id'], ticketBought['order_id'], ticketBought['order_detail_id'], 1, 'ZXK', re, helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToOuterZXK.SqlErr.log')


