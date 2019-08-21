# coding=UTF-8

import base64
import binascii
import hashlib
import hmac

import pyDes
from pyDes import des, ECB, PAD_PKCS5, CBC

from util import helper

res = 'lKsnT1+5Mw6bDttvuo7EG3vurddkXgh/OP2f0Ju2mqXOlpMxNzadvQ=='




key = '63e76824-2fab-4d38-931f-de5d4237cfeb'
password = ''
payPassword = ''
sIV = "hellocxp"

def UPPER_MD5(value):
    return helper.md5(value).upper()

md5Password = UPPER_MD5(password)

# print 'UPPER_MD5为%s' % md5Password

# 会话秘钥
sha256key = key + md5Password


KEY = hashlib.sha256(sha256key.encode('utf-8'))
KEY = KEY.digest() 

KEY = KEY[0:24]


# KEY = str(KEY2)  # 密钥
IV = sIV  # 偏转向量



desObj = pyDes.triple_des(KEY, ECB, IV, pad=None, padmode=PAD_PKCS5)  # 使用DES对称加密算法的CBC模式加密

str = desObj.encrypt(UPPER_MD5(payPassword))

print base64.b64encode(str)
print res

