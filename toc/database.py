from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, ForeignKey, inspect
from sqlalchemy.types import Integer, String, DateTime, Text
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from datetime import datetime
from contextlib import contextmanager
from helper import flatten
import pandas as pd
import random

Base = declarative_base()


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
    independent_audit_report = relationship('IndependentAuditReport', uselist=False, backref='aunnal_report')  # one to one

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.news_id}, {self.date_time}, {self.stock_code}, {self.file_link})>"


class IndependentAuditReport(Base):
    __tablename__ = 'independent_audit_report'
    id = Column(Integer, primary_key=True)
    news_id = Column(Integer, ForeignKey('annual_report.news_id'))
    audit_firm = relationship(
        'Auditor', backref='indepentent_auditor_report')  # one to many
    kams = relationship(
        'KeyAuditMatter', backref='indepentent_auditor_report')  # one to many

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.id}, {self.annual_report_id})>"


class Auditor(Base):
    __tablename__ = 'auditor'
    id = Column(Integer, primary_key=True)
    independent_audit_report_id = Column(
        Integer, ForeignKey('independent_audit_report.id'))
    name = Column(Text, nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.id}, {self.independent_audit_report_id}, {self.name})>"


class KeyAuditMatter(Base):
    __tablename__ = 'key_audit_matter'
    id = Column(Integer, primary_key=True)
    independent_audit_report_id = Column(
        Integer, ForeignKey('independent_audit_report.id'))
    item = Column(Text)
    tag = Column(String)

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id}, {self.independent_audit_report_id}, {self.item}, {self.tag})>'




class KeyAuditMatterKeywords(Base):
    __tablename__ = 'key_audit_matter_keywords'
    id = Column(Integer, primary_key=True)
    keyword = Column(String, nullable=False, unique=True)
    
    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id}, {self.keyword})>'


class ValidatedAuditor(Base):
    __tablename__ = 'validated_auditor'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id}, {self.name})>'


class CommonCurrency(Base):
    __tablename__ = 'common_currency'
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    symbol = Column(String)
    symbol_native = Column(String)

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id}, {self.code}, {self.symbol}, {self.symbol_native})>'


class DataBase:
    INIT_KAM_KEYWORDS_CSV = 'kam_keywords.csv'
    INIT_CURRENCY_JSON = 'Common-Currency.json'

    def __init__(self, path):
        self.path = path


    @classmethod
    def init(cls, Base, name='foo'):
        path = f'sqlite:///{name}.db'
        engine = create_engine(path, echo=True)
        Base.metadata.create_all(engine)
        cls.insert_currencies_to_db(engine)
        cls.insert_kam_keywords_to_db(engine)
        return cls(path=path)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path
        self._engine = create_engine(path, echo=True)
        self._Session = sessionmaker(bind=self._engine)

    @property
    def engine(self):
        return self._engine

    @property
    def inspector(self):
        return inspect(self.engine)

    @contextmanager
    def Session(self):
        session = self._Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def insert_kam_keywords_to_db(cls, engine):
        kam_kws = pd.read_csv(cls.INIT_KAM_KEYWORDS_CSV, names=['keyword'])
        try:
            kam_kws.to_sql('key_audit_matter_keywords', con=engine,
                       if_exists='append', index=True, index_label='id')
        except Exception as e:
            print(e)

    @classmethod
    def insert_currencies_to_db(cls, engine):
        currency = pd.read_json(cls.INIT_CURRENCY_JSON)
        currency = currency.T.reset_index(drop=True)
        cols = ['code', 'symbol', 'symbol_native']
        try:
            currency[cols].to_sql('common_currency', con=engine,if_exists='append', index=True, index_label='id')
        except Exception as e:
            print(e)

    @property
    def tables(self) -> list:
        inspector = self.inspector
        tables = {tablename: [column['name'] + '*' if column['primary_key'] else column['name'] + '+' if column['name'] in flatten(
            [fk_col['constrained_columns'] for fk_col in inspector.get_foreign_keys(tablename)]) else column['name'] for column in inspector.get_columns(tablename)] for tablename in inspector.get_table_names()}
        return tables

    def show_tables(self):
        return {tablename: pd.DataFrame(pd.read_sql(f"select * from {tablename}", con = db.engine)) for tablename in db.tables.keys()}

    def add(self, instance):
        with self.Session() as session:
            session.add(instance)


if __name__ == "__main__":
    db = DataBase.init(Base)
    # kam_keywords = KeyAuditMatterKeywords(keyword='TESTING!!')
    # db.add(kam_keywords)
    with db.Session() as session:
        # print(session.query(KeyAuditMatterKeywords).all())
        currencies = session.query(CommonCurrency).all()
        for c in currencies:
            print(c.id, c.code)
    #     session.add(kam_keywords)

    # sql_df = pd.DataFrame(pd.read_sql("select * from key_audit_matter_keywords", con=db.engine))
    # print(sql_df)
    # sql_df = pd.DataFrame(pd.read_sql(
    #     "select * from common_currency", con=db.engine))
    # print(sql_df)
    

    # print(q_results)
    # sql_results = engine.execute('select * from key_audit_matter_keywords').fetchall()
    # print(len(sql_results))
    # for r in sql_results:
    #     print(r.keyword)


# charlie = User(first_name='Charlie')
# david = User(first_name='David')
# session.add(charlie)
# session.add(david)
# session.commit()
# users = session.query(User).all()
# for user in users:
#     print(f'user.fullname: {user.fullname}')
# print(f'user.fullname: {user.fullname}')
