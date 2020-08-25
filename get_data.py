import json
import requests
import datetime
import html
from typing import Generator
from collections import namedtuple
from helper import over_a_year, yesterday, today, date_fmt_validate, n_yearsago
import logging

class HKEX_API:
    '''
    payloads is defauled to get the annual report from calling hkex api
    `instance.payloads = None` if `payload` was customised and now want to rollback to default value            
    '''
    endpoint = 'https://www1.hkexnews.hk/search/titleSearchServlet.do'
    dt_fmt = '%Y%m%d'
    
    def __init__(self, from_date, to_date, payloads=None):
        self.from_date = from_date
        self.to_date = to_date
        self.payloads = payloads
        
    @property
    def data(self):
        return (i for i in self.get_data())

    @property
    def payloads(self):
        return self._payloads

    @payloads.setter
    def payloads(self, payloads):
        if payloads is None:
            self._payloads = set_payloads(self.from_date, self.to_date)
        else:
            if type(payloads) is dict:
                print(f'custom payload input: {payloads}')
                self._payloads = payloads
            else:
                raise TypeError(f'payloads type: {type(payloads)} is not dict')
    
    @property
    def from_date(self):
        return self._from_date
    
    @from_date.setter
    def from_date(self, from_date:str):
        self._from_date = date_fmt_validate(from_date, HKEX_API.dt_fmt)
    
    @property
    def to_date(self):
        return self._to_date
     
    @to_date.setter
    def to_date(self, to_date:str):
        self._to_date = date_fmt_validate(to_date, HKEX_API.dt_fmt)
    
    def get_data(self):
        return call_api(HKEX_API.endpoint, self.payloads)
    
   

def set_payloads(from_date:str, to_date=today('%Y%m%d')):
    '''
    set payload for the hkex api call
    '''
    date_fmt_validate(from_date, '%Y%m%d')
    date_fmt_validate(to_date, '%Y%m%d')

    if over_a_year(from_date=from_date):
        ytd = n_yearsago(1)
        raise ValueError(f'Date range over a year. can only query from {ytd}')

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
        'rowRange': '100',
        'lang': 'EN'
    }
    return payloads


# def _get_data(from_date:str=n_yearsago(1), to_date:str=today()) -> tuple:
#     '''
#     get data from hkex API.
#     endpoint is given by the query decorator
#     default to get 1 year data
#     '''
#     payloads = set_payloads(from_date, to_date)
#     endpoint = 'https://www1.hkexnews.hk/search/titleSearchServlet.do'
#     return call_api(endpoint, payloads)


def call_api(endpoint:str, payloads:dict) -> tuple:
    '''
    call hkex api
    '''
    with requests.get(endpoint, params=payloads) as response:
        site_json = json.loads(response.text)
        if site_json['hasNextRow']:
            payloads['rowRange'] = site_json['recordCnt']
            return call_api(endpoint, payloads=payloads)
        results = json.loads(site_json['result'], object_hook=data_decoder)
        return tuple(results)

def data_decoder(data):
    data = {k.lower(): html.unescape(v) for k, v in data.items()}
    data['file_link'] = "https://www1.hkexnews.hk" + data['file_link']
    return namedtuple('data', data.keys())(*data.values())

if __name__ == '__main__':
    pass
    # print(_get_data())
    # query = HKEX_API(from_date=yesterday(), to_date=today())
    # query = HKEX_API(from_date=n_yearsago(n=1), to_date=today())
    # print(query.get_data()