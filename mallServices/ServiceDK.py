#coding=UTF-8
#道控闸机系统 （海龙屯在用）
#date: 2018-06-05
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

def ServiceDK(config, mallBoughtList):
    # print config.keys();exit()
    # print mallBoughtList;exit()
    # print config

    if len(mallBoughtList) < 1:
        return

    #循环检查门票
    ts = [] #同步门票到第三方系统的线程列表
    for mallBought in mallBoughtList:
        #同步门票
        for conf in config:
            try:
                if conf == 'mall_ProductID_' + str(mallBought['mall_product_id']) and config[conf] != '' :
                    # print mallBought['id']
                    # print config, config[conf] + ':mall_ProductID_' + str(mallBought['mall_product_id'])
                    # 给第三方增加门票
                    t = threading.Thread(target = addTicketToOuterDK, args=(config, mallBought,))
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
def addTicketToOuterDK(config, mallBought):
    # global dbObj
    # dbObj = globalVar.getDbObj()
    dbObj = db.db()

    #查询游客信息
    # userInfo = ''
    userInfo = dbObj.select("select user_id, name, mobile, id_number from t_user_identity_info where id = %d" % mallBought['identity_info_id'])
    # userInfo = []
    # userInfo.append({
        # 'name': '微景通',
        # 'mobile' : '18523876001'
    # })
    if userInfo == False or len(userInfo) < 1:
        visitorName = 'weijingtongVisitor'
        visitorMobile = '18523876001'
        userInfo = {'id_number': ''}
    else:
        userInfo = userInfo[0]
        visitorMobile = userInfo['mobile']
##        visitorName = userInfo['user_id']
        visitorName = userInfo['name']
        visitorName = repr(visitorName.decode('UTF-8'))[2:-1]
##        visitorName = '\u5f20\u8001\u5927'
##        visitorName = urllib.urlencode({1:visitorName})[2:]

    # visitorName = 'wjtVisitor'
    ticketName = dbObj.getValue("select name from t_mall_product where id = %d" % mallBought['mall_product_id'], 'name')
    # ticketName = '成人票'
    ticketName = repr(ticketName.decode('UTF-8'))[2:-1][0:48]
    # ticketName = 'test'
    Order = {}
    Order['OrderNO'] = str(mallBought['order_number'])
    Order['LinkName'] = visitorName
    Order['LinkPhone'] = visitorMobile
    Order['LinkICNO'] = userInfo['id_number']
    Order['TotalAmount'] = str(round(mallBought['price'] * mallBought['buy_count'], 2))
    Order['CreateTime'] = str(mallBought['create_time'])

    Visitor = {}
    Visitor['VisitorName'] = visitorName
    Visitor['VisitorPhone'] = visitorMobile
    Visitor['VisitorICNO'] = userInfo['id_number']

    Details = {}
    Details['OrderNO'] = mallBought['order_number']
    Details['ItemID'] = mallBought['order_number']
    Details['ProductCode'] = config['mall_ProductCode_' + str(mallBought['mall_product_id'])]
    Details['ProductID'] = config['mall_ProductID_' + str(mallBought['mall_product_id'])]
    Details['ProductPackID'] = config['mall_ProductPackID_' + str(mallBought['mall_product_id'])]
    Details['ProductMarketPrice'] = str(round(mallBought['list_price'], 2))
    Details['ProductPrice'] = str(round(mallBought['price'], 2))
    Details['ProductSellPrice'] = str(round(mallBought['price'], 2))
    Details['ProductCount'] = mallBought['buy_count']
    Details['ProductSDate'] = str(mallBought['plan_time'])[0:10]
    Details['ProductEDate'] = str(mallBought['plan_time'])[0:10]
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
    # try:
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
        parameters['otaOrderNO'] = str(mallBought['order_number'])
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

        res = helper.webservice(host, int(port), "/service.asmx", data2, "http://tempuri.org/OrderFinish", 0)
        # print res
        responseBody2 = res[0]
        re2 = res[1]
        reBody = json.loads(helper.subStr(responseBody2, '<OrderFinishResult>', '</OrderFinishResult>'))
        # print reBody
        if '00' == reBody['ResultCode']:
            re = re + "\n\n" + re2
            #生成二维码
            resultJson = json.loads(reBody['ResultJson'])[0]
            qrcodeImg = 'http://pwx.weijingtong.net/index.php/Api/Qrcode/?data=' + resultJson['ECode']
            # sql = "update t_ticket_bought set out_app_code = 'DK', temp_receiving_code = '%s', receiving_code='%s', dimen_code_path = '%s' where id = %d" %  (mallBought['receiving_code'], resultJson['ECode'], qrcodeImg, mallBought['id'])
            sql = "update t_mall_bought set out_app_code = 'DK', out_app_no = '%s', dimen_code_path='%s' where id = '%d'" % (resultJson['ECode'], qrcodeImg, mallBought['id'])
            # print sql
            if not True == dbObj.update(sql):
                helper.getLog(sql, 'addTicketToOuterDK.UpdateTicketboughtlistErr.log')
        else:
            re = "%s\nPostData1:%s\n\n%s\nPostData2:%s" % (re, data, re2, data2)
            pass

    else:
        re = "%s \nPostData:%s" % (re, data)
        pass
    # except Exception, e:
        # re = str(Exception) + ":" + str(e)
        # re = "%s \nPostData:%s" %(re, data)
    re =  re.replace("'", '"')
    # print re;exit()
    #保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
           values ('%d', '%d', '%s', '%d', '%s', '%s', '%s') "
    values = (mallBought['client_id'], mallBought['order_id'], mallBought['order_number'], 1, 'DK', re, helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToOuterDK.SqlErr.log')

