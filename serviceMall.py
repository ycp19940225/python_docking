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

import mallServices.Service_WJT as MallService_WJT #外部系统直接调用我们核销接口(我们需要给验证码更新为二维码)(code:_WJT)
import mallServices.ServiceXiRuan as MallServiceXiRuan # 安缇缦商城酒店(code: XiRuan)
import mallServices.ServiceKZZN2 as MallServiceKZZN2 # 科装智能票务系统2版本系统服务(code: KZZN2)
import mallServices.ServiceDK as MallServiceDK # 道控（小径平台）(code: DK)


# 调用自定义服务
def runService(clientConfig, mallProductConfig, mallBoughts, code, configType):
    # for mallBought in mallBoughts:
       # if mallBought['client_id'] == 1257:
    # print clientConfig , code, mallBoughts,'==============================='

    #python
    if configType == 2:
        eval('Service'+ code +'.MallService' + code)(clientConfig, mallProductConfig, mallBoughts)
    #java
    elif configType == 1:
        for mallBought in mallBoughts:
            requestData = {
                'type': 'mall',
                'key': '3e3bcd9d71d52132a9b413a57be173ca',
                'orderId': str(mallBought['order_id'])
            }
            # print urllib.urlencode(requestData);
            url = helper.confGet('host', 'nwxService') + 'api/order'
            reChar = helper.httpPost(url, requestData)
            res = json.loads(reChar)
            if res['isok']:
                #返回的验证码，如果下单失败，则为空
                if not res['codes']:
                    # print requestData
                    helper.getLog('重新下单失败 -- ' + url + ' -- ' + reChar + ' -- ' + urllib.urlencode(requestData))
                else:
                    helper.getLog('重新下单成功 -- ' + url + ' -- ' + reChar + ' -- ' + urllib.urlencode(requestData))
            else:
                helper.getLog('重新下单失败 -- ' + url + ' -- ' + reChar + ' -- ' + urllib.urlencode(requestData))
    elif configType == 3:
        eval('Service'+ code +'.MallService' + code)(clientConfig, mallProductConfig, mallBoughts)

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
    # maxBoughtId = dbObj.getValue("select id from t_mall_bought order by id desc ", 'id')
    # globalVar.setMaxBoughtId(maxBoughtId)
    globalVar.setMaxBoughtId('0')
    globalVar.setMaxBoughtId('6159')
##    print maxBoughtId

    #为了减少数据库查询，初始化时查询出查询商家列表。新添加商家后，需要重启本服务，否则无法监听添加新的。
    # clientList = dbObj.select("select client_id, content, code from t_out_app_config where code in('%s')" % "','".join(codes))

    #启动服务
    i = -1
    while True:
        print i,globalVar.getMaxBoughtId(),'========'
        # 不用每次循环都查询配置
        i += 1
        if i > 100:
            i = 0
        if i % 4 == 0:
            #为了商家修改了配置信息时立即生效，改为每次查询
            clientList = dbObj.select("select client_id, content, code, type from t_mall_out_config where code in('%s')" % "','".join(codes))
            clientList2 = dbObj.select("select client_id, content, code, type from t_out_app_config")

        #按code给商家列表分组
        clientIds = [] #client id
        clientCodes = {} #
        clientConfigTypes = {} #
        clientConfigs = {} #client config
        #分别合并商城和门票的outconfig，商城优先，可覆盖门票
        for client in clientList2:
            clientCodes[str(client['client_id'])] = client['code']
            clientConfigTypes[str(client['client_id'])] = client['type']
            clientIds.append(str(client['client_id']))
            if client['content'] and (client['type'] == 1 or client['type'] == 2):
                # print client
                clientConfigs[str(client['client_id'])] = json.loads( client['content'] )
        for client in clientList:
            clientCodes[str(client['client_id'])] = client['code']
            clientConfigTypes[str(client['client_id'])] = client['type']
            clientIds.append(str(client['client_id']))
            if client['content'] and (client['type'] == 1 or client['type'] == 2):
                clientConfigs[str(client['client_id'])] = json.loads( client['content'] )[client['code']]
        # print clientCodes; print clientConfigTypes;  exit()

        #查询product的配置
        sql = ' '.join([
            'select id, client_id, out_code, out_config',
            'from t_mall_product',
            "where is_out_app = 1 and out_code in( '%s')" % ( "','".join(codes) )
        ])
        mallProductList = dbObj.select(sql)
        mallProductConfigs = {} #产品的配置信息
        for mallProduct in mallProductList:
            if mallProduct['out_code'] == clientCodes[str(mallProduct['client_id'])]:
                try:
                    mallProductConfigs[ mallProduct['client_id'] ][mallProduct['id']] = json.loads(mallProduct['out_config'])
                except:
                    mallProductConfigs[ mallProduct['client_id'] ] = {}
                    mallProductConfigs[ mallProduct['client_id'] ][mallProduct['id']] = json.loads(mallProduct['out_config'])

        # print  mallProductConfigs;exit()

        #查询已购列表
        now = helper.now(-3600 * 24 * 160)
        # now = helper.now(-60)
        sql = ' '.join([
            "select id, client_id,  mall_product_id, buy_count, order_id, order_detail_id, price, total_pay_price, identity_info_id, create_time, plan_time, remark, remark2, receiving_code ",
            # "select id, client_id",
            "from t_mall_bought ",
            "where id > '%s' and status = 2 and out_app_code is null and create_time > '%s' and client_id in (%s) " % ( globalVar.getMaxBoughtId(), now, ','.join(clientIds) ),
            # "where id = 6778",
            "order by id asc limit 0, 100", # limit 0, 50
        ])
        mallBoughtList = dbObj.select(sql)
        # print  sql;
        # print mallBoughtList;
        # exit()

        #把最大的id记录下来
        try:
            maxBoughtId = mallBoughtList[-1]['id']
            globalVar.setMaxBoughtId(maxBoughtId)
            # print  maxBoughtIds['YMXY']
        except:
            pass

        #按client_id给mallBoughtList分组
        mallBoughts = {}
        if len(mallBoughtList) > 0:
            for mallBought in mallBoughtList:
                try:
                    mallBoughts[ mallBought['client_id'] ].append(mallBought)
                except:
                    mallBoughts[ mallBought['client_id'] ] = []
                    mallBoughts[ mallBought['client_id'] ].append(mallBought)

        # print mallBoughts;exit()
        # print clientIds;exit()
        # print clientConfigs;exit()

        clientIds = ['1257']
        #循环检查每个商家
        for clientId in clientIds:
            # try:
            code = clientCodes[clientId]
            try:
                mallProductConfig = mallProductConfigs[ int(clientId) ]
            except:
                mallProductConfig = {}
            try:
                mallBoughtList = mallBoughts[ int(clientId) ]
            except:
                mallBoughtList = None
            # print code
            # print clientId
            # print mallBoughtList
            # print mallProductConfig
            # print clientConfigTypes
            if mallBoughtList:
                t = threading.Thread(target = runService, args=(clientConfigs[clientId], mallProductConfig, mallBoughtList, code, clientConfigTypes[clientId], ))
                t.start()
                ts.append(t)
            # except:
                # pass

        for t in ts :
            t.join()

        # print globalVar.getMaxBoughtId()
        #每x秒执行一次
        time.sleep( 30 )

if __name__ == "__main__":

    #需要监听的codes
    codes = []
    codes.append('XiRuan')
    codes.append('_WJT')

    #初始化服务
    serviceInit(codes)

    print 'end'







