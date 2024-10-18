import numpy as np
import RTLearner as rt
import random
import indicators
from util import get_crypto_data, get_data
import pandas as pd
import datetime as dt

import requests

class StrategyLearner(object):

    def __init__(self, symbol, learner=rt.RTLearner, kwargs={}, boost=False, impact=0.00, commission=0.00, verbose=False):
        self.learner = learner
        self.kwargs = kwargs
        self.bags = 100
        self.boost = boost
        self.learners = []
        self.commission = commission
        self.impact = impact
        self.data = []
        self.symbol = symbol
        self.sd = dt.datetime(2021, 1, 1)
        self.ed = dt.datetime(2022, 1, 1)
        self.rsi_window = 14
        self.ema_window = 50
        self.bb_window = 14
        self.stochastic_window1 = 14
        self.stochastic_window2 = 3
        self.macd_signal_short = 12
        self.macd_signal_long = 26
        self.macd_signal_window = 9
        self.start_index = max([self.rsi_window - 1, self.bb_window - 1, self.stochastic_window1 + self.stochastic_window2 - 2])
        self.changes = []
        self.days = 5
        np.random.seed(903951120)

        url = 'https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey=5ZKLWPZVUDZADNUU'
        r = requests.get(url)
        bond_json = r.json()
        df_data = [(entry['date'], float(entry['value'])) for entry in bond_json['data'] if entry['value'] != '.']
        # Creating DataFrame
        self.bond_data = pd.DataFrame(df_data, columns=['Date', 'Value'])
        self.bond_data['Date'] = pd.to_datetime(self.bond_data['Date'])
        self.bond_data.set_index('Date', inplace=True)
        self.bond_data = self.bond_data[self.bond_data.index.year >= 2010]
        full_range_dates = pd.date_range(start=self.bond_data.index.min(), end=self.bond_data.index.max())
        # Create a DataFrame with the full range of dates and NaN values
        full_range_df = pd.DataFrame(index=full_range_dates, columns=self.bond_data.columns)
        # Merge the full range DataFrame with the existing bond_data DataFrame
        merged_df = pd.merge(full_range_df, self.bond_data, how='left', left_index=True, right_index=True)
        # Forward fill the missing values
        merged_df = merged_df.ffill()
        # Update bond_data with the merged and forward-filled DataFrame
        self.bond_data = merged_df['Value_y']
        self.bond_data = self.bond_data.to_frame()
        self.bond_data.index = self.bond_data.index.tz_localize('UTC')


        print(self.bond_data)


    def add_evidence(self, symbol, sd, ed, crypto=False):
        if crypto:
            data = get_crypto_data(symbol=symbol, start_date=sd, end_date=ed)
        else:
            data = get_data(symbol=symbol, start_date=sd, end_date=ed)
        data.reset_index(level='symbol', inplace=True)
        closes = data['close']
        closes = closes.resample('D').mean()
        self.data = data
        self.symbol = symbol
        self.sd = sd
        self.ed = ed
        ema = indicators.ema(closes, self.ema_window)
        momentum = indicators.momentum(closes)
        rsi = indicators.rsi(closes, self.rsi_window)
        sto = indicators.stochastic(closes, self.stochastic_window1, self.stochastic_window2)
        bbp_upper, bbp_lower = indicators.bollinger_bands(closes, self.bb_window)
        macd_signal = indicators.macd_signal(closes, self.macd_signal_short, self.macd_signal_long, self.macd_signal_window)
        
        changes = closes.shift(-self.days)/closes

        combined_df = pd.concat([ema, momentum, rsi, sto, bbp_upper, bbp_lower, macd_signal, self.bond_data, changes], axis=1)
        combined_df = combined_df.dropna()
        all_data = combined_df.to_numpy()

        for i in range(self.bags):
            new_learner = self.learner(**self.kwargs)
            data = np.array([all_data[random.randint(0,len(all_data)-1)] for _ in range(len(all_data))])
            new_learner.add_evidence(data[:, 0:-1], data[:, -1])
            self.learners.append(new_learner)
        return

    def testPolicy(self, num_shares, sd_test, ed_test, crypto):
        symbol = self.symbol
        sd = sd_test
        ed = ed_test
        if crypto:
            data = get_crypto_data(symbol=symbol, start_date=sd, end_date=ed)
        else:
            data = get_data(symbol=symbol, start_date=sd, end_date=ed)
        data.reset_index(level='symbol', inplace=True)
        closes = data['close']
        closes = closes.resample('D').mean()

        ema = indicators.ema(closes, self.ema_window)
        momentum = indicators.momentum(closes)
        rsi = indicators.rsi(closes, self.rsi_window)
        sto = indicators.stochastic(closes, self.stochastic_window1, self.stochastic_window2)
        bbp_upper, bbp_lower = indicators.bollinger_bands(closes, self.bb_window)
        macd_signal = indicators.macd_signal(closes, self.macd_signal_short, self.macd_signal_long, self.macd_signal_window)

        combined_df = pd.concat([ema, momentum, rsi, sto, bbp_upper, bbp_lower, macd_signal, self.bond_data], axis=1)
        combined_df = combined_df.dropna()
        x = combined_df.to_numpy()

        results = np.array([self.learners[0].query(x)])
        for i in range(1, len(self.learners)):
            results = np.vstack((results, self.learners[i].query(x)))
        low_threshold = 1
        high_threshold = 1

        signals = np.ones((len(results), len(results[0])))

        buy = 1
        sell = 2

        for i in range(len(results)):
            for j in range(len(results[0])):
                if results[i][j] < low_threshold:
                    signals[i][j] = sell
                elif results[i][j] <= high_threshold:
                    signals[i][j] = 0


        signals = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=signals.astype(int))
        
        changes = closes.shift(-self.days)/closes

        changes = changes.to_numpy()
        changes[-1] = 1
        changes = changes[self.start_index:]

        #10-day
        new = []
        for i in range(0, len(signals), self.days):  # Generate signals every 10 days
            new.append((np.round(changes[i], 3), signals[i]))
        #End 10-day

        correct = 0
        wrong = 0
        for news in new:
            if (news[0] < 1 and news[1] == sell) or (news[0] > 1 and news[1] == buy):
                correct += 1
            elif news[1] == 0:
                continue
            else:
                wrong += 1
        print(correct, wrong)

        df_trades = pd.DataFrame()
        i = 0
        empty = True
        shares = 0
        
        while empty and i < len(signals):
            if signals[i] == buy:
                trades_data = [{"Date": combined_df.index[i], "Symbol": symbol, "Order": "BUY", "Shares": num_shares}]
                df_trades = pd.DataFrame(trades_data)
                shares = num_shares
                empty = False
            #10-day
            i += self.days

        #10-day
        for pred in range(i, len(signals), self.days):

            if signals[pred] == sell and shares == num_shares:
                trades_data = [{"Date": combined_df.index[pred], "Symbol": symbol, "Order": "SELL", "Shares": num_shares}]
                new_trade = pd.DataFrame(trades_data)
                df_trades = pd.concat([df_trades, new_trade], ignore_index=True)
                shares = 0
            if signals[pred] == buy and shares == 0:
                trades_data = [{"Date": combined_df.index[pred], "Symbol": symbol, "Order": "BUY", "Shares": num_shares}]
                new_trade = pd.DataFrame(trades_data)
                df_trades = pd.concat([df_trades, new_trade], ignore_index=True)
                shares = num_shares

        print(df_trades)
        df_trades = df_trades.set_index('Date')
        return df_trades

    #For experiment 2
    """def get_trade(self, current_position, crypto):
        symbol = self.symbol
        sd_recent = dt.datetime.utcnow() - dt.timedelta(days = 1.1*max([self.rsi_window, self.ema_window, self.bb_window, self.stochastic_window2]))
        ed_recent = dt.datetime.utcnow()
        ed_recent = dt.datetime(ed_recent.year, ed_recent.month, ed_recent.day)
        if crypto:
            recent_data = get_crypto_data(symbol=symbol, start_date=sd_recent, end_date=ed_recent)
        else:
            recent_data = get_data(symbol=symbol, start_date=sd_recent, end_date=ed_recent)
        recent_data.reset_index(level='symbol', inplace=True)
        print("Last pulled bar\n", recent_data.iloc[-1])
        ema = indicators.ema(recent_data['close'], self.ema_window, True)
        momentum = indicators.momentum(recent_data['close'], True)
        rsi = indicators.rsi(recent_data['close'], self.rsi_window, True)
        sto = indicators.stochastic(recent_data['close'], self.stochastic_window1, self.stochastic_window2)
        bb_upper, bb_lower = indicators.bollinger_bands(recent_data['close'], self.bb_window)
        combined_df = pd.concat([ema, momentum, rsi, sto], axis=1)
        combined_df = combined_df.dropna()
        x = combined_df.to_numpy()

        nan_mask = np.isnan(x).any(axis=1)
        x = x[~nan_mask]

        results = []
        for i in range(len(self.learners)):
            results.append(self.learners[i].query([x[-1]]))
        low_threshold = 1 - self.impact
        high_threshold = 1 + self.impact

        buys = 0
        sells = 0
        holds = 0

        for i in range(len(results)):
            if results[i] < low_threshold:
                sells += 1
            elif results[i] <= high_threshold:
                holds += 1
            else:
                buys += 1

        print("Buys, sells, holds: ", buys, sells, holds)
        if buys > sells and buys > holds and current_position == 0:
            return 1
        elif sells > buys and sells > holds and not current_position == 0:
            return -1
        else:
            return 0"""
