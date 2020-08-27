import json, requests, datetime, html, logging
from typing import Generator
from collections import namedtuple
from os import sys, path
# sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from helper import over_a_year, yesterday, today, n_yearsago

class HKEX_API:
    
    '''
    usage:
        make query to hkex api with specified time range stock id and document type
    
    note:
        - query date format is '%Y%m%d' e.g. 20200825
        - stock id is complusory for query which is over a year
        - document types are annual report, half year report and quaterly report. (default: annual report)
    '''
    
    endpoint = 'https://www1.hkexnews.hk/search/titleSearchServlet.do'
    dt_fmt = '%Y%m%d'
    doc_code = {
        'annual_report': '40100',
        'half_year_report': '40200',
        'quaterly_report': '40300'    
    }

    
    def __init__(self, from_date, to_date, stock_id=None, doc='annual_report'):
        self.from_date = from_date
        self.to_date = to_date
        self.stock_id= stock_id
        self.doc = doc
    
    
    @property
    def from_date(self) -> str:
        return self._from_date
    
    
    @from_date.setter
    def from_date(self, from_date:str) -> str:
        self._from_date = self.date_fmt_validator(from_date, HKEX_API.dt_fmt)
    
    
    @property
    def to_date(self) -> str:
        return self._to_date
    
    @to_date.setter
    def to_date(self, to_date:str) -> str:
        self._to_date = self.date_fmt_validator(to_date, HKEX_API.dt_fmt)
    
    
    @property
    def payloads(self) -> dict:
        return self.set_payloads(from_date=self.from_date, to_date=self.to_date, stock_id=self.stock_id, doc=self.doc)
        
    @property
    def data(self) -> Generator['namedtuple', None, None]:
        return (i for i in self.get_data())

    
    @staticmethod
    def data_decoder(data):
        data = {k.lower(): html.unescape(v) for k, v in data.items()}
        data['file_link'] = "https://www1.hkexnews.hk" + data['file_link']
        return namedtuple('data', data.keys())(*data.values())
    
    
    @staticmethod
    def date_fmt_validator(date_str:str, dt_fmt:str='%Y%m%d') -> None:
        try:
            datetime.datetime.strptime(date_str, dt_fmt)
            return date_str
        except ValueError as e:
            logging.critical(f'{e}, date str format is not {dt_fmt}')
            raise ValueError(f'{e}, date str format is not {dt_fmt}')
    
    @staticmethod
    def call_api(endpoint:str, payloads:dict) -> tuple:
               
        with requests.get(endpoint, params=payloads) as response:
            response.raise_for_status()
            site_json = json.loads(response.text)
            if site_json['hasNextRow']:
                payloads['rowRange'] = site_json['recordCnt']
                return HKEX_API.call_api(endpoint, payloads=payloads)
            results = json.loads(site_json['result'], object_hook = HKEX_API.data_decoder)
            return tuple(results)
    

    @staticmethod
    def set_payloads(from_date:str, to_date:str=today('%Y%m%d'), stock_id:str=None, doc:str=None) -> dict:
               
        HKEX_API.date_fmt_validator(from_date, '%Y%m%d')
        HKEX_API.date_fmt_validator(to_date, '%Y%m%d')

        if over_a_year(from_date=from_date) and stock_id is None:
            ytd = n_yearsago(1)
            raise ValueError(f'Query over a year must specify stock_id e.g "1", global query can only from "{ytd}"')

        payloads = {
            'sortDir': '0',
            'sortByOptions': 'DateTime',
            'category': '0',
            'market': 'SEHK',
            'stockId': stock_id or '-1',
            'documentType': '-1',
            'fromDate': from_date,
            'toDate': to_date,
            'title': '',
            'searchType': '1',
            't1code': '40000',
            't2Gcode': '-2', 
            't2code': HKEX_API.doc_code.get(doc, None) or '40100', # 40100: annual report, 40200: half_year_report, 40300: quaterly_report
            'rowRange': '100',
            'lang': 'EN'
        }
        
        return payloads

    def get_data(self) -> list:
        return HKEX_API.call_api(endpoint=HKEX_API.endpoint, payloads=self.payloads)
    

    

if __name__ == '__main__':
    # pass
    # print(_get_data())
    # query = HKEX_API(from_date=yesterday(), to_date=today())
    query = HKEX_API(from_date=n_yearsago(n=1), to_date=today())
    print(query.doc)
    print(query.payloads['t2code'])
    print(len(query.get_data()))
    print(len([i for i in query.data]))
    # query = HKEX_API(from_date=n_yearsago(n=1), to_date=today(), doc='half_year_report') 
    print('>>>>>>')
    query.doc = 'half_year_report'
    print(query.doc)
    print(query.payloads['t2code'])
    print(len(query.get_data()))
    print(len([i for i in query.data]))
    print('>>>>>>')
    print(query.from_date)
    query.from_date = yesterday()
    print(query.from_date)
    print(query.payloads['fromDate'])
    print(len(query.get_data()))
    print(len([i for i in query.data]))
    # print(query.data)
    # query.data = 'hehe'