#coding=UTF-8
#圆明新园票务系统
#code: YMXY

import time
import threading
import string
import json
import urllib,urllib2,httplib
import MySQLdb
import util.helper as helper
import util.db as db
import config.globalVar as globalVar #系统定义的全局变量

def test():
    print 'test'
    return 'hhh'

def ServiceYMXY(config, ticketBoughtList):
    # print ticketBoughtList;exit()

    if not 'CompanyCode' in config.keys():
        # print '==== no CompanyCode config ====' + config['url']
        return
    if len(ticketBoughtList) < 1:
        return

    # print ticketBoughtList;exit()

    #循环检查门票
    ts = [] #同步门票到第三方系统的线程列表
    for ticketBought in ticketBoughtList:
        # print ticketBought['id']
        #同步门票
        for conf in config:
            try:
                if conf == 'viewid_' + str(ticketBought['ticket_id']) and config[conf] != '' :
                    # 给第三方增加门票
                    t = threading.Thread(target = addTicketToOuterYMXY, args=(config, ticketBought,))
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
def addTicketToOuterYMXY(config, ticketBought):
    # global dbObj
    # dbObj = globalVar.getDbObj()
    dbObj = db.db()

    #查询微信单号
    weixinOrderId = dbObj.getValue("select transaction_id from t_payment where order_id = '%s'" % ticketBought['order_id'], 'transaction_id');

    #查询游客信息
    # userInfo = ''
    userInfo = dbObj.select("select user_id, name, mobile, id_number from t_user_identity_info where id = %d" % ticketBought['identity_info_id'])
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

    products = [
        {'viewid': config['viewid_' + str(ticketBought['ticket_id'])]},
        {'Viewname': ticketBought['ticket_id']},
        {'Type': config['Type_' + str(ticketBought['ticket_id'])]},
        {'number': ticketBought['count']}
    ]

    orderInfo = [
        {'TimeStamp': helper.now()},
        {'CompanyCode': config['CompanyCode']},
        {'CompanyName': 'weijingtong'},
        {'CompanyOrderID': str(weixinOrderId) + ',' + str(ticketBought['order_detail_id'])},
        {'OrderTime': ticketBought['create_time']},
        {'ArrivalDate': ticketBought['plan_time']},
        {'PayType': 1},
        {'VisitorName': visitorName},
        {'VisitorMobile': visitorMobile},
        {'IdCardNeed': 0},
        {'IdCard': userInfo['id_number']},
        {'Note': weixinOrderId},
        {'Products': helper.dict2xml('product', products).replace('<', '&lt;').replace('>', '&gt;')},
    ]
    data = helper.dict2xml('OrderInfo', orderInfo)
    data = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><OrderReq xmlns="http://tempuri.org/">%s</OrderReq></soap:Body></soap:Envelope>' % data
    # data = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><OrderReq xmlns="http://tempuri.org/"><OrderInfo><TimeStamp>2017-02-21 19:41:29</TimeStamp><CompanyCode>weijingtong96325812zfr</CompanyCode><CompanyName>weijingtong</CompanyName><CompanyOrderID>225534</CompanyOrderID><OrderTime>2017-02-21 19:34:33</OrderTime><ArrivalDate>2017-02-21 00:00:00</ArrivalDate><PayType>1</PayType><VisitorName>oZ9oauAoKfN1C4OptkqQbSeXhW-k</VisitorName><VisitorMobile>18723012341</VisitorMobile><IdCardNeed>0</IdCardNeed><IdCard>1X</IdCard><Note>weijingtong</Note><Products>&lt;product&gt;&lt;viewid&gt;E03&lt;/viewid&gt;&lt;Viewname&gt;2649&lt;/Viewname&gt;&lt;Type&gt;Adult&lt;/Type&gt;&lt;number&gt;1&lt;/number&gt;&lt;/product&gt;</Products></OrderInfo></OrderReq></soap:Body></soap:Envelope>'
    # data = '''<?xml version="1.0" encoding="UTF-8"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://tempuri.org/"><SOAP-ENV:Body><ns1:OrderReq><ns1:OrderInfo><ns1:TimeStamp>2017-02-21 15:34:49</ns1:TimeStamp><ns1:CompanyCode>weijingtong96325812zfr</ns1:CompanyCode><ns1:CompanyName>weijingtong</ns1:CompanyName><ns1:CompanyOrderID>186738</ns1:CompanyOrderID><ns1:OrderTime>2017-02-21 15:34:49</ns1:OrderTime><ns1:ArrivalDate>2017-02-21</ns1:ArrivalDate><ns1:PayType>1</ns1:PayType><ns1:VisitorName>WeijingtongVisitor</ns1:VisitorName><ns1:VisitorMobile>18523876001</ns1:VisitorMobile><ns1:IdCardNeed>0</ns1:IdCardNeed><ns1:IdCard>1X</ns1:IdCard><ns1:Products>&lt;product&gt;&lt;viewid&gt;E03&lt;/viewid&gt;&lt;Type&gt;Adult&lt;/Type&gt;&lt;number&gt;1&lt;/number&gt;&lt;viewname&gt;21&lt;/viewname&gt;&lt;/product&gt;</ns1:Products></ns1:OrderInfo></ns1:OrderReq></SOAP-ENV:Body></SOAP-ENV:Envelope>'''
    # data = '''<?xml version="1.0" encoding="UTF-8"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://tempuri.org/"><SOAP-ENV:Body><ns1:OrderCancel><ns1:orderInfo><ns1:TimeStamp>2017-02-21 19:39:50</ns1:TimeStamp><ns1:CompanyCode>weijingtong96325812zfr</ns1:CompanyCode><ns1:CompanyOrderID>186749</ns1:CompanyOrderID><ns1:IdCardNeed>0</ns1:IdCardNeed></ns1:orderInfo></ns1:OrderCancel></SOAP-ENV:Body></SOAP-ENV:Envelope>'''

