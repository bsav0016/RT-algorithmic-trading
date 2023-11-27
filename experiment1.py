import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd

import StrategyLearner as sl
import marketsimcode as msc
from ManualStrategy import benchmark_trades as benchmark_strategy

def ensure_tz_aware(timestamp, tz='UTC'):
    if timestamp.tzinfo is None:
        return timestamp.tz_localize(tz)
    else:
        return timestamp

def strategy_learner(symbol, sd_in, ed_in, sd_out, ed_out, sv, commission, impact, num_shares, crypto):
    learner = sl.StrategyLearner(verbose=False, impact=impact, commission=commission)
    learner.add_evidence(symbol=symbol, sd=sd_in, ed=ed_in, crypto=crypto)
 
    df_trades_in = learner.testPolicy(num_shares=num_shares, sd_test=sd_in, ed_test=ed_in, crypto=crypto)
    df_trades_out = learner.testPolicy(num_shares=num_shares, sd_test=sd_out, ed_test=ed_out, crypto=crypto)

    sl_portvals_in = msc.compute_portvals(df_trades_in, sv, commission, impact, crypto)
    sl_portvals_out = msc.compute_portvals(df_trades_out, sv, commission, impact, crypto)

    if not sl_portvals_in.index[0] == sd_in:
        sl_portvals_in = pd.concat([pd.DataFrame({'Value': [sv]}, index=[sd_in]), sl_portvals_in])
    if not sl_portvals_out.index[0] == sd_out:
        sl_portvals_out = pd.concat([pd.DataFrame({'Value': [sv]}, index=[sd_out]), sl_portvals_out])

    print(sl_portvals_out)

    date_range_in = pd.date_range(start=sd_in, end=ed_in)
    date_range_out = pd.date_range(start=sd_out, end=ed_out)
    date_range_in = date_range_in.map(lambda x: ensure_tz_aware(x, tz='UTC'))
    date_range_out = date_range_out.map(lambda x: ensure_tz_aware(x, tz='UTC'))


    sl_portvals_in.index = sl_portvals_in.index.to_series().apply(ensure_tz_aware, tz='UTC')
    sl_portvals_out.index = sl_portvals_out.index.to_series().apply(ensure_tz_aware, tz='UTC')
    sl_portvals_in = sl_portvals_in.sort_index(ascending=False)
    sl_portvals_out = sl_portvals_out.sort_index(ascending=False)
    sl_portvals_in = sl_portvals_in.reindex(index=date_range_in, method='ffill')
    sl_portvals_out = sl_portvals_out.reindex(index=date_range_out, method='ffill')
    print(sl_portvals_out)

    return sl_portvals_in, sl_portvals_out

def get_results(symbol, sd, ed, sv, commission, impact, num_shares, crypto):

    benchmark_trades = benchmark_strategy(symbol, sd, ed, sv, num_shares, crypto)
    benchmark_portvals = msc.compute_portvals(benchmark_trades, sv, commission, impact, crypto)

    return benchmark_portvals

def run_experiment():
    start_val = 100000
    commission = 0
    impact = 0.0025
    symbol = "ETH/USD"
    crypto = True
    num_shares = 25
    sd_in = dt.datetime(2021, 11, 27)
    ed_in = dt.datetime(2022, 11, 27)
    sd_out = dt.datetime(2022, 11, 27)
    ed_out = dt.datetime(2023, 11, 27)
    in_sample = get_results(symbol, sd_in, ed_in, start_val, commission, impact, num_shares, crypto)
    sl_result = strategy_learner(symbol, sd_in, ed_in, sd_out, ed_out, start_val, commission, impact, num_shares, crypto)
    sl_result_in = sl_result[0]

    plt.figure()
    title = "Benchmark and Strategy Learner Normalized Prices for In Sample"
    xlabel = "Date"
    ylabel = "Normalized Price"
    ax = (in_sample/start_val).plot(title=title, color='red', fontsize=12)
    (sl_result_in/start_val).plot(ax=ax, color='blue', label='Strategy Learner')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(["Benchmark", "Strategy Learner"])
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig('in_sample.png')

    out_sample = get_results(symbol, sd_out, ed_out, start_val, commission, impact, num_shares, crypto)
    sl_result_out = sl_result[1]

    plt.figure()
    title = "Benchmark and Strategy Learner Normalized Prices for Out Sample"
    xlabel = "Date"
    ylabel = "Normalized Price"
    ax = (out_sample/start_val).plot(title=title, color='red', fontsize=12)
    (sl_result_out/start_val).plot(ax=ax, color='blue', label='Strategy Learner')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(["Benchmark", "Strategy Learner"])
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig('out_sample.png')

if __name__ == "__main__":
    run_experiment()