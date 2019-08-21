#coding=UTF-8

import os   #Python的标准库中的os模块包含普遍的操作系统功能
import re   #引入正则表达式对象
import urllib   #用于对URL进行编解码
import util.db as db #db操作类
import json
import time
import platform
import urllib
from urlparse import urlparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler  #导入HTTP处理相关的模块

import util.helper as helper
import ticketServices.ServiceZXK as TicketServiceZXK  # 衡水旅游助销客票务系统服务(code: ZXK)
import ticketServices.ServiceYMXY as TicketServiceYMXY  # 圆明新园票务系统系统服务(code: YMXY)
import ticketServices.ServiceKZZN as TicketServiceKZZN  # 科装智能票务系统系统服务(code: KZZN)
import ticketServices.ServiceKZZN2 as TicketServiceKZZN2  # 科装智能票务系统2版本系统服务(code: KZZN2)
import ticketServices.ServiceJYZY as TicketServiceJYZY  # 芝樱小镇聚赢智业票务系统服务(code: JYZY)
import ticketServices.Service_WJT as TicketService_WJT  #
import ticketServices.ServiceDK as TicketServiceDK  # 道控（小径平台）(code: DK)
import ticketServices.ServiceJKB as TicketServiceJKB  # 集客宝(code: JKB)
import ticketServices.ServiceYBX as TicketServiceYBX  # 游宝星(code: YXB)
import ticketServices.ServiceHQ2 as TicketServiceHQ2  # 环企票务(code: HQ2)

import mallServices.Service_WJT as MallService_WJT #外部系统直接调用我们核销接口(我们需要给验证码更新为二维码)(code:_WJT)
import mallServices.ServiceXiRuan as MallServiceXiRuan # 安缇缦商城酒店(code: XiRuan)
import mallServices.ServiceKZZN2 as MallServiceKZZN2 # 科装智能票务系统2版本系统服务(code: KZZN2)
import mallServices.ServiceDK as MallServiceDK  # 道控（小径平台）(code: DK)
import mallServices.ServiceYBX as MallServiceYBX  # 游宝星（酉阳桃花源）(code: YXB)

class Sys():
    def __init__(self, GET):
        self.GET = GET

    def exc_command(self):
        GET = self.GET
        command = urllib.unquote(GET['command'])
        output = os.popen(command)
        outinfo = output.read()
        print outinfo
        print command
        return {'msg': outinfo, 'data': 'command:' + command, 'code': 0}

