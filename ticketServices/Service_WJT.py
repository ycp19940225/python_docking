#coding=UTF-8
#外部系统直接调用我们核销接口(我们需要给验证码更新为二维码)(code:_WJT)
#date 2018-04-26
#code: _WJT

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

def Service_WJT(config, ticketBoughtList ,orderId):
    # print 'debug:';print config;print ticketBoughtList;print print 'debugEnd.';exit()
    helper.getLog('-----------start: orderId: '+str(orderId)+', boughtCount: '+str(len(ticketBoughtList))+'-------------', 'addTicketToService_WJT.log')
    if len(ticketBoughtList) < 1:
        return

    # print ticketBoughtList;exit()
    

    #循环检查门票
    ts = [] #同步门票到第三方系统的线程列表
    for bought in ticketBoughtList:
        # print bought['id']
        #同步门票
        try:
            # if conf == 'viewid_' + str(bought['mall_id']):
            # 给第三方增加门票
            # 配置为空，直接执行
            if len(config) == 0 :
                helper.getLog('pos - 39', 'addTicketToService_WJT.log')
                t = threading.Thread(target = addTicketToOuter_WJT, args=(config, bought,))
                t.start()
                ts.append(t)
            #配置有 ticket_ids 的情况，要进行判断
            if config.has_key('ticket_ids') and config['ticket_ids'] != '':
                ticketIds = config['ticket_ids'].split(",")
                helper.getLog('ticket_id: '+str(bought['ticket_id'])+' ticketIds - '+config['ticket_ids'], 'addTicketToService_WJT.log')
                # 只有指定了对接门票id 的门票才执行
                if str(bought['ticket_id']) in ticketIds:
                    t = threading.Thread(target = addTicketToOuter_WJT, args=(config, bought,))
                    t.start()
                    ts.append(t)
            # break

            # print '========='
        except:
            # print '========='
            pass

    for t in ts :
        t.join()


    return True

#同步门票到第三方系统的线程列表
def addTicketToOuter_WJT(config, bought):
    #print config;print print bought;exit()
    helper.getLog('thread start - '+str(bought['id']), 'addTicketToService_WJT.log')
    dbObj = db.db()
    try:
        re = '更新out_app_no为receiving_code：' + bought['receiving_code']
    except Exception, e:
        errMsg = "[Service_WJT - 71]" + str(Exception) + ":" + str(e)
        re = 'update out_app_no to receiving_code: ' + bought['receiving_code']
        helper.getLog(errMsg, 'addTicketToService_WJT.Err.log')

    helper.getLog('pos - 77', 'addTicketToService_WJT.log')

    try:
        qrcodeUrl = 'http://pwx.weijingtong.net/index.php/Api/Qrcode/index/?data=' + str(bought['receiving_code'])
        sql = "update t_ticket_bought set out_app_code = '_WJT', temp_receiving_code = '%s', dimen_code_path='%s' where id = '%d'" % (bought['receiving_code'], qrcodeUrl, bought['id'])

        if not True == dbObj.update(sql):
            helper.getLog(sql, 'addTicketToService_WJT.UpdateTicketboughtlistErr.log')
    except Exception, e:
        re = str(Exception) + ":" + str(e)

    helper.getLog('pos - 88', 'addTicketToService_WJT.log')
    re =  re.replace("'", '"')
    # print re;exit()
    #保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
        values ('%d', '%d', '%d', '%d', '%s', '%s', '%s') "
    values = (bought['client_id'], bought['order_id'], bought['order_detail_id'], 1, '_WJT', re + "\n", helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    helper.getLog('end---', 'addTicketToService_WJT.log')
    # print re
    if not re == True:
        helper.getLog(re, 'addTicketToService_WJT.SqlErr.log')


