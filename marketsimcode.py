import datetime as dt
from datetime import timedelta
from datetime import time
import os  		  	   		  		 		  		  		    	 		 		   		 		  
  		  	   		  		 		  		  		    	 		 		   		 		  
import numpy as np  		  	   		  		 		  		  		    	 		 		   		 		  	  		 		  		  		    	 		 		   		 		  
import pandas as pd  	

from util import get_crypto_data, get_data
  		  	   		  		 		  		  		    	 	
def compute_portvals(  		  	   		  		 		  		  		    	 		 		   		 		  
    trades,
    start_val=1000000,  		  	   		  		 		  		  		    	 		 		   		 		  
    commission=9.95,  		  	   		  		 		  		  		    	 		 		   		 		  
    impact=0.005,
    crypto=False  		  	   		  		 		  		  		    	 		 		   		 		  
):  	

    df = trades.copy()
    df.sort_index(ascending=True)
    start_date = df.index[0]
    end_date = df.index[-1]
    stock_names = []
    stock_values = []
    data = []
    cash = start_val
    portvals = []
    for i, r in df.iterrows():
        try:
            stock_value = data[0].loc[i]
        except:
            if crypto:
                stock_value = get_crypto_data(symbol=r["Symbol"], start_date=i, end_date=i+timedelta(days=5)).iloc[0]['close'] #Should this be iloc[-1]?
            else:
                stock_value = get_data(symbol=r["Symbol"], start_date=i, end_date=i+timedelta(days=5)).iloc[0]['close'] #Should this also be iloc[-1]?
        if i == start_date:
            try:
                index = stock_names.index(r["Symbol"])
                if r["Order"] == 'BUY':
                    stock_values[index] += r["Shares"]
                    cash -= stock_value * r["Shares"]
                    cash -= (commission + stock_value * impact * r["Shares"])
                else:
                    stock_values[index] -= r["Shares"]
                    cash += stock_value * r["Shares"]
                    cash -= (commission + stock_value * impact * r["Shares"])
            except:
                stock_names.append(r["Symbol"])
                if crypto:
                    daily_vals = get_crypto_data(symbol=r['Symbol'], start_date=start_date, end_date=end_date).ffill()
                else:
                    daily_vals = get_data(symbol=r['Symbol'], start_date=start_date, end_date=end_date).ffill()
                daily_vals.reset_index(level='symbol', inplace=True)
                daily_vals = daily_vals['close']
                daily_vals = daily_vals.resample('D').mean()
                if i == start_date:
                    data = [daily_vals]
                else:
                    data.append(daily_vals)
                if r["Order"] == 'BUY':
                    stock_values.append(r["Shares"])
                    cash -= stock_value * r["Shares"]
                    cash -= (commission + stock_value * impact * r["Shares"])
                else:
                    stock_values.append(-r["Shares"])
                    cash += stock_value * r["Shares"]
                    cash -= (commission + stock_value * impact * r["Shares"])
            total = calculate_total(cash, stock_names, stock_values, i, data)
            portvals = pd.DataFrame({'Value': [total]}, index=[start_date])

        else:
            date = portvals.index[-1]
            date = date + timedelta(days=1)
            while date < i:
                try:
                    total = calculate_total(cash, stock_names, stock_values, date, data)
                    new_portval = pd.DataFrame({'Value': total}, index=[date])
                    portvals = pd.concat([portvals, new_portval], ignore_index=False)
                    date = date + timedelta(days=1)
                except:
                    date = date + timedelta(days=1)
            try:
                index = stock_names.index(r["Symbol"])
                if r["Order"] == 'BUY':
                    stock_values[index] += r["Shares"]
                    cash -= stock_value*r["Shares"]
                    cash -= (commission+stock_value*impact*r["Shares"])
                else:
                    stock_values[index] -= r["Shares"]
                    cash += stock_value*r["Shares"]
                    cash -= (commission+stock_value*impact*r["Shares"])
            except:
                stock_names.append(r["Symbol"])
                if i == start_date:
                    daily_vals = get_data([r["Symbol"]], pd.date_range(start_date, end_date)).ffill()
                    daily_vals = daily_vals.resample('D').mean()
                    data = [daily_vals]
                else:
                    daily_vals = get_data([r["Symbol"]], pd.date_range(start_date, end_date)).ffill()
                    daily_vals = daily_vals.resample('D').mean()
                    data.append(daily_vals)
                if r["Order"] == 'BUY':
                    stock_values.append(r["Shares"])
                    cash -= stock_value*r["Shares"]
                    cash -= (commission+stock_value*impact*r["Shares"])
                else:
                    stock_values.append(-r["Shares"])
                    cash += stock_value*r["Shares"]
                    cash -= (commission+stock_value*impact*r["Shares"])
        total = calculate_total(cash, stock_names, stock_values, i, data)
        if total:
            new_portval = pd.DataFrame({'Value': total}, index=[i])
            portvals = pd.concat([portvals, new_portval], ignore_index=False)
    portvals = portvals[~portvals.index.duplicated(keep='last')]

    return portvals

def calculate_total(cash, stock_names, stock_values, date, data):
    total = cash
    new_date = date.replace(hour=0)
    try:
        daily_val = data[0].loc[new_date]
        total += stock_values[0]*daily_val
        return total
    except:
        print("Could not find date: ", new_date)
        return None
    
