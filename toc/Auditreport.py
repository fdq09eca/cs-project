import pandas as pd
from pdf import PDF
from toc import TableOfContent
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from get_pdf import _by_pdfplumber
from helper import turn_n_page, is_landscape, is_full_cn, abnormal_page, flatten
from helper import search_pattern_from_page_or_cols, validate_auditor
from itertools import combinations
import logging, datetime, pdfplumber

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
    # currency_regex = r'(?P<currency>^[(]*[HK$USDRMB]{2,3})(?P<unit>((\W?0{3})*|\s*mil[lion ])[)]*$)'
    currency_regex = r'(?P<currency>^[(]*[HK$USDRMB]{2,3})(?P<unit>((\W?0{3})*|\W?\s?mil[lion ]*)[)]*$)'
    currency_amount_regex = r'(?P<amount>^\d{1,3}(\W\d{3})*$|^[-–]+$)'
    
    
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
    def sections(self):
        return [self.target_section(page) for page in self.audit_fee_page]


    @property
    def txts(self):
        txts = []
        for section in self.sections:
            print(section.extract_text())
            txts.append(section.extract_text())
        return txts
    
    @property
    def tables(self):
        tables = []
        for p in self.audit_fee_page:
            section = self.target_section(p)
            print(f'Parsing table in page {p}...')
            table = AuditFeeTable(section)
            if table.check():
                tables.append(table)
            else:
                print(table.raw_table)
        return tables
        
    # @staticmethod
    # def get_table_from_section(section:object):
    #     table = AuditFeeTable(section)
    #     print(table.currency, table.unit, table.years, table.amount)
    #     print(table.focus_col)
    #     print(table.summary)
    #     # print(table.raw_table)
    #     # print(table.table)
    #     return table.check()

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
        b_df = b_df[b_df['size'] > main_fontsizes.min()]
        
        b_df = b_df.groupby(['top', 'bottom'])['text'].apply(''.join).reset_index()
        
        lower_than_target_top = b_df.top > self.target_top(df)
        not_empty = b_df.text.str.contains(r'\w+')
        no_tailling_words = ~b_df.text.str.contains(r'REMUNERATION', flags=re.IGNORECASE)
        # condition = (b_df.top > self.target_top(df)) & (b_df.text.str.contains(r'\w+')) & (~b_df.text.str.contains(r'REMUNERATION', flags=re.IGNORECASE)) 
        condition = lower_than_target_top & not_empty & no_tailling_words
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


