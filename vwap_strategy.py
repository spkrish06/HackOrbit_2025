import yfinance as yf
import pandas as pd
import numpy as np
def run_strategy_vwap(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol):

    each_trade_amt = invest_cap/turnover
    invest_copy = invest_cap
    def get_data():  
        ohlcv_data = {}
        try:
            temp = yf.download(stock,period='60d',interval="5m")
            temp.dropna(how='any',inplace= True)

            if temp.empty:
                print("Error: Downloaded data for {stock} is empty.")
            else:
                ohlcv_data[stock] = temp

        except Exception as e:
            print(e, "Error in fetching data")

        return temp