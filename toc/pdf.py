from io import BytesIO
from typing import Union, Pattern, Match
from contextlib import contextmanager
from itertools import zip_longest, groupby
from operator import itemgetter
import pandas as pd
import requests
import re
import logging
import os
import time
import pdfplumber
import PyPDF2

def consecutive_int_list(li):
    '''
    helper: return a list of list of consecutive integers
    '''
    
    return [list(map(itemgetter(1), g)) for k, g in groupby(enumerate(li), lambda xi: xi[0]-xi[1])]

def utf8_str(string: str) -> str:
    '''
    helper: ensure string has utf-8 encoding
    '''
    if not isinstance(string, str):
        string = string.decode('utf-8', errors="ignore")
    return re.sub(r'\r|\n|\ufeff', '', string)


def flatten(li: list) -> list:
    '''
    helper: flatten a irregular list recursively;
    for flattening multiple levels of outlines.
    '''
    return sum(map(flatten, li), []) if isinstance(li, list) else [li]


class PDF:
    def __init__(self, src):
        self.src = src
    
    @classmethod
    def create(cls, src):
        src_types = {
           type(src) is str and cls.is_url(src) : lambda: cls.byte_obj_from_url(src),
           type(src) is str and os.path.isfile(src) : lambda: open(src, 'rb'),
           type(src) is not str and cls.is_binary(src): lambda: src
        }
        pdf_obj = src_types.get(True, lambda: None)()
        if pdf_obj and pdf_obj.read().startswith(b'%PDF'):
            return cls(src)
        return None


    @property
    def src(self):
        return self._src

    @src.setter
    def src(self, src):
        self._pdf_obj = self.byte_obj_from_url(src) or src
        self._pb_pdf = pdfplumber.open(self._pdf_obj)
        self._src = src

    @property
    def pdf_obj(self) -> Union[str, object]:
        return self._pdf_obj

    @property
    def pb_pdf(self) -> object:
        return self._pb_pdf

    @property
    def pypdf_reader(self):
        pdf_obj = self.pdf_obj
        if type(pdf_obj) is str and os.path.isfile(pdf_obj):
            pdf_obj = open(src, 'rb')
        return PyPDF2.PdfFileReader(pdf_obj, strict=False)

    @property
    def max_page_num(self):
        pdf = self.pb_pdf
        return len(pdf.pages)
    
    @staticmethod
    def is_binary(obj) -> bool:
        return hasattr(obj ,'read')

    @staticmethod
    def is_url(src: str) -> bool:
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
        return True if re.match(url_regex, src) else False

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

    def get_page(self, p: int):
        pdf = self.pb_pdf
        return Page.create(pdf.pages[p])

    @property
    def outlines(self):
        pypdf_reader = self.pypdf_reader
        outlines = flatten(pypdf_reader.getOutlines())
        
        def get_page_num(outline):
            try:
                return pypdf_reader.getDestinationPageNumber(outline)
            except AttributeError:
                return None
        
        outlines = [outline for outline in outlines if get_page_num(outline)]
        titles = [outline.title for outline in outlines]
        starting_pages = [get_page_num(outline) for outline in outlines]
        ending_pages = [page_num - 1 for page_num in starting_pages[1:]]
        page_ranges = zip_longest(starting_pages, ending_pages, fillvalue=max(starting_pages, default=None))
        return [Outline(title, page_range, self.pb_pdf) for title, page_range in zip(titles, page_ranges)]

    @property
    def toc(self):
        outlines = self.outlines
        outline = [[outline.title, outline.from_page, outline.to_page]
                   for outline in outlines]
        toc = pd.DataFrame(outline, columns=['title', 'from_page', 'to_page'])
        column_types = {'title': str, 'from_page': int, 'to_page': 'Int64'}
        return toc.astype(column_types)

    def get_outline(self, regex: Pattern) -> list:
        '''
        return a list of outline
        '''
        outlines = self.outlines
        if outlines:
            return [outline for outline in outlines if re.search(regex, outline.title, flags=re.IGNORECASE)]
        return self.search_outline(regex)

    def search_outline(self, regex: Pattern, scope=None) -> list:
        pdf = self.pb_pdf
        pages = scope or pdf.pages
        matched_page_nums = []
        for p in pages:
            page = Page.create(p)
            if not page or page.df_feature_text.empty:
                continue
            if any(page.df_feature_text.text.str.contains(regex, flags=re.IGNORECASE)):
                matched_page_nums.append(page.page_number)
            print(f'searching page {page.page_number}...')

        matched_page_num = max(consecutive_int_list(matched_page_nums), key=len, default=None)
        if matched_page_num is None:
            return []
        page_range = min(matched_page_num), max(matched_page_num)
        scope = 'Local' if scope else 'Global'
        return [Outline(f'{scope} search keywords: {regex}', page_range, self.pb_pdf)]

    
    def __repr__(self):
        return f'{self.__class__.__name__}(src="{self.src}")'