class AuditFeeTable:
    
    setting = {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            }
    
    def __init__(self, section):
        self.section = section

    @property
    def section(self):
        return self._section 
    
    @section.setter
    def section(self, section: object):
        if type(section) is not pdfplumber.page.CroppedPage:
            raise ValueError(f'section type: {type(section)} is not pdfplumber.page.CroppedPage')
        self._section = section


    @property
    def raw_table(self):
        return self.section.extract_table(AuditFeeTable.setting)


    @property
    def table(self):

        table = [
            row for row in self.raw_table 
            if any(map(AuditFeeTable.year_cell, row))
            or any(map(AuditFeeTable.currency_cell, row)) 
            or any(map(AuditFeeTable.amount_cell, row))
        ]
        return table


    @staticmethod
    def year_cell(cell:str) -> bool:
        current_yr = int(datetime.datetime.now().year)
        yr_range = range(current_yr - 2, current_yr + 1)
        return cell in [str(yr) for yr in yr_range]


    @staticmethod
    def amount_cell(cell:str) -> bool:
        return re.match(AuditFee.currency_amount_regex, cell)


    @staticmethod
    def currency_cell(cell:str) -> bool:
        return re.match(AuditFee.currency_regex, cell)
    
    @property
    def year_idx(self) -> set: # col_idx
        return {(r_idx, c_idx) for r_idx, row in enumerate(self.table) for c_idx, cell in enumerate(row) if self.year_cell(cell)}

    @property
    def currency_idx(self) -> set: # col_idx
        return {(r_idx, c_idx) for r_idx, row in enumerate(self.table) for c_idx, cell in enumerate(row) if self.currency_cell(cell)}
    
    @property
    def amount_idx(self) -> set: # col_idx
        return {(r_idx, c_idx) for r_idx, row in enumerate(self.table) for c_idx, cell in enumerate(row) if self.amount_cell(cell)}
    
    
    @property
    def co_row_idx(self) -> set: #co_col_idx
        row_idx = lambda idx: idx[0]
        year_row_idx = {row_idx(idx) for idx in self.year_idx}
        currency_row_idx = {row_idx(idx) for idx in self.currency_idx}
        amount_row_idx = {row_idx(idx) for idx in self.amount_idx}
        if year_row_idx:
            idxs = [year_row_idx, amount_row_idx, currency_row_idx]
            col_row_idxs = flatten([list(i.intersection(j))  for i, j in combinations(idxs, 2) if i.intersection(j)])
            return set(col_row_idxs)
        return currency_row_idx.intersection(amount_row_idx)

    @property
    def co_col_idx(self) -> set: 
        col_idx = lambda idx: idx[1]
        year_col_idx = {col_idx(idx) for idx in self.year_idx}
        currency_col_idx = {col_idx(idx) for idx in self.currency_idx}
        amount_col_idx = {col_idx(idx) for idx in self.amount_idx}
        if year_col_idx:
            idxs = [year_col_idx, amount_col_idx, currency_col_idx]
            col_col_idxs = flatten([list(i.intersection(j))  for i, j in combinations(idxs, 2) if i.intersection(j)])
            return set(col_col_idxs)
        return currency_col_idx.intersection(amount_col_idx)
    
   
    @property
    def focus_col(self) -> dict:
        return {idx : [row[idx] for row in self.table] for idx in self.co_col_idx}
        
    
    @property
    def amount(self) -> list:
        amounts = []
        str_to_int = lambda string : int(re.sub(r'[-–]','0',string.replace(',','')))
        for col in self.focus_col.values():
            amount = [str_to_int(cell) for cell in col if self.amount_cell(cell)]
            if sum(amount[:-1]) == amount[-1]:
                amount = amount[:-1]
            amounts.append(amount)
        return amounts
    

    @property
    def actual_amount(self) -> list:
        amounts = []
        
        if len(self.unit_in_num) == 1:
            unit = list(self.unit_in_num)[0]
            for amount in self.amount:
                m = [unit * i if type(unit) is int else i for i in amount]
                amounts.append(m)
        else:
            for unit, amount in zip(self.unit_in_num, self.amount):
                m = [unit * i if type(unit) is int else i for i in amount]
                amounts.append(m)
        
        return amounts


    @property
    def years(self) -> set:
        flatten_cols = sum(self.focus_col.values(), [])
        years = {cell for cell in flatten_cols if self.year_cell(cell)}
        return years


    @property
    def unit(self) -> set:
        flatten_cols = sum(self.focus_col.values(), [])
        get_unit = lambda cell: self.currency_cell(cell).group('unit')
        unit = {get_unit(cell) for cell in flatten_cols if self.currency_cell(cell)}
        return unit
    
    @property
    def unit_in_num(self) -> set:
        if not self.unit:
            return {1}
        unit_in_num = set()
        
        thousand_regex = r'0{3}'
        n_100 = lambda unit: len(re.findall(thousand_regex, unit))
        mil_regex = 'mil(lion)?\s*'
        
        for unit in self.unit:
            if n_100(unit):
                unit_in_num.add(1_000 ** n_100(unit))
            elif re.match(mil_regex, unit):
                unit_in_num.add(1_000_000)
            else:
                unit_in_num.add(unit)
        return unit_in_num
        

    @property
    def currency(self) -> set:
        flatten_cols = sum(self.focus_col.values(), [])
        get_curr = lambda cell: self.currency_cell(cell).group('currency')
        curr = {get_curr(cell) for cell in flatten_cols if self.currency_cell(cell)}
        return curr

    @property
    def last2_idx(self) -> set:
        row = self.table[0]
        row_len = len(row)
        return set(range(row_len - 2, row_len))

    @property
    def is_in_last_two_col(self) -> bool:
        if self.co_col_idx.intersection(self.last2_idx):
            return True
        return False

    @property
    def is_in_format(self) -> bool:
        for idx in self.co_col_idx:
            
            if self.currency_cell(self.focus_col[idx][0]):
                if not all(map(self.amount_cell, self.focus_col[idx][1:])):
                    return False
            
            if self.year_cell(self.focus_col[idx][0]):
                if not self.currency_cell(self.focus_col[idx][1]) and not all(map(self.amount_cell, self.focus_col[idx][2:])):
                    return False
        
        return True
    

    @property
    def summary(self):
        
        if self.check() is None:
            return None
        
        summary = {
            'year': self.years,
            'currency': self.currency,
            'unit': self.unit,
            'unit_in_num': self.unit_in_num,
            'amount': self.amount,
            'actual_amount': self.actual_amount,
            'total': list(map(sum, self.actual_amount)),
        }
        
        return summary


    def check(self):
        if not self.table or not self.co_col_idx or self.co_row_idx:
            return None
        if self.is_in_last_two_col and self.is_in_format:
            return self.table
        return None




if __name__ == "__main__":
    import get_pdf, re
    from test_cases import test_cases
    from get_data import HKEX_API
    from helper import write_to_csv, n_yearsago, today
    from helper import get_title_liked_txt, search_pattern_from_txt
    from get_pdf import _by_pdfplumber
    
    def test():
        # logging.basicConfig(level=logging.INFO)
        query = HKEX_API(from_date=n_yearsago(n=1), to_date=today())
        for data in query.data:

            url = data.file_link
            print(url)
            pdf = PDF(url)
            pdf_obj = pdf.pdf_obj
            f = AuditFee(pdf_obj)
            for table in f.tables:
                print(table.summary)
    
    
    url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0731/2020073101878.pdf', 40 # wrong number row
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/gem/2020/0831/2020083100445.pdf',33 # text
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0729/2020072900505.pdf', 40 # normal
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0730/2020073000620.pdf', 24 # normal
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0728/2020072800460.pdf', 104 # normal, two found result 
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0730/2020073000009.pdf', 76 # normal, with years
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0904/2020090402077.pdf', 21 # with `-` amount
    # url , p = 'https://www1.hkexnews.hk/listedco/listconews/gem/2020/0831/2020083100934.pdf', 59 # hkd000
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0827/2020082700690.pdf', 41 # None type rawtable
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0830/2020083000035.pdf', 41 # abnormal
    
    def debug(url, p):
        pdf = PDF(url)
        pdf_obj = pdf.pdf_obj
        f = AuditFee(pdf_obj)

        section = f.target_section(p)
        print(section.extract_text())

        table = AuditFeeTable(section)
        print('curr_idx:', table.currency_idx)
        print("amount_idx:", table.amount_idx)
        print("year_idx", table.year_idx)
        print("co_row_idx:", table.co_row_idx)
        print("co_col_idx:",table.co_col_idx)

        # print(table.raw_table)
        print(table.table)
        print(table.summary)
    
    # test()
    debug(url, p)