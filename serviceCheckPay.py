#coding=UTF-8
# /usr/bin/python -u /datas/www/python/serviceCheckPay.py
import config.globalVar as globalVar #系统定义的全局变量
import time
import threading
import string
import json
import urllib,urllib2,httplib
import MySQLdb
import util.helper as helper #工具集
import util.db as db #db操作类
from meliae import scanner

#连接数据库
dbObj = None

def reBuyDo(serviceUrl, order, sql):
    re = helper.httpPost(serviceUrl, order)
    helper.getLog( 're_buy_do_info -- order_id:' + str(order['orderId']) + ' -- order_create_time:' + str(order['create_time']) + ' -- ' + sql + ' -- ' + re, 'serviceCheckPay.log' )
    # print ' ==== ' + str(order['type']) + ':' + helper.now()
    pass

def findOrders(serviceUrl, sql, type):
    # global dbObj
    dbObj = db.db()
    orderList = dbObj.select(sql)
    # print '=========='
    # print helper.now()
    # print sql
    # print orderList
    # print len(orderList)
    # helper.getLog( 'len(orderList)['+ str(type) +']:' + str(len(orderList)) + ' -- ' + sql, 'serviceCheckPay.log' )
    ts = [] #线程列表
    for order in orderList:
        if not order['pay_status'] == 0:
            order['confirmDo'] = 1

        t = threading.Thread(target = reBuyDo, args=(serviceUrl, order, sql, ))
        t.start()
        ts.append(t)
    for t in ts :
        t.join()

# 初始化服务
def serviceInit(types):
    # print types;


    #启动服务
    serviceUrl = helper.confGet('host', 'commonService') + 'Order/Index/reBuyDo'
    now = helper.now(- 3600 * 2, '%Y-%m-%d %H:00:00')
    orderId = 0
    paybackId = 0
    ids = {}
    # print now;
    test = 0
    while True:
        ts = [] #线程列表
        #连接数据库
        # global dbObj
        dbObj = db.db()

        # 不用每次循环都查询配置
        if not now == helper.now(- 3600 * 1, '%Y-%m-%d %H:00:00'):
            if test == 1:
                now = helper.now(- 3600 * 20, '%Y-%m-%d %H:00:00') #改变这个时间，重启，则重新开始扫描
            else:
                now = helper.now(- 3600 * 1, '%Y-%m-%d %H:00:00') #改变这个时间，重启，则重新开始扫描

            # print now;

            orderId = dbObj.getValue('SELECT id FROM t_order WHERE create_time > "%s" ORDER BY id ' % (now), 'id')
            if orderId == None:
                orderId = dbObj.getValue('SELECT id FROM t_order WHERE 1=1 ORDER BY id DESC limit 0, 1', 'id')
                if orderId == None:
                    orderId = 0

            paybackId = dbObj.getValue('SELECT id FROM t_payback WHERE create_time > "%s" ORDER BY id ' % (now), 'id')
            if paybackId == None:
                paybackId = dbObj.getValue('SELECT id FROM t_payback WHERE 1=1 ORDER BY id DESC limit 0, 1', 'id')
                if paybackId == None:
                    paybackId = 0

            # print orderId; print paybackId;
            helper.getLog('orderId:%d -- paybackId: %d' % (orderId, paybackId), 'serviceCheckPay.log')

            for type in types:
                ids[type] = dbObj.getValue("SELECT id FROM %s WHERE create_time > '%s' ORDER BY id " % (types[type], now), 'id')
                if ids[type] == None:
                    ids[type] = dbObj.getValue("SELECT id FROM %s WHERE 1 =1 ORDER BY id DESC limit 0, 1" % (types[type]), 'id')
                    if ids[type] == None:
                        ids[type] = 0
            # print ids;

        for type in types:
            # print str(type) + '/' + types[type]
            status = '1'
            if test == 1:
                status = '1, 9'
            sql = ' '.join([
                "SELECT id AS orderId, pay_status, type, client_id AS clientId, create_time FROM t_order WHERE id > %d AND type = %d AND status in (%s) AND pay_time BETWEEN '%s' AND '%s' " % (orderId, type, status, now, helper.now(-5)),
                "AND id IN ( SELECT order_id FROM t_payback WHERE id > %d AND order_id NOT IN ( SELECT order_id FROM %s WHERE id >= %d ) ) " % (paybackId, types[type], ids[type]),
                "ORDER BY id DESC LIMIT 0, 10"
            ])
            # print sql
            t = threading.Thread(target = findOrders, args=(serviceUrl, sql, type, ))
            t.start()
            ts.append(t)
        for t in ts :
            t.join()

        time.sleep( 10 )

        scanner.dump_all_objects('/logs/python/mem.log')
        # print 'ok'

if __name__ == "__main__":

    #需要监听的codes
    types = {}
    types[1] = 't_ticket_bought'
    types[7] = 't_cashier_trade_record'
    types[16] = 't_mall_bought'
    types[21] = 't_equipment_lease_bought'

    #初始化服务
    serviceInit(types)

    print 'end'







