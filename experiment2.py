import datetime as dt

import StrategyLearner as sl
import marketsimcode as msc
from ManualStrategy import benchmark_trades as benchmark_strategy  

import util

from alpaca_trade_api.stream import Stream
import asyncio
import time

symbol = "ETH/USD"
crypto = True
"""symbol = "AAPL"
crypto = False"""

def get_buy_power():
    return util.get_buy_power()

def get_current_position(symbol):
    return util.get_current_position(symbol)

def get_trade(symbol, sd_in, ed_in, impact, commission, current_position, crypto=False):
    learner = sl.StrategyLearner(verbose=False, impact=impact, commission=commission)
    learner.add_evidence(symbol=symbol, sd=sd_in, ed=ed_in, crypto=crypto)

    return learner.get_trade(current_position)

def make_trade(symbol, quantity, order_type, crypto):
    util.make_trade(symbol, quantity, order_type, crypto)
    return

async def run_experiment(bar):
    timestamp = bar.timestamp
    timestamp /= 10**9
    if crypto:
        if not int(timestamp % 86400) == 0:
            return
    else:
        if not int(timestamp % 86400) == 52140:
            return
    print("Bar", bar)
    price = bar.close
    commission = 0
    impact = 0.005
    sd_in = dt.date.today() - dt.timedelta(days = 365)
    ed_in = dt.date.today()
    sd_in = dt.datetime(sd_in.year, sd_in.month, sd_in.day)
    ed_in = dt.datetime(ed_in.year, ed_in.month, ed_in.day)

    print(sd_in, ed_in)

    buy_power = get_buy_power()
    current_position = get_current_position(symbol)
    trade_type = get_trade(symbol, sd_in, ed_in, impact, commission, current_position, crypto)
    quantity = float(buy_power)/float(price)*0.95
    if trade_type == -1:
        quantity = current_position
    make_trade(symbol, quantity, trade_type, crypto)
    
    return

def run_connection(conn):
    try:
        conn.run()
    except KeyboardInterrupt:
        print("Interrupted execution by user")
        asyncio.get_event_loop().run_until_complete(conn.stop_ws())
        exit(0)
    except Exception as e:
        print(f'Exception from websocket connection: {e}')
    finally:
        print("Trying to re-establish connection")
        time.sleep(3)
        run_connection(conn)

def stream_data(symbol):
    conn = Stream(util.get_api_key(),
                  util.get_secret_key(),
                  base_url=util.get_base_url(),
                  data_feed='iex')

    if crypto:
        conn.subscribe_crypto_bars(run_experiment, symbol)
    else:
        conn.subscribe_bars(run_experiment, symbol)

    run_connection(conn)

if __name__ == "__main__":
    stream_data(symbol)
    