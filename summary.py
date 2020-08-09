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
