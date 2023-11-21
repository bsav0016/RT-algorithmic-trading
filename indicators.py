import os	   		  		 		  		  		    	 		 		   		 		  
import numpy as np  		  	   		  		 		  		  		    	 		 		   		 		  
  		  	   		  		 		  		  		    	 		 		   		 		  
import pandas as pd  		  	   		  		 		  		  		    	 		 		   		 		  
import datetime as dt


def bollinger_bands(test_data, bb_window, sd, ed):
  data = test_data.copy()
  sma = test_data.rolling(window=bb_window).mean()
  std = test_data.rolling(window=bb_window).std()
  bb_lower = sma-2*std
  bb_upper = sma+2*std
  bbp_lower = (data-bb_lower)/bb_lower
  bbp_upper = (data-bb_upper)/bb_upper
  return bbp_lower, bbp_upper

def rsi(test_data, rsi_window, sd, ed, verbose=False):
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

def ema(test_data, ema_window, sd, ed, verbose=False):
  ema = test_data.ewm(span=ema_window, adjust=False).mean()-test_data
  if verbose:
    print("EMA: ", ema.iloc[-1])
  return ema

def momentum(test_data, sd, ed, verbose=False):
  momentum = test_data/test_data.shift(1)
  if verbose:
    print("Momentum: ", momentum.iloc[-1])
  return momentum

def stochastic(test_data, stochastic_window1, stochastic_window2, sd, ed):
  data = test_data.copy()
  data['High'] = test_data.rolling(window=stochastic_window1).max()
  data['Low'] = test_data.rolling(window=stochastic_window1).min()
  data['K'] = 100 * ((test_data-data['Low']) / (data['High']-data['Low']))
  data['D'] = data['K'].rolling(window=stochastic_window2).mean()
  return stochastic
