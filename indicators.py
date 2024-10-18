import os	   		  		 		  		  		    	 		 		   		 		  
import numpy as np  		  	   		  		 		  		  		    	 		 		   		 		  
  		  	   		  		 		  		  		    	 		 		   		 		  
import pandas as pd  		  	   		  		 		  		  		    	 		 		   		 		  
import datetime as dt


def bollinger_bands(test_data, bb_window):
  data = test_data.copy()
  sma = test_data.rolling(window=bb_window).mean()
  std = test_data.rolling(window=bb_window).std()
  bb_lower = sma-2*std
  bb_upper = sma+2*std
  bbp_lower = (data-bb_lower)/bb_lower
  bbp_upper = (data-bb_upper)/bb_upper
  return bbp_lower, bbp_upper

def rsi(test_data, rsi_window, verbose=False):
  data = test_data.copy()
  data['Diff'] = data - data.shift(1)
  data['Gain'] = data['Diff'].where(data['Diff'] > 0, 0)
  data['Loss'] = -data['Diff'].where(data['Diff'] < 0, 0)

  avg_gain = data['Gain'].rolling(window=rsi_window).mean()
  avg_loss = data['Loss'].rolling(window=rsi_window).mean()
  rsi = 100-(100/(1+avg_gain/avg_loss))
  if verbose:
    print("RSI: ", rsi.iloc[-1])
  return rsi

def ema(test_data, ema_window, verbose=False):
  data = test_data.copy()
  ema = (data.ewm(span=ema_window, adjust=False).mean()-data) / data
  if verbose:
    print("EMA: ", ema.iloc[-1])
  return ema

def momentum(test_data, verbose=False):
  data = test_data.copy()
  momentum = data/data.shift(1)
  if verbose:
    print("Momentum: ", momentum.iloc[-1])
  return momentum

def stochastic(test_data, stochastic_window1, stochastic_window2):
  data = test_data.copy()
  data['High'] = test_data.rolling(window=stochastic_window1).max()
  data['Low'] = test_data.rolling(window=stochastic_window1).min()
  data['K'] = 100 * ((test_data-data['Low']) / (data['High']-data['Low']))
  data['D'] = data['K'].rolling(window=stochastic_window2).mean()
  return data['D']

def macd_signal(test_data, short_window, long_window, signal_window):
  data = test_data.copy()
  short_ema = data.ewm(span=short_window, adjust=False).mean()
  long_ema = data.ewm(span=long_window, adjust=False).mean()
  
  # Calculate MACD line
  macd_line = short_ema - long_ema
  
  # Calculate signal line (EMA of MACD)
  signal_line = macd_line.ewm(span=signal_window, adjust=False).mean()
  
  return signal_line
