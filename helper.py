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
from io import BytesIO
import pdfplumber
import requests
from typing import Union

def page_cn_ratio(src:Union[str, object], page_num: int) -> float:
    '''
    take url, local path, byte object as src
    return cn to txt ratio of a pdf page.
    typically full cn page is over cn_to_txt_ratio is >85%
    '''
    import get_pdf
    pdf = get_pdf.by_pdfplumber(src)
    page = pdf.pages[page_num]
    txt = page.extract_text()
    cn_txt = re.sub("([\x00-\x7F])+", "", txt)
    cn_to_txt_ratio = len(cn_txt)/len(txt)
    return cn_to_txt_ratio

def is_landscape(src:Union[str, object], page_num):
    '''
    check a pypdf2 page object is landscape
    '''
    from get_pdf import byte_obj_from_url, by_pypdf
    pdf = by_pypdf(src)
    page = pdf.getPage(page_num).mediaBox
    page_width = page.getUpperRight_x() - page.getUpperLeft_x()
    page_height = page.getUpperRight_y() - page.getLowerRight_y()
    return page_width > page_height

def is_url(url:str) -> bool:
    if not isinstance(url, str):
        raise TypeError(f'Input type {type(url)} is not str.')
    url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(url_regex, url)

def get_pdf(path: str) -> object:
    '''
    get the pdf file from path
    '''
    try:
        response = requests.get(path)
        open_pdf_file = io.BytesIO(response.content)
        pdf = PyPDF2.PdfFileReader(open_pdf_file, strict=False)
    except PyPDF2.utils.PdfReadError:
        logging.warning(f'PdfReadError occur, check {url}')
        return None
    finally:
        return pdf

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


def new_get_auditor(url, page):
    '''
    get audit firm name by searching the regex pattern on a page
    '''
    rq = requests.get(url)
    if rq.status_code == 200:
        # logging.info('request success. start extracting text...')
        print('request success, loading pdf...')
    try:
        pdf = pdfplumber.load(BytesIO(rq.content))
        txt = pdf.pages[page].extract_text()
    except:
        logging.warning(f'Not pdf file. check {url}.')
        return None
    txt = re.sub("([^\x00-\x7F])+", "", txt)  # diu no chinese
    pattern = r'\n(?!.*?Institute.*?).*?(?P<auditor>.+?)(?:LLP\s*)?\s*((PRC.*?|Chinese.*?)?[Cc]ertified [Pp]ublic|[Cc]hartered) [Aa]ccountants'
    auditor = re.search(pattern, txt, flags=re.MULTILINE).group('auditor').strip()
    return auditor
