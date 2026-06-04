import datetime as dt
import QuantLib as ql
import pandas as pd


class DateUtils:
    def __init__(self, calendar: ql.Calendar = None):
        self.calendar = calendar or ql.UnitedStates(ql.UnitedStates.NYSE)
    
    def get_prev_business_day(self, date=ql.Date.todaysDate()):
        if isinstance(date, pd.Timestamp):
            date = self.timestamp_to_ql(date)
        elif isinstance(date, (dt.date, dt.datetime)):
            date = self.dt_to_ql(date)
        
        return self.calendar.advance(date, -1, ql.Days)
    
    def get_last_business_day(self, date=ql.Date.todaysDate()): 
        if isinstance(date, pd.Timestamp):
            date = self.timestamp_to_ql(date)
        elif isinstance(date, (dt.date, dt.datetime)):
            date = self.dt_to_ql(date)
        
        if self.calendar.isBusinessDay(date):
            return date
        else:
            return self.calendar.advance(date, -1, ql.Days)
    
    def get_next_business_day(self, date=ql.Date.todaysDate()) -> ql.Date:
        if isinstance(date, pd.Timestamp):
            date = self.timestamp_to_ql(date)
        elif isinstance(date, (dt.date, dt.datetime)):
            date = self.dt_to_ql(date)
        
        return self.calendar.advance(date, 1, ql.Days)
    
    def advance(self, start_date, period, unit):
        return self.calendar.advance(start_date, period, unit)
    
    @staticmethod
    def dt_to_ql(dt_date):
        return ql.Date(dt_date.day, dt_date.month, dt_date.year)
    
    @staticmethod
    def timestamp_to_ql(ts_date):
        ts_date = ts_date.tz_localize(None)
        return ql.Date(ts_date.day, ts_date.month, ts_date.year)
    
    @staticmethod
    def ql_to_timestamp(ql_date):
        return pd.Timestamp(year=ql_date.year(), month=ql_date.month(), day=ql_date.dayOfMonth())
    
    @staticmethod
    def ql_to_datetime(ql_date):
        return dt.datetime(ql_date.year(), ql_date.month(), ql_date.dayOfMonth())
    
    @staticmethod
    def ql_vs_timestamp(ql_date, ts_date):
        converted_ts = DateUtils.timestamp_to_ql(ts_date)
        return ql_date == converted_ts
    
    @staticmethod
    def ql_vs_dt(ql_date, dt_date) -> bool:
        return ql_date == DateUtils.dt_to_ql(dt_date)
    
    @staticmethod
    def ql_to_string(ql_date: ql.Date, fmt: str = '%Y-%m-%d') -> str:
        if fmt == 'ISO': return ql_date.ISO()
        dt_date = DateUtils.ql_to_datetime(ql_date)
        return dt_date.strftime(fmt)
    
    @staticmethod
    def string_to_ql(date_str: str, fmt: str = '%Y-%m-%d') -> ql.Date:
        dt_date = dt.datetime.strptime(date_str, fmt)
        return DateUtils.dt_to_ql(dt_date)
    
    def business_days_between(self, start: ql.Date, end: ql.Date) -> int:
        return self.calendar.businessDaysBetween(start, end)
    
    @staticmethod
    def compare_dates(ql_date: ql.Date, pd_timestamp: pd.Timestamp) -> bool:
        return DateUtils.ql_vs_timestamp(ql_date, pd_timestamp)

