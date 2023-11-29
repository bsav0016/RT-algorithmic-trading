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

current_day = True

def get_buy_power():
    return util.get_buy_power()

def get_current_position(symbol):
    return util.get_current_position(symbol)

def get_trade(symbol, sd_in, ed_in, impact, commission, current_position, crypto=False):
    learner = sl.StrategyLearner(verbose=False, impact=impact, commission=commission)
    learner.add_evidence(symbol=symbol, sd=sd_in, ed=ed_in, crypto=crypto)

    return learner.get_trade(current_position, crypto)

def make_trade(symbol, quantity, order_type, crypto):
    util.make_trade(symbol, quantity, order_type, crypto)
    return

async def run_experiment(bar):
    global current_day
    if current_day == True:
        current_day = dt.datetime.utcnow().date() - dt.timedelta(days = 2)
        #current_day = dt.date.today() - dt.timedelta(days = 1)
    timestamp = bar.timestamp
    timestamp_seconds = timestamp/10**9
    converted_datetime = dt.date.fromtimestamp(timestamp_seconds)
    seconds_in_day = timestamp_seconds % 86400
    bar_start = 21659 # we need to wait for the old bar to load (06:00:59 gives extra time)
    too_late = 43200 # we don't want to do anything if it's afternoon
    #too_late = 86400 # for testing only
    if converted_datetime == current_day or seconds_in_day <= bar_start or seconds_in_day > too_late:
        return
    else:
        current_day = converted_datetime
    price = bar.close
    commission = 0
    impact = 0.004
    sd_in = dt.datetime.utcnow() - dt.timedelta(days = 365)
    ed_in = dt.datetime.utcnow()
    sd_in = dt.datetime(2022, 5, 27) #testing new method
    ed_in = dt.datetime(2023, 5, 27) #testing new method

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
    