##    print data;

    try:
        # 发起同步
        url = config['url']   #http://ydpt.hdyuanmingxinyuan.com/interface/AgentInterface.asmx
        host = helper.subStr(url, 'http://', '/interface')

        webservice = httplib.HTTPConnection(host, 80, timeout = 50)
        # webservice.set_debuglevel(1)

        # print response.getheaders() #获取头信息
        #连接到服务器后的第一个调用。它发送由request字符串到到服务器
        webservice.putrequest("POST", "/interface/AgentInterface.asmx")
        # webservice.putheader("Accept-Encoding", "text")
        # webservice.putheader("Host", "ydpt.hdyuanmingxinyuan.com")
        webservice.putheader("User-Agent", "WeijingtongService-python")
        webservice.putheader("Content-Type", "text/xml; charset=utf-8")
        # webservice.putheader("Connection", "Keep-Alive")
        webservice.putheader("Content-Length", "%d" % len(data))
        webservice.putheader("SOAPAction", "\"http://tempuri.org/OrderReq\"")
        # webservice.putheader("SOAPAction", "\"http://tempuri.org/OrderCancel\"")
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
##        print res
        # exit()
        re = "\n".join(res)
        # re = re.decode('gb2312').encode('utf-8')

        webservice.close() #关闭链接


        #成功同步
        if 'true' == helper.subStr(responseBody, '<Result>', '</Result>'):
            sql = "update t_ticket_bought set out_app_code = 'YMXY', temp_receiving_code = '%s' where id = %d" % (ticketBought['receiving_code'], ticketBought['id'])
            if not True == dbObj.update(sql):
                helper.getLog(sql, 'addTicketToOuterYMXY.UpdateTicketboughtlistErr.log')
        else:
            re = "%s \npostdata:%s" % (re, data)
            pass
    except Exception, e:
        re = str(Exception) + ":" + str(e)
        re = "%s \npostdata:%s" %(re, data)
    re =  re.replace("'", '"')

    # print re;exit()
    #保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
           values ('%d', '%d', '%d', '%d', '%s', '%s', '%s') "
    values = (ticketBought['client_id'], ticketBought['order_id'], ticketBought['order_detail_id'], 1, 'YMXY', re, helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToOuterYMXY.SqlErr.log')


