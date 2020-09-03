import pandas as pd
from pdf import PDF
from toc import TableOfContent
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from get_pdf import _by_pdfplumber
from helper import turn_n_page, is_landscape, is_full_cn, abnormal_page
from helper import search_pattern_from_page_or_cols, validate_auditor
import logging, datetime

class AuditReport(TableOfContent):
    
    title_regex = r'^(?!.*internal)(?=.*report|responsibilities).*auditor.*$'
    auditor_regex = r'\n(?!.*?(Institute|Responsibilities).*?).*?(?P<auditor>.{4,}\S|[A-Z]{4})(?:LLP\s*)?\s*((PRC\s*?|Chinese\s*?)?Certified\s*Public|Chartered)\s*Accountants*'
    validation_src = 'valid_auditors.csv'
    
    def __init__(self, pdf_obj):
        super().__init__(pdf_obj)
    
    @property
    def page_range(self):
        pages = super().search_outline_page_range(pattern=AuditReport.title_regex)
        return pages
    
    
    @property
    def auditor(self):
        return self.valid_auditor() or self.raw_auditor()
    
    def raw_auditor(self):
        with _by_pdfplumber(self.pdf_obj) as pdf:
            auditor_report_last_pages = [pdf.pages[page_nums[-1]] for page_nums in self.page_range]
            search_results = [search_pattern_from_page_or_cols(page=page, pattern=AuditReport.auditor_regex) for page in auditor_report_last_pages]

            if not any(search_results) and any(map(abnormal_page, auditor_report_last_pages)):
                auditor_report_last_pages = [turn_n_page(pdf, page, 2) if is_landscape(page) else turn_n_page(pdf, page, -1) if is_full_cn(page) else page for page in auditor_report_last_pages]
                search_results = [search_pattern_from_page_or_cols(page=page, pattern=AuditReport.auditor_regex) for page in auditor_report_last_pages]

            auditors = set()
    
            for result in filter(None, search_results):
                if type(result) is tuple:
                    for r in filter(None, result):
                        auditors.add(r.group('auditor'))
                else:
                    auditors.add(result.group('auditor'))
            return tuple(auditors)
    
    def valid_auditor(self, src: str = None, min_similarity: float = 90.0):
        '''
        vaildate auditor with database/local csvfile with column valid_auditor
        return the default auditor name if the pair is over the min_similarity
        '''
        
        if src is None:
            src = self.validation_src
        
        v_auditors = pd.read_csv(src).valid_auditor.values
        r_auditors = self.raw_auditor()
        result = [validate_auditor(r_auditor, v_auditors, min_similarity) for r_auditor in r_auditors]
        return tuple(filter(None, result))
    
    @property
    def audit_fee(self):
        pass


    @property
    def kam(self):
        pass

