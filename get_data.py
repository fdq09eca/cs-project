import json, requests, datetime, html
from typing import Generator
from collections import namedtuple

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
        raise ValueError(f'Date range over a year. can only query from {datetime.datetime.strftime(yearsago(1), "%Y%m%d")}')
    def Inner(call_api):
        def wrapper(*args, **kwargs):
            return (i for i in call_api(endpoint=endpoint, payloads=payloads))
        return wrapper
    return Inner


def data_decoder(data):
    data = {k.lower(): html.unescape(v) for k, v in data.items()}
    data['file_link'] = "https://www1.hkexnews.hk" + data['file_link']
    return namedtuple('data', data.keys())(*data.values())


def yearsago(years, from_date=datetime.datetime.now()):
    try:
        return from_date.replace(year=from_date.year - years)
    except ValueError:
        # Must be 2/29!
        assert from_date.month == 2 and from_date.day == 29  # can be removed
        return from_date.replace(month=2, day=28, year=from_date.year-years)


@query(from_date=yearsago(1, datetime.date.today()).strftime("%Y%m%d"))
def get_data(endpoint: str, payloads: dict) -> list:
    '''
    get data from hkex API.
    endpoint is given by the query decorator
    '''

    with requests.get(endpoint, params=payloads) as response:
        site_json = json.loads(response.text)
        if site_json['hasNextRow']:
            payloads['rowRange'] = site_json['recordCnt']
            return get_data(endpoint, payloads)
        results = json.loads(site_json['result'], object_hook=data_decoder)
        return results


if __name__ == '__main__':
    # pass
    print([i for i in get_data()])