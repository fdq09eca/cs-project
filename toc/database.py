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

name = 'foo2'
path = f'sqlite:///{name}.db'
# path = 'sqlite:///:memory:'
engine = create_engine(path, echo=True)
Base = declarative_base(bind = engine)

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
    # created_on = Column(DateTime, default=datetime.now),
    # updated_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    audit_firms = relationship('Auditor', backref='annual_report')  # one to many
    kams = relationship('KeyAuditMatter', backref='annual_report') # one to many

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.news_id}, {self.date_time}, {self.stock_code}, {self.file_link})>"


class Auditor(Base):
    __tablename__ = 'auditor'
    id = Column(Integer, primary_key=True)
    news_id = Column(Integer, ForeignKey('annual_report.news_id'))
    name = Column(Text, nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.id}, {self.news_id}, {self.name})>"


class KeyAuditMatter(Base):
    __tablename__ = 'key_audit_matter'
    id = Column(Integer, primary_key=True)
    news_id = Column(Integer, ForeignKey('annual_report.news_id'))
    item = Column(Text)
    tags = relationship('KeyAuditMatterTag', backref='kam_item')

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.id}, {self.news_id} {self.item})>"


class KeyAuditMatterTag(Base):
    __tablename__ = 'key_audit_matter_tag'
    id = Column(Integer, primary_key=True)
    kam_id = Column(Integer, ForeignKey('key_audit_matter.id'))
    tag = Column(String)

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id}, {self.kam_id}, {self.tag})>'

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
    def init(cls, Base=Base, path=path):
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
            print('SESSION ROLLBACK!!')
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
        
    def add_all(self, iterables_instance):
        with self.Session() as session:
            session.add_all(iterables_instance)


if __name__ == "__main__":
    db = DataBase.init()
    print(db.show_tables())