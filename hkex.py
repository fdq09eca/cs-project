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
import requests
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


def query(from_date, to_date=datetime.date.today().strftime('%Y%m%d')) -> Generator[object, None, None]:
    '''
    **It is a decorator function.**
    It loads the params of getting 500 companies' annual reports per request to hkexnews API.
    It return a generator
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
        'toDate': to_date,
        'title': '',
        'searchType': '1',
        't1code': '40000',
        't2Gcode': '-2',
        't2code': '40100',
        'rowRange': '500',
        'lang': 'EN'
    }

    def Inner(call_api):
        def wrapper(*args, **kwargs):
            return (i for i in call_api(endpoint=endpoint, payloads=payloads, *args, **kwargs))
        return wrapper
    return Inner


def data_decoder(data):
    data = {k.lower(): html.unescape(v) for k, v in data.items()}
    data['file_link'] = "https://www1.hkexnews.hk" + data['file_link']
    return namedtuple('data', data.keys())(*data.values())


@query(from_date='20200629')
# @print_results
def get_data(endpoint: str, payloads: dict) -> list:
    '''
    get data from hkex API.
    '''
    response = requests.get(endpoint, params=payloads)
    site_json = json.loads(response.text)
    if site_json['hasNextRow']:
        payloads['rowRange'] = site_json['recordCnt']
        return get_data(endpoint, payloads)
    results = json.loads(site_json['result'], object_hook=data_decoder)
    return results


def get_pdf(url: str) -> object:
    '''
    get the pdf file from url
    '''
    response = requests.get(url)
    open_pdf_file = io.BytesIO(response.content)
    try:
        pdf = PyPDF2.PdfFileReader(open_pdf_file, strict=False)
        return pdf
    except PyPDF2.utils.PdfReadError:
        logging.warning(f'PdfReadError occur, check {url}')
        return None


def flatten(li: list) -> list:
    '''
    helper: flatten a irregular list recursively;
    for flattening multiple levels of outlines.
    '''
    return sum(map(flatten, li), []) if isinstance(li, list) else [li]


def get_toc(pdf: object) -> dict:
    '''
    get the TOC with page number
    '''
    try:
        outlines = pdf.getOutlines()
        outlines = flatten(outlines)
        if not outlines:
            logging.warning('Outline is unavailable.')
    except AttributeError:
        logging.warning(
            f'Input type: {type(pdf)}. Not PdfReadObject, return None')
        return None

    outlines, next_outlines = itertools.tee(outlines, 2)
    next_outlines = itertools.chain(
        itertools.islice(next_outlines, 1, None), [None])

    toc = {}

    for outline, next_outline in zip(outlines, next_outlines):

        title = outline.title
        if isinstance(title, str):
            title = title.replace('\r', '')
        else:
            title = title.decode('utf-8', errors="ignore").replace('\r', '')

        try:
            from_page = pdf.getDestinationPageNumber(outline)
        except AttributeError:
            from_page = None
        try:
            to_page = pdf.getDestinationPageNumber(
                next_outline) - 1 if next_outline is not None else from_page
        except AttributeError:
            to_page = None

        logging.debug(f'{title.capitalize()}: {from_page} - {to_page}')
        toc[title.capitalize()] = f'{from_page} - {to_page}'

    return toc


def main():
    logging.basicConfig(level=logging.DEBUG, filename=f'log-{os.path.splitext(__file__)[0]}.txt')
    for data in get_data():
        pdf = get_pdf(data.file_link)
        toc = get_toc(pdf)


# main()
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, filename=f'log-{os.path.splitext(__file__)[0]}.txt')
url = '/listedco/listconews/sehk/2020/0730/2020073001154.pdf'
url = 'https://www1.hkexnews.hk' + url

pdf = get_pdf(url)
get_toc(pdf)
