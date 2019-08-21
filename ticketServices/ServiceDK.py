#coding=UTF-8
#道控闸机系统 （海龙屯在用）
#date: 2018-05-03
#code: DK

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

def ServiceDK(config, ticketBoughtList):
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
                if conf == 'ProductID_' + str(ticketBought['ticket_id']) and config[conf] != '' :
                    # print ticketBought['id']
                    # print config, config[conf] + ':ProductID_' + str(ticketBought['ticket_id'])
                    # 给第三方增加门票
                    t = threading.Thread(target = addTicketToOuterDK, args=(config, ticketBought,))
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
def addTicketToOuterDK(config, ticketBought):
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
        visitorName = repr(visitorName.decode('UTF-8'))[2:-1]
##        visitorName = '\u5f20\u8001\u5927'
##        visitorName = urllib.urlencode({1:visitorName})[2:]

    # visitorName = 'wjtVisitor'
    ticketName = dbObj.getValue("select name from t_ticket where id = %d" % ticketBought['ticket_id'], 'name')
    # ticketName = '成人票'
    ticketName = repr(ticketName.decode('UTF-8'))[2:-1][0:48]
    # ticketName = 'test'
    Order = {}
    Order['OrderNO'] = str(ticketBought['order_detail_id'])
    Order['LinkName'] = visitorName
    Order['LinkPhone'] = visitorMobile
    Order['LinkICNO'] = userInfo['id_number']
    Order['TotalAmount'] = str(round(ticketBought['price'] * ticketBought['count'], 2))
    Order['CreateTime'] = str(ticketBought['create_time'])

    Visitor = {}
    Visitor['VisitorName'] = visitorName
    Visitor['VisitorPhone'] = visitorMobile
    Visitor['VisitorICNO'] = userInfo['id_number']

    Details = {}
    Details['OrderNO'] = ticketBought['order_detail_id']
    Details['ItemID'] = ticketBought['order_detail_id']
    Details['ProductCode'] = config['ProductCode_' + str(ticketBought['ticket_id'])]
    Details['ProductID'] = config['ProductID_' + str(ticketBought['ticket_id'])]
    Details['ProductPackID'] = config['ProductPackID_' + str(ticketBought['ticket_id'])]
    Details['ProductMarketPrice'] = str(round(ticketBought['list_price'], 2))
    Details['ProductPrice'] = str(round(ticketBought['price'], 2))
    Details['ProductSellPrice'] = str(round(ticketBought['price'], 2))
    Details['ProductCount'] = ticketBought['count']
    Details['ProductSDate'] = str(ticketBought['plan_time'])[0:10]
    Details['ProductEDate'] = str(ticketBought['plan_time'])[0:10]
    Details['Visitor'] = json.dumps(Visitor)

    postOrder = {}
    postOrder['Ptime'] = helper.now()
    postOrder['parkCode'] = config['parkCode']
    postOrder['timestamp'] = helper.now()
    postOrder['Order'] = json.dumps(Order)
    postOrder['Details'] = json.dumps([Details])

    # print postOrder
    # print json.dumps(postOrder)
    postOrder = json.dumps(postOrder);
    # exit()
    sign = base64.encodestring(helper.md5(config['merchantCode'] + config['privateKey'] + postOrder + str(int(helper.thisTime()))).upper()).strip()
    # sign = '1'
    # print sign;exit()

    data = '''<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <OrderOccupies xmlns="http://tempuri.org/">
                          <merchantCode>%s</merchantCode>
                          <postOrder>%s</postOrder>
                          <signature>%s</signature>
                    </OrderOccupies>
                </soap:Body>
            </soap:Envelope>''' % (config['merchantCode'], postOrder, sign)
    # print data;
    # exit();
    try:
        # 发起同步
        '''
        responseBody = helper.httpPost(config['url'] + '/OrderOccupies', data, {'Content-Type' : 'application/x-www-form-urlencoded'})
        '''
        url = config['url']   #http://123.11.226.80:8118/service.asmx
        # url  = 'http://112.74.131.57:10006/service.asmx'
        host = helper.subStr(url, 'http:/', 'service')
        host = helper.subStr(host, '/', ':')
        port = helper.subStr(url, '://', 'service')
        port = helper.subStr(port, ':', '/')
        # print host;exit()

        #占用定单
        res = helper.webservice(host, int(port), "/service.asmx", data, "http://tempuri.org/OrderOccupies", 0)
        responseBody = res[0]
        re = res[1]
        reBody = json.loads(helper.subStr(responseBody, '<OrderOccupiesResult>', '</OrderOccupiesResult>'))
        # print reBody
        #成功同步
        if '00' == reBody['ResultCode']:
            #支付定单
            parameters = {}
            parameters['otaOrderNO'] = str(ticketBought['order_detail_id'])
            parameters['parkCode'] = config['parkCode']
            parameters['timestamp'] = helper.now()
            parameters = json.dumps(parameters)

            sign = base64.encodestring(helper.md5(config['merchantCode'] + config['privateKey'] + parameters + str(int(helper.thisTime()))).upper()).strip()

            data2 = '''<?xml version="1.0" encoding="utf-8"?>
                    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                        <soap:Body>
                            <OrderFinish xmlns="http://tempuri.org/">
                              <otaCode>%s</otaCode>
                              <parameters>%s</parameters>
                              <signature>%s</signature>
                            </OrderFinish>
                        </soap:Body>
                    </soap:Envelope>''' % (config['merchantCode'], parameters, sign)

            res = helper.webservice(host, int(port), "/service.asmx", data2, "http://tempuri.org/OrderFinish", True)
            responseBody2 = res[0]
            re2 = res[1]
            reBody = json.loads(helper.subStr(responseBody2, '<OrderFinishResult>', '</OrderFinishResult>'))
            # print reBody
            if '00' == reBody['ResultCode']:
                re = re + "\n\n" + re2
                #生成二维码
                resultJson = json.loads(reBody['ResultJson'])[0]
                qrcodeImg = 'http://pwx.weijingtong.net/index.php/Api/Qrcode/?data=' + resultJson['ECode']
                sql = "update t_ticket_bought set out_app_code = 'DK', temp_receiving_code = '%s', receiving_code='%s', dimen_code_path = '%s' where id = %d" %  (ticketBought['receiving_code'], resultJson['ECode'], qrcodeImg, ticketBought['id'])
                # print sql
                if not True == dbObj.update(sql):
                    helper.getLog(sql, 'addTicketToOuterDK.UpdateTicketboughtlistErr.log')
            else:
                re = "%s\nPostData1:%s\n\n%s\nPostData2:%s" % (re, data, re2, data2)
                pass

        else:
            re = "%s \nPostData:%s" % (re, data)
            pass
    except Exception, e:
        re = str(Exception) + ":" + str(e)
        re = "%s \nPostData:%s" %(re, data)
    re =  re.replace("'", '"')
    # print re;exit()
    #保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
           values ('%d', '%d', '%d', '%d', '%s', '%s', '%s') "
    values = (ticketBought['client_id'], ticketBought['order_id'], ticketBought['order_detail_id'], 1, 'DK', re, helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToOuterDK.SqlErr.log')