class Api():
    def __init__(self, GET):
        self.GET = GET

    def re_order(self):
        GET = self.GET
        dbObj = db.db()

        # 门票
        # http://127.0.0.1:8099/api/re_order?clientId=41&type=ticket&orderId=587580
        # @params clientId int GET 必须 景区id
        # @params type string GET 必须 ticket（门票）
        # @params orderDetailIds string GET 非必须 定单详情ID
        # @params orderId string GET 非必须 定单ID
        if GET['type'] == 'ticket':
            # 查询该景区所有对接的闸机信息
            configListInfo = dbObj.select("select client_id, content, code, type from t_out_app_config where client_id = '%s' order by type" % GET['clientId'])

            try:
                where = "where order_detail_id in ( %s )" % GET['orderDetailIds']
            except:
                where = "where order_id = '%s'" % GET['orderId']

            try:
                sql = ' '.join([
                          "select id, client_id, user_id, ticket_id, count, order_id, order_detail_id, list_price, price, identity_info_id, create_time, plan_time, receiving_code, start_time ",
                          # "select id, client_id",
                          "from t_ticket_bought ",
                           where,
                          "order by id asc", # limit 0, 50
                          ])
                ticketBoughtListAll = dbObj.select(sql)

                orderInfo = dbObj.selectOne("select id, count from t_order where id = '%s'" % GET['orderId'])
                # 若是bought 数量和订单购买数量不同（拆分订单的情况），第一个bought 的购买数量和订单购买数量也不同（不拆分订单的情况）
                if len(ticketBoughtListAll) == 0 or (len(ticketBoughtListAll) != orderInfo['count'] and ticketBoughtListAll[0]['count'] != orderInfo['count']):
                    time.sleep(1)
                    helper.getLog('-----------'+str(GET['orderId'])+',re select', 'service.webservice.log')
                    ticketBoughtListAll = dbObj.select(sql)

                helper.getLog('-----------start: orderId: '+str(GET['orderId'])+', boughtCount: '+str(len(ticketBoughtListAll))+'-------------', 'service.webservice.log')
            except Exception, e:
                re = str(Exception) + ':' + str(e)
                helper.getLog('系统错误: %s' % re, 'service.webservice.log')
                return {'code': -1, 'msg': '系统错误:%s' % re}

            # 需要删除的bought索引id，存放是对接外部闸机的bought 索引id
            popIndexs = []

            for configInfo in configListInfo:
                outCode = configInfo['code'] # code
                outCodeType = str(configInfo['type']) # code

                try:
                    config = json.loads(configInfo['content']) #配置
                except:
                    config = {}

                ticketBoughtList = []
                # _wjt 有可能配置 ticket_ids
                if len(config) == 0 or config.has_key('ticket_ids'):
                    helper.getLog('if---outCodeType: '+outCodeType+' - popIndexs: '+','.join([str(x) for x in popIndexs]), 'service.webservice.log')
                    # outCodeType 为3 的情况，type 为 3 是最后执行
                    for k ,ticketBought in enumerate(ticketBoughtListAll):
                        if k not in popIndexs:
                            ticketBoughtList.append(ticketBought)
                else:
                    # 获取配置的本站门票id
                    ticketIds = helper.getTicketIds(config)
                    helper.getLog('else---outCode: '+outCode+' - ticketIds:'+','.join([str(x) for x in ticketIds]), 'service.webservice.log')
                    for k ,ticketBought in enumerate(ticketBoughtListAll):
                        # 若bought的门票id 存在
                        if ticketBought['ticket_id'] in ticketIds:
                            ticketBoughtList.append(ticketBought)
                            #outCodeType 为3 的情况，记录索引id，剩下的就是对接我们自己的系统
                            popIndexs.append(k)

                helper.getLog('outCode: '+outCode+' - outCodeType: '+outCodeType+' - popIndexs: '+','.join([str(x) for x in popIndexs]), 'service.webservice.log')
                # print sql
                # print ticketBoughtList
                #return {'s': 'ok'}
                # 循环判断闸机
                if outCode == 'ZXK':
                    TicketServiceZXK.ServiceZXK(config, ticketBoughtList)
                elif outCode == 'YMXM':
                    TicketServiceYMXY.ServiceYMXY(config, ticketBoughtList)
                elif outCode == 'KZZN':
                    TicketServiceKZZN.ServiceKZZN(config, ticketBoughtList)
                elif outCode == 'KZZN2':
                    TicketServiceKZZN2.ServiceKZZN2(config, ticketBoughtList)
                elif outCode == 'JYZY':
                    TicketServiceJYZY.ServiceJYZY(config, ticketBoughtList)
                elif outCode == 'DK':
                    TicketServiceDK.ServiceDK(config, ticketBoughtList)
                elif outCode == 'JKB':
                    TicketServiceJKB.ServiceJKB(config, ticketBoughtList)
                elif outCode == 'YBX':
                    TicketServiceYBX.ServiceYBX(config, ticketBoughtList)
                elif outCode == 'HQ2':
                    TicketServiceHQ2.ServiceHQ2(config, ticketBoughtList)
                elif outCodeType == '3':
                    helper.getLog("exe WJT - boughtCount -"+str(len(ticketBoughtList)), 'service.webservice.log')
                    TicketService_WJT.Service_WJT(config, ticketBoughtList, GET['orderId'])
                else:
                    continue
                    #return {'code': 9999, 'msg': '没有对接闸机'}
        # 商城
        # http://127.0.0.1:8099/api/re_order?clientId=41&type=mall&orderDetailIds=790440
        # http://127.0.0.1:8099/api/re_order?clientId=41&type=mall&orderId=670108
        # @params clientId int GET 必须 景区id
        # @params type string GET 必须 mall（商城）
        # @params orderDetailIds string GET 非必须 定单详情ID
        # @params orderId string GET 非必须 定单ID
        else:
            configListInfo = dbObj.select("select client_id, content, code from t_mall_out_config where client_id = '%s' and status = 1" % GET['clientId'])
            if not configListInfo:
                configListInfo = dbObj.select("select client_id, content, code, type from t_out_app_config where client_id = '%s'" % GET['clientId'])

            try:
                where = "where order_detail_id in ( %s )" % GET['orderDetailIds']
            except:
                where = "where order_id = '%s'" % GET['orderId']

            try:
                sql1 = sql = ' '.join([
                    "select id, client_id, user_id, mall_product_id, buy_count, order_id, order_detail_id, list_price, price, total_pay_price, identity_info_id, order_number, create_time, plan_time, remark, remark2, receiving_code, start_time",
                    # "select id, client_id",
                    "from t_mall_bought ",
                     where
                ])
                mallBoughtListAll = dbObj.select(sql)
            except Exception, e:
                re = str(Exception) + ':' + str(e)
                helper.getLog('系统错误: %s' % re, 'service.webservice.log')
                return {'code': -1, 'msg': '系统错误:%s' % re}

            for configInfo in configListInfo:
                outCode = configInfo['code'] # code
                try:
                    config = json.loads(configInfo['content']) #配置
                except:
                    config = {}
                if len(config) == 0 :
                    continue;

                productConfig = {}
                if outCode == 'XiRuan' or outCode == '_WJT':
                    mallBoughtList = mallBoughtListAll
                    sql = ' '.join([
                        'select out_config',
                        'from t_mall_product',
                        "where id = '%s'" % mallBoughtList[0]['mall_product_id']
                    ])

                    try:
                        productConfig = {
                            mallBoughtList[0]['mall_product_id']: json.loads(dbObj.getValue(sql, 'out_config'))
                        }
                    except:
                        pass

                else:
                    # 获取配置的本站商城门票id
                    productIds = helper.getTicketIds(config,'mall')

                    mallBoughtList = []
                    for mallBought in mallBoughtListAll:
                        # 若bought的门票id 存在
                        if mallBought['mall_product_id'] in productIds:
                            mallBoughtList.append(mallBought)


                #outCode:_WJT -- mallBoughtList:[{'remark': u'', 'identity_info_id': 453421L, 'user_id': u'ogs93t-7DXyYiWjnAs_FhOpNW1I0', 'order_id': 1320739L, 'price': Decimal('0.010'), 'buy_count': 1L, 'mall_product_id': 2786L, 'total_pay_price': Decimal('0.000'), 'order_detail_id': 1510248L, 'create_time': datetime.datetime(2019, 4, 12, 12, 47, 4), 'client_id': 41L, 'remark2': u'1', 'receiving_code': u'0874891', 'list_price': Decimal('0.010'), 'order_number': u'1904121247046341', 'id': 16116L, 'plan_time': datetime.datetime(2019, 4, 12, 0, 0)}]
                helper.getLog('outCode:' + str(outCode) + ' -- mallBoughtList:' + str(mallBoughtList) + ' -- config:' + str(config) , 'service.webservice.log')
                helper.getLog('outCode:' + outCode , 'service.webservice.log')
                if outCode == 'XiRuan':
                    MallServiceXiRuan.ServiceXiRuan(config[outCode], productConfig, mallBoughtList)
                elif outCode == 'KZZN2':
                    MallServiceKZZN2.ServiceKZZN2(config, mallBoughtList)
                elif outCode == 'DK':
                    # print [sql, outCode, config, productConfig]
                    # print  mallBoughtList
                    MallServiceDK.ServiceDK(config, mallBoughtList)
                elif outCode == '_WJT':
                    MallService_WJT.Service_WJT(config, productConfig, mallBoughtList)
                    # print [sql1, outCode, config, mallBoughtList, productConfig]
                elif outCode == 'YBX':
                    MallServiceYBX.ServiceYBX(config, mallBoughtList)
                else:
                    #return {'code': 9999, 'msg': '没有对接闸机'}
                    url = helper.confGet('host', 'commonService') + 'Order/Index/reOrderOutApp/clientId/' + GET['clientId'] + '/orderId/' + str(mallBoughtList[0]['order_id']) + '/orderDetailId/0/type/mall/isRemote/1/outType/1';
                    re = helper.httpGet(url)
                    helper.getLog('url:' + url + ' -- re:' + re, 'service.webservice.log')
                    continue
        # return {'code': 0, 'msg': }
        return {'code': 0, 'msg': '提交成功'}