class AuditFee(TableOfContent):
    corporate_gov_report_regex = r'^(?=.*report).*corporate governance.*$'
    # audit_fee_regex = r"AUDIT.*?REMUNERATION|(external|independent|accountability).*auditor"
    audit_fee_regex = r"^(?!.*Nomination|.*Report)(?=.*REMUNERATION|.*independent|.*external|.*Accountability).*auditor.*$"
    currency_regex = r'(?P<currency>^[A-Za-z]{2,3})(?P<unit>(\W0{0,3})*$)'
    currency_amount_regex = r'(?P<amount>^\d{1,3}(\W\d{3})*$)'
    # in_text_currency_amount_regex = r'(?P<amount>^\D{2,3}\d{1,3}(\W\d{3})*$)'
    # Accountability and audit
    
    def __init__(self, pdf_obj):
        super().__init__(pdf_obj)
    
    @property
    def page_range(self):
        return super().search_outline_page_range(pattern=AuditFee.corporate_gov_report_regex)
    
    @property
    def audit_fee_page(self):
        page_range = self.flatten_tuple(self.page_range)
        audit_fee_page, self.matched_pattern = super().search_outline_in_pages(
            pattern=AuditFee.audit_fee_regex,
            page_range=page_range,
            verbose=True,
            show_matched=True
            )
        target_pages = self.flatten_tuple(audit_fee_page)
        return target_pages
    
    @property
    def section_txt(self):
        txt = []
        for p in self.audit_fee_page:
            section = self.target_section(p)
            # return section.extract_text())
            print(section.extract_text())
            txt.append(section.extract_text())
            return txt
    
    @property
    def section_tables(self):
        tables = []
        for p in self.audit_fee_page:
            section = self.target_section(p)
            tables.append(self.get_table_from_section(section))
        return tables
        

    @staticmethod    
    def get_table_co_idx(table:list):
    
        currency_cell = lambda cell: re.match(AuditFee.currency_regex, cell)
        amount_cell = lambda cell: re.match(AuditFee.currency_amount_regex, cell)
        currency_idx = {idx for row in table for idx, cell in enumerate(row) if currency_cell(cell)}
        amount_idx = {idx for row in table for idx, cell in enumerate(row) if amount_cell(cell)}
        # print(currency_idx, amount_idx)
        co_idx = currency_idx.intersection(amount_idx)
    
        return co_idx

    @staticmethod
    def get_table_from_section(section:object):
        
        table_setting = {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            }
        
        raw_table = section.extract_table(table_setting)
        row_len = len(raw_table[0])
        current_yr = int(datetime.datetime.now().year)
        yr_range = range(current_yr - 1, current_yr + 1)
        
        
        year_cell = lambda cell: cell in [str(yr) for yr in yr_range]
        currency_cell = lambda cell: re.match(AuditFee.currency_regex, cell)
        amount_cell = lambda cell: re.match(AuditFee.currency_amount_regex, cell)
        
        table = [
            row 
            for row in raw_table 
            if any(map(year_cell, row))
            or any(map(currency_cell, row)) 
            or any(map(amount_cell, row))
            ]
        
        in_text_pattern = lambda cell: re.match(AuditFee.in_text_currency_amount_regex, cell)
        currency_idx = {idx for row in table for idx, cell in enumerate(row) if currency_cell(cell)}
        amount_idx = {idx for row in table for idx, cell in enumerate(row) if amount_cell(cell)}
        
        co_idx = currency_idx.intersection(amount_idx)
        
        last_two_idx = set(range(row_len - 2, row_len))
        if not co_idx.intersection(last_two_idx):
            return None
        
        for row in table:
            col = [row[idx] for idx in co_idx ]
            if map(currency_cell, [col[0]]):
                if not all(map(amount_cell, col[1:])):
                    return None
            elif map(year_cell, [col[0]]):
                if not all(map(amount_cell, col[2:])): #consider '-' case
                    return None
        
        return table 



    def target_section(self, p):
        
        with _by_pdfplumber(self.pdf_obj) as pdf:
            page = pdf.pages[p]
            df = pd.DataFrame(page.chars)
            df = df[~df.text.str.contains(r'[^\x00-\x7F]+')]
            
            x0, x1 = 0, float(page.width)
            target_top = float(self.target_top(df))
            target_bottom = self.target_bottom(df) or page.height
            
            section = page.crop((x0, target_top , x1, float(target_bottom)), relative=True)
            
            return section


    def target_top(self, df):
        main_fontsizes = df['fontname'].mode()
        t_df = df[~df['fontname'].isin(main_fontsizes)]
        t_df = t_df.groupby(['top', 'bottom', 'fontname' , 'size'])['text'].apply(''.join).reset_index()
        target_top = t_df[t_df.text.str.contains(AuditFee.audit_fee_regex, flags=re.IGNORECASE)]['top'].values[0]
        return target_top

    
    def target_bottom(self, df):
        main_fontsizes = df['size'].mode()
        b_df = df[~df['size'].isin(main_fontsizes)]
        b_df = b_df.groupby(['top', 'bottom'])['text'].apply(''.join).reset_index()
        condition = (b_df.top > self.target_top(df)) & (b_df.text.str.contains(r'\w+')) & (~b_df.text.str.contains(r'REMUNERATION', flags=re.IGNORECASE)) 
        # print(b_df)
        # print(self.target_top(df))
        
        try:
            next_title = b_df[condition].head(1)
            # print(next_title)
            target_bottom = next_title.top.values[0]
        except IndexError as e:
            logging.warning(f'No next title, see error: {e}')
            return None
        return target_bottom


    @staticmethod
    def flatten_tuple(list_of_tuple) -> tuple:
        return sum(list_of_tuple, ())

    
    def test(self):
        from helper import write_to_csv
        
        # result = {}
        # result['report_page_range'] = self.page_range
        # result['f.audit_fee_page'] = self.audit_fee_page
        # result['f.matched_pattern'] = self.matched_pattern
        # result['url'] = url
        # write_to_csv(result, 'result_3.csv')
        
        try:
            result = {}
            # result['report_page_range'] = self.page_range
            # result['f.audit_fee_page'] = self.audit_fee_page
            # result['f.matched_pattern'] = self.matched_pattern
            # result['url'] = url
            result['txt'] = self.section_txt
            result['url'] = url
            write_to_csv(result, 'result_3.csv')
        
        except Exception as e:
            # result['report_page_range'] = 'ERROR'
            result['txt'] = 'ERROR'
            # result['f.audit_fee_page'] = e
            result['url'] = url
            write_to_csv(result, 'result_3.csv')


    





