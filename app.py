from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from vwap_strategy import run_strategy_vwap, get_trade_df
from pos3_strategy import run_strategy_3pos, get_trade_df
from macd_ema_strategy import run_strategy_macd_ema, get_trade_df
from triple_ema_crossover import run_strategy_triple_ema_crossover, get_trade_df
from adx_dmi_strategy import run_strategy_adx_dmi, get_trade_df
from bollinger_adx_spike_strategy import run_strategy_bb_adx_spike, get_trade_df
from rsi_macd import run_strategy_rsi_macd_crossover, get_trade_df
from hma_ema_strategy import run_strategy_hma_ema, get_trade_df
from elder_triple import run_strategy_elder_triple_screen, get_trade_df
import plotly.io as pio
import pandas as pd


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

trade_df_copy = pd.DataFrame() 
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == '1234':
            return redirect(url_for('index'))  
        else:
            return "Invalid credentials. Try again."

    return render_template('login.html') 


@app.route('/index', methods=['GET', 'POST'])
def index():
    metrics = None
    plot_div = None
    selected_strategies = []

    if request.method == 'POST':
        strategy = request.form['strategy']
        stock = request.form['stock']
        invest_cap = float(request.form['invest_cap'])
        turnover = int(request.form['turnover'])
        min_trade_bal = float(request.form['min_trade_bal'])
        is_crypto = request.form.get('is_crypto', 'false').lower() == 'true'
        rf_symbol = request.form.get('rf_symbol', '^IRX')  

       
        if min_trade_bal >= invest_cap:
            flash("Minimum Trade Balance must be less than Investment Capital.", "warning")
            return redirect(url_for('index'))

        session.update({
            'stock': stock,
            'invest_cap': invest_cap,
            'turnover': turnover,
            'min_trade_bal': min_trade_bal
        })

        if strategy == 'vwap':
            results = run_strategy_vwap(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        
        elif strategy == '3_pos':
            results = run_strategy_3pos(stock, invest_cap, turnover, min_trade_bal, is_crypto,rf_symbol)
        
        elif strategy == 'macd_ema':
            results = run_strategy_macd_ema(stock, invest_cap, turnover, min_trade_bal,is_crypto,rf_symbol)
        
        elif strategy == 'triple_ema':
            results = run_strategy_triple_ema_crossover(stock, invest_cap, turnover, min_trade_bal,is_crypto,rf_symbol)
        
        elif strategy == 'adx_dmi':
            results = run_strategy_adx_dmi(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        
        elif strategy == 'bb_adx':
            results = run_strategy_bb_adx_spike(stock, invest_cap, turnover, min_trade_bal,is_crypto,rf_symbol)
        
        elif strategy == 'rsi_macd':
            results = run_strategy_rsi_macd_crossover(stock, invest_cap, turnover, min_trade_bal,is_crypto,rf_symbol)
        
        elif strategy == 'hma_ema':
            results = run_strategy_hma_ema(stock, invest_cap, turnover, min_trade_bal,is_crypto,rf_symbol)

        elif strategy == 'elder_triple':
            results = run_strategy_elder_triple_screen(stock, invest_cap, turnover, min_trade_bal,is_crypto,rf_symbol)

        else:
            flash("Last strategy coming soon!!")
            return redirect(url_for('index'))
       
        plot_div = pio.to_html(results['plotly_fig'], full_html=False)
        metrics = {
                'invested_capital': results['Invested Capital'],
                'portfolio_value': results['Portfolio value'],
                'sharpe_ratio': results['sharpe'],
                'sortino_ratio': results['sortino'],
                'calmar_ratio': results['calmar'],
                'std': results['std'],
                'mean': results['mean'],
                'median': results['median'],
                'win_rate': results['win_rate'],
                'loss_rate': results['loss_rate'],
                'max_drawdown': results['max_drawdown'],
                'cagr': results['CAGR']
                }
    
        session['latest_metrics'] = metrics
        session['portfolio_data'] = results.get('portfolio_data')
        session['latest_csv'] = results['csv_path']
        selected_strategies = [strategy]

    return render_template(
        'index.html',
        metrics=metrics,
        plot_div=plot_div,
        selected_strategies=selected_strategies
    )


@app.route('/trades')
def trades():
    global trade_df_copy
    if trade_df_copy.empty:
        return "No trades available. Run the strategy first."
    
    table_html = trade_df_copy.to_html (classes='table table-striped', index=False, border=0, table_id="tradeTable")
    return render_template('trades.html', table=table_html)

if __name__ == '__main__':
    app.run(debug=True)
