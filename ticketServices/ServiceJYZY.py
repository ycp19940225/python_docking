#coding=UTF-8
#聚赢智业 芝樱小镇
#date: 2017-12-14
#outcode: JYZY

import time
import threading
import string
import json
import urllib,urllib2,httplib
import MySQLdb
import socket
import base64
import util.helper as helper
import util.db as db
import config.globalVar as globalVar #系统定义的全局变量

def test():
    print 'test'
    return 'hhh'

def ServiceJYZY(config, ticketBoughtList):
    # print config.keys();exit()
    # print ticketBoughtList;exit()
    if not 'uid' in config.keys():
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
                if conf == 'ticketId_' + str(ticketBought['ticket_id']) and config[conf] != '' :
                    # print ticketBought['id']
                    # print config, config[conf] + ':ticketId_' + str(ticketBought['ticket_id'])
                    # 给第三方增加门票
                    t = threading.Thread(target = addTicketToOuterJYZY, args=(config, ticketBought,))
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
def addTicketToOuterJYZY(config, ticketBought):
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
        idNumber = ''
    else:
        userInfo = userInfo[0]
        visitorMobile = userInfo['mobile']
        visitorName = userInfo['name']
        idNumber = userInfo['id_number']
        # visitorName = repr(visitorName.decode('UTF-8'))[2:-1]
        # visitorName = visitorName.decode('UTF-8')
    # visitorName = 'wjtVisitor'

    ticketName = dbObj.getValue("select name from t_ticket where id = %d" % ticketBought['ticket_id'], 'name')
    ticketName = ticketName.decode('UTF-8')[0:10]
    # ticketName = 'chengrenpiao'
    # ticketName = '成人票'

    data = '''<?xml version="1.0" encoding="UTF-8"?>
    <request xsi:schemaLocation="http://piao.qunar.com/2013/QMenpiaoRequestSchema QMRequestDataSchema-2.0.1.xsd" xmlns="http://piao.qunar.com/2013/QMenpiaoRequestSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <header>
            <application>Qunar.Menpiao.Agent</application>
            <processor>SupplierDataExchangeProcessor</processor>
            <version>v2.0.1</version>
            <bodyType>CreateOrderForBeforePaySyncRequestBody</bodyType>
            <createUser>SupplierSystemName</createUser>
            <createTime>%s</createTime>
            <supplierIdentity>%s</supplierIdentity>
        </header>
        <body xsi:type="CreateOrderForBeforePaySyncRequestBody">
            <orderInfo>
                <orderId>%s</orderId>
                <product>
                    <resourceId>%s</resourceId>
                    <productName>%s</productName>
                    <visitDate>%s</visitDate>
                    <sellPrice>%s</sellPrice>
                    <cashBackMoney>0</cashBackMoney>
                </product>
                <contactPerson>
                    <name>%s</name><namePinyin></namePinyin>
                    <mobile>%s</mobile>
                    <idCard>%s</idCard>
                    <email></email>
                    <address></address>
                    <zipCode></zipCode>
                </contactPerson>
                <visitPerson>
                    <person>
                        <name></name><namePinyin></namePinyin>
                        <credentials></credentials>
                        <credentialsType></credentialsType>
                        <defined1Value></defined1Value>
                        <defined2Value></defined2Value>
                    </person>
                </visitPerson>
                <orderQuantity>%s</orderQuantity>
                <orderPrice>%s</orderPrice>
                <orderCashBackMoney></orderCashBackMoney>
                <orderStatus>CASHPAY_ORDER_INIT</orderStatus>
                <orderRemark></orderRemark>
                <orderSource></orderSource>
                <eticketNo></eticketNo>
            </orderInfo>
        </body>
    </request>
    ''' % (
        helper.now(), config['uid'], ticketBought['order_detail_id'], config['ticketId_' + str(ticketBought['ticket_id'])], ticketName, str(ticketBought['plan_time']),
        int(ticketBought['price']*100), visitorName, visitorMobile, idNumber, ticketBought['count'], int(ticketBought['count']*ticketBought['price']*100)
    )

    data = data.replace("\n", '')
    # print data;
    # exit();
    processOuterJYZY(config, ticketBought, data, 1)

