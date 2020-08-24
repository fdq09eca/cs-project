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
from get_toc import *
# from get_toc import _get_toc, _get_page_by_outline, _get_page_by_page_search
from lab import *
import get_pdf


@query(from_date=yearsago(1, datetime.date.today()).strftime("%Y%m%d"))
def get_data(endpoint: str, payloads: dict) -> list:
    '''
    get data from hkex API.
    endpoint is given by the query decorator
    '''
    response = requests.get(endpoint, params=payloads)
    site_json = json.loads(response.text)
    if site_json['hasNextRow']:
        payloads['rowRange'] = site_json['recordCnt']
        return get_data(endpoint, payloads)
    results = json.loads(site_json['result'], object_hook=data_decoder)
    return results


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
        
        pdf_obj = get_pdf.byte_obj_from_url(data.file_link)
        pdf = get_pdf.by_pypdf(pdf_obj)
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
        result = {}
        if to_page is not None:
            try:
                page = get_pdf.by_pdfplumber(pdf_obj).pages[to_page]
                audit_firm = remove_noise_by_croping(page)
                # audit_firm = new_get_auditor(data.file_link, to_page)
                print(f'audit firm: {audit_firm} found on page: {to_page}')
                logging.info(
                    f'audit firm: == {audit_firm} ==; found on page: {to_page}')
            except AttributeError:
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
                finally:
                    write_to_csv(result)


def test(url):
    pdf_obj = get_pdf.byte_obj_from_url(url)
    py_pdf = get_pdf.by_pypdf(pdf_obj)
    plumber_pdf = get_pdf.by_pdfplumber(pdf_obj)
    toc = _get_toc(py_pdf)
    indpentent_auditor_report_pattern = r".*?(independent|audit[or’'s]*|report)((?!committee|executive|director|non-standard).)*(report|firm|audit[or’'s]*)"
    if _get_page_by_outline(toc, indpentent_auditor_report_pattern):
        print('find by outline!')
        pages = _get_page_by_outline(toc, indpentent_auditor_report_pattern)
    else:
        print('find by page!')
        pages = _get_page_by_page_search(plumber_pdf, indpentent_auditor_report_pattern)
    
    if pages:
        for p in pages:
            page = plumber_pdf.pages[int(p)]
            search_result = search_pattern_from_page(page)
            audit_firm = search_result.group('auditor').strip() if search_result else None
            print(audit_firm)


if __name__ == "__main__":
    
    main()
    unique_result()
    error_result()
    