# from bs4 import BeautifulSoup as bs
import requests
import time
import random
import urllib
import re
import html
import os
import sys
import argparse
import datetime
import json
N = 100
# url = 'https://www1.hkexnews.hk/search/titlesearch.xhtml'
# payloads = {
#     'lang': 'EN',
#     'category': '0',
#     'market': 'SEHK',
#     'searchType': '1',
#     't1code': '40000',
#     't2Gcode': '-2',
#     't2code': '40100',
#     'stockId': '',
#     'from': '20200629',
#     'to': '20200729',
#     'MB-Daterange': '0',
# }

# response = requests.post(url, data=payloads)
# page = bs(response.content, 'html.parser')
# print(page.prettify())
hkex_url = 'https://www1.hkexnews.hk'
endpoint_url = hkex_url + '/search/titleSearchServlet.do'

payloads = {
    'sortDir': '0',
    'sortByOptions': 'DateTime',
    'category': '0',
    'market': 'SEHK',
    'stockId': '-1',
    'documentType': '-1',
    'fromDate': '20200629',
    'toDate': '20200728',
    'title': '',
    'searchType': '1',
    't1code': '40000',
    't2Gcode': '-2',
    't2code': '40100',
    'rowRange': N,
    'lang': 'EN'
}
response = requests.get(endpoint_url, params=payloads)
site_json = json.loads(response.text)

max_result = site_json['recordCnt']
loaded_result = site_json['loadedRecord']

if loaded_result < max_result:
    payloads['rowRange'] = max_result
    response = requests.get(endpoint_url, params=payloads)
    site_json = json.loads(response.text)

results = json.loads(site_json['result'])
for result in results:
    for k, v in result.items():
        print(f'{k} : {html.unescape(v)}')
    print('====================')

print(f'== {len(results)} results are loaded. ==')