class Page:

    def __init__(self, page):
        self.page = page
        self.df_lang = None
        self.remove_noise()

    @classmethod
    def create(cls, page, **kwargs):
        try:
            return cls(page=page, **kwargs)
        except Exception as e:
            print(f'{cls.__name__}({page}, {kwargs}) instance initalise failed: {e}')
            return None

    @property
    def page_number(self) -> int:
        return self.page.page_number - 1

    @property
    def text(self) -> str:
        txt = self.page.extract_text()
        txt = txt.replace('ﬁ', 'fi')  # must clean before chinese
        txt = re.sub(r'\ufeff', ' ', txt)  # clear BOM
        return txt

    @property
    def df_char(self) -> pd.DataFrame:
        df = pd.DataFrame(self.page.chars)
        df_langs = {
            'en': df[~df['text'].str.contains(r'[^\x00-\x7F]+')],
            'cn': df[df['text'].str.contains(r'[^\x00-\x7F]+')]
        }
        return df_langs.get(self.df_lang, df)

    @property
    def df_decarative_text(self) -> pd.DataFrame:
        df_char = self.df_char
        return df_char[df_char['upright'] == 0]

    @property
    def df_main_text(self) -> pd.DataFrame:
        df_char = self.df_char
        is_main_fontname = df_char['fontname'].isin(self.main_fontname)
        is_main_fontsize = df_char['size'].isin(self.main_fontsize)
        is_upright = df_char['upright'] == 1
        mt_df = df_char[is_main_fontname & is_main_fontsize & is_upright]
        return mt_df

    @property
    def df_feature_text(self) -> pd.DataFrame:
        self.df_lang = 'en'
        df_ft = self.df_char[~self.df_char['fontname'].isin(self.main_fontname)]
        df_feature_text = df_ft.groupby(['top', 'bottom', 'fontname', 'size']).agg(
            {'x0': 'min', 'x1': 'max', 'text': lambda x: ''.join(x)}).reset_index()
        if df_feature_text.empty:
            return df_feature_text
        df_feature_text = df_feature_text[df_feature_text.text.str.contains(r'\w+')]
        self.df_lang = None
        return df_feature_text

    @property
    def df_bold_text(self) -> pd.DataFrame:
        df_feature_text = self.df_feature_text
        df_bt = df_feature_text[df_feature_text['size'].isin(
            self.main_fontsize)]
        df_bold_text = df_bt.groupby(['top', 'bottom', 'fontname', 'size']).agg(
            {'x0': 'min', 'x1': 'max', 'text': lambda x: ''.join(x)}).reset_index()
        return df_bold_text

    @property
    def df_title_text(self) -> pd.DataFrame:
        df_feature_text = self.df_feature_text
        df_tt = df_feature_text[df_feature_text['size'] > self.main_fontsize.max()]
        df_title_text = df_tt.groupby(['top', 'bottom', 'fontname', 'size']).agg(
            {'x0': 'min', 'x1': 'max', 'text': lambda x: ''.join(x)}).reset_index()
        if df_title_text.empty:
            return self.df_bold_text
        return df_title_text

    @property
    def df_section_text(self) -> pd.DataFrame:
        df = self.df_title_text
        title_interval = df['bottom'].shift() - df['top']
        indicator = (title_interval.abs() > df['size']).cumsum()
        df_section_text = df.groupby(indicator).agg({
            'top': 'first',
            'bottom': 'last',
            'fontname': 'first',
            'size': 'first',
            'x0': 'first',
            'x1': 'first',
            'text': ''.join
        })
        df_section_text['next_top'] = df_section_text.top.shift(-1)
        df_section_text.fillna(self.bbox_main_text[-1], inplace=True)
        return df_section_text

    @property
    def main_fontname(self) -> pd.Series:  # should i only care about english?
        return self.df_char['fontname'].mode()

    @property
    def main_fontsize(self) -> pd.Series:
        df_char = self.df_char
        return df_char[df_char['fontname'].isin(self.main_fontname)]['size'].mode()

    @property
    def bbox_main_text(self) -> tuple:

        def bbox(self, lang):
            self.df_lang = lang
            if self.df_main_text.empty:
                return None
            df_main_text = self.df_main_text
            x0, top = df_main_text[['x0', 'top']].min()
            x1, bottom = df_main_text[['x1', 'bottom']].max()
            # print(lang, x0, top, x1, bottom)

            top = [top]
            top.append(self.df_feature_text.top.min())
            top = [t if t >= 0 else 0 for t in top]

            x1 = [x1]
            x1.append(self.df_feature_text.x1.max())

            self.df_lang = None
            return x0, min(top), max(x1), bottom

        en_bbx, cn_bbx = bbox(self, 'en'), bbox(self, 'cn')

        if cn_bbx is None:
            return en_bbx
        x0, top, x1, bottom = zip(en_bbx, cn_bbx)

        return min(x0), min(top), max(x1), max(bottom)

    @property
    def col_division(self) -> float:
        min_x0 = self.df_title_text.x0.min()
        max_x0 = self.df_title_text.x0.max()
        if min_x0 != max_x0:
            print(f'There is another colmun divided at {float(max_x0)}.')
            return max_x0
        return None

    @property
    def left_column(self) -> object:
        col_division = self.col_division
        if col_division is None:
            return None
        x0, top, x1, bottom = self.bbox_main_text
        l_bbx = x0, top, col_division, bottom
        left_col = self.page.within_bbox(l_bbx, relative=False)
        return Section.create(left_col, title='Left Column')

    @property
    def right_column(self) -> object:
        col_division = self.col_division
        if col_division is None:
            return None
        x0, top, x1, bottom = self.bbox_main_text
        r_bbx = col_division, top, x1, bottom
        right_col = self.page.within_bbox(r_bbx, relative=False)
        return Section.create(right_col, title='Right Column')

    @property
    def sections(self):
        df_section_text = self.df_section_text

        def section_bbx(self, section):
            x0, top, x1, bottom = self.bbox_main_text
            return x0, section.top, x1, section.next_top

        sections = []
        for sec in df_section_text.itertuples(index=False):
            sec_bbx = section_bbx(self, sec)
            section = self.page.within_bbox(sec_bbx, relative=False)
            section = Section.create(section, title=sec.text)
            # section = self.create_section(sec_bbx, title = sec.text)
            if section:
                sections.append(section)
        return sections

    def remove_noise(self) -> None:
        page = self.page.crop(self.bbox_main_text, relative=False)
        self.page = page

    def search(self, regex: Pattern) -> Union[Match, None]:
        return re.search(regex, self.text, flags=re.IGNORECASE | re.DOTALL)

    def get_section(self, regex: Pattern) -> list:
        sections = self.sections
        return [section for section in sections if re.match(regex, section.title, flags=re.IGNORECASE)]

    def create_section(self, sec_bbx, title=None, relative=False):
        sec = self.page.within_bbox(sec_bbx, relative=relative)
        return Section.create(sec, title=title)

    def divide_into_two_cols(self, d=0.5, relative=True):
        l0, l1 = 0 * float(self.page.width), d * float(self.page.width)
        r0, r1 = d * float(self.page.width), 1 * float(self.page.width)
        top, bottom = 0, float(self.page.height)
        l_bbx = (l0, top, l1, bottom)
        r_bbx = (r0, top, r1, bottom)

        left_col = self.create_section(
            self, l_bbx, title='Left Column', relative=relative)
        right_col = self.create_section(
            self, r_bbx, title='Right Column', relative=relative)
        return left_col, right_col

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.page_number}>'


