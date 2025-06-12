import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import timedelta

# === CONFIGURATION ===
symbols_df = pd.read_csv('EQUITY_L.csv')  # Replace with your actual file path
STOCKS = symbols_df['SYMBOL'].dropna().unique()
STOCKS = [symbol.strip().upper() + '.NS' for symbol in STOCKS]  # Replace with your list or load from CSV
START_DATE = '2025-04-15'
END_DATE = '2025-05-15'
LOOKBACK_DAYS = 7
BUY_THRESHOLD = -5  # percent
SELL_THRESHOLD = 10  # percent
INITIAL_CASH = 1000000  # starting portfolio cash

# === DATA COLLECTION ===
data = yf.download(STOCKS, start=START_DATE, end=END_DATE)['Close']
if isinstance(data, pd.Series):  # if only one stock
    data = data.to_frame()

# === BACKTESTING LOGIC ===
portfolio = {s: 0 for s in STOCKS}  # shares held (can be negative for shorts)
cash = INITIAL_CASH
trade_log = []

for current_date in data.index[LOOKBACK_DAYS:]:
    for symbol in STOCKS:
        price_now = data.loc[current_date, symbol]
        price_7d_ago = data.loc[data.index[data.index.get_loc(current_date) - LOOKBACK_DAYS], symbol]
        pct_change = ((price_now - price_7d_ago) / price_7d_ago) * 100

        # BUY logic: always buy 1 share if condition met (can accumulate)
        if pct_change <= BUY_THRESHOLD:
            cash -= price_now
            portfolio[symbol] += 1
            trade_log.append({'Date': current_date, 'Symbol': symbol, 'Action': 'BUY', 'Price': price_now, 'Shares': 1, 'Cash': cash, 'Holdings': portfolio[symbol]})

        # SELL logic: always sell 1 share if condition met (can go short)
        elif pct_change >= SELL_THRESHOLD:
            cash += price_now
            portfolio[symbol] -= 1
            trade_log.append({'Date': current_date, 'Symbol': symbol, 'Action': 'SELL', 'Price': price_now, 'Shares': 1, 'Cash': cash, 'Holdings': portfolio[symbol]})

# === PERFORMANCE ANALYSIS ===
# Calculate daily portfolio value
portfolio_values = []
for current_date in data.index:
    value = cash
    for symbol in STOCKS:
        value += portfolio[symbol] * data.loc[current_date, symbol]
    portfolio_values.append(value)

portfolio_series = pd.Series(portfolio_values, index=data.index)

# === RESULTS ===
print("Final Portfolio Value:", portfolio_series.iloc[-1])
print("Total Return: {:.2f}%".format((portfolio_series.iloc[-1] - INITIAL_CASH) / INITIAL_CASH * 100))
print("Number of Trades:", len(trade_log))
print(pd.DataFrame(trade_log))

# === PLOT ===
plt.figure(figsize=(12, 6))
plt.plot(portfolio_series, label='Strategy Portfolio Value')
plt.title('Momentum Strategy Backtest (3 months)')
plt.xlabel('Date')
plt.ylabel('Portfolio Value (INR)')
plt.legend()
plt.grid(True)
plt.show()
