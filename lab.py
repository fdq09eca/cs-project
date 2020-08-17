from test_cases import unknown_cases, err_cases
from io import BytesIO
import pdfplumber
import requests
import os
import csv
import PyPDF2
import io
import itertools
import re
from test_cases import test_cases, noise_cases
from test_cases import two_cols_cases
from typing import Union
import get_pdf


def get_page(url, p):
    rq = requests.get(url)
    pdf = pdfplumber.open(BytesIO(rq.content))
    return pdf.pages[p]


def test_two_cols(test_cases):
    for url, page in test_cases.items():
        rq = requests.get(url)
        pdf = pdfplumber.load(BytesIO(rq.content))
        txt = pdf.pages[page].extract_text()
        # txt = re.sub("([^\x00-\x7F])+", "", txt)
        print(txt)
        col_1 = re.sub(r"\s{2}.*", "", txt)
        col_2 = re.sub(r".*\s{2}", "", txt)
        print(col_1)
        print('====')
        print(col_2)
        print('====')


def pdf_extracted_txt(url, page):
    rq = requests.get(url)
    pdf = pdfplumber.load(BytesIO(rq.content))
    txt = pdf.pages[page].extract_text()
    return txt


def found_noise(txt:str):
    txt = re.sub('\n+', '\n', txt)
    # noiseRegx = re.compile(r'^.{1,3}$|^\S{1,3}\s+(?=[A-Z])|\s+.{1,2}$', flags=re.MULTILINE)
    noiseRegx = re.compile(r'^.{1,3}$|\s+.{1,2}$', flags=re.MULTILINE)
    noises = noiseRegx.findall(txt)
    return len(noises) > 10


def is_landscape(src: Union[str, object], page_num):
    '''
    check a pypdf2 page object is landscape
    '''
    import get_pdf
    pdf = get_pdf.by_pypdf(src)
    page = pdf.getPage(page_num).mediaBox
    page_width = page.getUpperRight_x() - page.getUpperLeft_x()
    page_height = page.getUpperRight_y() - page.getLowerRight_y()
    return page_width > page_height


def page_cn_ratio(src: Union[str, object], page_num: int) -> float:
    '''
    take url, local path, byte object as src
    return cn to txt ratio of a pdf page.
    typically full cn page is over cn_to_txt_ratio is >85%
    '''
    import get_pdf
    pdf = get_pdf.by_pdfplumber(src)
    page = pdf.pages[page_num]
    txt = page.extract_text()
    cn_txt = re.sub("([\x00-\x7F])+", "", txt)
    cn_to_txt_ratio = len(cn_txt)/len(txt)
    return cn_to_txt_ratio


def search_pattern_from_txt(txt: str, pattern=None) -> Union[str, object]:
    '''
    search pattern from txt
    return result if pattern is found else return None
    '''
    if pattern is None:
        pattern = r'\n(?!.*?(Institute|Responsibilities).*?).*?(?P<auditor>.{4,}\S|[A-Z]{4})(?:LLP\s*)?\s*((PRC.*?|Chinese.*?)?[Cc]ertified [Pp]ublic|[Cc]hartered) [Aa]ccountants*'
    try:
        txt = re.sub(r'\ufeff', ' ', txt)  # clear BOM
        txt = re.sub(r"([^\x00-\x7F])+", "", txt)  # no chinese
        return re.search(pattern, txt, flags=re.MULTILINE | re.IGNORECASE).group('auditor').strip()
    except (AttributeError, TypeError):
        return None


def search_pattern_from_page(page: object, d=0.95, pattern=None) -> str:
    '''
    take pdf_plumber page object as input
    read from 2 edges and strink to the middle to remove noise text
    return result if pattern found else return None.
    '''
    x0, x1 = (1-d) * float(page.width), d * float(page.width)
    top, bottom = 0, float(page.height)
    c_page = page.crop((x0, top, x1, bottom), relative=True)
    txt = c_page.extract_text()
    found_result = search_pattern_from_txt(txt, pattern)
    d -= 0.01
    if found_result is None and round(d):
        return search_pattern_from_page(page, d, pattern)
    return found_result

def search_pattern_from_cols(page: object, d=0.5, pattern=None) -> list:
    '''
    take a pdf_plumber page object as input
    divide the page into two columns: left and right and search pattern recursively
    return a list of result that found in each column
    '''
    result = [search_pattern_from_page(page=col, d=1, pattern=pattern) for col in divide_page_into_two_cols(page, d)]
    d -= .01
    if not any(result) and d:
        return search_pattern_from_cols(page, d, pattern)
    return result

def divide_page_into_two_cols(page:object, d=0.5)-> tuple:
    '''
    take pdf_plumber page object as input
    divide a page into left and right colums
    return left and right columns as pdf_plumber page object
    '''
    x0, x1 = 0 * float(page.width), d * float(page.width)
    top, bottom = 0, float(page.height)
    left_col = page.crop((x0, top, x1, bottom))
    x0, x1 = d * float(page.width), 1 * float(page.width)
    right_col = page.crop((x0, top, x1, bottom))
    return left_col, right_col

