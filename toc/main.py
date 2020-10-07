from annual_report import AnnualReport
from hkex_api import HKEX_API

def main():
    query = HKEX_API()
    urls = [data.file_link for data in query.get_data()]
    # err_url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0721/2020072100713.pdf'
    # idx = urls.index(err_url)
    # urls = urls[idx:]
    # urls = ['https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0827/2020082700690.pdf']
    for url in urls:
        print(url)
        annual_report = AnnualReport(src = url)
        print(annual_report.auditors)
        print(annual_report.kams[0].kams)
        # try:
        #     print(url)
        #     annual_report = AnnualReport(src = url)
        #     print(annual_report.auditors)
        #     print(annual_report.kams)
        # except Exception as e:
        #     with open('error.txt', 'a') as f:
        #         f.write(f'{url}, {e}\n')
        

if __name__ == '__main__':
    main()