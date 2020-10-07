from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy.types import  Integer, String, DateTime, Text
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from datetime import datetime
import random

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class AnnualReport(Base):
    __tablename__ = 'annual_report'
    id = Column(Integer, primary_key=True)
    news_id = Column(Integer, nullable=False, unique=True)
    date_time = Column(String, nullable=False)
    stock_code = Column(Integer, nullable=False)
    stock_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    long_text = Column(String, nullable=False)
    file_link = Column(String, nullable=False)
    created_on = Column(DateTime, default=datetime.now),
    updated_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    independent_audit_report = relationship('IndependentAuditReport', uselist=False, backref='aunnal_report') # one to one

    def __init__(self, news_id, date_time, stock_code, stock_name, title, long_text, file_link):
        self.news_id = news_id
        self.date_time = date_time
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.title = title
        self.long_text = long_text
        self.file_link = file_link

    def __repr__(self):
       return f"<{self.__class__.__name__}({self.news_id}, {self.date_time})>"

class IndependentAuditReport(Base):
    __tablename__ = 'independent_audit_report'
    id = Column(Integer, primary_key=True)
    news_id = Column(Integer, ForeignKey('annual_report.news_id'))
    audit_firm = relationship('Auditor', backref='indepentent_auditor_report') # one to many
    kams = relationship('KeyAuditMatter', backref='indepentent_auditor_report') # one to many
    
    def __repr__(self):
       return f"<{self.__class__.__name__}({self.id}, {self.annual_report_id})>"


class Auditor(Base):
    __tablename__ = 'auditor'
    id = Column(Integer, primary_key=True)
    independent_audit_report_id = Column(Integer, ForeignKey('independent_audit_report.id'))
    name = Column(Text, nullable=False)
    def __repr__(self):
        return f"<{self.__class__.__name__}({self.id}, {self.name})>"


class KeyAuditMatter(Base):
    __tablename__ = 'key_audit_matter'
    id = Column(Integer, primary_key=True)
    independent_audit_report_id = Column(Integer, ForeignKey('independent_audit_report.id'))
    item = Column(Text)
    tag = Column(String)

class KeyAuditMatterKeywords(Base):
    __tablename__ = 'key_audit_matter_keywords'
    id = Column(Integer, primary_key=True)
    keyword = Column(String, nullable=False, unique=True)

class ValidatedAuditor(Base):
    __tablename__ = 'validated_auditor'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

Base.metadata.create_all(engine)

# session = Session()
# charlie = User(first_name='Charlie')
# david = User(first_name='David')
# session.add(charlie)
# session.add(david)
# session.commit()
# users = session.query(User).all()
# for user in users:
#     print(f'user.fullname: {user.fullname}')
# print(f'user.fullname: {user.fullname}')
