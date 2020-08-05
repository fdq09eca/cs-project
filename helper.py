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
from collections import namedtuple
from typing import Generator
import PyPDF2
import io
import itertools
import logging


def print_results(results):
    '''
    **It is a decorator function**
    it prints out the results for API response
    '''
    def wrapper(*args, **kwargs):
        _results = results(*args, **kwargs)
        counter = 0
        for result in _results:
            counter += 1
            for k, v in dict(result._asdict()).items():
                print(f'{k} : {v}')
            print('====================')
        print(f'== {counter} results are loaded. ==')

        return _results
    return wrapper


def yearsago(years, from_date=datetime.datetime.now()):
    try:
        return from_date.replace(year=from_date.year - years)
    except ValueError:
        # Must be 2/29!
        assert from_date.month == 2 and from_date.day == 29  # can be removed
        return from_date.replace(month=2, day=28, year=from_date.year-years)


def query(from_date, to_date=datetime.date.today()) -> Generator[object, None, None]:
    '''
    **decorator function.**
    It loads the params of getting 500 companies' annual reports per request to hkexnews API.
    It returns a generator
    '''
    hkex_url = 'https://www1.hkexnews.hk'
    endpoint = hkex_url + '/search/titleSearchServlet.do'

    payloads = {
        'sortDir': '0',
        'sortByOptions': 'DateTime',
        'category': '0',
        'market': 'SEHK',
        'stockId': '-1',
        'documentType': '-1',
        'fromDate': from_date,
        'toDate': to_date.strftime('%Y%m%d'),
        'title': '',
        'searchType': '1',
        't1code': '40000',
        't2Gcode': '-2',
        't2code': '40100',
        'rowRange': '100',
        'lang': 'EN'
    }
    over_a_year = datetime.datetime.strptime(from_date, '%Y%m%d') < datetime.datetime.strptime(
        yearsago(1, to_date).strftime("%Y%m%d"), '%Y%m%d')
    if over_a_year:
        raise ValueError(
            f'Date range over a year. can only query from {datetime.datetime.strftime(yearsago(1), "%Y%m%d")}')

    def Inner(call_api):
        def wrapper(*args, **kwargs):
            return (i for i in call_api(endpoint=endpoint, payloads=payloads))
        return wrapper
    return Inner


def data_decoder(data):
    data = {k.lower(): html.unescape(v) for k, v in data.items()}
    data['file_link'] = "https://www1.hkexnews.hk" + data['file_link']
    return namedtuple('data', data.keys())(*data.values())


def flatten(li: list) -> list:
    '''
    helper: flatten a irregular list recursively;
    for flattening multiple levels of outlines.
    '''
    return sum(map(flatten, li), []) if isinstance(li, list) else [li]


def get_pageRange(pageRange, from_to):
    '''
    get the min and max page in a list
    ignore page 1, 2 or 3 because they are likely table of content
    '''
    if from_to == 'from':
        try:
            if min(pageRange) in range(3):
                return get_pageRange(pageRange[1:], from_to)
        except ValueError:
            return None
        return min(pageRange)
    elif from_to == 'to':
        try:
            if max(pageRange) in range(3):
                return get_pageRange(pageRange[:-1], from_to)
        except ValueError:
            return None
        return max(pageRange)


def get_auditor(indpt_audit_report, p):
    '''
    get audit firm name by searching the regex pattern on a page
    '''
    page = indpt_audit_report.getPage(p)
    text = page.extractText()
    text = re.sub('\n+', '', text)
    pattern = r'.*\.\s*?((?P<auditor>[A-Z].*?):?( LLP)?)\s?(Certi.*?)?\s?Public Accountants'
    # pattern = r'(:?.*\.[\s\n]?(?P<auditor>.*))[\s\n]?(?:Certified )?Public Accountants'
    auditor = re.search(pattern, text).group('auditor')
    return auditor


def write_to_csv(data: dict, csvname='result.csv'):
    import csv
    import os
    if not os.path.exists(f'./{csvname}'):
        with open(csvname, 'a') as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            writer.writeheader()
            writer.writerow(data)
    else:
        with open(csvname, 'a') as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            writer.writerow(data)
    # print('result wrote to ./{csvname}')
