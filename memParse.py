#coding=UTF-8

import os   #Python的标准库中的os模块包含普遍的操作系统功能
import re   #引入正则表达式对象
import urllib   #用于对URL进行编解码
import util.db as db #db操作类
import json
from meliae import loader

if __name__ == "__main__":


    #加载dump文件
    om = loader.load('/logs/python/mem.log')

    #计算各Objects的引用关系
    om.compute_parents()

    #去掉各对象Instance的_dict_属性
    om.collapse_instance_dicts()

    #分析内存占用情况
    print om.summarize()
