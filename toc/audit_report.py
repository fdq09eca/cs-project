import pandas as pd, re
from helper import flatten
from pdf import PDF, Outline, ReportOutline, PageWithSection

class IndependentAuditorReport(ReportOutline):

    title_regex = r'^(?!.*internal)(?=.*report|.*responsibilities).*auditor.*$'
    
    def __init__(self, outline):
        super().__init__(outline)

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

class KeyAuditMatter(PageWithSection):
    section_regex = r'Key Audit Matter[s]*'
    keywords = list(pd.read_csv('kam_keywords.csv', header=None, names = ['kam_kws']).kam_kws.sort_values().unique())
    
    def __init__(self, kam_pages):
        super().__init__(kam_pages)
    
    # @classmethod
    # def retrieve(cls, pages):
    #     kam_page_range = []
    #     for page in pages:
    #         if page.df_feature_text.empty:
    #             continue
    #         df_kam_feature_text = page.df_feature_text[page.df_feature_text.text.str.contains(cls.section_regex, flags=re.IGNORECASE)]
    #         if not df_kam_feature_text.empty:
    #             kam_page_range.append(page.page_number)
    #     kam_pages = [page for page in pages if kam_page_range and page.page_number in range(min(kam_page_range), max(kam_page_range) + 1)]
    #     return cls(kam_pages) if kam_pages else None
    

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
    




