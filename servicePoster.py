#coding=UTF-8
# /usr/bin/python /datas/www/python/servicePoster.py

import config.globalVar as globalVar #系统定义的全局变量
import os
import time
import threading
import string
import json
import urllib,urllib2,httplib
import MySQLdb
import util.helper as helper #工具集
import util.db as db #db操作类


# 初始化服务
def serviceInit():

    # 连接数据库
    dbObj = db.db()


    # 初始化所有code的maxId为0
    # maxId = dbObj.getValue("select id from aaa order by id desc ", 'id')
    # globalVar.setMaxId(maxId)
    globalVar.setMaxId(0)
    # print maxId


    # 启动服务
    while True:
        ts = [] #线程列表
        maxId = globalVar.getMaxId()
        print maxId
        print helper.now()

        # 查询已购门票列表
        now = helper.now(-3600 * 1)
        # now = helper.now(-60)   from `t_qrcode_temporary_record` where status = 2 and type = 167
        sql = ' '.join([
                      "select * ",
                      # "select id, client_id",
                      "from t_qrcode_temporary_record ",
                      "where id > %d and status = 2 and type = 167 and create_time > '%s'" % (maxId, now),
                      # "where id > '%d' " % maxId,
                      # "where id = 802010",
                      "order by id asc limit 0, 20", # limit 0, 50
                      ])
        recordList = dbObj.select(sql)
        # print  sql;
        # print recordList;exit()

        #查询二维码的scene_id是否属于拉粉宝
        sceneIds = []
        for record in recordList:
            sceneIds.append(str(record['scene_id']))
        if len(sceneIds) > 0:
            sql = "select id, client_id, scene_id from t_poster_get_fans_user where scene_id in (%s)" % ','.join(sceneIds)
            fansUserList = dbObj.select(sql)
            # print  fansUserList;
            sceneIds = {}
            for fans in fansUserList:
                sceneIds[fans['scene_id']] = 1

        #把最大的id记录下来
        try:
            maxId = recordList[-1]['id']
            globalVar.setMaxId(maxId)
            # print  maxIds['YMXY']
        except:
            pass

        for record in recordList:
            # print record
            try:
                #拉粉宝的情况
                if record['scene_id'] in sceneIds:
                    t = threading.Thread(target = processDoGetFans, args=(record, ))
                #普通海报接力
                else:
                    t = threading.Thread(target = processDoPoster, args=(record, ))
                t.start()
                ts.append(t)
            except:
                pass

        # for t in ts :
            # t.join()

        # print globalVar.getMaxId()
        # 每x秒执行一次
        # print ' ==== ' + helper.now()
        time.sleep( 5 )


# 普通海报接力
def processDoPoster(record):
    param = '{"id":"%s","client_id":"%s","user_id":"%s","scene_id":"%s","status":"%s","object_id":"%s"}' % (record['id'], record['client_id'], record['user_id'], record['scene_id'], record['status'], record['object_id'])
    # print param
    # print str(param).replace(' ', '')
    # print urllib.quote(param)
    # re = os.system('php E:\webserver\htdocs\common-service\cli.php  /SystemService/PosterByPython/process/data/%s' % urllib.quote(param))
    re = os.system('nohup /opt/lampp/bin/php /datas/www/php/common-service/cli.php /SystemService/PosterByPython/process/data/%s' % urllib.quote(param) + ' &')
    # re = os.system('/opt/lampp/bin/php /datas/www/php/common-service/cli.php /SystemService/PosterByPython/process/data/%s' % urllib.quote(param) + ' &')
    # print re
    # time.sleep(10)
    print helper.now() + " == "
    pass


# 拉粉宝的情况
def processDoGetFans(record):
    param = '{"id":"%s","client_id":"%s","user_id":"%s","scene_id":"%s","status":"%s","object_id":"%s"}' % (record['id'], record['client_id'], record['user_id'], record['scene_id'], record['status'], record['object_id'])
    # print param
    # print str(param).replace(' ', '')
    # print urllib.quote(param)
    re = os.system('nohup /opt/lampp/bin/php /datas/www/php/common-service/cli.php /SystemService/PosterGetFansByPython/process/data/%s' % urllib.quote(param) + ' &')
    # print re
    # time.sleep(10)
    print helper.now() + " == "
    pass


if __name__ == "__main__":

    #初始化服务
    serviceInit()

    print 'end'







