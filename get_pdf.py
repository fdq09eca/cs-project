from helper import is_url
import logging
import PyPDF2, os, pdfplumber, requests
from typing import Union
from contextlib import contextmanager
from io import BytesIO


def byte_obj_from_url(url: str) -> object:
    '''
    get byteIO object from url
    '''
    from io import BytesIO
    import requests
    if not is_url(url):
        return None
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)


def by_pypdf(stream:Union[str, object]) -> Union[None, object]:
    '''
    take url, local path, or BtyeIO objectas input 
    return a pypdf2 object 
    '''
    import PyPDF2, os
    if isinstance(stream, str):
        if is_url(stream):
            stream = byte_obj_from_url(stream)
        elif os.path.isfile(stream):
            # with  as f:
            stream = open(stream, 'rb')
    return PyPDF2.PdfFileReader(stream, strict=False)


def by_pdfplumber(stream:Union[str, object]) -> Union[None, object]:
    '''
    take url, local path, or BtyeIO objectas input 
    return a pdfplumber object 
    '''
    import pdfplumber
    import os
    if isinstance(stream, str):
        if is_url(stream):
            stream = byte_obj_from_url(stream)
        elif os.path.isfile(stream):
            return pdfplumber.open(stream)
        else:
            logging.critical(f'Invaild url or local path.')
    return pdfplumber.open(stream)


####################################################################

@contextmanager
def _byte_obj_from_url(url: str) -> object:
    '''
    get byteIO object from url
    '''
    if is_url(url) is None:
        raise ValueError('Invalid url.')
    with requests.get(url) as response:
        response.raise_for_status()
        byte_obj = BytesIO(response.content)
        yield byte_obj
    byte_obj.close()

@contextmanager
def _by_pypdf(stream:Union[str, object]) -> Union[None, object]:
    '''
    take url, local path, or BtyeIO objectas input 
    return a pypdf2 object 
    '''
    if isinstance(stream, str):
        if is_url(stream):
            with byte_obj_from_url(stream) as byte_obj:
                yield PyPDF2.PdfFileReader(byte_obj, strict=False)
            # byte_obj.close()
        elif os.path.isfile(stream):
            with open(stream, 'rb') as file_obj:
                yield PyPDF2.PdfFileReader(file_obj, strict=False)
            # file_obj.close()
    else:
        yield PyPDF2.PdfFileReader(stream, strict=False)

@contextmanager
def _by_pdfplumber(stream:Union[str, object]) -> Union[None, object]:
    '''
    take url, local path, or BtyeIO objectas input 
    return a pdfplumber object 
    '''
    if isinstance(stream, str) and is_url(stream):
        with _byte_obj_from_url(stream) as byte_obj:
            yield pdfplumber.open(byte_obj)
    else:
        yield pdfplumber.open(stream)

def test(func):
    url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0424/2020042401194.pdf'
    local = '/Users/macone/Documents/cs-project/2020060500706.pdf'
    with _byte_obj_from_url(url) as obj:
        print(f'\n== here is obj ==\n {func(obj)}')
        with func(obj) as pdf:
            print(f'\n== here is loaded pdf ==\n {pdf.getOutlines()}')    
        # print(f'here is the loaded pdf {pdf}:')
    with func(url) as pdf:
        print(f'\n== here is url ==\n {pdf.getOutlines()}')
    with func(local) as pdf:
        print(f'\n== here is local==\n {pdf.getOutlines()}')
    # print(f'here is local: {func(local).getOutlines()}')

if __name__ == "__main__":
    for f in [_by_pdfplumber]:
        test(_by_pypdf)
    