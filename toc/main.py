from annual_report import AnnualReport
from hkex_api import HKEX_API
from database import DataBase
from helper import flatten
import database as DB

def main():
    query = HKEX_API()
    db = DataBase.init()
    urls = [data.file_link for data in query.get_data()]
    for data in query.get_data():
        annual_report = AnnualReport(news_id = data.news_id, date_time = data.date_time, stock_code = data.stock_code, stock_name = data.stock_name, title = data.title, long_text = data.long_text, src = data.file_link)
        audit_reports = annual_report.audit_reports
        auditors = annual_report.auditors
        kams_items = flatten([kam.items for kam in annual_report.kams])
        DB_AnnualReport = DB.AnnualReport(news_id = annual_report.news_id, date_time = annual_report.date_time, stock_code = annual_report.stock_code, stock_name = annual_report.stock_name, title = annual_report.title, long_text = annual_report.long_text, file_link = annual_report.src)
        DB_IndependentAuditReports = [DB.IndependentAuditReport(news_id = annual_report.news_id) for _ in audit_reports]
        DB_Auditors = [DB.Auditor(news_id = annual_report.news_id, name = auditor) for auditor in auditors]
        DB_KeyAuditMatters = [DB.KeyAuditMatter(news_id = annual_report.news_id, item = item) for item in kams_items]
        db.add(DB_AnnualReport)
        db.add_all(DB_IndependentAuditReports)
        db.add_all(DB_Auditors)
        db.add_all(DB_KeyAuditMatters)
        # db.add_all()

        


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