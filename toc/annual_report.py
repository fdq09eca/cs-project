from audit_report import IndependentAuditorReport, KeyAuditMatter
from pdf import PDF
from hkex_api import HKEX_API
import pandas as pd, re
from helper import flatten
import database as DB

class AnnualReport(PDF):
    def __init__(self, src, news_id, date_time, stock_code, stock_name, title, long_text):
    # def __init__(self, src):
        super().__init__(src)
        self.news_id = news_id
        self.date_time = date_time
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.title = title
        self.long_text = long_text
        self.src = src
    
    @PDF.src.setter
    def src(self, src):
        PDF.src.fset(self, src)
        audit_report_outlines = self.get_outline(IndependentAuditorReport.title_regex)
        audit_reports = [IndependentAuditorReport.create(outline) for outline in audit_report_outlines if audit_report_outlines]
        self._audit_reports = audit_reports
            
    @property
    def audit_reports(self) -> list:
        return self._audit_reports

    @property
    def auditors(self) -> set:
        audit_reports = self.audit_reports
        auditors = [list(audit_report.auditors) for audit_report in audit_reports if audit_reports and audit_report.auditors]
        auditors = {auditor for auditor in flatten(auditors) if auditor}
        return auditors
    
    @property
    def kams(self):
        audit_reports = self.audit_reports
        kams = [audit_report.kams for audit_report in audit_reports if audit_reports and audit_report.kams]
        return kams
    

    def add_to_db(self):
        print('== loading to annual report db ==')
        db = DB.DataBase.init()
        
        with db.Session() as session:
            annual_report_record = DB.AnnualReport(
                news_id = self.news_id, 
                date_time = self.date_time, 
                stock_code = self.stock_code, 
                stock_name = self.stock_name, 
                title = self.title, 
                long_text = self.long_text, 
                file_link = self.src)
        
            session.add(annual_report_record)
            session.commit()

            print('== loading to auditor db ==')

            for auditor in self.auditors:
                auditor_record = DB.Auditor(news_id = annual_report_record.news_id, name = auditor)
                session.add(auditor_record)
                session.commit()
                print(auditor_record)

            
            print('== loading kam and kam tag to db ==')
            kam_items = flatten([kam.items for kam in self.kams])
        
            for kam_item in kam_items:
                print(kam_item)
                kam_item_record = DB.KeyAuditMatter(news_id = annual_report_record.news_id, item = kam_item)
                session.add(kam_item_record)
                session.commit()
                print(kam_item_record)

                tags = KeyAuditMatter.get_tags(kam_item)
                for tag in tags:
                    kam_tag_record = DB.KeyAuditMatterTag(kam_id = kam_item_record.id, tag = tag)
                    session.add(kam_tag_record)
                    session.commit()
                    print(kam_tag_record)