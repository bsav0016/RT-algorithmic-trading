import numpy as np
import RTLearner as rt
import random
import indicators
from util import get_crypto_data, get_data
import pandas as pd
import datetime as dt

class StrategyLearner(object):

    def __init__(self, learner=rt.RTLearner, kwargs={}, bags=10, boost=False, impact=0.00, commission=0.00, verbose=False):
        self.learner = learner
        self.kwargs = kwargs
        self.bags = bags
        self.boost = boost
        self.learners = []
        self.commission = commission
        self.impact = impact
        self.data = []
        self.symbol = "BTC/USD"
        self.sd = dt.datetime(2021, 1, 1)
        self.ed = dt.datetime(2021, 12, 31)
        self.sv = 100000
        np.random.seed(903951120)

    def add_evidence(self, symbol, sd, ed, crypto=False):
        if crypto:
            data = get_crypto_data(symbol=symbol, start_date=sd, end_date=ed)
        else:
            data = get_data(symbol=symbol, start_date=sd, end_date=ed)
        data.reset_index(level='symbol', inplace=True)
        self.data = data
        self.symbol = symbol
        self.sd = sd
        self.ed = ed
        rsi_window = 14  
        ema_window = 14
        rsi = indicators.rsi(data['close'], rsi_window)
        ema = indicators.ema(data['close'], ema_window)
        momentum = indicators.momentum(data['close'])
        combined_df = pd.concat([rsi, ema, momentum], axis=1)
        x = combined_df.values
        changes = data['close']/data['close'].shift(1)
        y = changes.values

        all_data = np.array([np.append(x[i], y[i]) for i in range(len(x))])
        nan_mask = np.isnan(all_data).any(axis=1)
        all_data = all_data[~nan_mask]

        for i in range(self.bags):
            new_learner = self.learner(**self.kwargs)
            data = np.array([all_data[random.randint(0,len(all_data)-1)] for j in range(len(all_data))])
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
        sv = self.sv
        rsi_window = 14
        ema_window = 14
        rsi = indicators.rsi(data['close'], rsi_window)
        ema = indicators.ema(data['close'], ema_window)
        momentum = indicators.momentum(data['close'])
        combined_df = pd.concat([rsi, ema, momentum], axis=1)
        combined_df = combined_df.dropna()
        x = combined_df.to_numpy()

        nan_mask = np.isnan(x).any(axis=1)
        x = x[~nan_mask]

        results = np.array([self.learners[0].query(x[1:])])
        for i in range(1, len(self.learners)):
            results = np.vstack((results, self.learners[i].query(x[1:])))
        low_threshold = 1 - self.impact
        high_threshold = 1 + self.impact

        signals = np.ones((len(results), len(results[0])))

        buy = 1
        sell = -1
        temp_sell = 2

        for i in range(len(results)):
            for j in range(len(results[0])):
                if results[i][j] < low_threshold:
                    signals[i][j] = temp_sell
                elif results[i][j] <= high_threshold:
                    signals[i][j] = 0

        signals = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=signals.astype(int))

        for i in range(len(signals)):
            if signals[i] == temp_sell:
                signals[i] = sell

        df_trades = pd.DataFrame()
        i = 0
        empty = True
        shares = 0
        
        while empty and i < len(signals):
            if signals[i] == 1:
                trades_data = [{"Date": combined_df.index[i], "Symbol": symbol, "Order": "BUY", "Shares": num_shares}]
                df_trades = pd.DataFrame(trades_data)
                shares = num_shares
                empty = False
            i += 1

        for pred in range(i, len(signals)):
            if signals[pred] == -1 and shares == num_shares:
                trades_data = [{"Date": combined_df.index[pred], "Symbol": symbol, "Order": "SELL", "Shares": num_shares}]
                new_trade = pd.DataFrame(trades_data)
                df_trades = pd.concat([df_trades, new_trade], ignore_index=True)
                shares = 0
            if signals[pred] == 1 and shares == 0:
                trades_data = [{"Date": combined_df.index[pred], "Symbol": symbol, "Order": "BUY", "Shares": num_shares}]
                new_trade = pd.DataFrame(trades_data)
                df_trades = pd.concat([df_trades, new_trade], ignore_index=True)
                shares = num_shares

        df_trades = df_trades.set_index('Date')
        return df_trades

    def get_trade(self, current_position, crypto):
        data = self.data
        symbol = self.symbol
        sv = self.sv
        rsi_window = 14
        ema_window = 14
        sd_recent = dt.datetime.utcnow() - dt.timedelta(days = 2*max([rsi_window, ema_window]))
        ed_recent = dt.datetime.utcnow()
        if crypto:
            recent_data = get_crypto_data(symbol=symbol, start_date=sd_recent, end_date=ed_recent)
        else:
            recent_data = get_data(symbol=symbol, start_date=sd_recent, end_date=ed_recent)
        recent_data.reset_index(level='symbol', inplace=True)
        print("Last pulled bar", recent_data.iloc[-1])
        rsi = indicators.rsi(recent_data['close'], rsi_window, True)
        ema = indicators.ema(recent_data['close'], ema_window, True)
        momentum = indicators.momentum(recent_data['close'], True)
        combined_df = pd.concat([rsi, ema, momentum], axis=1)
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
            return 0
