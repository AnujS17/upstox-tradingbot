import requests
import pandas as pd
from datetime import datetime, timedelta

# Example mappings (replace with your actual data)
SYMBOL_TO_ISIN = {
    "RELIANCE": "INE002A01018",
    "TCS": "INE467B01029",
    "INFY": "INE009A01021"
}
sector_params = {}  # Add your sector params if needed
base_url = "https://api.upstox.com/v2"  # Upstox API v2 base URL

class SwingTraderPro:
    def __init__(self, client_id, access_token):
        self.base_url = base_url
        self.client_id = client_id
        self.access_token = access_token
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'Api-Version': '2.0',
            'Content-Type': 'application/json'
        }
        self.SYMBOL_TO_ISIN = SYMBOL_TO_ISIN
        self.ISIN_TO_SYMBOL = {v: k for k, v in self.SYMBOL_TO_ISIN.items()}
        self._verify_connection()
        self.sector_params = sector_params

    def _verify_connection(self):
        """Verify API connection works with proper client_id"""
        try:
            url = f"{self.base_url}/user/profile"
            params = {'client_id': self.client_id}
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                print("Successfully connected to Upstox API v2")
                return True
            else:
                error_msg = response.json().get('message', 'Unknown error')
                raise ConnectionError(f"API connection failed: {error_msg}")
        except Exception as e:
            raise ConnectionError(f"API connection error: {str(e)}")

    def _get_instrument_details(self, symbol):
        try:
            isin = self.SYMBOL_TO_ISIN.get(symbol)
            if not isin:
                print(f"ISIN not found for {symbol}. Please add to SYMBOL_TO_ISIN mapping.")
                return None
            instrument_key = f"NSE_EQ|{isin}"
            return {
                'symbol': symbol,
                'isin': isin,
                'instrument_key': instrument_key,
                'exchange': 'NSE'
            }
        except Exception as e:
            print(f"Error getting instrument details: {str(e)}")
            return None

    def get_ohlc_data(self, symbol, interval='day', days_back=7):
        """Get OHLC data from Upstox API v2 with proper client_id"""
        try:
            instrument = self._get_instrument_details(symbol)
            if not instrument:
                print(f"Instrument details not found for {symbol}")
                return None
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            encoded_key = instrument['instrument_key'].replace("|", "%7C")
            url = f"{self.base_url}/historical-candle/{encoded_key}/{interval}/{to_date}/{from_date}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                candles = data['data']['candles']
                df = pd.DataFrame(candles, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'
                ])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                df.sort_index(ascending=True, inplace=True)
                return df
            else:
                print(f"OHLC API Error for {symbol}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error in get_ohlc_data for {symbol}: {str(e)}")
            return None

    def place_order(self, symbol, quantity, side='BUY', order_type='MARKET', product='I', validity='DAY'):
        """Place a buy or sell order using Upstox API v2."""
        instrument = self._get_instrument_details(symbol)
        if not instrument:
            print(f"Cannot place order: Instrument details not found for {symbol}")
            return None
        url = f"{self.base_url}/order/place"
        payload = {
            "quantity": quantity,
            "product": product,
            "validity": validity,
            "price": 0,
            "tag": "SwingTraderPro",
            "instrument_token": instrument['instrument_key'],
            "transaction_type": side,
            "order_type": order_type,
            "disclosed_quantity": 0,
            "trigger_price": 0
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            print(f"{side} order placed for {symbol}: {quantity} shares")
            return response.json()
        else:
            print(f"Order failed: {response.status_code} - {response.text}")
            return None

    def buy_stock(self, symbol, amount_usd):
        """Buy $amount_usd worth of stock at current market price."""
        df = self.get_ohlc_data(symbol, interval='day', days_back=2)
        if df is None or df.empty:
            print(f"Cannot buy {symbol}: No price data.")
            return None
        last_close = df['close'][-1]
        # If your account is in INR, convert USD to INR here.
        quantity = max(1, int(amount_usd / last_close))
        return self.place_order(symbol, quantity, side='BUY')

    def sell_stock(self, symbol):
        """Sell all holdings of a stock (for simplicity)."""
        holding_qty = self.get_holding_quantity(symbol)
        if holding_qty > 0:
            return self.place_order(symbol, holding_qty, side='SELL')
        else:
            print(f"No holdings found for {symbol} to sell.")
            return None

    def get_holding_quantity(self, symbol):
        """Fetch current holding quantity for a symbol (stub, implement as needed)."""
        # Replace this stub with actual Upstox holdings API call.
        return 10  # Dummy value for demonstration

    def weekly_rebalance(self, tickers, buy_amount_usd=5):
        """Buy stocks down 5% in a week, sell stocks up 10% in a week."""
        for symbol in tickers:
            df = self.get_ohlc_data(symbol, interval='day', days_back=7)
            if df is None or len(df) < 2:
                print(f"Not enough data for {symbol}")
                continue
            week_ago_close = df['close'].iloc[0]
            last_close = df['close'].iloc[-1]
            pct_change = ((last_close - week_ago_close) / week_ago_close) * 100
            print(f"{symbol}: {pct_change:.2f}% change this week")
            if pct_change <= -5:
                print(f"Buying ${buy_amount_usd} of {symbol} (down {pct_change:.2f}%)")
                self.buy_stock(symbol, buy_amount_usd)
            elif pct_change >= 10:
                print(f"Selling all holdings of {symbol} (up {pct_change:.2f}%)")
                self.sell_stock(symbol)
            else:
                print(f"No action for {symbol}")

UPSTOX_CLIENT_ID = "23a76d31-981d-4223-a315-9e19b8cff6f0"
UPSTOX_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NEFMNVoiLCJqdGkiOiI2ODI2Y2Y2YzdmZWVjZjQ1YTEzNWI5NWQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzQ3MzczOTMyLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDk5Mzg0MDB9.dKJB4HGLsEyQaYGjeZHGvlNQIDnEE0iTB9f02wQ0C2E"

csv_file = "EQUITY_L.csv"
# Read the CSV
df = pd.read_csv(csv_file)
# Preview columns
print(df.columns)

# Create a symbol-to-ISIN mapping
SYMBOL_TO_ISIN = dict(zip(df['SYMBOL'], df[' ISIN_NUMBER']))
# Get all tickers
tickers = list(SYMBOL_TO_ISIN.keys())[:10]
tickers = ['63MOONS']
sector_params = {}
# Now, initialize the class
trader = SwingTraderPro(
    client_id=UPSTOX_CLIENT_ID,
    access_token=UPSTOX_ACCESS_TOKEN
)


trader.weekly_rebalance(tickers)