def processOuterJYZY(config, ticketBought, data, processCount):
    dbObj = db.db()
    # 发起同步
    dataOld = data
    data = buildParam(data, config['pkey'], 'createOrderForBeforePaySync')
    re = sendDataToOuterJYZY(config['url'], data)
    # redata, re = sendDataToOuterJYZY(config['url'], None)

    try:
        code = helper.subStr(re, '<code>', '</code>')
        # print responseBody
        # print re
        #成功同步
        if '1000' == code:
            re1 = re
            partnerorderId = helper.subStr(re, '<partnerorderId>', '</partnerorderId>')
            re, postData = payTicketToOuterJYZY(config, ticketBought, partnerorderId)
            # print partnerorderId;exit()

            code = helper.subStr(re, '<code>', '</code>')
            if '1000' == code:
                qrcodeUrl = 'http://pwx.weijingtong.net/index.php/Api/Qrcode/index/?data=' + str(ticketBought['order_detail_id'])
                sql = "update t_ticket_bought set out_app_code = 'JYZY', temp_receiving_code = '%s', receiving_code = '%s', dimen_code_path='%s' where id = %d" %  (ticketBought['receiving_code'], partnerorderId, qrcodeUrl, ticketBought['id'])
                # print sql
                if not True == dbObj.update(sql):
                    helper.getLog(sql, 'addTicketToOuterJYZY.UpdateTicketboughtlistErr.log')
            else:
                re = "re1:%s \nre2:%s \nPostData1:%s \nPostData2:%s" % (re1, re, data, postData)
        else:
            re = "%s \nPostData:%s" % (re, data)
            print 'processCount:' + str(processCount)
            if processCount < 2:
                processCount += 1
                processOuterJYZY(config, ticketBought, dataOld, processCount)
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
    values = (ticketBought['client_id'], ticketBought['order_id'], ticketBought['order_detail_id'], 1, 'JYZY', re, helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToOuterJYZY.SqlErr.log')

def payTicketToOuterJYZY(config, ticketBought, partnerorderId, count = 1):
    url = config['url']
    data = '''<?xml version="1.0" encoding="UTF-8"?>
        <request xsi:schemaLocation="http://piao.qunar.com/2013/QMenpiaoRequestSchema QMRequestDataSchema-2.0.1.xsd" xmlns="http://piao.qunar.com/2013/QMenpiaoRequestSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <header>
                <application>Qunar.Menpiao.Agent</application>
                <processor>SupplierDataExchangeProcessor</processor>
                <version>v2.0.1</version>
                <bodyType>PayOrderForBeforePaySyncRequestBody</bodyType>
                <createUser>SupplierSystemName</createUser>
                <createTime>%s</createTime>
                <supplierIdentity>%s</supplierIdentity>
            </header>
            <body xsi:type="PayOrderForBeforePaySyncRequestBody">
                <orderInfo>
                    <partnerOrderId>%s</partnerOrderId>
                    <orderStatus>PREPAY_ORDER_PRINTING</orderStatus>
                    <orderPrice>%s</orderPrice>
                    <paymentSerialno></paymentSerialno>
                    <eticketNo></eticketNo>
                </orderInfo>
            </body>
        </request>
        ''' % ( helper.now(), config['uid'], partnerorderId, ticketBought['count']*ticketBought['price']*100 )

    data = data.replace("\n", '')
    data = buildParam(data, config['pkey'], 'payOrderForBeforePaySync');
    # print data;

    re = sendDataToOuterJYZY(url, data)

    code = helper.subStr(re, '<code>', '</code>')
    if( count < 2 and  '1000' != code ):
       re, data = payTicketToOuterJYZY(config, ticketBought, partnerorderId, 2)
       data = data + "\nprocessCount:2"

    return [re, data]

def buildParam(data, key, method):
    data = base64.b64encode(data).replace("\n", '')
    # print data;exit()
    sign = helper.md5(key + data).upper();

    param = "method=" + method + "&requestParam=" + json.dumps({
            "data" : data,
            "signed" : sign,
            "securityType" : "MD5",
        }).replace(' ', '')

    return param

def sendDataToOuterJYZY(url, data):
    # print data
    # print url;
    # url = 'http://www.juyingzhiye.com/service/open'
    # data = 'method=createOrderForBeforePaySync&requestParam={"data":"PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4gICAgPHJlcXVlc3QgeHNpOnNjaGVtYUxvY2F0aW9uPSJodHRwOi8vcGlhby5xdW5hci5jb20vMjAxMy9RTWVucGlhb1JlcXVlc3RTY2hlbWEgUU1SZXF1ZXN0RGF0YVNjaGVtYS0yLjAuMS54c2QiIHhtbG5zPSJodHRwOi8vcGlhby5xdW5hci5jb20vMjAxMy9RTWVucGlhb1JlcXVlc3RTY2hlbWEiIHhtbG5zOnhzaT0iaHR0cDovL3d3dy53My5vcmcvMjAwMS9YTUxTY2hlbWEtaW5zdGFuY2UiPiAgICAgICAgPGhlYWRlcj4gICAgICAgICAgICA8YXBwbGljYXRpb24+UXVuYXIuTWVucGlhby5BZ2VudDwvYXBwbGljYXRpb24+ICAgICAgICAgICAgPHByb2Nlc3Nvcj5TdXBwbGllckRhdGFFeGNoYW5nZVByb2Nlc3NvcjwvcHJvY2Vzc29yPiAgICAgICAgICAgIDx2ZXJzaW9uPnYyLjAuMTwvdmVyc2lvbj4gICAgICAgICAgICA8Ym9keVR5cGU+Q3JlYXRlT3JkZXJGb3JCZWZvcmVQYXlTeW5jUmVxdWVzdEJvZHk8L2JvZHlUeXBlPiAgICAgICAgICAgIDxjcmVhdGVVc2VyPlN1cHBsaWVyU3lzdGVtTmFtZTwvY3JlYXRlVXNlcj4gICAgICAgICAgICA8Y3JlYXRlVGltZT4yMDE3LTEyLTIwIDE4OjE0OjM4PC9jcmVhdGVUaW1lPiAgICAgICAgICAgIDxzdXBwbGllcklkZW50aXR5PjY1MTY8L3N1cHBsaWVySWRlbnRpdHk+ICAgICAgICA8L2hlYWRlcj4gICAgICAgIDxib2R5IHhzaTp0eXBlPSJDcmVhdGVPcmRlckZvckJlZm9yZVBheVN5bmNSZXF1ZXN0Qm9keSI+ICAgICAgICAgICAgPG9yZGVySW5mbz4gICAgICAgICAgICAgICAgPG9yZGVySWQ+NjAzNDAxPC9vcmRlcklkPiAgICAgICAgICAgICAgICA8cHJvZHVjdD4gICAgICAgICAgICAgICAgICAgIDxyZXNvdXJjZUlkPjEwMjQ1PC9yZXNvdXJjZUlkPiAgICAgICAgICAgICAgICAgICAgPHByb2R1Y3ROYW1lPua1i+ivleelqDwvcHJvZHVjdE5hbWU+ICAgICAgICAgICAgICAgICAgICA8dmlzaXREYXRlPjIwMTctMTItMjA8L3Zpc2l0RGF0ZT4gICAgICAgICAgICAgICAgICAgIDxzZWxsUHJpY2U+MTA8L3NlbGxQcmljZT4gICAgICAgICAgICAgICAgICAgIDxjYXNoQmFja01vbmV5PjA8L2Nhc2hCYWNrTW9uZXk+ICAgICAgICAgICAgICAgIDwvcHJvZHVjdD4gICAgICAgICAgICAgICAgPGNvbnRhY3RQZXJzb24+ICAgICAgICAgICAgICAgICAgICA8bmFtZT7mtYvor5U8L25hbWU+ICAgICAgICAgICAgIA==ICAgICAgIDxuYW1lUGlueWluPjwvbmFtZVBpbnlpbj4gICAgICAgICAgICAgICAgICAgIDxtb2JpbGU+MTUyMTMyNDk3NzU8L21vYmlsZT4gICAgICAgICAgICAgICAgICAgIDxlbWFpbD48L2VtYWlsPiAgICAgICAgICAgICAgICAgICAgPGFkZHJlc3M+PC9hZGRyZXNzPiAgICAgICAgICAgICAgICAgICAgPHppcENvZGU+PC96aXBDb2RlPiAgICAgICAgICAgICAgICA8L2NvbnRhY3RQZXJzb24+ICAgICAgICAgICAgICAgIDx2aXNpdFBlcnNvbj4gICAgICAgICAgICAgICAgICAgIDxwZXJzb24+ICAgICAgICAgICAgICAgICAgICAgICAgPG5hbWU+PC9uYW1lPiAgICAgICAgICAgICAgICAgICAgICAgIDxuYW1lUGlueWluPjwvbmFtZVBpbnlpbj4gICAgICAgICAgICAgICAgICAgICAgICA8Y3JlZGVudGlhbHM+PC9jcmVkZW50aWFscz4gICAgICAgICAgICAgICAgICAgICAgICA8Y3JlZGVudGlhbHNUeXBlPjwvY3JlZGVudGlhbHNUeXBlPiAgICAgICAgICAgICAgICAgICAgICAgIDxkZWZpbmVkMVZhbHVlPjwvZGVmaW5lZDFWYWx1ZT4gICAgICAgICAgICAgICAgICAgICAgICA8ZGVmaW5lZDJWYWx1ZT48L2RlZmluZWQyVmFsdWU+ICAgICAgICAgICAgICAgICAgICA8L3BlcnNvbj4gICAgICAgICAgICAgICAgPC92aXNpdFBlcnNvbj4gICAgICAgICAgICAgICAgPG9yZGVyUXVhbnRpdHk+MTwvb3JkZXJRdWFudGl0eT4gICAgICAgICAgICAgICAgPG9yZGVyUHJpY2U+MTA8L29yZGVyUHJpY2U+ICAgICAgICAgICAgICAgIDxvcmRlckNhc2hCYWNrTW9uZXk+PC9vcmRlckNhc2hCYWNrTW9uZXk+ICAgICAgICAgICAgICAgIDxvcmRlclN0YXR1cz5DQVNIUEFZX09SREVSX0lOSVQ8L29yZGVyU3RhdHVzPiAgICAgICAgICAgICAgICA8b3JkZXJSZW1hcms+PC9vcmRlclJlbWFyaz4gICAgICAgICAgICAgICAgPG9yZGVyU291cmNlPjwvb3JkZXJTb3VyY2U+ICAgICAgICAgICAgICAgIDxldGlja2V0Tm8+PC9ldGlja2V0Tm8+ICAgICAgICAgICAgPC9vcmRlckluZm8+ICAgICAgICA8L2JvZHk+ICAgIDwvcmVxdWVzdD4gICAg","securityType":"MD5","signed":"002867F0B33D0B82A04A5FDCF0E48D84"}'
    re = helper.httpPost(url, data, {'Content-Type': 'application/x-www-form-urlencoded'})
    # re = helper.httpPost(url, data)

    res = json.loads(re)
    redata = base64.decodestring(res['data'])
    # print redata
    # exit()

    return redata