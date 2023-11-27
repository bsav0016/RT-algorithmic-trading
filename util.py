import alpaca_trade_api as tradeapi
import datetime as dt
import numpy as np
import pandas as pd
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import logging
from alpaca_trade_api.common import URL
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


ALPACA_API_KEY = 'AK66FMJPPNJZGUSYE6GK' #Live
ALPACA_SECRET_KEY = '3ptrgezKzcddpq4SE9vbIdSUnBetgwPBPQjuUote' #Live
base_url = URL('https://api.alpaca.markets') #Live
paper = False
ALPACA_API_KEY = 'PKDMVI1V5BV5KDB4UA56' #Paper
ALPACA_SECRET_KEY = '2u7znRYX2ljbxmXHz8N9motcvkV6RIoM8du4Xkmi' #Paper
base_url = URL('https://paper-api.alpaca.markets') #Paper
paper = True

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def get_api_key():
    return ALPACA_API_KEY

def get_secret_key():
    return ALPACA_SECRET_KEY

def get_base_url():
    return base_url

def get_crypto_data(symbol="BTC/USD", time_frame=TimeFrame.Day, start_date=dt.datetime(2020, 1, 1), end_date=dt.datetime(2022, 1, 1)):
    client = CryptoHistoricalDataClient()

    request_params = CryptoBarsRequest(
                        symbol_or_symbols=[symbol],
                        timeframe=time_frame,
                        start=start_date,
                        end=end_date
                        )
    
    btc_bars = client.get_crypto_bars(request_params)

    return btc_bars.df

def get_data(symbol="AAPL", time_frame=TimeFrame.Day, start_date=dt.datetime(2020, 1, 1), end_date=dt.datetime(2022, 1, 1)):
    client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)

    request_params = StockBarsRequest(
                        symbol_or_symbols=[symbol],
                        timeframe=time_frame,
                        start=start_date,
                        end=end_date
                        )
    
    bars = client.get_stock_bars(request_params)

    return bars.df

def get_buy_power():
    trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)

    account = trading_client.get_account()
    for property_name, value in account:
        if property_name == "non_marginable_buying_power":
            return value

def get_current_position(symbol):
    symbol = "".join([char for char in symbol if char != "/"])

    trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)

    positions = trading_client.get_all_positions()

    for position in positions:
        if position.symbol == symbol:
            return position.qty

    return 0

def make_trade(symbol, quantity, order_type, crypto):
    print("Symbol, quantity, order type")
    print(symbol, quantity, order_type)
    print("\n")
    if order_type == 0:
        return
    
    trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=paper)

    account = trading_client.get_account()
    
    if order_type == 1:
        order_type = OrderSide.BUY
    elif order_type == -1:
        order_type = OrderSide.SELL
    
    if crypto:
        market_order_data = MarketOrderRequest(
                        symbol=symbol,
                        qty=quantity,
                        side=order_type,
                        time_in_force='gtc'
                    )
    else:
        market_order_data = MarketOrderRequest(
                        symbol=symbol,
                        qty=quantity,
                        side=order_type,
                        time_in_force='day'
                    )

    market_order = trading_client.submit_order(market_order_data)