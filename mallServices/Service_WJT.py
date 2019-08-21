#coding=UTF-8
#外部系统直接调用我们核销接口(我们需要给验证码更新为二维码)(code:_WJT)
#date 2018-04-25
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

def Service_WJT(config, productConfig, mallBoughtList):
    # print 'debug:';print config;print mallBoughtList;print productConfig;print 'debugEnd.';exit()

    if len(mallBoughtList) < 1:
        return

    # print mallBoughtList;exit()

    #循环检查门票
    ts = [] #同步门票到第三方系统的线程列表
    for mallBought in mallBoughtList:
        # print mallBought['id']
        #同步门票
        try:
            # if conf == 'viewid_' + str(mallBought['mall_id']):
            # 给第三方增加门票
            t = threading.Thread(target = addMallToOuter_WJT, args=(config, productConfig[mallBought['mall_product_id']], mallBought,))
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
def addMallToOuter_WJT(config, productConfig, mallBought):
    # print config;print productConfig;print mallBought;exit()

    dbObj = db.db()
    re = ''
    try:
        productConfig = dbObj.selectOne('select id, out_code from t_mall_product where id = %d' % mallBought['mall_product_id'])
        if productConfig['out_code'] == '_WJT':
            re = '更新out_app_no为receiving_code：' + mallBought['receiving_code']
            sql = "update t_mall_bought set out_app_code = '_WJT', out_app_no = '%s' where id = '%d'" % (mallBought['receiving_code'], mallBought['id'])
            if not True == dbObj.update(sql):
                re += '(更新出错)'
                helper.getLog(sql, 'addMallToService_WJT.UpdateMallboughtlistErr.log')
        else:
            re = '产品没有配置第三方系统代码。不处理。'

    except Exception, e:
        re = str(Exception) + ":" + str(e)

    re =  re.replace("'", '"')
    # print re;exit()
    #保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
        values ('%d', '%d', '%s', '%d', '%s', '%s', '%s') "
    values = (mallBought['client_id'], mallBought['order_id'], mallBought['order_number'], 1, '_WJT', re + "\n", helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addMallToService_WJT.SqlErr.log')


