import os
import csv
import datetime
import pandas as pd
import upstox_client
from upstox_client.rest import ApiException
import requests

# --- CONFIGURATION ---
SANDBOX_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NEFMNVoiLCJqdGkiOiI2ODI2ZDYyODdmZWVjZjQ1YTEzNWI5NWUiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzQ3Mzc1NjU2LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDk5Mzg0MDB9.5xN5z1-7wdTJLX1GE8Va3DVmThNEi7r-lphRKOcjNYo"
CSV_FILE = 'EQUITY_L.csv'                # <-- Replace with your CSV filename
LIVE_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NEFMNVoiLCJqdGkiOiI2ODJjMWJkYTA4ZjVkZTYxM2MyMmJlYzIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc0NzcyMTE3OCwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzQ3Nzc4NDAwfQ.FPikIKWW1UO9xNoTQSIV-Heu1eCX9wmfHNWjtlSdhe0"
CSV_FILE = 'EQUITY_L.csv'
PORTFOLIO_FILE = 'sandbox_portfolio.xlsx'

# Upstox LIVE API for fetching historical and LTP data
# Upstox LIVE API for fetching historical and LTP data
live_config = upstox_client.Configuration(sandbox=False)
live_config.access_token = LIVE_ACCESS_TOKEN
live_client = upstox_client.ApiClient(live_config)
history_api = upstox_client.HistoryApi(live_client)
market_api = upstox_client.MarketQuoteApi(live_client)

def get_instrument_key(isin):
    return f"NSE_EQ|{isin}"

def fetch_weekly_prices(instrument_key):
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)
    api_version = '2.0'
    interval = 'day'
    to_date = today.strftime('%Y-%m-%d')
    from_date = seven_days_ago.strftime('%Y-%m-%d')
    try:
        api_response = history_api.get_historical_candle_data1(
            instrument_key=instrument_key,
            interval=interval,
            to_date=to_date,
            from_date=from_date,
            api_version=api_version
        )
        candles = api_response.data.candles
    except ApiException as e:
        print(f"Error fetching candles for {instrument_key}: {e}")
        return None, None

    if not candles or len(candles) < 2:
        print(f"Not enough data for {instrument_key}.")
        return None, None

    price_7_days_ago = candles[0][1]
    price_now = candles[-1][4]
    return price_7_days_ago, price_now

def fetch_ltp(instrument_key, live_access_token):
    url = f'https://api.upstox.com/v2/market-quote/quotes?instrument_key={instrument_key}'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {live_access_token}'
    }
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        for v in data['data'].values():
            return v['last_price']
        print(f"Instrument key {instrument_key} not found in API response keys: {list(data['data'].keys())}")
        return None
    except Exception as e:
        print(f"Error fetching LTP for {instrument_key}: {e}")
        return None

def place_order(instrument_key, transaction_type, sandbox_access_token):
    url = "https://api-sandbox.upstox.com/v2/order/place"
    payload = {
        "quantity": 1,
        "product": "D",
        "validity": "DAY",
        "price": 0,
        "tag": "algo_trade",
        "instrument_token": instrument_key,
        "order_type": "MARKET",
        "transaction_type": transaction_type.upper(),
        "disclosed_quantity": 0,
        "trigger_price": 0,
        "is_amo": False
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {sandbox_access_token}'
    }
    response = requests.post(url, headers=headers, json=payload)
    try:
        resp_json = response.json()
        if resp_json.get("status") == "success":
            print(f"Order placed in SANDBOX: {transaction_type.upper()} {instrument_key} | Order ID: {resp_json['data']['order_id']}")
            return True
        else:
            print(f"Order failed for {instrument_key}: {resp_json}")
            return False
    except Exception as e:
        print(f"Order failed for {instrument_key}: {e}\nResponse: {response.text}")
        return False

def calculate_trade_charges(buy_price, sell_price, quantity, is_sell):
    turnover = (buy_price + sell_price) * quantity

    # Brokerage (Upstox delivery) - zero for delivery as per latest policy
    brokerage = 0

    # STT (Securities Transaction Tax)
    stt = 0.001 * buy_price * quantity + (0.001 * sell_price * quantity if is_sell else 0)

    # Transaction charges (NSE)
    txn_charges = 0.0000297 * turnover

    # SEBI charges
    sebi = 0.000001 * turnover

    # Stamp duty (on buy side only)
    stamp = 0.00015 * buy_price * quantity

    # DP charges (on sell only)
    dp_charges = (20 + 0.18 * 20) if is_sell else 0

    # GST
    gst = 0.18 * (brokerage + txn_charges + sebi + dp_charges)

    total_charges = brokerage + stt + txn_charges + sebi + stamp + dp_charges + gst
    return round(total_charges, 2)

