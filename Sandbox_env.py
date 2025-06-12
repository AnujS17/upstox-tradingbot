import csv
import datetime
import upstox_client
from upstox_client.rest import ApiException
import requests

# --- CONFIGURATION ---
SANDBOX = True
SANDBOX_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NEFMNVoiLCJqdGkiOiI2ODI2ZDYyODdmZWVjZjQ1YTEzNWI5NWUiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzQ3Mzc1NjU2LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDk5Mzg0MDB9.5xN5z1-7wdTJLX1GE8Va3DVmThNEi7r-lphRKOcjNYo"
CSV_FILE = 'EQUITY_L.csv'                # <-- Replace with your CSV filename
LIVE_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NEFMNVoiLCJqdGkiOiI2ODI2ZDU1MTQxM2I0ZTAxYTJhMDRmMTkiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc0NzM3NTQ0MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzQ3NDMyODAwfQ.G8k07pu9ORnYjWjDxni5b-XDqr-s8jrfNxtlOW5lomw"
# Upstox API setup
live_config = upstox_client.Configuration(sandbox=False)
live_config.access_token = LIVE_ACCESS_TOKEN
live_client = upstox_client.ApiClient(live_config)
history_api = upstox_client.HistoryApi(live_client)

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
        else:
            print(f"Order failed for {instrument_key}: {resp_json}")
    except Exception as e:
        print(f"Order failed for {instrument_key}: {e}\nResponse: {response.text}")

def main():
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

            if pct_change <= -5:
                print(f"BUY SIGNAL: {stock_name} ({isin}) dropped {pct_change:.2f}% in last week.")
                place_order(instrument_key, 'BUY', SANDBOX_ACCESS_TOKEN)
            elif pct_change >= 10:
                print(f"SELL SIGNAL: {stock_name} ({isin}) rose {pct_change:.2f}% in last week.")
                place_order(instrument_key, 'SELL', SANDBOX_ACCESS_TOKEN)
            else:
                print(f"HOLD: {stock_name} ({isin}) changed {pct_change:.2f}% in last week.")

if __name__ == '__main__':
    main()