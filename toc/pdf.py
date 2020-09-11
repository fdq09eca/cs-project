from io import BytesIO
from typing import Union, Pattern, Match
from contextlib import contextmanager
import pandas as pd
import requests
import re
import logging
import pdfplumber


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
    def is_url(src: str) -> Match[str]:
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

    def get_page(self, p: int):
        pdf = pdfplumber.open(self.pdf_obj)
        return Page.create(pdf.pages[p])

    @staticmethod
    def crop_page(page: object, bbox: tuple):
        if not isinstance(page, pdfplumber.page.Page):
            raise TypeError('page is not pdfplumber.page.Page')
        return page.crop(bbox, relative=True)

    @staticmethod
    def get_text(page):
        if not isinstance(page, pdfplumber.page.Page):
            raise TypeError('page is not pdfplumber.page.Page')
        return page.extract_text()

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
        df_ft = self.df_char[~self.df_char['fontname'].isin(
            self.main_fontname)]
        df_feature_text = df_ft.groupby(['top', 'bottom', 'fontname', 'size']).agg(
            {'x0': 'min', 'x1': 'max', 'text': lambda x: ''.join(x)}).reset_index()
        df_feature_text = df_feature_text[df_feature_text.text.str.contains(
            r'\w+')]
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
        df_tt = df_feature_text[df_feature_text['size']
                                > self.main_fontsize.max()]
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

            self.df_lang = None
            return x0, min(top), x1, bottom

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
        '''
        return a list of section instance
        '''
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
        '''
        return a list of Section that matches with the regex
        '''
        sections = self.sections
        return [section for section in sections if re.match(regex, section.title, flags=re.IGNORECASE)]

    def create_section(self, sec_bbx, title=None, relative=False):
        col = self.page.within_bbox(sec_bbx, relative=relative)
        return Section.create(col, title=title)

    def divide_into_two_cols(self, d=0.5, relative=True):
        l0, l1 = 0 * float(self.page.width), d * float(self.page.width)
        r0, r1 = d * float(self.page.width), 1 * float(self.page.width)
        top, bottom = 0, float(self.page.height)
        l_bbx = (l0, top, l1, bottom)
        r_bbx = (r0, top, r1, bottom)

        left_col = self.create_section(
            self, l_bbx, title='Left Column', relative=relative)
        right_col = self.create_section(
            self, r_bbx, title='Left Column', relative=relative)
        return left_col, right_col


class Section(Page):
    def __init__(self, page, title=None):
        super().__init__(page)
        self.title = title

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.title}>'


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0424/2020042401194.pdf', 10
    # nocol, parse wrong, hk$000
    url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0717/2020071700849.pdf', 90
    # url , p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2019/1028/ltn20191028063.pdf', 20 # 2cols, correct!!
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0823/2020082300051.pdf', 73

    pdf_obj = PDF.byte_obj_from_url(url)
    pdf = PDF(pdf_obj)
    print(pdf.pdf_obj)
    print(pdf.src)
    page = pdf.get_page(p)
    # page.df_lang = 'cn'
    # print(page.df_decarative_text)
    # print(page.bbox_main_text)
    # page.remove_noise()
    # print(page.text)
    # print(page.df_main_text[['fontname','size']])
    # print(page.df_feature_text)
    # print(page.df_title_text)
    # print(page.df_section_text)
    print(page.sections)
    # page.remove_noise()
    # page.remove_noise()
    # page.remove_noise()
    # page.remove_noise()
    # page.left_column.remove_noise()
    # print(page.left_column.text)
    # print(page.right_column.text)
    # for section in page.sections:
    #     print(section.text)
