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
from helper import *
from summary import *
from get_toc import  *
# import get_pdf
ytd = yearsago(1, datetime.date.today()).strftime("%Y%m%d")


@query(from_date=ytd)
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
    return int(from_page), int(to_page)


def get_pages_by_page_search(pdf, keywords_pattern):
    '''
    search page by keywords pattern from page 3
    if found, return the respective page range in list.
    '''
    pageRange = []
    pages = pdf.getNumPages()
    for p in range(3, pages):
        page = pdf.getPage(p)
        page_txt = re.sub('\n+', '', page.extractText())
        if re.search(keywords_pattern, page_txt, flags=re.IGNORECASE):
            pageRange.append(p)
    logging.info(f'{keywords_pattern} found in pages {pageRange}')
    from_page = get_pageRange(pageRange, 'from')
    to_page = get_pageRange(pageRange, 'to')
    return from_page, to_page


def main():
    # logging.basicConfig(level=logging.INFO,
    #                     filename=f'log-{os.path.splitext(__file__)[0]}.txt')
    print('== start ==')
    for data in get_data():
        pdf = get_pdf(data.file_link)
        if not pdf:
            continue
        toc = get_toc(pdf)
        title_pattern = r".*?(independent|audit[or’'s]*|report)((?!committee|executive|director|non-standard).)*(report|firm|audit[or’'s]*)"

        if get_pages_by_outline(toc, title_pattern):
            from_page, to_page = get_pages_by_outline(toc, title_pattern)
        else:
            print('search by page!')
            from_page, to_page = get_pages_by_page_search(pdf, title_pattern)
        print(f"from_page: {from_page}, to_page: {to_page}")
        # print(f"from_page_type: {type(from_page)}, to_page_type: {type(to_page)}")
        result = {}
        if to_page is not None:
            # result = dict(data._asdict())
            try:
                audit_firm = new_get_auditor(data.file_link, to_page)
                # audit_firm = get_auditor(pdf, to_page)
                # result['search_by'] = 'outline'
                print(f'audit firm: {audit_firm} found on page: {to_page}')
                logging.info(
                    f'audit firm: == {audit_firm} ==; found on page: {to_page}')
            except AttributeError:
                # result['search_by'] = 'page'
                print(f'audit firm not found on page: {to_page}')
                logging.warning(
                    f'audit firm not found on page: {to_page}, check {data.file_link}')
                audit_firm = 'None'
            finally:
                result['auditor'] = audit_firm
                result['auditReportPageRange'] = f'{from_page} - {to_page}'
                result['link'] = data.file_link
                result['page_text'] = re.sub(
                    '\n+', '', pdf.getPage(to_page).extractText())
                try:
                    result['normal'] = len(audit_firm) < 50
                    if result['normal']:
                        write_to_csv(result, 'normal.csv')
                    else:
                        write_to_csv(result, 'abnormal.csv')
                except TypeError:
                    write_to_csv(result, 'abnormal.csv')
                # finally:
                #     write_to_csv(result)


def test():
    total, found, no_toc = 0, 0, 0
    for data in get_data():
        pdf = get_pdf(data.file_link)
        if not pdf:
            continue
        toc = get_toc(pdf)
        # title_pattern = r"(.*?independent|audit[or’'s]*?)(.*?audit[or’'s]*?)?.*(report|firm|audit[or’'s]*?)" # 97.x%
        title_pattern = r".*?(independent|audit[or’'s]*|report)((?!committee|executive|director|non-standard).)*(report|firm|audit[or’'s]*)"

        if toc:
            total += 1
            search_results = [re.search(title_pattern, outline, flags=re.IGNORECASE)
                              for outline, page_range in toc.items()]
            search_results = [r for r in search_results if r]
            if search_results:
                write_to_csv(
                    {'result': search_results[0].group(0), "link": data.file_link})
                found += 1
            else:
                write_to_csv({'result': toc, "link": data.file_link})
        else:
            no_toc += 1
    summary = f'total: {total}; toc missing rate: {no_toc/total:.2%}; success rate: {found/total:.2%}'
    print(summary)
    write_to_csv({'result': summary, 'link' : 'N/A'})

main()
unique_result()
error_result()