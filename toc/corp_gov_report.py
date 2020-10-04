from pdf import PDF, Outline, ReportOutline, PageWithSection
from helper import flatten
import datetime
import re
import pandas as pd


class CorporateGovReport(ReportOutline):

    title_regex = r'^(?=.*report).*corporate governance.*$'

    def __init__(self, outline):
        super().__init__(outline)

    @property
    def audit_fee(self):
        return AuditFee.retrieve(self.pages)


class AuditFee(PageWithSection):

    section_regex = r"^(?!.*Nomination|.*Report)(?=.*REMUNERATION|.*independent|.*external|.*Accountability).*auditor.*$"

    def __init__(self, pages):
        super().__init__(pages)

    @property
    def sections(self):
        return flatten([page.get_section(AuditFee.section_regex) for page in self.pages])

    @property
    def tables(self):
        return [AuditFeeTable.retrieve(section) for section in self.sections]


class AuditFeeTable:
    setting = {
        "vertical_strategy": "text",
        "horizontal_strategy": "text"
    }

    currency_regex = 'HK'
    financial_num_regex = '\d,?\d*'
    year_regex = '|'.join(map(str, range(int(datetime.datetime.now().year) - 2, int(datetime.datetime.now().year) + 1)))

    def __init__(self, section):
        self.section = section

    @classmethod
    def retrieve(cls, section):
        return cls(section.page)

    @classmethod
    def set_year_regex(cls, current_year: int):
        cls.year_regex = '|'.join(
            map(str, range(current_year - 2, current_year + 1)))
        print(f'Set {cls.__name__}.year_regex to {cls.year_regex}')

    @property
    def raw_table(self):
        return self.section.extract_table(AuditFeeTable.setting)

    @property
    def df_raw_table(self):
        df = pd.DataFrame(self.raw_table)
        return df

    @staticmethod
    def currency_element(x):
        return x.str.contains(AuditFeeTable.currency_regex)

    @staticmethod
    def financial_num_element(x):
        return x.str.contains(AuditFeeTable.financial_num_regex)

    @staticmethod
    def year_element(x):
        return x.str.contains(AuditFeeTable.year_regex)
    
    @staticmethod
    def eng_element(x):
        return x.str.contains(r'[A-Za-z0-9]+')
    
    @staticmethod
    def get_cond_cols(df, element_cond_func):
        return df.apply(element_cond_func).any()
    
    @staticmethod
    def get_cond_rows(df, element_cond_func):
        return df.apply(element_cond_func).any(axis=1)
    
    @property
    def df_fee(self):
        df = self.df_raw_table
        currency_cols = self.get_cond_cols(df, self.currency_element)
        currency_rows = self.get_cond_rows(df, self.currency_element)
        financial_num_rows = self.get_cond_rows(df, self.financial_num_element)
        year_rows = self.get_cond_rows(df, self.year_element)
        df_fee = df.loc[(financial_num_rows|year_rows) , currency_cols]
        return df_fee

   
    @property
    def df_filtered_table(self):
        df_fee = self.df_fee
        df_filtered_table = self.df_raw_table.iloc[df_fee.index]
        df_filtered_table = df_filtered_table.loc[:, self.get_cond_cols(df_filtered_table, self.eng_element)]
        return df_filtered_table
    
    
    @property
    def df_clean_table(self):
        df_filtered_table = self.df_filtered_table
        currency_cols = self.get_cond_cols(df_filtered_table, self.currency_element)
        financial_num_cols = self.get_cond_cols(df_filtered_table, self.financial_num_element)
        currency_rows= self.get_cond_rows(df_filtered_table, self.currency_element)
        year_rows = self.get_cond_rows(df_filtered_table, self.year_element)


        currency_row_idx = df_filtered_table.loc[currency_rows, financial_num_cols].index
        currency_row = df_filtered_table.loc[currency_row_idx]
        currency_header = currency_row[currency_row.apply(self.currency_element, axis=1)].fillna('')
        
        year_row_idx = df_filtered_table.loc[year_rows, currency_cols].index
        year_row = df_filtered_table.loc[year_row_idx]
        year_header = year_row[year_row.apply(self.year_element, axis=1)].fillna('')

        # print(f'year_header: {year_header}')
        # print(f'currency_header: {currency_header}')

        # return year_header
        if not year_header.empty and not currency_header.enpty:
        #     print(f'year_header: {year_header}')
            df_filtered_table.columns = pd.MultiIndex.from_arrays([year_header.iloc[0], currency_header.iloc[0]], names = ['year', 'currency'])
        else:
            # print(f'currency_header: {currency_header}')
            df_filtered_table.columns = pd.MultiIndex.from_arrays([currency_header.iloc[0]], names=['currency'])
        # print(df_filtered_table)
        return df_filtered_table.drop(year_row_idx.append(currency_row_idx))
        # return df_filtered_table


    @property
    def currency(self):
        pass

    @property
    def currency_unit(self):
        pass

    @property
    def total(self):
        pass

    def __repr__(self):
        return f'{self.__class__.__name__} - {self.section}'


if __name__ == '__main__':
    url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0721/2020072100713.pdf', 61
    # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0721/2020072100653.pdf', 94
    pdf = PDF.create(url)

    corp_gov_report = pdf.get_outline(CorporateGovReport.title_regex)
    corp_gov_report = CorporateGovReport.create(corp_gov_report[0])
    page = corp_gov_report.audit_fee.pages[0]
    sec = corp_gov_report.audit_fee.sections[0]
    table = corp_gov_report.audit_fee.tables[0]
    print(table.df_clean_table)
    print(sec.text)
    # print(corp_gov_report.pages)

    # page = pdf.
