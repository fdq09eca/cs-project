import pandas as pd, re
from helper import flatten
from pdf import PDF, Outline
from hkex_api import HKEX_API

class IndependentAuditorReport:

    title_regex = r'^(?!.*internal)(?=.*report|.*responsibilities).*auditor.*$'
    auditor_regex = r'\n(?!.*?(Institute|Responsibilities).*?).*?(?P<auditor>.{4,}\S|[A-Z]{4})(?:LLP\s*)?\s*((PRC\s*?|Chinese\s*?)?Certified\s*Public|Chartered)\s*Accountants*'

    def __init__(self, outline):
        self.pages = outline
    
    @classmethod
    def create(cls, outline):
        fail_conditions = {
            isinstance(outline, Outline) is False: lambda err_msg: TypeError(err_msg + f'argument must be an Outline instance.'),
            not any(outline.pages): lambda err_msg: ValueError(err_msg + f'outline instance must have at least one page.'),
            re.search('audit', outline.title, flags=re.IGNORECASE) is None: lambda err_msg: ValueError(err_msg + f'outline title: {outline.title} must contain keyword: "audit".'),
        }
        create_failed = fail_conditions.get(True, False)
        if create_failed:
            raise create_failed('Failed to initialise Independent Auditor Report instance.')
        return cls(outline)
    
    @property
    def pages(self):
        return self._pages
    
    @pages.setter
    def pages(self, outline):
        self._pages = [page for page in outline.pages if page]


    @property
    def auditors(self) -> set:
        return Auditor.retrieve(self.pages[-1]).auditors
        
    @property
    def kams(self) -> list:
        return KeyAuditMatter.retrieve(self.pages)
     

class Auditor:
    auditor_regex = r'\n(?!.*?(Institute|Responsibilities).*?).*?(?P<auditor>.{4,}\S|[A-Z]{4})(?:LLP\s*)?\s*((PRC\s*?|Chinese\s*?)?Certified\s*Public|Chartered)\s*Accountants*'

    def __init__(self, auditor_page):
        self.auditor_page = auditor_page
    
    @classmethod
    def retrieve(cls, auditor_page):
        report_last_page = auditor_page.to_bilingual()
        return cls(report_last_page)

    @property
    def page_results(self) -> list:
        return [self.auditor_page.search(Auditor.auditor_regex)]

    @property
    def columns(self) -> list:
        return [self.auditor_page.left_column, self.auditor_page.right_column]
    
    @property
    def cols_results(self) -> list:
        columns = self.columns
        cols_results = [col.search(Auditor.auditor_regex) for col in columns if col]
        return [result for result in cols_results if result]
    
    @property
    def auditors(self) -> set:
        results = self.cols_results or self.page_results
        return {result.group('auditor').strip() for result in results if result}
    
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.auditor_page}> - {self.auditors}'
  
    
class KeyAuditMatter:
    kam_regex = r'Key Audit Matter[s]*'
    keywords = list(pd.read_csv('kam_keywords.csv', header=None, names = ['kam_kws']).kam_kws.sort_values().unique())
    
    def __init__(self, kam_pages):
        self.pages = kam_pages
    

    @classmethod
    def retrieve(cls, pages):
        kam_page_range = []
        for page in pages:
            if page.df_feature_text.empty:
                continue
            df_kam_feature_text = page.df_feature_text[page.df_feature_text.text.str.contains(cls.kam_regex, flags=re.IGNORECASE)]
            if not df_kam_feature_text.empty:
                kam_page_range.append(page.page_number)
        kam_pages = [page for page in pages if kam_page_range and page.page_number in range(min(kam_page_range), max(kam_page_range) + 1)]
        return cls(kam_pages) if kam_pages else None
    

    @property
    def kams(self) -> list:
        df_kams = self.df_kams
        return df_kams.text.to_list() if not df_kams.empty else []

    @property
    def tags(self) -> set:
        kams = self.kams
        keywords = self.keywords
        tags = {keyword for keyword in keywords if any(re.search(keyword, kam, flags=re.IGNORECASE) for kam in kams)}
        return sorted(tags)


    @property
    def df_kams(self) -> pd.DataFrame:
        dfs_feature_text = self.dfs_feature_text
        kam_cond = dfs_feature_text.text.str.contains('|'.join(KeyAuditMatter.keywords), flags=re.IGNORECASE)
        return dfs_feature_text[kam_cond]

    @property
    def dfs_feature_text(self):
        df = pd.DataFrame()
        for page in self.pages:
            df_feature_text = page.df_feature_text
            if not df_feature_text.empty:
                df_feature_text = self.group_feature_text(df_feature_text)
                df_feature_text['page_num'] = page.page_number
                df = df.append(df_feature_text, ignore_index=True)
        return df
    
    @staticmethod
    def group_feature_text(df_feature_text):
        text_interval = df_feature_text['bottom'].shift() - df_feature_text['top']
        indicator = (text_interval.abs() > df_feature_text['size']).cumsum()
        df_feature_text = df_feature_text.groupby(indicator).agg({
            'top': 'first',
            'bottom': 'last',
            'fontname': 'first',
            'size': 'first',
            'x0': 'first',
            'x1': 'first',
            'text': ''.join
        })
        return df_feature_text
    
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.pages}> - {self.tags}'

