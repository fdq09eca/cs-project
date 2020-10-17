from annual_report import AnnualReport
from hkex_api import HKEX_API
from database import DataBase
from helper import flatten
import database as DB

def main():
    query = HKEX_API()
    for data in query.get_data():
        print(data)
        annual_report = AnnualReport(news_id = data.news_id, date_time = data.date_time, stock_code = data.stock_code, stock_name = data.stock_name, title = data.title, long_text = data.long_text, src = data.file_link)
        print(annual_report.auditors)
        print(annual_report.kams)
        annual_report.add_to_db()

if __name__ == '__main__':
    main()