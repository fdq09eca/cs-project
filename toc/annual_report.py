from audit_report import IndependentAuditorReport
from pdf import PDF
from hkex_api import HKEX_API
import pandas as pd, re
from helper import flatten

class AnnualReport(PDF):
    def __init__(self, src, news_id, date_time, stock_code, stock_name, title, long_text, file_link):
    # def __init__(self, src):
        super().__init__(src)
        self.news_id = news_id
        self.date_time = date_time
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.title = title
        self.long_text = long_text
        self.file_link = file_link
    
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
        auditors = {auditor for auditor in flatten(auditors) if auditor} or None
        return auditors
    
    @property
    def kams(self):
        audit_reports = self.audit_reports
        kams = [audit_report.kams for audit_report in audit_reports if audit_reports and audit_report.kams]
        return kams

