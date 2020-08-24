from helper import flatten, turn_n_page
from get_pdf import _by_pypdf, _by_pdfplumber
import pandas as pd
import get_data
from AnnualReport import AnnualReport
from helper import consecutive_int_list, divide_page_into_two_cols, search_pattern_from_page_or_cols, search_pattern_from_page, search_pattern_from_cols, flatten
from test_cases import two_cols_cases, full_cn_cases


def pd_setting():
    pd.set_option('display.max_rows', None)
    # pd.set_option('display.max_columns', None)
    # pd.set_option('max_colwidth', None)
    # pd.set_option('display.width', None)

def all_to_lower(str_tuple):
    _tuple = eval(str_tuple)
    return tuple(i.lower().strip() for i in _tuple)

def mi_len(_tuple):
    return min([len(i.strip().split()) for i in _tuple])



pd_setting()

df = pd.read_csv('result.csv')
not_none = (~(df['auditor'] == 'None'))
not_na = (~df.auditor.isna())
df = df[not_na & not_none]
# print(df)
# clean_auditor = df.auditor[not_na | not_none].apply(all_to_lower)
df['auditor'] = df.auditor.apply(all_to_lower)
# unique_auditor = []
# print(df['auditor'].value_counts().sort_index())
def cap_words(_str):
    return ' '.join([s.capitalize() for s in _str.split()])
r_auditors = list(set([ t.replace('\t',' ').lower() for _tuple in df['auditor'].unique() for t in _tuple]))
unique_auditor = [r for r in sorted(r_auditors) if len(r.split()) <= 7]
# print(unique_auditor)
# pd.DataFrame({'unique_auditor': unique_auditor}).to_csv('auditor_option_2.csv', index = False)
from fuzzywuzzy import process, fuzz
_df = pd.read_csv('valid_auditors.csv')
for r_auditor in sorted(r_auditors):
    v_auditor = process.extractOne(r_auditor, _df.valid_auditor.values, scorer=fuzz.token_set_ratio)
    print(r_auditor, v_auditor)

# print(unique_auditor)
# print(df['auditor'].value_counts())
# df['mi_len'] = df['auditor'].apply(mi_len)
# print()
# print(clean_auditor)
# cond = df['mi_len'] < 7
# print(df[cond]['auditor'].value_counts())
# print(df[cond]['auditor'].shape[0])

# total = df[not_na].shape[0]
# not_found = df[not_none].shape[0]
# print(f'not_found:{not_found}, total: {total}')
# print(not_found/total)
# print(df['auditor'].value_counts())

def check_err():
    df_err = pd.read_csv('result.csv')
    err_url = df_err[df_err['auditor'].isna()]['file_link'].to_list()
    print(f'there are {len(err_url)} error')
    d = [dict(data._asdict()) for data in get_data.get_data()]
    df = pd.DataFrame(d)
    df['auditor'] = 'None'
    print(f'unique news id: {df.shape[0] == df.news_id.unique().shape[0]}')
    for data in get_data.get_data():
        url = data.file_link
        if url in err_url:
            try:
                ar = AnnualReport(url)
                condition = df['news_id'] == data.news_id
                df.loc[condition, 'auditor'] = pd.Series(
                    [ar.auditor]).values if ar.auditor else 'None'
                # print(ar.auditor, url)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f'N/A, {e.message}')
                df.loc[condition, 'auditor'] = 'NaN'
            finally:
                print(df[condition])

# def _get_toc(pdf: object) -> dict:
#     '''
#     under development
#     get the TOC with page number from a pypdf2 object
#     '''
#     outlines = pdf.getOutlines()
#     outlines = flatten(outlines)
#     return outlines
#
# errs = [
#     'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0729/2020072900533.pdf',
#     'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0429/2020042902583.pdf',
#     'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0424/2020042402212.pdf',
#     'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0424/2020042400723.pdf',
# ]
# url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0724/2020072400775.pdf', 86
# for url, p in full_cn_cases.items():
    # ar = AnnualReport(url)
    # print(ar.toc)
    # print(ar.get_outline_pageRange())
    # print(ar.auditor)

# ar = AnnualReport(url)


# with _by_pdfplumber(url) as pdf:
    # page = pdf.pages[p]
    # pattern = r'\n(?!.*?(Institute|Responsibilities).*?).*?(?P<auditor>.{4,}\S|[A-Z]{4})(?:LLP\s*)?\s*((PRC\s*?|Chinese\s*?)?Certified\s*Public|Chartered)\s*Accountants*'
    # d = 0.95
    # x0, x1 = (1-d) * float(page.width), d * float(page.width)
    # print(x0, x1)
    # print(float(page.width))
    # result_p = search_pattern_from_page(page, pattern)
    # result_c = search_pattern_from_cols(page, pattern)
    # result_c_2 = [search_pattern_from_page(page=col, d=1, pattern=pattern) for col in divide_page_into_two_cols(page, 0.5)]
    # result_c3 = search_pattern_from_page_or_cols(page, pattern)


# url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0429/2020042900171.pdf'

# with _by_pypdf(url) as pdf:
#     toc = _get_toc(pdf)
#     print(pd.DataFrame(toc))
# for d in get_data():
#     if not d.file_link.endswith('pdf'):
#         print(d.file_link)
