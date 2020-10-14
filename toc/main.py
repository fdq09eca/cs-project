from annual_report import AnnualReport
from hkex_api import HKEX_API
from database import engine

def main():
    query = HKEX_API()
    urls = [data.file_link for data in query.get_data()]
    for data in query.get_data():
        url = data.file_link
        print(url)
        annual_report = AnnualReport(src = url)

        print(annual_report.auditors)
        print(annual_report.kams)
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