if __name__ == "__main__":
    from os import sys, path, getpid
    import concurrent.futures 
    import time

    # urls = [
    # 'https://www1.hkexnews.hk/listedco/listconews/gem/2020/0629/2020062901807.pdf',
    # 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0730/2020073001097.pdf',
    # 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0730/2020073000811.pdf',
    # 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0729/2020072900505.pdf',
    # 'https://www1.hkexnews.hk/listedco/listconews/gem/2020/0629/2020062901859.pdf',
    # 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0428/2020042801316.pdf',
    # 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0731/2020073100265.pdf', # hsbc
    # 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0823/2020082300051.pdf'

    # ]
    def test_code(url):
        pdf = PDF.create(url)
        audit_report_outline = pdf.get_outline(IndependentAuditorReport.title_regex)
        if not audit_report_outline: return None
        try:
            audit_report = IndependentAuditorReport.create(audit_report_outline[0])
        except:
            return None
        _last_page = audit_report.pages[-1].page
        last_page = Page_bilingual.create(_last_page)
        cols = last_page.left_column, last_page.right_column
        cols_results = [col.search(IndependentAuditorReport.auditor_regex) if col else None for col in cols if any(cols)]
        page_results = [last_page.search(IndependentAuditorReport.auditor_regex)]
        print([result.group('auditor') for result in cols_results + page_results if result])
        return last_page
    
    
    def test_kam(url):
        print(url)
        pdf = PDF.create(url)
        if pdf is None:
            return None
        audit_report_outline = pdf.get_outline(IndependentAuditorReport.title_regex)
        if not audit_report_outline:
            return None
        try:
            audit_report = IndependentAuditorReport.create(audit_report_outline[0])
        except Exception as e:
            print(e)
            return None
        kams = KeyAuditMatter.retrieve(audit_report.pages)
        print(kams)
        if kams is None:
            with open('no_kams.csv', 'a') as f:
                f.write(f'{url}\n')
            return None
        elif not kams.df_kams.empty:
            print(kams.df_kams)
            kams.df_kams.text.to_csv('kams.csv', index=False,  header=False, mode='a')
            return kams

    
    def job(url):
        print(url)
        
        pdf = PDF.create(url)
        if not pdf:
            return None
        
        audit_report_outlines = pdf.get_outline(IndependentAuditorReport.title_regex)       
        audit_reports = [IndependentAuditorReport.create(outline) for outline in audit_report_outlines if audit_report_outlines]
        auditors = [list(audit_report.auditors) for audit_report in audit_reports if audit_reports and audit_report.auditors]
        auditors = {auditor for auditor in flatten(auditors) if auditor} or None
        print(auditors)
        # with open('auditors.txt', 'a') as f:
        #     f.write(f'{auditors}, {url}\n')

        

    start = time.perf_counter()

    # query = HKEX_API(from_date=n_yearsago(n=1), to_date=today())
    query = HKEX_API()
    urls = [data.file_link for data in query.get_data()]
    urls = ['https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0721/2020072100713.pdf']
    
    # err_url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0428/2020042800145.pdf'
    # idx = urls.index(err_url)
    # urls = urls[idx:]
    for url in urls:
        job(url)
        # kams = test_kam(url)
        # last_page = test_code(url)

    end = time.perf_counter()

    print(f'time uesd {round(end - start, 2)}s')