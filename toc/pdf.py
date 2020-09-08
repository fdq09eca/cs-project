from io import BytesIO
from typing import Union, Pattern, Match
from contextlib import contextmanager
import pandas as pd
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

    def get_page(self, p:int):
        pdf =  pdfplumber.open(self.pdf_obj)
        return Page(pdf.pages[p])
    

    @staticmethod
    def crop_page(page:object, bbox:tuple):
        if not isinstance(page, pdfplumber.page.Page):
            raise TypeError('page is not pdfplumber.page.Page')
        return page.crop(bbox, relative = True)
    

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
        self.left_col = None
        self.right_col = None
    
    @property
    def page_number(self) -> int:
        return self.page.page_number - 1
    
    @property
    def text(self) -> str:
        txt = self.page.extract_text()
        txt = txt.replace('ﬁ', 'fi') # must clean before chinese
        txt = re.sub(r'\ufeff', ' ', txt)  # clear BOM
        return txt
    
    @property
    def en_text(self) -> str:
        return re.sub(r"([^\x00-\x7F])+", "", self.text)
    
    @property
    def cn_text(self) -> str:
        return re.sub(r"([\x00-\x7F])+", "", self.text)
    
    # @property 
    # def feature_text(self):
    #     pass
    
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
        return self.df_char[self.df_char.upright == 0]


    @property
    def main_fontname(self) -> pd.Series:
        return self.df_char['fontname'].mode()
    
    @property
    def main_fontsize(self) -> pd.Series:
        return self.df_char[self.df_char['fontname'].isin(self.main_fontname)]['size'].mode()
    
    @property
    def df_main_text(self) -> pd.DataFrame:
        is_main_fontname = self.df_char['fontname'].isin(self.main_fontname)
        is_main_fontsize = self.df_char['size'].isin(self.main_fontsize)
        is_upright = self.df_char['upright'] == 1
        mt_df = self.df_char[is_main_fontname & is_main_fontsize & is_upright]
        return mt_df
    
    @property
    def df_feature_text(self) -> pd.DataFrame:
        self.df_lang = 'en'
        c_df = self.df_char[~self.df_char['fontname'].isin(self.main_fontname)]
        ft_df = c_df.groupby(['top', 'bottom', 'fontname' , 'size']).agg({'x0':'min','x1':'max', 'text': lambda x: ''.join(x)}).reset_index()
        self.df_lang = None
        return ft_df
    
    @property
    def df_title_text(self) -> pd.DataFrame:
        # self.df_lang = 'en'
        c_df = self.df_feature_text[self.df_feature_text['size'] >= self.main_fontsize.max()]
        tt_df = c_df.groupby(['top', 'bottom', 'fontname' , 'size']).agg({'x0':'min','x1':'max', 'text': lambda x: ''.join(x)}).reset_index()
        # self.df_lang = None
        return tt_df
    
    @property
    def bbox_main_text(self) -> tuple:
        
        def bbox(self, lang):
            self.df_lang = lang
            if self.df_main_text.empty:
                return None
            x0, top = self.df_main_text[['x0','top']].min()
            x1, bottom = self.df_main_text[['x1','bottom']].max()
            self.df_lang = None
            print(lang, x0, top, x1, bottom)
            return x0, top, x1, bottom
        
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
            print(f'There is another colmun divide at {float(max_x0)}.')
            return max_x0
        return None
    
    @property
    def bbox_left_column(self) -> float:
        col_division = self.col_division
        if col_division is None:
            return None
        x0, top, x1, bottom = self.bbox_main_text
        return x0, top, col_division, bottom
    
    @property
    def bbox_right_column(self) -> float:
        col_division = self.col_division
        if col_division is None:
            return None
        x0, top, x1, bottom = self.bbox_main_text
        return col_division, top, x1, bottom

    @property
    def left_column(self) -> object:
        l_bbx = self.bbox_left_column
        left_col = self.page.within_bbox(l_bbx, relative = False)
        return self.__class__(left_col)
    
    @property
    def right_column(self) -> object:
        r_bbx = self.bbox_right_column
        right_col = self.page.within_bbox(r_bbx, relative = False)
        return self.__class__(right_col)
    
    @property
    def is_landscape(self) -> bool:
        return self.page.width > self.page.height
    
    @property
    def is_full_cn(self) -> bool:
        txt = re.sub("\n+|\s+", "", self.text)
        cn_to_txt_ratio = len(self.cn_text)/len(txt)
        return cn_to_txt_ratio > 0.85
    
    def remove_noise(self) -> None:
        page = self.page.crop(self.bbox_main_text, relative=True)
        self.page = page

    def search(self, regex:Pattern) -> Union[Match, None]:
        return re.search(regex, self.text, flags=re.IGNORECASE|re.DOTALL)

        
    def get_section(self, regex:Pattern):
        pass
        # self.df_feature_text.str.contains(regex, flags=re.IGNORECASE)

    def divide_into_two_cols(self, d=0.5):
        l0, l1 = 0 * float(self.page.width), d * float(self.page.width)
        r0, r1 = d * float(self.page.width), 1 * float(self.page.width)
        top, bottom = 0, float(self.page.height)
        l_bbx = (l0, top, l1, bottom)
        r_bbx = (r0, top, r1, bottom)
        left_col = self.page.within_bbox(l_bbx, relative = True)
        right_col = self.page.within_bbox(r_bbx, relative = True)
        return self.__class__(left_col), self.__class__(right_col)
    

    



if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0424/2020042401194.pdf', 10
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0717/2020071700849.pdf', 90
    url , p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2019/1028/ltn20191028063.pdf', 20

    pdf_obj = PDF.byte_obj_from_url(url)
    pdf = PDF(pdf_obj)
    print(pdf.pdf_obj)
    print(pdf.src)
    page = pdf.get_page(p)
    # page.df_lang = 'cn'
    # print(page.df_decarative_text)
    # print(page.bbox_main_text)
    page.remove_noise()
    # print(page.text)

    print(page.df_title_text)
    # print(page.df_feature_text)
    # print(page.main_fontsize)
    print(page.left_column.text)
    print(page.right_column.text)
    # print(page.feature_text_x0s)
    


    # pdf = PDF(url)
    # print(pdf.pdf_obj)
    # print(pdf.pdf_obj)
    # pdf.src = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0802/2020080200033.pdf'
    # print(pdf.pdf_obj)
    # print(pdf.pdf_obj)
    # print(pdf)
