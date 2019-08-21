# -*- coding: utf8 -*-
import time
import MySQLdb
import util.helper as helper
import ConfigParser
import sys


class db:

    conn = None #数据库链接资源
    cur = None  #游标
    rowcount = 0 #数据库操作影响的行数
    sql = '' #SQL语句

    def __init__(self):
        self._conn()

    #检查数据库链接
    def _checkConn(self):
        try:
            re = self.conn.ping()
            helper.getLog('check conn mysql: %s -- sql: %s' % (re, self.sql), 'db.%s.log' % helper.now(0, '%Y-%m-%d'))
            print 'check conn mysql: %s -- sql: %s' % (re, self.sql)
        except Exception,e:
            while True:
                print 're connect mysql'
                helper.getLog('re conn mysql -- SQL:%s' % self.sql, 'db.%s.log' % helper.now(0, '%Y-%m-%d'))
                if self._conn():
                    break
                time.sleep(2)

    #链接数据库
    def _conn(self):
        try:
            # 读取数据库配置
            conf = ConfigParser.ConfigParser()
            conf.read("%s/config/config.ini" % sys.path[0])
            # print "%s/config/config.ini" % sys.path[0]

            #链接数据库
            conn = MySQLdb.connect(host = conf.get('db', 'dbHost'), user = conf.get('db', 'dbUser'), passwd = conf.get('db', 'dbPasswd'), db = conf.get('db', 'dbName'),
                                    port = int(conf.get('db', 'dbPort')), charset = conf.get('db', 'dbCharset'))

            conn.autocommit(True)
            cur = conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)

            self.conn = conn
            self.cur = cur
            # print '1t conn mysql'
            return True
        except Exception, e:
            re = str(Exception) + ':' + str(e)
            print 'conn err: %s' % (re)
            helper.getLog('conn err:  -- SQL:%s -- %s' % (self.sql, re), 'db.%s.log' % helper.now(0, '%Y-%m-%d'))
            return False

    #查询数据库
    def select(self, sql):
        self.sql = sql
        print self.sql
        try:
            self._checkConn()

            re = self.cur.execute(sql)
            results = self.cur.fetchall()
            # print results;exit()

            res = []
            for rs in results:
                res.append(rs)

            return res
        except Exception, e:
            re = str(Exception) + ':' + str(e) + ' -- sql:' + sql
            print re
            return None

    #查询数据库某个字段的值
    def selectOne(self, sql):
        res = self.select(sql)
        if not res:
            return None
        return res[0]

    #查询数据库某个字段的值
    def getValue(self, sql, field):
        if sql.find('limit') < 0:
            sql = "%s limit 0, 1" % sql

        re = self.select(sql)
        try:
            value = re[0][field]
        except Exception, e:
            value = None

        return value

    #更新数据
    def update(self, sql, values = ()):
        self.sql = sql % values
        try:
            self._checkConn()

            re = self.cur.execute(sql, values)
            self.rowcount = self.cur.rowcount
            return True
        except Exception, e:
            re = str(Exception) + ':' + str(e) + ' -- sql:' + sql
            # print re
            return re

    #新增数据
    def insert(self, sql, values):
        self.sql = sql % values
        vs = []
        strtype = type('str')
        for v in values:
            if type(v) == strtype:
                vs.append( MySQLdb.escape_string( v ) )
            else:
                vs.append( v )

        # print tuple(values);
        # print tuple(vs);exit()
        sql = sql % tuple(vs)
        try:
            self._checkConn()
            self.cur.execute(sql)
            re = True
        except Exception, e:
            re = str(Exception) + ':' + str(e) + ' -- sql:' + sql
            # print re
        return re