def update_portfolio_excel(trade_log, portfolio_file, symbol_to_isin):
    # If file exists, load it, else create new DataFrame
    if os.path.exists(portfolio_file):
        df = pd.read_excel(portfolio_file)
    else:
        df = pd.DataFrame(columns=[
            'Date', 'Symbol', 'Action', 'Quantity', 'LTP', 'Avg Price', 'Total Qty', 'PnL', 'Charges',
            'Total Amount Invested', 'Total Portfolio Value', 'Total P&L'
        ])

    for trade in trade_log:
        symbol = trade['symbol']
        action = trade['action']
        ltp = trade['ltp']
        price = trade['price']
        qty = trade['quantity']
        date = trade['date']
        charges = trade.get('charges', 0)

        mask = (df['Symbol'] == symbol)
        if mask.any():
            row = df.loc[mask].iloc[-1]
            prev_qty = row['Total Qty']
            prev_avg = row['Avg Price']
            prev_charges = row['Charges']
            prev_invested = row['Total Amount Invested']
            if action == 'BUY':
                new_qty = prev_qty + qty
                new_avg = ((prev_avg * prev_qty) + (price * qty)) / new_qty if new_qty != 0 else 0
                new_charges = prev_charges + charges
                new_invested = prev_invested + (price * qty) + charges
            else:  # SELL
                new_qty = prev_qty - qty
                new_avg = prev_avg
                new_charges = prev_charges + charges
                # Reduce invested amount by avg price * qty sold (not by sell price)
                new_invested = prev_invested - (prev_avg * qty)
        else:
            new_qty = qty if action == 'BUY' else -qty
            new_avg = price
            new_charges = charges
            new_invested = (price * qty) + charges if action == 'BUY' else 0

        total_portfolio_value = ltp * new_qty
        total_pnl = total_portfolio_value - new_invested

        # Remove old row if exists
        df = df[~((df['Symbol'] == symbol))]

        # Add new row
        df = pd.concat([df, pd.DataFrame([{
            'Date': date,
            'Symbol': symbol,
            'Action': action,
            'Quantity': qty,
            'LTP': ltp,
            'Avg Price': round(new_avg, 2),
            'Total Qty': new_qty,
            'PnL': round((ltp - new_avg) * new_qty - new_charges if new_qty != 0 else 0, 2),
            'Charges': round(new_charges, 2),
            'Total Amount Invested': round(new_invested, 2),
            'Total Portfolio Value': round(total_portfolio_value, 2),
            'Total P&L': round(total_pnl, 2)
        }])], ignore_index=True)

    # --- Update LTP and PnL for all holdings after processing trades ---
    for idx, row in df.iterrows():
        if row['Total Qty'] != 0:
            symbol = row['Symbol']
            isin = symbol_to_isin.get(symbol)
            if isin:
                instrument_key = get_instrument_key(isin)
                ltp = fetch_ltp(instrument_key, LIVE_ACCESS_TOKEN)
                if ltp is not None:
                    df.at[idx, 'LTP'] = ltp
                    total_portfolio_value = ltp * row['Total Qty']
                    total_pnl = total_portfolio_value - row['Total Amount Invested']
                    df.at[idx, 'Total Portfolio Value'] = round(total_portfolio_value, 2)
                    df.at[idx, 'Total P&L'] = round(total_pnl, 2)
                    df.at[idx, 'PnL'] = round((ltp - row['Avg Price']) * row['Total Qty'] - row['Charges'], 2)

    # --- Add summary row ---
    if not df.empty:
        summary = {
            'Date': '',
            'Symbol': 'TOTAL',
            'Action': '',
            'Quantity': '',
            'LTP': '',
            'Avg Price': '',
            'Total Qty': df['Total Qty'].sum(),
            'PnL': df['PnL'].sum(),
            'Charges': df['Charges'].sum(),
            'Total Amount Invested': df['Total Amount Invested'].sum(),
            'Total Portfolio Value': df['Total Portfolio Value'].sum(),
            'Total P&L': df['Total P&L'].sum()
        }
        df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)

    # Save to Excel
    df.to_excel(portfolio_file, index=False)
    return df

def main():
    # --- Build symbol to ISIN mapping from CSV ---
    symbol_to_isin = {}
    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            symbol_to_isin[row['StockName']] = row['ISIN']

    trade_log = []
    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            stock_name = row['StockName']
            isin = row['ISIN']
            instrument_key = get_instrument_key(isin)

            price_7d, price_now = fetch_weekly_prices(instrument_key)
            if price_7d is None or price_now is None:
                print(f"Skipping {stock_name} ({isin}) due to insufficient data.")
                continue

            pct_change = ((price_now - price_7d) / price_7d) * 100

            action = None
            if pct_change <= -5:
                action = 'BUY'
                print(f"BUY SIGNAL: {stock_name} ({isin}) dropped {pct_change:.2f}% in last week.")
            elif pct_change >= 10:
                action = 'SELL'
                print(f"SELL SIGNAL: {stock_name} ({isin}) rose {pct_change:.2f}% in last week.")
            else:
                print(f"HOLD: {stock_name} ({isin}) changed {pct_change:.2f}% in last week.")

            if action:
                executed = place_order(instrument_key, action, SANDBOX_ACCESS_TOKEN)
                if executed:
                    ltp = fetch_ltp(instrument_key, LIVE_ACCESS_TOKEN)
                    charges = calculate_trade_charges(
                        buy_price=price_now if action == 'BUY' else 0,
                        sell_price=price_now if action == 'SELL' else 0,
                        quantity=1,
                        is_sell=(action == 'SELL')
                    )
                    trade_log.append({
                        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'symbol': stock_name,
                        'action': action,
                        'ltp': ltp,
                        'price': price_now,  # Use executed price if available
                        'quantity': 1,
                        'charges': charges
                    })

    # Update Excel portfolio and refresh LTP/PnL for all holdings
    df = update_portfolio_excel(trade_log, PORTFOLIO_FILE, symbol_to_isin)
    print("Portfolio updated in Excel.")
    print(df)

if __name__ == '__main__':
    main()
