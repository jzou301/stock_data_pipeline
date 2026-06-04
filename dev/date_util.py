# Import packages
import QuantLib as ql
import pandas as pd
import datetime as dt

class myDates:
    def __init__(self):
        self.calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
       
    def get_prev_business_day(self, date=ql.Date.todaysDate()):
        if isinstance(date, pd.Timestamp):
            date = self.timestamp_to_ql(date)
        elif isinstance(date, dt.date) or isinstance(date, dt.datetime):
            date = self.dt_to_ql(date)
        return self.calendar.advance(date, -1, ql.Days)

    def get_last_business_day(self, date=ql.Date.todaysDate()):
        if isinstance(date, pd.Timestamp):
            date = self.timestamp_to_ql(date)
        elif isinstance(date, dt.date) or isinstance(date, dt.datetime):
            date = self.dt_to_ql(date)
        if self.calendar.isBusinessDay(date): 
            return date
        else: 
            return self.calendar.advance(date, -1, ql.Days)

    def get_next_business_day(self, date=ql.Date.todaysDate()):
        if isinstance(date, pd.Timestamp):
            date = self.timestamp_to_ql(date)
        elif isinstance(date, dt.date) or isinstance(date, dt.datetime):
            date = self.dt_to_ql(date)
        return self.calendar.advance(date, 1, ql.Days)
        
    def dt_to_ql(self, dt_date):
        return ql.Date(dt_date.day, dt_date.month, dt_date.year)
    
    def timestamp_to_ql(self, ts_date):
        ts_date = ts_date.tz_localize(None)
        return ql.Date(ts_date.day, ts_date.month, ts_date.year)
    
    def ql_to_timestamp(self, ql_date):
        return pd.Timestamp(year=ql_date.year(), month=ql_date.month(), day=ql_date.dayOfMonth())
    
    def ql_vs_timestamp(self, ql_date, ts_date):
        converted_ts = self.timestamp_to_ql(ts_date)
        return ql_date == converted_ts
    
    def ql_vs_dt(self, ql_date, dt_date):
        return ql_date == self.dt_to_ql(dt_date)
    
    

