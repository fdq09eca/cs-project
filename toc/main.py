from annual_report import AnnualReport
from hkex_api import HKEX_API
import database as DB
from logger import Logger

class Worker(Logger):
    
    def __init__(self, db_path=DB.path, query = HKEX_API(), verbose = True):
        super().__init__()
        self.db = DB.DataBase()
        self.query = query
        if verbose:
            super().show_stream_log()
    
    @property
    def last_entry(self, table = DB.AnnualReport):
        last_entry = self.db.last_entry(table)
        self.logger.info(f'Last entry of {table.__tablename__}: {last_entry}')
        return last_entry
    
    @property
    def all_news_ids(self, table = DB.AnnualReport):
        news_ids = self.db.all_news_ids(table)
        return news_ids

    @property
    def query(self):
        return self._query

    @query.setter
    def query(self, query):
        self._query = query
        self._datas = self._query.get_data()
        all_news_ids = self.all_news_ids
        self._datas = [data for data in self._datas if int(data.news_id) not in all_news_ids]
        self.logger.info(f'{len(self._datas)} rows of new data since last run.')
    
    @property
    def datas(self):
        return self._datas
    
    @Logger.track
    def start(self):
        datas = self.datas
        for data in datas:
            self.logger.info(f'Start processing {data}')
            
            annual_report = AnnualReport.create(
            news_id = data.news_id,
            date_time = data.date_time,
            stock_code = data.stock_code,
            stock_name = data.stock_name,
            title = data.title,
            long_text = data.long_text,
            src = data.file_link,
            file_info = data.file_info
            )

            if annual_report:
                try:
                    annual_report.add_to_db()
                except Exception as e:
                    self.logger.error(e)
                    continue
            self.logger.info(f'Finish processing {data}')
            self.logger.info(f'{datas.index(data)/len(datas):.2%} complete. {len(datas) - (datas.index(data) + 1)} remains.')
    
    def get_market_share(self, pct = False, alphabetical_order=False):
        df_auditors = self.db.query_auditors()
        df_auditors['auditors'] = df_auditors.auditors.str.upper().str.replace(r'\s+', ' ')
        df_market_share = (df_auditors.auditors.value_counts(normalize=True).mul(100).round(2).astype(str) + '%').rename_axis('auditors').to_frame('pct') if pct else \
            df_auditors.auditors.value_counts().rename_axis('auditors').to_frame('count')
        return df_market_share.sort_index() if alphabetical_order else df_market_share
    
    def kam_tags_to_csv(self):
        df_kam_tags =  self.db.query_kams_tags()
        kam_tags = df_kam_tags.tag.sort_values().unique().to_list()
        for tag in kam_tags:
            df_relative_annual_report = 



if __name__ == '__main__':
    worker = Worker()
    print(worker.get_market_share(pct=True))
