#coding=UTF-8
#科装智能闸机系统第二版 （乐和乐都在用）
#date: 2017-11-27
#code: KZZN2

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

def test():
    print 'test'
    return 'hhh'

def ServiceKZZN2(config, ticketBoughtList):
    # print config.keys();exit()
    # print ticketBoughtList;exit()
    if not 'cid' in config.keys():
        # print '==== no CompanyCode config ====' + config['url']
        return
    if len(ticketBoughtList) < 1:
        return

    #循环检查门票
    ts = [] #同步门票到第三方系统的线程列表
    for ticketBought in ticketBoughtList:
        #同步门票
        for conf in config:
            try:
                if conf == 'nTicketType_' + str(ticketBought['ticket_id']) and config[conf] != '' :
                    # print ticketBought['id']
                    # print config, config[conf] + ':nTicketType_' + str(ticketBought['ticket_id'])
                    # 给第三方增加门票
                    t = threading.Thread(target = addTicketToOuterKZZN2, args=(config, ticketBought,))
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
def addTicketToOuterKZZN2(config, ticketBought):
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
        visitorName = '散客'
        visitorMobile = '18523876001'
    else:
        userInfo = userInfo[0]
        visitorMobile = userInfo['mobile']
        visitorName = userInfo['name']
        # visitorName = repr(visitorName.decode('UTF-8'))[2:-1]
        # visitorName = visitorName.decode('UTF-8')
    # visitorName = 'wjtVisitor'

    ticketName = dbObj.getValue("select name from t_ticket where id = %d" % ticketBought['ticket_id'], 'name')
    ticketName = ticketName.decode('UTF-8')[0:10]
    # ticketName = 'chengrenpiao'
    # ticketName = '成人票'

    planDate = ''
    if ticketBought['plan_time']:
        planDate = str(ticketBought['plan_time'])[0:10]

    orderInfo = [
        {'cid': config['cid']},
        {'ccipher': config['ccipher']},
        # {'CEntrypriseCode': config['CEntrypriseCode']},
        {'cOrderID': ticketBought['order_detail_id']},
        {'nTicketType': config['nTicketType_' + str(ticketBought['ticket_id'])]},
        {'cTicketType': ticketName},
        {'dDateIn': planDate},
        {'cOtaSource': '微景通'},
        {'nHumanNum': ticketBought['count']},
        {'cPayType': 'weixin'},
        {'cCustName': visitorName[0:24]},
        {'cTel': visitorMobile},
        # {'cSecID': str(userInfo['id_number']) + 'X'},
        {'cSecID': str(userInfo['id_number'])},
    ]
    data = helper.dict2xml('OnWebOrder', orderInfo, 'xmlns="http://127.0.0.1/WebSellWx/"')
    data = ''.join(['<?xml version="1.0" encoding="utf-8"?>',
                    '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">',
                    '<soap:Body>%s</soap:Body>' % data,
                    '</soap:Envelope>'
                ])

    # print data;
    # exit();
    processOuterKZZN2(config, ticketBought, data, 1)

def processOuterKZZN2(config, ticketBought, data, processCount):
    dbObj = db.db()
    try:
        # 发起同步
        url = config['url']   #http://123.11.226.80:8118/service.asmx
        url = helper.subStr(url, 'http://', '/service')
        host = helper.subStr(url, '', ':')
        port = int(helper.subStr(url, ':', ''))

        responseBody, re = sendDataToOuterKZZN2(host, port, data)

        reBody = helper.subStr(responseBody, '<nStatus>', '</nStatus>')
        # print responseBody
        # print re
        #成功同步
        if '1' == reBody:
            cQrCode = helper.subStr(responseBody, '<cQrCode>', '</cQrCode>')
            cUrl = 'http://' + host + ':' + str(port) + helper.subStr(responseBody, '<cUrl>', '</cUrl>')
            cStatus = helper.subStr(responseBody, '<cStatus>', '</cStatus>')
            sql = "update t_ticket_bought set out_app_code = 'KZZN2', temp_receiving_code = '%s', receiving_code = '%s', dimen_code_path='%s', remark2='%s' where id = %d" %  (ticketBought['receiving_code'], cQrCode, cUrl, cStatus, ticketBought['id'])
            # print sql
            # print ticketBought
            if not True == dbObj.update(sql):
                helper.getLog(sql, 'addTicketToOuterKZZN2.UpdateTicketboughtlistErr.log')

            try:
                # 发送消息
                textMessage = '微景通验证码：'+ ticketBought['receiving_code'] +' \n票务验证码：'+ cQrCode +' \n购票张数：' + str(ticketBought['count']) + ' \n购票时间：' + str(ticketBought['create_time'])
                time = int(helper.thisTime())
                re = re + "\nsendMessageToUser:" + helper.sendMessageToUser(ticketBought['client_id'], ticketBought['user_id'], time, textMessage)
                # print helper.sendMessageToUser(ticketBought['client_id'], 'oRAx7ju3yK19Ll0WEwxlMBeFcia4', time, textMessage)
            except Exception, e:
                re = re + "\nsendMessageToUserError:" + str(Exception) + ":" + str(e)
        else:
            re = "%s \nPostData:%s" % (re, data)
            # print 'processCount:' + str(processCount)
            if processCount < 2:
                processCount += 1
                processOuterKZZN2(config, ticketBought, data, processCount)
                return
            else:
                re = "%s \nprocessCount:%s" % (re, str(processCount))
    except Exception, e:
        re = str(Exception) + ":" + str(e)
        re = "%s \nPostData:%s" %(re, data)
    re =  re.replace("'", '"')
    # print re;exit()
    #保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
           values ('%d', '%d', '%d', '%d', '%s', '%s', '%s') "
    values = (ticketBought['client_id'], ticketBought['order_id'], ticketBought['order_detail_id'], 1, 'KZZN2', re, helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToOuterKZZN2.SqlErr.log')

def sendDataToOuterKZZN2(host, port, data):
    # return ['<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><OnWebOrderResponse xmlns="http://127.0.0.1/WebSellWx/"><OnWebOrderResult><nStatus>1</nStatus><cStatus>OK</cStatus><cUrl>/images/722399640.jpg</cUrl><cQrCode>722399640</cQrCode></OnWebOrderResult></OnWebOrderResponse></soap:Body></soap:Envelope>', '']
    webservice = httplib.HTTPConnection(host, port, timeout = 50)
    # webservice.set_debuglevel(1)

    #连接到服务器后的第一个调用。它发送由request字符串到到服务器
    webservice.putrequest("POST", "/service.asmx")
    # webservice.putheader("Accept-Encoding", "text")
    # webservice.putheader("Host", "123.11.226.80")
    webservice.putheader("User-Agent", "WeijingtongService-python")
    webservice.putheader("Content-Type", "text/xml; charset=utf-8")
    # webservice.putheader("Connection", "Keep-Alive")
    webservice.putheader("Content-Length", "%d" % len(data))
    webservice.putheader("SOAPAction", '"http://127.0.0.1/WebSellWx/OnWebOrder"')
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