import yfinance as yf
import pandas as pd
import numpy as np
from collections import defaultdict, OrderedDict
import plotly.graph_objects as go

trade_df_copy = pd.DataFrame()
def run_strategy_macd_ema(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol):
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


    # CALCULATION OF TECHNICAL INCIDATORS TO BE IMPLEMENTED IN THE STRATEGY

    def calculate_technical_indicators(): 
        temp = get_data()

        def ema(series, span):
            return series.ewm(span=span, adjust=False).mean()

        df = pd.DataFrame()
        df['Open'] = temp['Open']
        df['High'] = temp['High']
        df['Low'] = temp['Low']
        df['Close'] = temp['Close']
        df['Change'] = df['Close'] - df['Close'].shift(1)
        df['EMA_12'] = ema(df['Close'], 12)
        df['EMA_26'] = ema(df['Close'], 26)
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['Signal'] = ema(df['MACD'], 9)
        return df


    # GENERATING BUY AND SELL SIGNALS ALONG WITH ENTRY/EXIT CONDITIONS
    def signals_generation(): 
        df = calculate_technical_indicators()
        df['Buy_Signal'] = (df['MACD'] > df['Signal']) & (df['MACD'].shift(1) <= df['Signal'].shift(1))
        df['Sell_Signal'] = pd.Series([None]*len(df), dtype='object')

        buy_indices = sorted(df.index[df['Buy_Signal'] == True].tolist())
        for buy_index in buy_indices:
            buy_price = df.loc[buy_index, 'Close']
            stoploss_price = 0.98 * buy_price
            target_price = 1.03 * buy_price
            start_idx = df.index.get_loc(buy_index)

            for j in range(start_idx + 1, len(df)):
                low_price = df['Low'].iloc[j]
                high_price = df['High'].iloc[j]

                if(low_price < stoploss_price):
                    df.at[df.index[j], 'Sell_Signal'] = "Stop Loss"
                    break

                elif(high_price > target_price):
                    df.at[df.index[j], 'Sell_Signal'] = "Target Profit"
                    break
        return df



    # CALCULATION OF PROFITS, PORTFOLIO VALUES, BUY AND SELL DATES AND TRADES THAT ARE SKIPPED

    def track_portfolio_values():        
        nonlocal invest_cap
        df = signals_generation()
        global trade_df_copy
       

        trade_summary = []
        all_trade_profits = []
        skipped_dates = []

        daily_trade_count = defaultdict(int)
        open_positions = []

        buy_indices = df.index[df['Buy_Signal'] == True].tolist()

        cumulative_stocks = 0

        daily_portfolio_state = OrderedDict()  
        df['DateOnly'] = df.index.date
        daily_closes = df.groupby('DateOnly')['Close'].last().to_dict()

        for buy_index in buy_indices:
            trade_date = buy_index.date()

            buy_price = df.loc[buy_index, 'Close']
            trailing_stop_pct = 0.02
            stoploss_price = (1 - trailing_stop_pct) * buy_price
            target_price = 1.03 * buy_price

            end_day_close = daily_closes.get(trade_date, np.nan)

            
            for pos in open_positions[:]:
                if pos['sell_time'] <= buy_index:
                    invest_cap += pos['return_amt']
                    cumulative_stocks -= pos['stock_num']
                    pos['closed'] = True
                    open_positions.remove(pos)

            if is_crypto:
                stock_num = each_trade_amt / buy_price 
            else:
                stock_num = int(each_trade_amt // buy_price)

            total_buy_price = stock_num * buy_price

            if (invest_cap < min_trade_bal or
                invest_cap < each_trade_amt or
                daily_trade_count[trade_date] >= turnover or
                stock_num == 0 or
                invest_cap < total_buy_price):
                skipped_dates.append(trade_date)
                continue

        
            invest_cap -= total_buy_price
            cumulative_stocks += stock_num

            
            daily_portfolio_state[trade_date] = {
                'cash': invest_cap,
                'stocks': cumulative_stocks
            }

        
            start_idx = df.index.get_loc(buy_index)
            trade_executed = False

            current_trade_profits = []
            current_trade_capital = []
            current_trade_portfolio = []
            current_trade_same_day_close = []
            current_trade_reason = None
            current_trade_sell_index = None

            buy_high = df.loc[buy_index, 'High']
            for j in range(start_idx + 1, len(df)):
                sell_index = df.index[j]
                idx = df.index[j]
                high_price = df.at[idx, 'High']
                low_price = df.at[idx, 'Low']

                buy_high =  max(buy_high, high_price)
                stoploss_price = max(stoploss_price, (1 - trailing_stop_pct) * buy_high)

                if(df['Sell_Signal'].iloc[j] == 'Stop Loss'):
                    if(low_price < stoploss_price):
                        current_trade_sell_index = sell_index
                        current_trade_reason = "Stop Loss"
                        profit_pct = ((stoploss_price - buy_price) / buy_price) * 100
                        current_trade_profits.append(profit_pct)
                        current_trade_capital.append(invest_cap)
                        current_trade_portfolio.append(cumulative_stocks)
                        current_trade_same_day_close.append(end_day_close)
                        trade_executed = True

                        open_positions.append({
                            'sell_time': sell_index,
                            'return_amt': stoploss_price * stock_num,
                            'stock_num': stock_num
                        })

                       
                        daily_portfolio_state[sell_index.date()] = {
                            'cash': invest_cap + stoploss_price * stock_num,
                            'stocks': cumulative_stocks - stock_num
                        }
                        break

                elif(df['Sell_Signal'].iloc[j] == 'Target Profit'):
                    if(high_price > target_price):
                        current_trade_sell_index = sell_index
                        current_trade_reason = "Target Profit"
                        profit_pct = ((target_price - buy_price) / buy_price) * 100
                        current_trade_profits.append(profit_pct)
                        current_trade_capital.append(invest_cap)
                        current_trade_portfolio.append(cumulative_stocks)
                        current_trade_same_day_close.append(end_day_close)
                        trade_executed = True

                        open_positions.append({
                            'sell_time': sell_index,
                            'return_amt': target_price * stock_num,
                            'stock_num': stock_num
                        })

                       
                        daily_portfolio_state[sell_index.date()] = {
                            'cash': invest_cap + target_price * stock_num,
                            'stocks': cumulative_stocks - stock_num
                        }
                        break

            if trade_executed:
                trade_data = {
                    'Buy Date': buy_index.date(),
                    'Buy Price': round(buy_price, 2),
                    'Sell Date': current_trade_sell_index.date(),
                    'Sell Price': round(df.loc[current_trade_sell_index, 'Close'], 2),
                    'Cumulative Stocks': round(current_trade_portfolio[0], 2),
                    'Portfolio Value at Sell Date': round((current_trade_portfolio[0] * current_trade_same_day_close[0]) + current_trade_capital[0], 2),
                    'Cash Balance': round(current_trade_capital[0], 2),
                    'Profit %': round(current_trade_profits[0], 2),
                    'End Day Close': round(current_trade_same_day_close[0], 2),
                    'Reason': current_trade_reason
                }
                trade_summary.append(trade_data)
                daily_trade_count[trade_date] += 1
                all_trade_profits.extend(current_trade_profits)

       
        all_dates = sorted(set(df.index.date))
        last_state = {'cash': invest_cap, 'stocks': cumulative_stocks}

        for date in all_dates:
            if date in daily_portfolio_state:
                last_state = daily_portfolio_state[date]
            else:
                daily_portfolio_state[date] = last_state

       
        portfolio_daily_value = {}
        for date in all_dates:
            day_df = df[df.index.date == date]
            if day_df.empty:
                continue
            close_price = day_df['Close'].iloc[-1]
            cash = daily_portfolio_state[date]['cash']
            stocks = daily_portfolio_state[date]['stocks']
            portfolio_val = cash + stocks * close_price
            portfolio_daily_value[date] = round(portfolio_val, 2)

        trade_df = pd.DataFrame(trade_summary)
        trade_df.sort_values(by='Buy Date', inplace=True)
        trade_df.reset_index(drop=True, inplace=True)

        trade_df_copy = trade_df.copy()

        return trade_df, skipped_dates, portfolio_daily_value, trade_summary, all_trade_profits
 
    def portfolio_curve():      
        trade_df, skipped_dates, portfolio_daily_value, trade_summary, all_trade_profits = track_portfolio_values()

        portfolio_series = pd.Series(portfolio_daily_value).sort_index()

        daily_cumulative = trade_df.groupby('Buy Date').tail(1).set_index('Buy Date')['Cumulative Stocks']
        daily_cumulative = daily_cumulative[daily_cumulative.index.isin(portfolio_series.index)]
        daily_cumulative = daily_cumulative.sort_index()

      
        diffs = daily_cumulative.diff()
        colors = ['green' if diff > 0 else 'red' for diff in diffs]
        colors[0] = 'green'  

     
        fig = go.Figure()

       
        fig.add_trace(go.Scatter(
            x=portfolio_series.index,
            y=portfolio_series.values,
            mode='lines',
            name='Portfolio Value',
            line=dict(color='blue', width=2),
            yaxis='y1'
        ))

       
        if 'skipped_dates' in locals() and skipped_dates:
            skipped_dates_filtered = [d for d in sorted(skipped_dates) if d in portfolio_series.index]
            skipped_values = [portfolio_series[d] for d in skipped_dates_filtered]
            fig.add_trace(go.Scatter(
                x=skipped_dates_filtered,
                y=skipped_values,
                mode='markers',
                name='Skipped Trade Days',
                marker=dict(color='red', size=8, symbol='x'),
                yaxis='y1'
            ))

       
        fig.add_trace(go.Bar(
            x=daily_cumulative.index,
            y=daily_cumulative.values,
            name='Cumulative Stocks (End of Day)',
            marker_color=colors,
            opacity=0.6,
            yaxis='y2'
        ))

        max_cum_stocks = daily_cumulative.max()
        scale_factor = 3 
      
        fig.update_layout(
            title="Portfolio Value and Daily Cumulative Stocks (End of Day)",
            xaxis=dict(
                title='Date',
                tickformat='%Y-%m-%d',
                tickangle=45
            ),
            yaxis=dict(
                title='Portfolio Value ($)',
                side='left',
                showgrid=False
            ),
            yaxis2=dict(
                title='Cumulative Stocks',
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max_cum_stocks * scale_factor]
            ),
            legend=dict(x=0.01, y=0.99),
            hovermode='x unified',
            height=600,
            width=900
        )
        return  fig, trade_summary, all_trade_profits,portfolio_daily_value 
        
    def performance_metrics():      
        fig, trade_summary, all_trade_profits,portfolio_daily_value = portfolio_curve()
        portfolio_daily_value = {k: round(v, 2) for k, v in portfolio_daily_value.items()}
  
        portfolio_df = pd.DataFrame(portfolio_daily_value.items(), columns=['Date', 'Portfolio Value'])
        portfolio_df['Date'] = pd.to_datetime(portfolio_df['Date'])
        portfolio_df = portfolio_df.sort_values('Date').reset_index(drop=True)

    
        first_date = portfolio_df['Date'].iloc[0] - pd.Timedelta(days=1)
        starting_row = pd.DataFrame([{
            'Date': first_date,
            'Portfolio Value': round(invest_copy, 2)  
        }])
        portfolio_df = pd.concat([starting_row, portfolio_df], ignore_index=True).sort_values('Date').reset_index(drop=True)

    
        full_date_range = pd.date_range(start=portfolio_df['Date'].min(), end=portfolio_df['Date'].max(), freq='B')

        
        portfolio_df.set_index('Date', inplace=True)
        portfolio_df = portfolio_df.reindex(full_date_range)

    
        portfolio_df = portfolio_df.ffill()

    
        portfolio_df = portfolio_df.rename_axis('Date').reset_index()

    
        portfolio_df['Returns'] = portfolio_df['Portfolio Value'].pct_change().fillna(0)

        def fetch_risk_free_rate(rf_symbol: str) -> float:
            try:
                rf_ticker = yf.Ticker(rf_symbol)
                hist = rf_ticker.history(period="5d")  # Last 1 month to get latest
                if hist.empty:
                    return 0.03  # fallback 3%
                latest_close = hist['Close'].iloc[-1]

                # Many T-bill rates from yfinance are in percentage points (e.g., 2.5 for 2.5%)
                # So convert to decimal
                rf_rate = float(latest_close) / 100.0
                return rf_rate

            except Exception as e:
                print(f"Error fetching RF rate for {rf_symbol}: {e}")
                return 0.03  # fallback 3%


        def sharpe_ratio(return_series, N, rf):
            mean = return_series.mean() * N -rf
            sigma = return_series.std() * np.sqrt(N)
            return mean / sigma

        N = 255 
        rf = fetch_risk_free_rate(rf_symbol)
        print(rf_symbol)
        sharpe = sharpe_ratio(portfolio_df['Returns'], N, rf)

        def sortino_ratio(series, N,rf):
            mean = series.mean() * N -rf
            std_neg = series[series<0].std()*np.sqrt(N)
            return mean/std_neg

        sortino = sortino_ratio(portfolio_df['Returns'], N, rf)

        pos_count = sum(p > 0 for p in all_trade_profits)
        neg_count = sum(p < 0 for p in all_trade_profits)
        total_trades = len(all_trade_profits)

        if total_trades > 0:
            win_rate = (pos_count / total_trades) * 100
            loss_rate = (neg_count / total_trades) * 100
        else:
            win_rate = loss_rate = 0

        def max_drawdown(return_series):
            running_max = return_series.cummax()
            drawdowns = (running_max - return_series) 
            return drawdowns.max()


        max_drawdown = max_drawdown(portfolio_df['Portfolio Value'])

        days = (portfolio_df['Date'].iloc[-1] - portfolio_df['Date'].iloc[0]).days
        years = days / 365.25
        CAGR = ((portfolio_df['Portfolio Value'].iloc[-1] / portfolio_df['Portfolio Value'].iloc[0]) ** (1 / years) - 1) * 100

        calmar = abs(CAGR) /(max_drawdown)
        portfolio_data_serialized = {str(k): v for k, v in portfolio_daily_value.items()}


        return {
                "Invested Capital": invest_copy,
                "Portfolio value": portfolio_df['Portfolio Value'].iloc[-1],
                "sharpe": sharpe,
                "sortino": sortino,
                "calmar": calmar,
                "std": np.std(portfolio_df['Returns']),
                "mean": np.mean(portfolio_df['Returns']),
                "median": np.median(portfolio_df['Returns']),
                "win_rate": win_rate,
                "loss_rate": loss_rate,
                "max_drawdown": max_drawdown,
                "CAGR": CAGR,
                "trades": trade_summary,
                'plotly_fig': fig,
                "portfolio_data": portfolio_data_serialized,
                "csv_path": "static/report.csv"
            }
    return performance_metrics()

def get_trade_df():
    global trade_df_copy
    return trade_df_copy


        