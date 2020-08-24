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
import itertools
import logging
from io import BytesIO
import pdfplumber
import requests
from typing import Union
import pandas as pd

# def valid_auditor(csv):
#     yield pd.read_csv(csv).to_list()


def df_to_csv(df, csv_name='result.csv'):
    '''
    pandas row to csv 
    '''
    if not os.path.exists(f'{csv_name}'):
        df.to_csv(csv_name, mode='a', index=False, header=True)
    else:
        df.to_csv(csv_name, mode='a', index=False, header=False)


def turn_n_page(pdf: object, page: object, n: int):
    '''
    take pdf_plumber pdf and page object and (+/-) int as input
    return an updated pdf_plumber page object w.r.t the turning number of page (n)
    '''
    current_page_num = page.page_number - 1
    new_page = pdf.pages[current_page_num + n]
    return new_page


def unique(li:list) -> list:
    '''
    result a sorted list with unqiue element
    '''
    return sorted(list(set(li)))


def consecutive_int_list(li):
    '''
    return a list of list of consecutive integers
    '''
    from itertools import groupby
    from operator import itemgetter
    return [list(map(itemgetter(1), g)) for k, g in groupby(enumerate(li), lambda xi: xi[0]-xi[1])]


def get_title_liked_txt(page: object, size='size') -> list:
    '''
    take pdf_plumber page object as input, size is the parameter of fontsize, could be 'adv' or 'size'
    return the text which its not the main text of the page
    it returns, if any, title aliked text in list
    '''
    if size not in ['size', 'adv']:
        raise ValueError("size must be 'size' or 'adv'")
    df = pd.DataFrame(page.chars)
    main_fontsizes = df[size].mode()
    df = df[~df[size].isin(main_fontsizes)]
    title_like_txt_df = df.groupby(['top', 'bottom'])['text'].apply(''.join).reset_index()
    return title_like_txt_df['text'].to_list()


def search_pattern_from_page_or_cols(page: object, pattern: str):
    '''
    return search result of pattern from page or columns
    page result returns if both exist
    '''
    return search_pattern_from_cols(page=page, pattern=pattern) or search_pattern_from_page(page=page, pattern=pattern)


def search_pattern_from_cols(page: object, pattern=None, d=0.5, step=0.01, stop_point = .3) -> list:
    '''
    take a pdf_plumber page object as input
    divide the page into two columns: left and right and search pattern recursively
    return a list of result that found in each column
    '''
    # print('search from cols')
    # col_result = lambda col: search_pattern_from_page(page=col, pattern=pattern, d = 1)
    # results = map(col_result, divide_page_into_two_cols(page=page, d=d))
    results = [search_pattern_from_page(page=col, pattern=pattern, d=1) for col in divide_page_into_two_cols(page=page, d=d)]
    d -= step
    print(round(d,2))
    if not any(results) and d > stop_point:
        try:
            return search_pattern_from_cols(page=page, pattern=pattern, d=d, stop_point=stop_point)
        except ValueError:
            logging.warning("Pattern is not found in left or right columns.")
            return None
    return tuple(results)



def divide_page_into_two_cols(page: object, d=0.5) -> tuple:
    '''
    take pdf_plumber page object as input
    divide a page into left and right colums
    return left and right columns as pdf_plumber page object
    '''
    l0, l1 = 0 * float(page.width), d * float(page.width)
    r0, r1 = d * float(page.width), 1 * float(page.width)
    top, bottom = 0, float(page.height)
    # print(l0, l1, top, bottom)
    # print(r0, r1, top, bottom)
    # print()
    # left_col = page.crop((l0, top, l1, bottom))
    # right_col = page.crop((r0, top, r1, bottom))
    left_col = page.within_bbox((l0, top, l1, bottom), relative = True)
    right_col = page.within_bbox((r0, top, r1, bottom), relative = True)
    return left_col, right_col


def search_pattern_from_page(page: object, pattern=None, d=0.95) -> str:
    '''
    take pdf_plumber page object as input
    read from 2 edges and strink to the middle to remove noise text
    return result if pattern found else return None.
    '''
    # print(d)
    
    x0, x1 = (1-d) * float(page.width), d * float(page.width)
    top, bottom = 0, float(page.height)
    c_page = page.crop((x0, top, x1, bottom), relative=True)
    # c_page = page.within_bbox((x0, top, x1, bottom), relative = True)
    txt = c_page.extract_text()
    found_result = search_pattern_from_txt(txt=txt, pattern=pattern)
    d -= 0.01
    if found_result is None and round(d):  # round(d) = 1is d still > 0.5
        return search_pattern_from_page(page=page, pattern=pattern, d=d)
    return found_result


def search_pattern_from_txt(txt: str, pattern=None) -> Union[str, object]:
    '''
    search pattern from txt
    return result if pattern is found else return None
    '''
    if pattern is None:
        pattern = r'\n(?!.*?(Institute|Responsibilities).*?).*?(?P<auditor>.{4,}\S|[A-Z]{4})(?:LLP\s*)?\s*((PRC.*?|Chinese.*?)?[Cc]ertified [Pp]ublic|[Cc]hartered) [Aa]ccountants*'
    try:
        txt = txt.replace('ﬁ', 'fi') # must clean before chinese
        txt = re.sub(r'\ufeff', ' ', txt)  # clear BOM
        txt = re.sub(r"([^\x00-\x7F])+", "", txt)  # no chinese
        return re.search(pattern, txt, flags=re.MULTILINE | re.IGNORECASE)
    except (AttributeError, TypeError):
        return None

def abnormal_page(page: object, func_list=None) -> bool:
    '''
    abornmal_page 
    '''
    if func_list is None:
        func_list = [is_full_cn, is_landscape]
    return any(map(lambda func: func(page), func_list))

def is_full_cn(page: object, threshold: float = 0.85) -> bool:
    '''
    take a pdf_plumber page object and a float as input
    return cn to txt ratio of a pdf page.
    typically full cn page is over cn_to_txt_ratio is >85%
    '''
    txt = page.extract_text()
    txt = re.sub("\n+|\s+", "", txt)
    cn_txt = re.sub("([\x00-\x7F])+", "", txt)
    cn_to_txt_ratio = len(cn_txt)/len(txt)
    return cn_to_txt_ratio > threshold


def is_landscape(page) -> bool:
    '''
    check a pdfplumber page object is landscape
    '''
    return page.width > page.height


def is_url(url: str) -> Union[object, None]:
    if not isinstance(url, str):
        logging.warning(f'Input type {type(url)} is not str.')
        return None
    url_regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
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
    auditor = re.search(pattern, txt, flags=re.MULTILINE).group(
        'auditor').strip()
    return auditor


def _validate(search_result):
    pass


