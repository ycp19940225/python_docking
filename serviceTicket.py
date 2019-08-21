#coding=UTF-8

import config.globalVar as globalVar #系统定义的全局变量
import time
import threading
import string
import json
import urllib,urllib2,httplib
import MySQLdb
import util.helper as helper #工具集
import util.db as db #db操作类

import ticketServices.ServiceYMXY as ServiceYMXY #圆明新园票务系统系统服务(code: YMXY)
import ticketServices.ServiceKZZN as ServiceKZZN #科装智能票务系统系统服务(code: KZZN)
import ticketServices.ServiceKZZN2 as ServiceKZZN2 #科装智能票务系统系统服务(code: KZZN2)
import ticketServices.ServiceZXK as ServiceZXK #衡水旅游助销客票务系统服务(code: ZXK)
import ticketServices.ServiceJYZY as ServiceJYZY #芝樱小镇聚赢智业票务系统服务(code: JYZY)
import ticketServices.ServiceDK as ServiceDK #道控（小径平台）(code: DK)
import ticketServices.ServiceJKB as ServiceJKB #集客宝(code: JKB)

# 调用自定义服务
def runService(clientConfig, ticketBought, code):
    # print clientConfig , code, ticketBought
    eval('Service'+ code +'.Service' + code)(clientConfig, ticketBought)

    pass

# 初始化服务
def serviceInit(codes):

    #连接数据库
    dbObj = db.db()
    # try:
        # dbObj = globalVar.getDbObj() #数据库链接
    # except:
        # dbObj = db.db()
        # globalVar.setDbObj(dbObj)

    ts = [] #线程列表

    #初始化所有code的maxBoughtId为0
    # maxBoughtId = dbObj.getValue("select id from t_ticket_bought order by id desc ", 'id')
    # globalVar.setMaxBoughtId(maxBoughtId)
    globalVar.setMaxBoughtId(320672)
    # print maxBoughtId

    #为了减少数据库查询，初始化时查询出查询商家列表。新添加商家后，需要重启本服务，否则无法监听添加新的。
    # clientList = dbObj.select("select client_id, content, code from t_out_app_config where code in('%s')" % "','".join(codes))

    #启动服务
    i = -1
    while True:
        maxBoughtId = globalVar.getMaxBoughtId()
        print i, maxBoughtId
        helper.getLog("%i -- maxBoughtId:%s" % (i, maxBoughtId), 'serviceTicket.log')
        # 不用每次循环都查询配置
        i += 1
        if i > 100:
            i = 0
        if i % 4 == 0:
            #为了商家修改了门票配置信息时立即生效，改为每次查询
            clientList = dbObj.select("select client_id, content, code from t_out_app_config where code in('%s')" % "','".join(codes))

        #按code给商家列表分组
        clientIds = [] #client id
        clientCodes = {} #
        clientConfigs = {} #client config
        for client in clientList:
            clientCodes[str(client['client_id'])] = client['code']
            clientIds.append(str(client['client_id']))
            clientConfigs[str(client['client_id'])] = json.loads( client['content'] )
        # print clientCodes;exit()

        #查询已购门票列表
        now = helper.now(-3600 * 24 * 1)
        # now = helper.now(-60)
        sql = ' '.join([
                      "select id, client_id,  ticket_id, count, order_id, order_detail_id, price, list_price, identity_info_id, create_time, plan_time, receiving_code ",
                      # "select id, client_id",
                      "from t_ticket_bought ",
                      "where id > '%d' and status = 1 and out_app_code is null and create_time < '%s' and create_time > '%s' and client_id in (%s) " % (globalVar.getMaxBoughtId(), helper.now(-20),  now, ','.join(clientIds) ),
                      # "where order_detail_id = 697201",
                      "order by id asc limit 0, 20", # limit 0, 50
                      ])
        ticketBoughtList = dbObj.select(sql)
        #print  sql;  print ticketBoughtList;
        # exit()

        #把最大的id记录下来
        try:
            maxBoughtId = ticketBoughtList[-1]['id']
            globalVar.setMaxBoughtId(maxBoughtId)
            # print  maxBoughtIds['YMXY']
        except:
            pass

        #按client_id给ticketBoughtList分组
        ticketBoughts = {}
        if len(ticketBoughtList) > 0:
            for ticketBought in ticketBoughtList:
                try:
                    ticketBoughts[ ticketBought['client_id'] ].append(ticketBought)
                except:
                    ticketBoughts[ ticketBought['client_id'] ] = []
                    ticketBoughts[ ticketBought['client_id'] ].append(ticketBought)
            # print ticketBoughts;exit()
            # print clientIds;exit()
            #循环检查每个商家
            for clientId in clientIds:
                # print clientId
                try:
                    code = clientCodes[clientId]
                    t = threading.Thread(target = runService, args=(clientConfigs[clientId], ticketBoughts[ int(clientId) ], code, ))
                    t.start()
                    ts.append(t)
                except:
                    pass

            for t in ts :
                t.join()

        # print globalVar.getMaxBoughtId()
        #每x秒执行一次
        time.sleep( 60 )

if __name__ == "__main__":

    #需要监听的codes
    codes = []
    codes.append('YMXY')
    codes.append('KZZN')
    codes.append('KZZN2')
    codes.append('ZXK')
    codes.append('JYZY')
    codes.append('DK')
    codes.append('JKB')

    #初始化服务
    serviceInit(codes)

    print 'end'







