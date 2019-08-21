#coding=UTF-8
#科装智能闸机系统 （桐柏山在用）
#date: 2017-05-08
#code: KZZN

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

def ServiceKZZN(config, ticketBoughtList):
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
                    t = threading.Thread(target = addTicketToOuterKZZN, args=(config, ticketBought,))
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
def addTicketToOuterKZZN(config, ticketBought):
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
    orderInfo = [
        {'cid': config['cid']},
        {'ccipher': config['ccipher']},
        {'cOrder': ticketBought['order_detail_id']},
        {'nHuman': ticketBought['count']},
        {'cName': visitorName[0:24]},
        {'cPhone': visitorMobile},
        {'nTicketType': config['nTicketType_' + str(ticketBought['ticket_id'])]},
        {'cTicketType': ticketName},
        {'dDateIn': str(ticketBought['plan_time'])[0:10]},
        {'cQrID': ticketBought['receiving_code']},
        {'nCustType': 1},
        {'cip': socket.gethostbyname(socket.gethostname())},
        {'fMoney': ticketBought['price']},
        {'cPayType': 'weixin'},
    ]
    data = helper.dict2xml('OnPreSellOrder', orderInfo, 'xmlns="http://localhost/WebSell/"')
    data = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>%s</soap:Body></soap:Envelope>' % data

    print data;
    # exit();

    try:
        # 发起同步
        url = config['url']   #http://123.11.226.80:8118/service.asmx
        host = helper.subStr(url, 'http:/', 'service')
        host = helper.subStr(host, '/', ':')
        # print host
        webservice = httplib.HTTPConnection(host, 8118, timeout = 50)
        # webservice.set_debuglevel(1)

        # print response.getheaders() #获取头信息
        #连接到服务器后的第一个调用。它发送由request字符串到到服务器
        webservice.putrequest("POST", "/service.asmx")
        # webservice.putheader("Accept-Encoding", "text")
        # webservice.putheader("Host", "123.11.226.80")
        webservice.putheader("User-Agent", "WeijingtongService-python")
        webservice.putheader("Content-Type", "text/xml; charset=utf-8")
        # webservice.putheader("Connection", "Keep-Alive")
        webservice.putheader("Content-Length", "%d" % len(data))
        webservice.putheader("SOAPAction", '"http://localhost/WebSell/OnPreSellOrder"')
        # webservice.putheader("SOAPAction", '"http://tempuri.org/OnPreSellOrder"')
        # webservice.putheader("SOAPAction", '"http://123.11.226.80/OnPreSellOrder"')
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

        reBody = helper.subStr(responseBody, '<OnPreSellOrderResult>', '</OnPreSellOrderResult>')
        print reBody
        #成功同步
        if '1' == reBody:
            #生成二维码
            reMakeQrcode = helper.httpGet( helper.confGet('host', 'commonService') + 'Api/TicketQrcode/saveFile/?clientId=' + str( ticketBought['client_id'] ) + '&receivingCode=' + ticketBought['receiving_code'] )
            reMakeQrcodeMap = json.loads(reMakeQrcode)
            # print reMakeQrcodeMap['code']
            if reMakeQrcodeMap['code'] == 0:
                sql = "update t_ticket_bought set out_app_code = 'KZZN', temp_receiving_code = '%s', dimen_code_path = '%s' where id = %d" %  (ticketBought['receiving_code'], reMakeQrcodeMap['filePath'], ticketBought['id'])
                # print sql
                if not True == dbObj.update(sql):
                    helper.getLog(sql, 'addTicketToOuterKZZN.UpdateTicketboughtlistErr.log')
            else:
                helper.getLog(reMakeQrcode, 'makeQrcodeErrorKZZN.log')

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
    values = (ticketBought['client_id'], ticketBought['order_id'], ticketBought['order_detail_id'], 1, 'KZZN', re, helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToOuterKZZN.SqlErr.log')


