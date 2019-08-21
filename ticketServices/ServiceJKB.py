#coding=UTF-8
#集客宝闸机系统 （1270 玩转北庭在用）
#date: 2018-05-24
#code: JKB

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
import base64

def test():
    print 'test'
    return 'hhh'

def ServiceJKB(config, ticketBoughtList):
    # print config.keys();exit()
    # print ticketBoughtList;exit()
    # print config

    if len(ticketBoughtList) < 1:
        return

    #循环检查门票
    ts = [] #同步门票到第三方系统的线程列表
    for ticketBought in ticketBoughtList:
        #同步门票
        for conf in config:
            try:
                if conf == 'resourceId_' + str(ticketBought['ticket_id']) and config[conf] != '' :
                    # print ticketBought['id']
                    # print config, config[conf] + ':resourceId_' + str(ticketBought['ticket_id'])
                    # 给第三方增加门票
                    t = threading.Thread(target = addTicketToOuterJKB, args=(config, ticketBought,))
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

#同步门票到第三方系统的线程列表
def addTicketToOuterJKB(config, ticketBought):
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
    else:
        userInfo = userInfo[0]
        visitorMobile = userInfo['mobile']
##        visitorName = userInfo['user_id']
        visitorName = userInfo['name']
        visitorName = urllib.quote(visitorName.encode('utf-8'))
        # visitorName = repr(visitorName.decode('UTF-8'))[2:-1]
##        visitorName = '\u5f20\u8001\u5927'
##        visitorName = urllib.urlencode({1:visitorName})[2:]

    # visitorName = 'wjtVisitor'
    ticketName = dbObj.getValue("select name from t_ticket where id = %d" % ticketBought['ticket_id'], 'name')
    ticketName = urllib.quote(ticketName.encode('utf-8'))
    # ticketName = '成人票'
    # ticketName = repr(ticketName.decode('UTF-8'))[2:-1][0:48]
    # ticketName = 'test'

    visitPerson = {}
    visitPerson['visitName'] = visitorName
    visitPerson['visitMobile'] = visitorMobile
    visitPerson['credentials'] = userInfo['id_number']
    visitPerson['credentialsType'] = 'Idcard'

    body = {}
    body['productName'] = ticketName
    body['contactMobile'] = visitorMobile
    body['contactName'] = visitorName
    body['orderPrice'] = str(round(ticketBought['price'], 2))
    body['orderQuantity'] = ticketBought['count']
    body['orderRemark'] = 'weijingtong'
    body['outOrderId'] = ticketBought['order_detail_id']
    body['resourceId'] = config['resourceId_' + str(ticketBought['ticket_id'])]
    body['sellPrice'] = str(round(ticketBought['list_price'], 2))
    body['useDate'] = str(ticketBought['plan_time'])[0:10]
    body['visitPerson'] = [visitPerson]

    data = {}
    data['body'] = body
    data['appKey'] = config['AppKey']

    data = json.dumps(data, ensure_ascii=False)
    # data = json.dumps(data)
    # print data
    # exit()
    # time = str(helper.thisTime())[0:10] + str(int(str(helper.thisTime())[12:])*100)
    time = str(int(round(helper.thisTime() * 1000)))
    # time = '1'
    print config['AppKey'] + data + time + config['SecretKey']
    sign = helper.md5(config['AppKey'] + data + time + config['SecretKey']).upper().strip()
    # sign = '1'

    httpHeader = {
        'Content-Type' : 'application/json;charset=utf-8',
        'APPKEY' : config['AppKey'],
        'TIMESTAMP' : time,
        'SIGN' : sign,
    }
    # print httpHeader;
    print sign
    # exit()
    try:
        # 发起同步
        re = helper.httpPost(config['url'] + '?method=createOrder', data, httpHeader)
        reBody = json.loads(re)
        # print reBody ;exit()
        #成功同步
        if 200 == reBody['rspCode']:
            #支付定单
            body = {}
            body['orderId'] = outOrderId = reBody['body']['orderId']
            body['paymentSerialno'] = ticketBought['id']

            data2 = {}
            data2['body'] = body
            data2['appKey'] = config['AppKey']
            data2 = json.dumps(data2);

            # print data2;exit()
            sign = helper.md5(config['AppKey'] + data2 + time + config['SecretKey']).upper().strip()
            httpHeader = {
                'Content-Type' : 'application/json;charset=utf-8',
                'APPKEY' : config['AppKey'],
                'TIMESTAMP' : time,
                'SIGN' : sign,
            }

            re2 = helper.httpPost(config['url'] + '?method=payOrder', data2, httpHeader)
            reBody = json.loads(re2)
            print reBody
            if 200 == reBody['rspCode']:
                re = re + "\n\n" + re2
                print re
                #生成二维码
                qrcodeImg = reBody['body']['qrcodeUrl']
                sql = "update t_ticket_bought set out_app_code = 'JKB', temp_receiving_code = '%s', receiving_code='%s', dimen_code_path = '%s', remark2 = '%s' where id = %d" %  (ticketBought['receiving_code'], reBody['body']['eticket'], qrcodeImg, '{"outOrderId":"'+outOrderId+'"}', ticketBought['id'])
                print sql
                if not True == dbObj.update(sql):
                    helper.getLog(sql, 'addTicketToOuterJKB.UpdateTicketboughtlistErr.log')
            else:
                re = "%s\nPostData1:%s\n\n%s\nPostData2:%s" % (re, data, re2, data2)
                print re
                pass

        else:
            re = "%s \nPostData:%s\nPostHead:%s" % (re, data, json.dumps(httpHeader))
            pass
    except Exception, e:
        re = str(Exception) + ":" + str(e)
        re = "%s \nPostData:%s" %(re, data)
    re =  re.replace("'", '"')
    # print re;exit()
    #保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
           values ('%d', '%d', '%d', '%d', '%s', '%s', '%s') "
    values = (ticketBought['client_id'], ticketBought['order_id'], ticketBought['order_detail_id'], 1, 'JKB', re, helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToOuterJKB.SqlErr.log')