class Section(Page):
    def __init__(self, page, title=None):
        super().__init__(page)
        self.title = title

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.title}>'

# class Outlines(Outline):
#     def __init__(self, pypdf_reader):
#         self.pypdf_reader = pypdf_reader

#     @property
#     def outlines(self):
#         return flatten(self.pypdf_reader.getOutlines())

class Outline:
    def __init__(self, title, page_range, pb_pdf):
        self.title = title
        self.page_range = page_range
        self.pb_pdf = pb_pdf

    @property
    def pages(self):
        page_range = self.page_range
        pb_pdf = self.pb_pdf
        return [Page.create(pb_pdf.pages[p]) for p in page_range]

    @property
    def page_range(self):
        from_page, to_page = self.from_page, self.to_page
        if from_page and to_page:
            return range(from_page, to_page + 1)
        return []

    @page_range.setter
    def page_range(self, page_range):
        if type(page_range) is not tuple:
            raise TypeError(f'page_range type {type(page_range)} is not tuple')
        self._page_range = page_range

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = utf8_str(title).capitalize()

    @property
    def from_page(self):
        return self._page_range[0]

    @property
    def to_page(self):
        return self._page_range[-1]

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.title} {self.from_page} - {self.to_page}>'


class IndependentAuditorReport:

    title_regex = r'^(?!.*internal)(?=.*report|responsibilities).*auditor.*$'
    auditor_regex = r'\n(?!.*?(Institute|Responsibilities).*?).*?(?P<auditor>.{4,}\S|[A-Z]{4})(?:LLP\s*)?\s*((PRC\s*?|Chinese\s*?)?Certified\s*Public|Chartered)\s*Accountants*'

    def __init__(self, outline):
        self.outline = outline
    
    @classmethod
    def create(cls, outline):
        fail_conditions = {
            isinstance(outline, Outline) is False: lambda: TypeError,
            not outline.pages: lambda: ValueError,
            re.search(IndependentAuditorReport.title_regex, outline.title, flags=re.IGNORECASE) is None: lambda: ValueError,
        }
        create_failed = fail_conditions.get(True, default=False)
        if create_failed:
            raise create_failed('Failed to initialise IndependentAuditorReport')
        return cls(outline)
    
    @property
    def outline(self):
        return self._outline
    
    @property
    def pages(self):
        return self._pages
    
    @outline.setter
    def outline(self, outline):
        self._outline = outline
        self._pages = outline.pages
    
    @property
    def auditor(self) -> list:
        pages = self.pages
        last_page = pages[-1]
        cols = [last_page.left_column, last_page.right_column]
        cols_results = [col.search(IndependentAuditorReport.auditor_regex) for col in cols if any(cols)]
        page_results = [last_page.search(IndependentAuditorReport.auditor_regex)]
        if any(cols_results) or any(page_results):
            results = cols_results + page_results
            return {result.group('auditor') for result in results if result}
        return None
    


                



    # @property
    # def auditor(self):
    #     pages = self.pages
    #     if pages:
    #         last_page = pages[-1]
    #         return last_page.search(IndependentAuditorReport.auditor_regex)
    #     self._pages = self.feature_text_g_search(IndependentAuditorReport.outline_regex)
    #     pages = self.pages
    #     return [page.search().group('auditor') for page in pages]

    @property
    def kams(self):
        pass


