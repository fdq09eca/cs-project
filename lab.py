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


def testing(
    d=test_cases,
    verbose=False,
    pattern=r'\n(?!.*?Institute.*?).*?(?P<auditor>.+?)(?:LLP\s*)?\s*((PRC.*?|Chinese.*?)?[Cc]ertified [Pp]ublic|[Cc]hartered) [Aa]ccountants',
    NG=0
):

    for url, page in d.items():
        rq = requests.get(url)
        pdf = pdfplumber.load(BytesIO(rq.content))
        txt = pdf.pages[page].extract_text()
        txt = re.sub("([^\x00-\x7F])+", "", txt)  # diu no chinese
        if verbose:
            print(txt)
        try:
            auditor = re.search(pattern, txt, flags=re.MULTILINE).group(
                'auditor').strip()
            print(repr(auditor))
        except AttributeError:
            print(txt)
            print('============')
            print(url)
            NG += 1
    print(f'NG:{NG}')


def get_page(url, p):
    rq = requests.get(url)
    pdf = pdfplumber.load(BytesIO(rq.content))
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

# test_two_cols(two_cols_cases)


def pdf_extracted_txt(url, page):
    rq = requests.get(url)
    pdf = pdfplumber.load(BytesIO(rq.content))
    txt = pdf.pages[page].extract_text()
    return txt


def remove_noise(txt):
    noiseRegx = re.compile(
        r'^.{1,3}$|^\S{1,3}\s+(?=[A-Z])|\s+.{1,2}$', flags=re.MULTILINE)
    txt = noiseRegx.sub('', txt)
    txt = re.sub('\n+', '\n', txt)
    print(txt)
    return txt


def get_audit_from_txt(txt, pattern=None):
    if pattern is None:
        pattern = r'\n(?!.*?(Institute).*?).*?(?P<auditor>.+?\S$)(?:LLP\s*)?\s*((PRC.*?|Chinese.*?)?[Cc]ertified [Pp]ublic|[Cc]hartered) [Aa]ccountant'
    try:
        return re.search(pattern, txt, flags=re.MULTILINE).group('auditor').strip()
    except AttributeError:
        return None


def remove_noise_by_croping(page, x0=None, x1=None, d=1):
    '''
    read from 2 edges and strink to the middle
    return auditor if found else return None.
    '''
    x0, x1 = (1-d) * float(page.width), d* float(page.width)
    top, bottom = 0, float(page.height)
    c_page = page.crop((x0, top, x1, bottom))
    txt = c_page.extract_text()
    auditor = get_audit_from_txt(txt)
    d-=0.01
    if auditor is None and round(d):
        print(round(d))
        return remove_noise_by_croping(page, x0, x1, d)
    return auditor


from test_cases import unknown_cases, err_cases
if __name__ == "__main__":
    # pattern = r'\n(?!.*?Institute.*?).*?(?P<auditor>.+?)(?:LLP\s*)?\s*((PRC.*?|Chinese.*?)?[Cc]ertified [Pp]ublic|[Cc]hartered) [Aa]ccountants'
    # for url, page_num in noise_cases.items():
    for url, page_num in err_cases.items():
    # url, page_num = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0415/2020041501285.pdf', 147
    # url, page_num = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0428/2020042800976.pdf', 60
    # url, page_num = 'https://www1.hkexnews.hk/listedco/listconews/gem/2019/1031/2019103100067.pdf', 73
        page = get_page(url, page_num)
        txt = page.extract_text()
        # print(txt)
        # print(get_audit_from_txt(txt))
        print(remove_noise_by_croping(page))
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