if __name__ == "__main__":
    import get_pdf, re
    from test_cases import test_cases
    from get_data import HKEX_API
    from helper import write_to_csv, n_yearsago, today
    from helper import get_title_liked_txt, search_pattern_from_txt
    from get_pdf import _by_pdfplumber

    # # logging.basicConfig(level=logging.INFO)
    # query = HKEX_API(from_date=n_yearsago(n=1), to_date=today())
    # for data in query.data:
        
    #     url = data.file_link
    #     pdf = PDF(url)
    #     print(pdf.src)
    #     f = AuditFee(pdf.pdf_obj)
    #     f.test()
    

    url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0731/2020073101878.pdf', 40 # wrong number row
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/gem/2020/0831/2020083100445.pdf',33 # text
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0729/2020072900505.pdf', 40 # normal
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0730/2020073000620.pdf', 24 # normal
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0728/2020072800460.pdf', 104 # normal
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0730/2020073000009.pdf', 76 # normal, with years
    
    pdf = PDF(url)
    pdf_obj = pdf.pdf_obj
    f = AuditFee(pdf_obj)
    p = f.audit_fee_page[0]
    section = f.target_section(p)
    table = f.get_table_from_section(section)
    # txt = f.section_txt
    print(table)
    # print(txt[0])
    # for row in table:
    #     print(row[1])
    # print(f.get_table_co_idx(table))
    # with _by_pdfplumber( pdf.pdf_obj) as pdf:
    #     page = pdf.pages[p]
    #     # print(page.extract_text())
    #     df = pd.DataFrame(page.chars)
    #     # df['text'] = df['text'].replace(r'[^\x00-\x7F]+', '')
    #     df = df[~df.text.str.contains(r'[^\x00-\x7F]+')]
    #     # print(df)
    #     main_fontsizes = df['fontname'].mode()
    #     t_df = df[~df['fontname'].isin(main_fontsizes)]
    #     t_df = t_df.groupby(['top', 'bottom', 'fontname' , 'size'])['text'].apply(''.join).reset_index()
    #     print(t_df)
    #     target_top = t_df[t_df.text.str.contains(AuditFee.audit_fee_regex, flags=re.IGNORECASE)]['top'].values[0]
    #     print(target_top)
    #     main_fontsizes = df['size'].mode()
    #     b_df = df[~df['size'].isin(main_fontsizes)]
    #     b_df = b_df.groupby(['top', 'bottom'])['text'].apply(''.join).reset_index()
    #     condition = (b_df.top > target_top) & (b_df.text.str.contains(r'\w+')) & (~b_df.text.str.contains(r'REMUNERATION', flags=re.IGNORECASE)) 
    #     next_title = b_df[condition].head(1)
    #     print(next_title)
    #     target_bottom = next_title.top.values[0]
    #     x0, x1 = 0, float(page.width)
    #     page = page.crop((x0, float(target_top), x1, float(target_bottom)), relative=True)
    #     print(page.extract_text())


        
    #     setting = {
    #         "vertical_strategy": "text",
    #         "horizontal_strategy": "text",
    #         }

    #     # print(page.extract_table(setting))
    #     table = [li for li in page.extract_table(setting) if re.match(r'.*?\d+|^.{3,4}(\d{3})?$', li[-1])]
    #     for r in table :
    #         print(r)

# import pandas as pd
# from io import BytesIO
# import pdfplumber, requests
# url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0731/2020073101878.pdf', 40
# url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0813/2020081300777.pdf', 28
# url, p  = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0724/2020072400731.pdf', 69

# with requests.get(url) as response:
#         response.raise_for_status()
#         byte_obj = BytesIO(response.content)
# pdf = pdfplumber.open(byte_obj)
# page = pdf.pages[p]
# print(page.extract_text()) #(^.{2,4}\d{0,3})\s*[^\x00-\x7F]*$|([,\d]+$)
# df = pd.DataFrame(page.chars)
# df = df[~df.text.str.contains(r'[^\x00-\x7F]+')]
# main_fontsizes = df['size'].mode()
# df = df[~df['size'].isin(main_fontsizes)]
# df = df.groupby(['top', 'bottom'])['text'].apply(''.join).reset_index()
# print(df.text)
# target_top = df[df.text.str.contains(r'AUDITORS REMUNERATION', flags=re.IGNORECASE)]['top'].values[0]
# condition = (df.top > target_top) & (df.text.str.contains(r'\w+'))
# next_title = df[condition].head(1)
# target_bottom = next_title.top.values[0]
# x0, x1 = 0, float(page.width)
# page = page.crop((x0, float(target_top), x1, float(target_bottom)), relative=True)
# print(page.extract_text()) #(^.{2,4}\d{0,3})\s*[^\x00-\x7F]*$|([,\d]+$)
# r'(?P<currency>^.{2,4}\d{0,3})\s*[^\x00-\x7F]*$|^[A-Za-z\s]*?(?P<amount>\d+,*[,\d]*)'
# print('====')
# setting = {
#             "vertical_strategy": "text",
#             "horizontal_strategy": "text",
# }

# for li in page.extract_table(setting):
#     if re.match(r'.*?\d+|^.{3,4}(\d{3})?$', li[-1]):
#         print(''.join(li[:-1]), "|",li[-1])