#自定义处理程序，用于处理HTTP请求
class httpHandler(BaseHTTPRequestHandler):
    def _init(self, url):
        self.res = None
        urls = urlparse(url)
        # print urls # ParseResult(scheme='', netloc='', path='/api/re_order', params='', query='type=ticket&orderDetailIds=1,2,3', fragment='')
        # url路径
        helper.getLog('url:' + url , 'service.webservice.log')

        self.paths = urls.path.split('/')
        # GET
        self.GET = {}

        gets = urls.query.split('&')
        for g in gets:
            gs = g.split('=')
            if len(gs) > 1:
                self.GET[ gs[0] ] = gs[1]


    #处理POST请求
    def do_POST(self):
        pass

    #处理GET请求
    def do_GET(self):
        self._init(self.path)
        http_code = 200

        paths = self.paths
        print paths
        if paths[1] == 'sys':
            sys = Sys(self.GET)
            if paths[2] == 'exc_command':
                self.res = sys.exc_command()

        elif paths[1] == 'api':
            api = Api(self.GET)

            if paths[2] == 're_order':
                self.res = api.re_order()
            elif paths[2] == 'order':
                self.res = api.re_order()
        else:
            http_code = 404
            self.res = '404'
        # print self.res

        self.protocal_version = 'HTTP/1.1'  #设置协议版本
        self.send_response(http_code) #设置响应状态码
        self.send_header("Server", "wjt-server/python/1.0")  #设置响应头
        self.send_header("Content-Type", "application/json; charset=utf-8")  #设置响应头
        self.end_headers()
        self.wfile.write( json.dumps(self.res) )   #输出响应内容

#启动服务函数
def start_server(ip, port):
    # n = 1
    # n += 1
    # print n
    # exit;
    print 'server start ...'
    http_server = HTTPServer((ip, int(port)), httpHandler)
    http_server.serve_forever() #设置一直监听并接收请求

#改变工作目录到 static 目录
sysInfo = platform.system()
if( sysInfo == "Windows" ):
    # os.chdir('E:\webserver\htdocs\python\static')
    os.chdir('D:/phpStudy/PHPTutorial/WWW/python/static')
    #os.chdir('H:/python/static')
    # os.chdir('E:/Ida/webserver/htdocs/python')
else:
    os.chdir('/datas/www/python/static')
start_server('127.0.0.1', 8099)  #启动服务，监听 8099 端口
# start_server('127.0.0.1', 18098)  #启动服务，监听 18098 端口  test

