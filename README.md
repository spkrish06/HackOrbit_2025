**AI-Powered Trading Strategy Dashboard with Live Signal**

**Executive Summary**

This project is an AI-powered, full-stack trading dashboard designed to empower traders by recommending the most effective trading strategy and enabling them to apply it in real time. 
It integrates advanced technical analysis strategies, a Random Forest Classifier for strategy selection, and a manual live signal generation feature that fetches real-time data and produces actionable BUY/SELL 
signals.
The dashboard supports both equity and crypto across 6 markets (US, UK, INDIA, GERMANY, CHINA & JAPAN), offers comprehensive performance metrics, and provides seamless UI/UX using cutting-edge frontend tools. 
An OpenAI-powered chatbot is embedded to assist users in comparing strategies, interpreting signals, and clarifying concepts.

 
 What the Project Does -->
**Key Functionalities:**

 Strategy Recommendation: Uses Random Forest Classifier trained on past performance metrics (Sharpe Ratio, CAGR, Win Rate, etc.) to select the best strategy for the selected equity/crypto.
 Strategy Simulator: Allows users to simulate trades using 10 advanced trading strategies.
 Live Signal Generation (Manual Trigger): After recommendation, the user can click "Apply Strategy" to instantly get real-time signals (BUY/SELL) with price and timestamp.
 Performance Metrics: Visualizes Sharpe Ratio, CAGR, Win Rate, Loss Rate, and Maximum Drawdown.
 Email Automation: Sends PDF summary of the selected strategy and simulated trades to the user.
 AI Chatbot: OpenAI chatbot assists in comparing strategy outcomes and user queries.

**Strategy Descriptions and Buy Logic (In-Depth)**

Below are the strategies implemented in the system with detailed explanations:

**1. ADX-DMI Crossover Strategy**
Logic:
**df['Buy_Signal'] = ((df['+DI'] > df['-DI']) & (df['+DI'].shift(1) <= df['-DI'].shift(1)) & (df['ADX'] > 20))**
Explanation:
**This strategy uses the Directional Movement Index (DMI) and Average Directional Index (ADX). 
A BUY signal is generated when the +DI line crosses above -DI, indicating bullish strength, and the trend strength (ADX) is greater than 20, confirming a valid trend.**


**2. Bollinger Band + ADX + Volume Spike**
Logic:
**df['Buy_Signal'] = ((df['Close'] < df['LowerBB']) & (df['ADX'] > 20) & (df['Volume_Spike']))**
Explanation:
**The strategy identifies oversold conditions (price below lower Bollinger Band), confirms trend strength with ADX > 20, and checks for unusual volume (spike), 
signaling institutional interest or strong reversal probability.**


**3. Elder Triple Screen Strategy**
Logic:
**df['Buy_Signal'] = ((df['MACD_Histogram'] > 0) & (df['RSI'] > 50) & (df['Close'] < df['EMA_13']))**
Explanation:
**Combines three filters: trend (MACD Histogram > 0), momentum (RSI > 50), and entry pullback (price below EMA_13). It captures entries in uptrends during short-term dips.**


**4. HMA-EMA RSI Crossover**
Logic:
****df['Buy_Signal'] = (df['RSI_MA_Hull_14'] > df['RSI_MA_Expo_25']) & (df['RSI_MA_Hull_14'].shift(1) <= df['RSI_MA_Expo_25'].shift(1))**
Explanation:
**This strategy uses Hull and Exponential MAs on RSI to identify changes in RSI momentum. A crossover from Hull > EMA indicates an early trend shift.****


**5. MACD-EMA Crossover**
Logic:
**df['Buy_Signal'] = (df['MACD'] > df['Signal']) & (df['MACD'].shift(1) <= df['Signal'].shift(1))**
Explanation:
**Classic MACD crossover strategy indicating bullish reversal when the MACD line crosses above the signal line.**


**6. 3-Positive Bars + RSI Confirmation**
Logic:
**if 3 consecutive bars are positive and RSI > RSI_MA:
    df['Buy_Signal'] = True**
Explanation:
**After 3 consecutive green candles, if RSI confirms strength (RSI > RSI MA), a BUY signal is generated. It captures sustained momentum.**


**7. RSI + Bollinger Breakout**
Logic:
**df['Buy_Signal'] = ((df['Close'] > df['BB_Upper']) & (df['RSI'] < 70))**
Explanation:
**Bullish breakout above the upper Bollinger Band with RSI still below overbought territory, suggesting room for upward movement.**


**8. RSI + MACD Crossover Strategy**
Logic:
**df['Buy_Signal'] = (df['RSI'] > 30) & df['macd_cross_up']**
Explanation:
**This strategy triggers a BUY when RSI is recovering from oversold (RSI > 30) and a MACD upward crossover has occurred, indicating upward momentum.**


**9. Triple EMA Crossover Strategy**
Logic:
**df['Buy_Signal'] = (df['EMA_5'] > df['EMA_13']) & (df['EMA_13'] > df['EMA_21'])**
Explanation:
**A strong bullish signal where short-term EMA crosses above mid and long-term EMAs in sequence, suggesting strong upward momentum.**


**10. VWAP Confirmation Strategy**
Logic:
**df['Buy_Signal'] = ((df['Close_1'] > df['VWAP_1']) & (df['Open_1'] < df['VWAP_1']) & (df['Close'] > df['High_1']))**

Explanation:
**This logic confirms a bullish breakout above VWAP and previous candle’s high, supported by intraday reversal pattern.**



**How Strategy Recommendation Works**

We use a Random Forest Classifier trained on labeled historical strategy performance. It analyzes a variety of input metrics (Sharpe Ratio, Drawdown, Win Rate, etc.) for each strategy applied to the stock, 
then classifies the best one.

Once a user clicks "Apply Strategy" (after strategy recommendation), then it:

Sends a POST request to /get_live_signal.
Fetches the latest price data.
Applies the selected strategy’s logic.

Displays:
 **BUY or  SELL Signal**
 **Current Price**
 **Timestamp**
Unlike a live polling system, signals are generated on demand when the user clicks the apply button.


**Tech Stack**

Frontend:
HTML, CSS, Bootstrap 5,  Bolt and v0 by Vercel for AI-assisted UI design

Backend:
Python (Flask),
Pandas, NumPy, scikit-learn (for Random Forest)

AI Chatbot:
OpenAI GPT-based assistant integrated in the dashboard



**Screenshots:**

![image](https://github.com/user-attachments/assets/333ab794-9692-4e22-bba0-bcc628c7f207)
![image](https://github.com/user-attachments/assets/af5a2300-4e77-419b-a3c0-5f77042f5bb8)

