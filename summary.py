import pandas as pd
from helper import validate_auditor
def unique_result(csvname='normal.csv', column='auditor', show_all=True):
    import pandas as pd
    import os
    if not os.path.exists(f'./{csvname}'):
        logging.warning('file does not exist.')
        return
    if show_all:
        pd.set_option('display.max_rows', None)
    df = pd.read_csv(csvname)
    uni_result = df['auditor'].value_counts()
    uni_result.to_csv('uni_result.csv', index=True)


def error_result(csvname='normal.csv', column='auditor', show_all=True):
    import pandas as pd
    import os
    if not os.path.exists(f'./{csvname}'):
        logging.warning('file does not exist.')
        return
    if show_all:
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
    df = pd.read_csv(csvname)
    df = df[df['auditor'] == 'None']
    df.to_csv('err_result.csv', index=False)


def find_row(key, value, csvname='normal.csv'):
    import pandas as pd
    import os
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('max_colwidth', None)
    pd.set_option('display.width', None)
    df = pd.read_csv(csvname)
    print(df[df[key] == value])

# find_row('VI.')
# testing(case, verbose=True)


def get_df(csvname='normal.csv'):
    import pandas as pd
    import os
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('max_colwidth', None)
    pd.set_option('display.width', None)
    df = pd.read_csv(csvname)
    return df


def get_noise_case():
    df = get_df('normal.csv')
    df['from_page'] = df.auditReportPageRange.apply(
        lambda x: x.split(' - ')[0])
    df['to_page'] = df.auditReportPageRange.apply(lambda x: x.split(' - ')[1])
    cols = ['auditor', 'link', 'to_page']
    df_noise = df[df.auditor.str.len() <= 3][cols]
    d_noise = {link: int(topage)
               for link, topage in zip(df_noise.link, df_noise.to_page)}
    print(d_noise)


if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('max_colwidth', None)
    pd.set_option('display.width', None)
    def my_v(r_auditors):
        import re
        v_auditors = pd.read_csv('valid_auditors.csv').valid_auditor.values
        result = {validate_auditor(re.sub('\s*limited', '', r_auditor, flags=re.IGNORECASE), v_auditors, 90) for r_auditor in eval(r_auditors)}    
        if any(result):
            return tuple(filter(None, result))
        else:
            return eval(r_auditors)
        # result = tuple(validate_auditor(r_auditor, v_auditors, 90) if auditor is not None else None for r_auditor in eval(auditor))
        # return tuple(filter(None, result)) if len(result) > 1 else result
    df = pd.read_csv('result.csv')
    not_none = (~(df['auditor'] == 'None'))
    
    not_na = (~df.auditor.isna())
    df = df[not_na & not_none]
    df.auditor = df.auditor.apply(my_v)
    freq = df.auditor.value_counts()
    print(freq)
    abnormal_cases = freq[freq==1].shape[0] + sum((~not_none))
    print('error rate:', (abnormal_cases)/freq.sum())
    print('error case:', abnormal_cases, 'single occurence:', freq[freq==1].shape[0], 'not found:', sum((~not_none)), 'total:', freq.sum())

    # print(df.auditor.value_counts().sort_index())
    # from fuzzywuzzy import process, fuzz
    # v_auditors = pd.read_csv('valid_auditors.csv').valid_auditor.values
    # print(process.extractOne('eloitte Touche Tohmatsu', v_auditors, scorer=fuzz.token_set_ratio))

    

    # df = get_df('indept_auditor_report.csv')
    # abnormal_df =  df[(df.result == 'not found') & (df.toc == 'available')]
    # print(1 - (abnormal_df.shape[0]/df.shape[0]))

    # # df = get_df('company_info.csv')
    # # abnormal_df =  df[(df.result == 'not found') & (df.toc == 'available')]
    # # print(1 - (abnormal_df.shape[0]/df.shape[0]))

    # print(df.result.value_counts())

