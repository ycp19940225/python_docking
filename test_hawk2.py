import time

import requests
from mohawk import Sender, Receiver

from util import helper

url = "http://121.41.6.55:8601/api/OrderAndPay/WithPrepayment"

payload = "{\r\n  \"orderinfo\": {\r\n    \"orderdetails\": [\r\n      {\r\n        \"productid\": \"sample string 1\",\r\n        \"amount\": 2,\r\n        \"identificationnumber\": \"sample string 3\",\r\n        \"fullname\": \"sample string 4\",\r\n        \"identificationtype\": \"sample string 5\",\r\n        \"mobile\": \"sample string 6\",\r\n        \"gateinmode\": \"sample string 7\",\r\n        \"seatitems\": [\r\n          {\r\n            \"seatid\": \"sample string 1\"\r\n          },\r\n          {\r\n            \"seatid\": \"sample string 1\"\r\n          }\r\n        ]\r\n      },\r\n      {\r\n        \"productid\": \"sample string 1\",\r\n        \"amount\": 2,\r\n        \"identificationnumber\": \"sample string 3\",\r\n        \"fullname\": \"sample string 4\",\r\n        \"identificationtype\": \"sample string 5\",\r\n        \"mobile\": \"sample string 6\",\r\n        \"gateinmode\": \"sample string 7\",\r\n        \"seatitems\": [\r\n          {\r\n            \"seatid\": \"sample string 1\"\r\n          },\r\n          {\r\n            \"seatid\": \"sample string 1\"\r\n          }\r\n        ]\r\n      }\r\n    ],\r\n    \"mobile\": \"sample string 1\",\r\n    \"otheruserid\": 2,\r\n    \"identificationnumber\": \"sample string 3\",\r\n    \"effectdate\": \"sample string 4\",\r\n    \"needinvoice\": \"sample string 5\",\r\n    \"invoicetitle\": \"sample string 6\",\r\n    \"invoicecode\": \"sample string 7\",\r\n    \"senderid\": \"sample string 8\",\r\n    \"servicecode\": \"sample string 9\",\r\n    \"timespanindex\": 10,\r\n    \"tripbillcode\": \"sample string 11\",\r\n    \"guidernumber\": \"sample string 12\",\r\n    \"marketareaid\": \"sample string 13\"\r\n  },\r\n  \"payinfo\": {\r\n    \"orderid\": \"sample string 1\",\r\n    \"paypassword\": \"sample string 2\"\r\n  }\r\n}"

hawkId = 'ybxkj'
key = '2b4747b3-788b-46ba-9ca4-c5d112a7c066'
hawkAuthKey = key + helper.md5('123456').upper()
ts = str(time.time())[0:10]
method = 'POST'
content_type = 'application/json'

credential = {}
credential['user'] = hawkId
credential['algorithm'] = 'sha256'
credential['authKey'] = hawkAuthKey

sender = Sender({'id': credential['user'],
              'key': credential['authKey'],
              'algorithm': credential['algorithm']},
               url,
               method,
               content_type=content_type,
              always_hash_content=False
            )

res = requests.post(url, data=payload, headers={'Authorization': sender.request_header})

print res
