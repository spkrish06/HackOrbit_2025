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
from rsi_bollinger import run_strategy_rsi_bb,get_trade_df
import plotly.io as pio
import pandas as pd
import os
import joblib as jb
from sklearn.ensemble import RandomForestClassifier
import traceback
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai._exceptions import RateLimitError 
import time



app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        
        elif strategy == 'rsi_bb':
            results = run_strategy_rsi_bb(stock, invest_cap, turnover, min_trade_bal,is_crypto,rf_symbol)

        else:
            flash("Invalid strategy!!")
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


@app.route("/recommend_strategy_page", methods=["GET"])
def recommend_strategy_page():
    return render_template("recommend_strategy.html")


@app.route("/recommend_strategy", methods=["POST"])
def recommend_strategy():
    try:
        # Input validation
        stock = request.form.get('stock')
        invest_cap = request.form.get('invest_cap')
        turnover = request.form.get('turnover')
        min_trade_bal = request.form.get('min_trade_bal')
        is_crypto = request.form.get('is_crypto', 'false').lower() == 'true'
        rf_symbol = request.form.get('rf_symbol', '^IRX')
        
        if not all([stock, invest_cap, turnover, min_trade_bal]):
            return jsonify({"error": "Missing one or more required form fields"}), 400
        
        invest_cap = float(invest_cap)
        turnover = int(turnover)
        min_trade_bal = float(min_trade_bal)

        # Run all strategies and collect their metrics
        ml_strategies = {
            'vwap': run_strategy_vwap(stock, invest_cap, turnover, min_trade_bal,is_crypto, rf_symbol),
            '3_pos': run_strategy_3pos(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol),
            'hma_ema': run_strategy_hma_ema(stock, invest_cap, turnover, min_trade_bal,is_crypto, rf_symbol),
            'macd_ema': run_strategy_macd_ema(stock, invest_cap, turnover, min_trade_bal,is_crypto, rf_symbol),
            'adx_dmi': run_strategy_adx_dmi(stock, invest_cap, turnover, min_trade_bal,is_crypto, rf_symbol),
            'rsi_macd': run_strategy_rsi_macd_crossover(stock, invest_cap, turnover, min_trade_bal,is_crypto, rf_symbol),
            'rsi_bb': run_strategy_rsi_bb(stock, invest_cap, turnover, min_trade_bal,is_crypto, rf_symbol),
            'bb_adx': run_strategy_bb_adx_spike(stock, invest_cap, turnover, min_trade_bal,is_crypto, rf_symbol),
            'triple_ema': run_strategy_triple_ema_crossover(stock, invest_cap, turnover, min_trade_bal,is_crypto, rf_symbol),
            'elder_triple': run_strategy_elder_triple_screen(stock, invest_cap, turnover, min_trade_bal,is_crypto, rf_symbol)
        }

        feature_rows = []
        strategy_names = []

        for name, result in ml_strategies.items():
            row = {
                'sharpe': result['sharpe'],
                'CAGR': result['CAGR'],
                'sortino': result['sortino'],
                'calmar': result['calmar'],
                'win_rate': result['win_rate'],
                'loss_rate': result['loss_rate'],
                'max_drawdown': result['max_drawdown'],
                'mean': result['mean'],
                'median': result['median'],
                'std': result['std'],
            }
            feature_rows.append(row)
            strategy_names.append(name)

        df = pd.DataFrame(feature_rows, index=strategy_names)
        labels = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]

        model_path = "strategy_classifier.pkl"

        if not os.path.exists(model_path):
            model = RandomForestClassifier(random_state=42)
            model.fit(df, labels)
            jb.dump(model, model_path)

        model = jb.load(model_path)

        predictions = model.predict_proba(df)
        best_idx = predictions[:, 1].argmax()
        best_strategy = strategy_names[best_idx]
        best_result = ml_strategies[best_strategy]

        response = {
            "recommended_strategy": best_strategy,
            "metrics": {
                "invested_capital": best_result.get('Invested Capital', None),
                "portfolio_value": best_result.get('Portfolio value', None),
                "sharpe_ratio": best_result['sharpe'],
                "sortino_ratio": best_result['sortino'],
                "calmar_ratio": best_result['calmar'],
                "cagr": best_result['CAGR'],
                "win_rate": best_result['win_rate'],
                "loss_rate": best_result['loss_rate'],
                "max_drawdown": best_result['max_drawdown'],
                "mean": best_result['mean'],
                "median": best_result['median'],
                "std": best_result['std'],
                "csv_path": best_result.get("csv_path", ""),
            }
        }

        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/send_email', methods=['POST'])
