import pandas as pd
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

    df = get_df('indept_auditor_report.csv')
    abnormal_df =  df[(df.result == 'not found') & (df.toc == 'available')]
    print(1 - (abnormal_df.shape[0]/df.shape[0]))

    # df = get_df('company_info.csv')
    # abnormal_df =  df[(df.result == 'not found') & (df.toc == 'available')]
    # print(1 - (abnormal_df.shape[0]/df.shape[0]))

    print(df.result.value_counts())

