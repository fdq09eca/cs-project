from helper import is_url
import logging
from typing import Union


def byte_obj_from_url(url: str) -> object:
    '''
    get byteIO object from url
    '''
    from io import BytesIO
    import requests
    if is_url(url) is None:
        raise ValueError('Invalid url.')
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)


def by_pypdf(stream:Union[str, object]) -> Union[None, object]:
    '''
    return  a pypdf2 object 
    '''
    import PyPDF2
    try:
        stream = byte_obj_from_url(
            stream) if isinstance(stream, str) else stream
        return PyPDF2.PdfFileReader(stream, strict=False)
    except PyPDF2.utils.PdfReadError:
        logging.warning(f'PdfReadError occur, check {stream}')
        return None


def by_pdfplumber(stream:Union[str, object]) -> Union[None, object]:
    import pdfplumber
    import os
    if isinstance(stream, str):
        if is_url(stream):
            stream = byte_obj_from_url(stream)
        elif os.path.isfile(stream):
            return pdfplumber.open(stream)
        else:
            logging.critical(f'stream string is neither url or local path.')
    return pdfplumber.load(stream)



def check():
    logging.basicConfig(level=logging.DEBUG)
    url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0727/2020072700471.pdf'
    pdf_obj = byte_obj_from_url(url)
    by_pypdf(pdf_obj)
    by_pdfplumber(pdf_obj)

if __name__ == "__main__":
    check()