def send_email():
    print("Email Submitted")
    print("Form data: ", request.form)
    user_email = request.form.get('user_email')
    print("User Email: ", user_email)
    pdf_path = session.get('latest_pdf')
    print("Session CSV path: ", pdf_path)
    if not pdf_path or not os.path.exists(pdf_path):
        flash("No PDF report found. Please run a strategy first.", "danger")
        return redirect(url_for('index'))
    
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    subject = "Your Strategy Report"
    body = "Hi,\n\nPlease find your trading strategy report attached.\n\nBest,\nTrading App"


    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = user_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(pdf_path, "rb") as file:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename="strategy_report.pdf")
        msg.attach(part)
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            flash("Email sent successfully!", "success")
            return jsonify({"message": "Email sent"}), 200


    except Exception as e:
        print("Error sending email", e)
        return jsonify({"error": "Failed to send email"}), 500

        


def chat_with_gpt(user_query, selected_strategies, metrics_summary, retries=3, delay=1.5):
    context = "You are a professional trading assistant.\n\n"
    if selected_strategies:
        context += f"The user is comparing the following strategies: {', '.join(selected_strategies)}.\n\n"

    context += "Portfolio Performance for each strategy:\n"

    for strategy in selected_strategies:
        metrics = metrics_summary.get(strategy, {})
        context += f"\nStrategy: {strategy}\n"
        context += f"- Capital Invested: {metrics.get('invested_capital', 'N/A')}\n"
        context += f"- Current Value: {metrics.get('portfolio_value', 'N/A')}\n"
        context += f"- Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}\n"
        context += f"- Sortino Ratio: {metrics.get('sortino_ratio', 'N/A')}\n"
        context += f"- Calmar Ratio: {metrics.get('calmar_ratio', 'N/A')}\n"
        context += f"- CAGR: {metrics.get('cagr', 'N/A')}\n"
        context += f"- Max Drawdown: {metrics.get('max_drawdown', 'N/A')}\n"
        context += f"- Win Rate: {metrics.get('win_rate', 'N/A')}%\n"
        context += f"- Loss Rate: {metrics.get('loss_rate', 'N/A')}%\n"
        context += f"- Mean Return: {metrics.get('mean', 'N/A')}\n"
        context += f"- Median Return: {metrics.get('median', 'N/A')}\n"
        context += f"- Std Dev: {metrics.get('std', 'N/A')}\n"

    context += """

Based on these metrics:
- Recommend whether the user should BUY or SELL.
- Explain the portfolio performance curve.
- Identify the better strategy and why.
- Use easy-to-understand explanations.
"""

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_query}
                ]
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            print("Rate limit hit. Retrying...")
            time.sleep(delay)
            delay *= 2
    return "Failed to retrieve response from GPT after multiple attempts."

def generate_metrics_summary(selected_strategies, stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol):
    summary = {}
    for strategy in selected_strategies:
        if strategy == 'vwap':
            results = run_strategy_vwap(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        elif strategy == '3_pos':
            results = run_strategy_3pos(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        elif strategy == 'hma_ema':
            results = run_strategy_hma_ema(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        elif strategy == 'macd_ema':
            results = run_strategy_macd_ema(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        elif strategy == 'adx_dmi':
            results = run_strategy_adx_dmi(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        elif strategy == 'rsi_macd':
            results = run_strategy_rsi_macd_crossover(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        elif strategy == 'rsi_bb':
            results = run_strategy_rsi_bb(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        elif strategy == 'bb_adx':
            results = run_strategy_bb_adx_spike(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        elif strategy == 'triple_ema':
            results = run_strategy_triple_ema_crossover(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        elif strategy == 'elder_triple':
            results = run_strategy_elder_triple_screen(stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)
        else:
            continue 

        summary[strategy] = {
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
            'cagr': results['CAGR'],
        }
    return summary




@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get('message')
    greetings = ["hi","hello","good morning","good evening"]
    
    selected_strategies = data.get('selected_strategies', [])

    stock = session.get('stock')
    invest_cap = session.get('invest_cap')
    turnover = session.get('turnover')
    min_trade_bal = session.get('min_trade_bal')
    is_crypto = request.form.get('is_crypto', 'false').lower() == 'true'
    rf_symbol = request.form.get('rf_symbol', '^IRX')

    if not all([stock, invest_cap, turnover, min_trade_bal]):
        return jsonify({'reply': " Missing session data. Please run a strategy first from the homepage."})

    metrics_summary = generate_metrics_summary(selected_strategies, stock, invest_cap, turnover, min_trade_bal, is_crypto, rf_symbol)

    response = chat_with_gpt(user_query, selected_strategies, metrics_summary)
    return jsonify({'reply': response})
   


if __name__ == '__main__':
    app.run(debug=True)