def is_two_cols(txt):
    double_spaces = re.findall(r'^(?=.+[ ]{2})(?!.+[ ]{2}.+[ ]{2})(.+)', txt, flags=re.MULTILINE)
    newlines = re.findall(r'.*?\n', txt, flags=re.MULTILINE)
    return len(double_spaces)/len(newlines)


def validated_result(result):
    return len(result) > 50

if __name__ == "__main__":
    # pattern = r'\n(?!.*?Institute.*?).*?(?P<auditor>.+?)(?:LLP\s*)?\s*((PRC.*?|Chinese.*?)?[Cc]ertified [Pp]ublic|[Cc]hartered) [Aa]ccountants'
    c = 0
    d = {'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0723/2020072300448.pdf':116 }
    # for url, page_num in two_cols_cases.items():
    # for url, page_num in noise_cases.items():
    # for url, page_num in test_cases.items():
    for url, page_num in two_cols_cases.items():
    # for url, page_num in d.items():
    # for url, page_num in {**test_cases, **noise_cases}.items():
        # for url, page_num in .items():
        # url, page_num = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0415/2020041501285.pdf', 147
        # url, page_num = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0428/2020042800976.pdf', 60
        # url, page_num = 'https://www1.hkexnews.hk/listedco/listconews/gem/2019/1031/2019103100067.pdf', 73

        # c += 1
        page = get_page(url, page_num)
        # page_obj = get_pdf.byte_obj_from_url(url)
        # if page_cn_ratio > .85:
            # page_num - 1
        # page = get_pdf.by_pdfplumber(page_obj).pages[page_num]
        txt = page.extract_text()
        # print(txt)
        # print(is_two_cols(txt), url)
        if is_two_cols(txt) > .05:
            # a = [search_pattern_from_txt(col.extract_text()) for col in divide_page_into_two_cols(page)]
            a = search_pattern_from_cols(page)
            print(a)
        #     print(url)
        # else:
        #     print(is_two_cols(txt))
        # print(page_cn_ratio(page_obj, page_num))
        # print(find_noise(txt))
        # print(search_pattern_from_page(page)
        # for col in divide_page_into_two_cols(page):
        #     print('=======')
        #     txt = col.extract_text()
        #     print(txt)
        #     print('=======')
        #     print(f'>>{search_pattern_from_txt(txt)}')
        #     print(f'>>{is_two_cols(txt)}')
            # print(search_pattern_from_page(col, d=1))
        

        # auditor = get_audit_from_txt(txt) if not find_noise else remove_noise_by_croping(page)
        # print(get_audit_from_txt(txt))
        # print(txt)
        # print(repr(txt))
        # print(get_audit_from_txt(txt))
        # with open('scanning.csv','a+') as f:
        #     csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        #     csv_writer.writerow([c, remove_noise_by_croping(page), url, find_noise(txt)])
        # csv_writer.writerow([c, auditor, url, find_noise(txt)])

    # print(page.extract_text())

    # print(page.extract_text())
        # print(remove_noise_by_croping(page))
    # pattern = r'\n(?!.*?Institute.*?).*?(?P<auditor>.+?)(\n\d.*\d)?(?:LLP\s*)?\s*((PRC.*?|Chinese.*?)?[Cc]ertified [Pp]ublic|[Cc]hartered) [Aa]ccountants'
    # testing(pattern=pattern)
    # from test_cases import noise_cases
    # testing(noise_cases, p_txt=True)
    # for url, page_num in noise_cases.items():
    #     txt = remove_noise_by_croping(url, page_num)

    # url, page = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0428/2020042800976.pdf', 60
    # txt = pdf_extracted_txt(url, page)
    # remove_noise(txt)
    # print(txt)
    # pattern = r'\n(?!.*?(Institute).*?).*?(?P<auditor>.+?)(?:LLP\s*)?\s*((PRC.*?|Chinese.*?)?[Cc]ertified [Pp]ublic|[Cc]hartered) [Aa]ccountant'

    # for url, page in noise_cases.items():
    #     print('======')
    #     # txt = pdf_extracted_txt(url, page)
    #     # txt = remove_noise(txt)
    #     txt = remove_noise_by_corping(url, page)

    #     auditor = re.search(pattern, txt, flags=re.MULTILINE).group('auditor').strip()
    #     print(f'>> {repr(auditor)}')
    #     print(url, page)
    #     print('======')
    # c = {'https://www1.hkexnews.hk/listedco/listconews/gem/2019/1031/2019103100067.pdf': 73}

    # testing(c, verbose=True, pattern=pattern)
    # url, page_num = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0513/2020051300203.pdf', 88
    # rq = requests.get(url)
    # pdf = pdfplumber.load(BytesIO(rq.content))
    # page = pdf.pages[page_num]
    # box = (0.1 * float(page.width), 0.05 * float(page.height), 0.95 * float(page.width), 0.95 * float(page.height))
    # c_page = page.crop(box)
    # txt = c_page.extract_text()
    # print(txt)
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0428/2020042800976.pdf', 60
    # page = get_page(url,p)
    # page_w = float(page.width)
    # for c in page.chars:
    #     if c['upright']:
    #         print(c['text'], end='')
