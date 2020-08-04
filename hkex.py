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
from functools import wraps


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
            f'Can only query from {datetime.datetime.strftime(yearsago(1), "%Y%m%d")}')

    def Inner(call_api):
        def wrapper(*args, **kwargs):
            return (i for i in call_api(endpoint=endpoint, payloads=payloads))
        return wrapper
    return Inner


def data_decoder(data):
    data = {k.lower(): html.unescape(v) for k, v in data.items()}
    data['file_link'] = "https://www1.hkexnews.hk" + data['file_link']
    return namedtuple('data', data.keys())(*data.values())


@query(from_date='20190804')
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
    try:
        response = requests.get(url)
        open_pdf_file = io.BytesIO(response.content)
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
    outlines = pdf.getOutlines()
    outlines = flatten(outlines)
    if not outlines:
        logging.warning('Outline is unavailable.')

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


def get_pages_by_outline(toc: dict, title_pattern: str) -> tuple:
    '''
    search outline title pattern, return the respective outline page range in list.
    '''
    pageRange = []
    for outline, page_range in toc.items():
        if re.search(title_pattern, outline, flags=re.IGNORECASE):
            pageRange.append(page_range.split(' - '))
    if len(pageRange) != 1:
        logging.debug(f'{len(pageRange)} pair of page range is found.')
        return None
    from_page, to_page = pageRange[0]
    return from_page, to_page


def get_pages_by_page_search(pdf, keywords_pattern):
    '''
    search page by keywords pattern, return the respective page range in list.
    '''
    pageRange = []
    pages = pdf.getNumPages()
    for p in range(pages):
        page = pdf.getPage(p)
        page_txt = re.sub('\n+', '', page.extractText())
        if re.search(keywords_pattern, page_txt, flags=re.IGNORECASE):
            pageRange.append(p)
    logging.info(f'{keywords_pattern} found in pages {pageRange}')
    if pageRange:
        from_page = min(pageRange) if min(pageRange) != 1 else min(pageRange.remove(1))
        to_page = max(pageRange)
        return from_page, to_page
    return None, None


def main():
    logging.basicConfig(level=logging.DEBUG,
                        filename=f'log-{os.path.splitext(__file__)[0]}.txt')
    for data in get_data():
        pdf = get_pdf(data.file_link)
        if not pdf:
            continue
        toc = get_toc(pdf)
        title_pattern = r"independent auditor['s]?( report)?"
        if get_pages_by_outline(toc, title_pattern):
            from_page, to_page = get_pages_by_outline(toc, title_pattern)
        else:
            print('search by page!')
            from_page, to_page = get_pages_by_page_search(pdf, title_pattern)
        print(f"from_page: {from_page}, to_page: {to_page}")
        # some pdf are scanned image which can't be searched by text..

        # get auditor
        # if outlines available
        # locate independent auditor report last page by toc
        # else:
        # search keywords by page
        # get the max from page range
        # search auditor name pattern from the max page for n time.
        # get auditor name by the last element


main()
