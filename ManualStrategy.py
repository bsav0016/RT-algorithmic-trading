from datetime import timedelta

import pandas as pd
from util import get_crypto_data, get_data

import indicators

def testPolicy(symbol, sd, ed, sv, crypto):
    if crypto:
        data = get_crypto_data(symbol=symbol, start_date=sd, end_date=ed)
    else:
        data = get_data(symbol=symbol, start_date=sd, end_date=ed)
    data.reset_index(level='symbol', inplace=True)
    rsi_window = 14
    rsi_low = 45
    rsi_high = 55
    ema_window = 14
    rsi = indicators.rsi(data['close'], rsi_window, sd, ed)
    ema = indicators.ema(data['close'], ema_window, sd, ed)
    momentum = indicators.momentum(data['close'], sd, ed)
    df_trades = pd.DataFrame()
    counter = 0
    for i, r in data.iterrows():
        if i == ed:
            pass
        next_date = i + timedelta(days=1)
        next_date_str = next_date.strftime('%Y-%m-%d')
        if df_trades.empty:
            while not next_date_str in data.index:
                next_date = next_date + timedelta(days=1)
                next_date_str = next_date.strftime('%Y-%m-%d')
            if rsi.iloc[counter] < rsi_low and ema.iloc[counter] < 0 and momentum.iloc[counter] < 1:
                trades_data = [{"Date": i, "Symbol": symbol, "Order": "BUY", "Shares": 1000}]
                df_trades = pd.DataFrame(trades_data)
                current_holdings = 1000
            elif rsi.iloc[counter] > rsi_high and ema.iloc[counter] > 0 and momentum.iloc[counter] > 1:
                trades_data = [{"Date": i, "Symbol": symbol, "Order": "SELL", "Shares": 1000}]
                df_trades = pd.DataFrame(trades_data)
                current_holdings = -1000
            else:
                pass
        else:
            while (not next_date_str in data.index) and next_date <= ed:
                next_date = next_date + timedelta(days=1)
                next_date_str = next_date.strftime('%Y-%m-%d')
            if next_date <= ed:
                if rsi.iloc[counter] < rsi_low and ema.iloc[counter] < 0 and momentum.iloc[counter] < 1:
                    if current_holdings == -1000:
                        trades_data = [{"Date": i, "Symbol": symbol, "Order": "BUY", "Shares": 2000}]
                        df_trades = df_trades.append(trades_data, ignore_index=True)
                        current_holdings = 1000
                elif rsi.iloc[counter] > rsi_high and ema.iloc[counter] > 0 and momentum.iloc[counter] > 1:
                    if current_holdings == 1000:
                        trades_data = [{"Date": i, "Symbol": symbol, "Order": "SELL", "Shares": 2000}]
                        df_trades = df_trades.append(trades_data, ignore_index=True)
                        current_holdings = -1000
        counter += 1
    if not df_trades.iloc[-1]['Date'] == ed:
        end_data = [{"Date": ed, "Symbol": symbol, "Order": "SELL", "Shares": 1000}]
        df_trades = df_trades.append(end_data, ignore_index=True)
    df_trades.set_index('Date', inplace=True)
    return df_trades


def benchmark_trades(symbol, sd, ed, sv, num_shares, crypto):
    if crypto:
        data = get_crypto_data(symbol=symbol, start_date=sd, end_date=ed)
    else:
        data = get_data(symbol=symbol, start_date=sd, end_date=ed)
    data.reset_index(level='symbol', inplace=True)
    data = data['close']
    date = data.index[0]
    start_data = [{"Date": date, "Symbol": symbol, "Order": "BUY", "Shares": num_shares}]
    benchmark = pd.DataFrame(start_data)
    end_date = data.index[-1]
    end_data = [{"Date": end_date, "Symbol": symbol, "Order": "SELL", "Shares": num_shares}]
    end_data = pd.DataFrame(end_data)
    benchmark = pd.concat([benchmark, end_data], ignore_index=True)
    benchmark.set_index('Date', inplace=True)
    return benchmark