if __name__ == "__main__":
    from os import sys, path, getpid
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from api.get_data import HKEX_API
    from helper import over_a_year, yesterday, today, n_yearsago
    # import multiprocessing as mp
    import concurrent.futures 
    import time
    start = time.perf_counter()

    # query = HKEX_API(from_date=n_yearsago(n=1), to_date=today())
    url = 'https://www1.hkexnews.hk/listedco/listconews/gem/2020/0828/2020082802897.pdf'
    pdf = PDF.create(url)
    audit_report_outline = pdf.get_outline(IndependentAuditorReport.title_regex)
    audit_report = IndependentAuditorReport.create(audit_report_outline)
    print(audit_report.auditor)
    # with open('empty_toc.txt', 'r') as f:
    #     urls = f.readlines()
    
    # def get_outline(url):
    #     url = url.replace('\n', '')
    #     print(getpid(), url)
    #     pdf = PDF.create(src=url)
    #     result = pdf.get_outline(r'audit')
    #     with open('test.txt', 'a') as f:
    #         f.write(f'{result}, {url}\n')
    
    # with concurrent.futures.ProcessPoolExecutor() as executor:
        # print([i for i in executor.map(get_outline, urls)])
        # executor.map(get_outline, urls)
        # futures = [executor.submit(get_outline, url) for url in urls]
        # for future in concurrent.futures.as_completed(futures):
        #     result = future.result()
        #     results.append(result)
    # print(results)
    # for r in results:
    #     print(r)
    # print(f'results: {results}')
    end = time.perf_counter()
    print(f'Finished in {round(end - start, 2)}sec')
        #     # print('finish mapping..')



    # for data in query.get_data():
    #     url = data.file_link
    #     print(url)
    #     pdf = PDF.create(src=url)
    #     if pdf is None:
    #         continue
    #     toc = pdf.toc
    #     print(toc)
    #     if toc.empty:
    #         with open('empty_toc.txt', 'a') as f:
    #             f.write(f'{url}\n')
            
    
    # logging.basicConfig(level=logging.DEBUG)
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0424/2020042401194.pdf', 10
    # nocol, parse wrong, hk$000
    # slow..
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0717/2020071700849.pdf', 90
    # url , p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2019/1028/ltn20191028063.pdf', 20 # 2cols, correct!!
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0823/2020082300051.pdf', 73
    # url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0731/2020073101878.pdf'
    # url, p  = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0428/2020042801961.pdf', 62
    # url = 'https://www1.hkexnews.hk/listedco/listconews/gem/2020/0828/2020082802897.pdf'  # empty.toc
    # url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0730/2020073000624.pdf'
    # local_path = '/Users/macone/Documents/cs_project/toc/2020073000624.pdf'
    # pdf = PDF.create(local_path)
    # pdf_obj = PDF.byte_obj_from_url(url)
    # pdf = PDF.create(pdf_obj)
    # print(pdf.max_page_num)
    # pdf_obj = PDF.byte_obj_from_url(url)
    # pdf = PDF(pdf_obj)
    # pdf = PDF(url)
    # print(pdf.toc)
    # page = pdf.get_page(7)
    # print(page.df_feature_text.text.str.contains(r'audit'))
    # print(pdf.search_outline(r'audit'))
    # print(pdf.get_outline(r'audit'))
    # print(pdf.toc)
    # print(pdf.outlines[5].pages)
    # print(pdf.get_outline(r'audit')[0].pages[-1].text)
    # print(pdf.pages[22])

    # print(pdf.toc)
    # print(pdf.pdf_obj)
    # print(pdf.src)
    # page = pdf.get_page(p)
    # page.df_lang = 'cn'
    # print(page.df_decarative_text)
    # print(page.bbox_main_text)
    # page.remove_noise()
    # print(page.text)
    # print(page.df_main_text[['fontname','size']])
    # print(page.df_feature_text)
    # print(page.df_title_text)
    # print(page.df_section_text)
    # print(page.sections)
    # page.remove_noise()
    # page.remove_noise()
    # page.remove_noise()
    # page.remove_noise()
    # page.left_column.remove_noise()
    # print(page.left_column.text)
    # print(page.right_column.text)
    # for section in page.sections:
    #     print(section.text)
