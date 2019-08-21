#coding=UTF-8
#西软的酒店系统
#date 2017-03-27
#code: XiRuan

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

def ServiceXiRuan(config, productConfig, mallBoughtList):
    # print config;print mallBoughtList;print productConfig;exit()

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
            #查询当前的productid的配置
                # 给第三方增加门票
                t = threading.Thread(target = addMallToOuterXiRuan, args=(config, productConfig[mallBought['mall_product_id']], mallBought,))
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
def addMallToOuterXiRuan(config, productConfig, mallBought):
    # print config;print productConfig;print mallBought;exit()

    # conf = ConfigParser.ConfigParser()
    # conf.read("%s/config/config.ini" % sys.path[0])
    # print "%s/config/config.ini" % sys.path[0]
    url = helper.confGet('host', 'commonService') + 'OuterApp/XiRuan/login/?clientId=' + str( mallBought['client_id'] )
    # print url
    session = json.loads(helper.httpGet(url))

    if not session['status']:
        helper.getLog(session['data'])
        return;
    # print session;exit()

    #查询游客信息
    # userInfo = ''
    # dbObj = globalVar.getDbObj()
    dbObj = db.db()

    userInfo = dbObj.select("select user_id, name, mobile, id_number from t_user_identity_info where id = %d" % mallBought['identity_info_id'])
    if userInfo == False or len(userInfo) < 1:
        visitorName = 'weijingtongVisitor'
        visitorMobile = '18523876001'
    else:
        userInfo = userInfo[0]
        visitorMobile = userInfo['mobile']
        visitorName = userInfo['user_id']
        visitorName = userInfo['name']
        # visitorName = 'visitor'
        visitorName = repr(visitorName.decode('UTF-8'))[2:-1]
        # visitorName = '\u5f20\u8001\u5927'
##        visitorName = urllib.urlencode({1:visitorName})[2:]

    #使用日期
    useDate = mallBought['remark2'].split(',')
    data = '''{
        "sign":"3E365195E5A5CFA2ABC5F5B302182F73",
        "ts":%s,
        "session":"%s",
        "hotelid":"%s",
        "appkey":"%s",
        "loc":"zh_CN",
        "method":"xmsopen.reservation.xopsavereservation",
        "ver":"1.0.0",
        "params":[
            {
                "blockcode":"%s",
                "rmtype":"%s",
                "holdname":"%s",
                "rmnum":"%s",
                "hotelid":"%s",
                "contact_name":"%s",
                "arr":"%s",
                "payamt":"%s",
                "mobile":"%s",
                "ratecode":"%s",
                "sex":"",
                "rate":"%s",
                "contact_mobile":"%s",
                "name":"%s",
                "dep":"%s",
                "gstno":"%s",
                "ref":"weixin",
                "channel":"weixin",
                "restype":"%s"
            }
        ],
        "cmmcode":"%s"
    }''' % ( str(helper.thisTime()).replace('.', ''), session['data'], config['hotelid'], config['appkey'], productConfig['ratecode'], productConfig['rmtype'], visitorName,
             mallBought['buy_count'], productConfig['hotelid'], visitorName, useDate[0], mallBought['total_pay_price'], visitorMobile, productConfig['ratecode'],
             mallBought['price'], visitorMobile, visitorName, useDate[1], mallBought['buy_count'], productConfig['restype'], config['cmmcode']
            );

    # print data
    try:
        re = helper.httpPost(config['host'], data)
        # print re
        #成功同步
        res = json.loads(re)
        # print res
        if res['success'] == True:
            sql = "update t_mall_bought set out_app_code = 'XiRuan', out_app_no = '%s' where id = '%d'" % (res['results'][0]['rsvno'], mallBought['id'])
            if not True == dbObj.update(sql):
                helper.getLog(sql, 'addMallToOuterXiRuan.UpdateMallboughtlistErr.log')
        else:
            sql = "update t_mall_bought set out_app_code = 'XiRuan' where id = '%d'" % mallBought['id']
            if not True == dbObj.update(sql):
                helper.getLog(sql, 'addMallToOuterXiRuan.UpdateMallboughtlistErr.log')

        pass
    except Exception, e:
        re = str(Exception) + ":" + str(e)
        re = "errmsg:%s \npostdata:%s" %(re, data)

    # print re;exit()
    #保存日志到数据库
    sql = "insert into t_order_outapp_msg (client_id, order_id, order_detail_id, type, outapp_code, content, create_time) \
        values ('%d', '%d', '%d', '%d', '%s', '%s', '%s') "
    values = (mallBought['client_id'], mallBought['order_id'], mallBought['order_detail_id'], 1, 'XiRuan', re, helper.now())
    # print sql
    re = dbObj.insert(sql, values)
    # print re
    if not re == True:
        helper.getLog(re, 'addMallToOuterXiRuan.SqlErr.log')


