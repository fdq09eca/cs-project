from io import BytesIO
from typing import Union, Pattern, Match
from contextlib import contextmanager
import requests, re, logging, pdfplumber


class PDF:
    def __init__(self, src):
        self.src = src
    
    @property
    def pdf_obj(self):
        return self._pdf_obj
    
    @property
    def src(self):
        return self._src
    
    @src.setter
    def src(self, src):
        self._pdf_obj = self.byte_obj_from_url(src) or src
        self._src = src
    
    
    @staticmethod
    def is_url(src:str) -> Match[str]:
        if not isinstance(src, str):
            logging.warning(f'Input type {type(src)} is not str.')
            return None
        url_regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            # domain...
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(url_regex, src)
    
    
    @staticmethod
    def byte_obj_from_url(url: str) -> object:
        '''
        get byteIO object from url
        '''
        if not PDF.is_url(url):
            return None
        with requests.get(url) as response:
            response.raise_for_status()
            byte_obj = BytesIO(response.content)
        return byte_obj

    def __repr__(self):
        return f'{self.__class__.__name__}(src="{self.src}")'



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0424/2020042401194.pdf'
    pdf_obj = PDF.byte_obj_from_url(url)
    pdf = PDF(pdf_obj)
    print(pdf.pdf_obj)
    print(pdf.src)

    # pdf = PDF(url)
    # print(pdf.pdf_obj)
    # print(pdf.pdf_obj)
    # pdf.src = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0802/2020080200033.pdf'
    # print(pdf.pdf_obj)
    # print(pdf.pdf_obj)
    # print(pdf)
