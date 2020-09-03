# import get_data
from get_data import HKEX_API
import re
import requests
import logging
import pdfplumber
import pandas as pd
import numpy as np
from helper import is_url, turn_n_page, is_landscape, is_full_cn, abnormal_page, df_to_csv, str_to_date, yesterday, today, n_yearsago, validate_auditor
from get_toc import _get_toc, _get_page_by_outline, _get_page_by_page_title_search
from get_pdf import byte_obj_from_url, _by_pypdf, _by_pdfplumber
from io import BytesIO
from helper import search_pattern_from_page_or_cols
from fuzzywuzzy import process, fuzz


class AnnualReport:
    
    audit_report_regex = r'^(?!.*internal)(?=.*report|responsibilities).*auditor.*$'
    auditor_regex = r'\n(?!.*?(Institute|Responsibilities).*?).*?(?P<auditor>.{4,}\S|[A-Z]{4})(?:LLP\s*)?\s*((PRC\s*?|Chinese\s*?)?Certified\s*Public|Chartered)\s*Accountants*'
    validation_src = 'valid_auditors.csv'

    def __init__(self, stream, company=None, stock_num=None, release_date=None, report_title=None):
        logging.warning(f'Initialising {type(self).__name__}("{stream}")')
        self.url = stream if is_url(stream) else stream
        self.pdf_obj = byte_obj_from_url(self.url) or stream
        self.toc = self._toc()
        self.auditor = self.valid_auditor() or self.raw_auditor()
        self.report_title = report_title
        self.company = company
        self.stock_num = int(stock_num)
        self.audit_fee = self._audit_fee()
        self.release_date = str_to_date(release_date, str_time_pattern='%d/%m/%Y %H:%M', format_pattern='%d %b %Y')
        # self.currency

    def _toc(self):
        with _by_pypdf(self.pdf_obj) as pdf:
            return _get_toc(pdf)

    def get_outline_pageRange(self, outline_pattern=None):
        if outline_pattern is None:
            outline_pattern = AnnualReport.audit_report_regex
        with _by_pdfplumber(self.pdf_obj) as pdf:
            return _get_page_by_outline(self.toc, outline_pattern) or _get_page_by_page_title_search(pdf, outline_pattern)

    def valid_auditor(self, src: str = None, min_similarity: float = 90.0):
        '''
        vaildate auditor with database/local csvfile with column valid_auditor
        return the default auditor name if the pair is over the min_similarity
        '''
        
        if src is None:
            src = self.validation_src
        
        v_auditors = pd.read_csv(src).valid_auditor.values
        r_auditors = self.raw_auditor()
        # def validate(r_auditor, v_auditors=v_auditors):
        #     valid_auditor = process.extractOne(r_auditor, v_auditors, scorer=fuzz.token_set_ratio)[0]
        #     similarity = process.extractOne(r_auditor, v_auditors, scorer=fuzz.token_set_ratio)[1]
        #     return valid_auditor if similarity >= min_similarity else None
        result = [validate_auditor(r_auditor, v_auditors, min_similarity) for r_auditor in r_auditors]
        return tuple(filter(None, result))

    #     return df.valid_auditor.values

    def raw_auditor(self):
        with _by_pdfplumber(self.pdf_obj) as pdf:
            auditor_report_last_pages = [pdf.pages[page_nums[-1]] for page_nums in self.get_outline_pageRange()]
            search_results = [search_pattern_from_page_or_cols(page=page, pattern=AnnualReport.auditor_regex) for page in auditor_report_last_pages]
            

            if not any(search_results) and any(map(abnormal_page, auditor_report_last_pages)):
                auditor_report_last_pages = [turn_n_page(pdf, page, 2) if is_landscape(page) else turn_n_page(pdf, page, -1) if is_full_cn(page) else page for page in auditor_report_last_pages]
                search_results = [search_pattern_from_page_or_cols(page=page, pattern=AnnualReport.auditor_regex) for page in auditor_report_last_pages]
            
            auditors = set()

            for result in filter(None, search_results):
                if type(result) is tuple:
                    for r in filter(None, result):
                        auditors.add(r.group('auditor'))
                else:
                    auditors.add(result.group('auditor'))
            return tuple(auditors)

    def _audit_fee(self):
        return None

    def __repr__(self):
        return f'{type(self).__name__}("{self.url}")'


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    query = HKEX_API(from_date=n_yearsago(n=1), to_date=today())
    d = [dict(data._asdict()) for data in query.data]
    df = pd.DataFrame(d)
    df['auditor'] = 'None'
    for data in query.data:
        kwargs = {
            'stream': data.file_link,
            'company': data.stock_name,
            'stock_num': data.stock_code,
            'release_date': data.date_time,
            'report_title': data.title
        }
        try:
            ar = AnnualReport(**kwargs)
            condition = df.news_id == data.news_id
            df.at[condition, 'auditor'] = pd.Series([ar.auditor]).values if ar.auditor else 'None'
            df.at[condition, 'date_time'] = ar.release_date
            # print(ar.auditor)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f'N/A, {e}')
            df.loc[condition, 'auditor'] = 'NaN'
        finally:
            row = df[condition]
            # df_to_csv(row)
            print(row)
