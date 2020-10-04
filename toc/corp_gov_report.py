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

    currency_regx = 'HK'
    financial_num_regex = '\d,?\d*'
    year_regx = '|'.join(map(str, range(
        int(datetime.datetime.now().year) - 2, int(datetime.datetime.now().year) + 1)))

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
        return x.str.contains(AuditFeeTable.currency_regx)

    @staticmethod
    def financial_num_element(x):
        return x.str.contains(AuditFeeTable.financial_num_regex)

    @staticmethod
    def year_element(x):
        return x.str.contains(AuditFeeTable.year_regex)

    @property
    def df_clean_table(self):
        df = self.df_raw_table
        currency_rows = df.apply(self.currency_element).any(axis=1)
        financial_num_rows = df.apply(self.financial_num_element).any(axis=1)
        year_rows = df.apply(self.year_element).any(axis=1)
        df = df[currency_rows | financial_num_rows]
        df = df.loc[:, df.apply(
            lambda x: x.str.contains(r'[A-Za-z0-9]+')).any()]
        return df

    @property
    def df_currency(self):
        df = self.df_clean_table
        df = df.loc[:, df.apply(lambda x: x.str.contains(
            AuditFeeTable.currency_regx)).any()]

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
    print(sec.text)
    # print(corp_gov_report.pages)

    # page = pdf.
