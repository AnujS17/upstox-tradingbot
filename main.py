import yfinance as yf
import pandas as pd
import numpy as np
import requests
from upstox_api.api import Upstox
from datetime import datetime, timedelta
import requests

url = "https://api.upstox.com/v2/login/authorization/dialog"

payload={}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

class SwingTraderPro:
    def __init__(self, client_id, access_token):
        # Upstox API v2 configuration
        self.base_url = "https://api.upstox.com/v2"
        self.client_id = client_id
        self.access_token = access_token
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'Api-Version': '2.0'
        }
        
        # Verify connection
        self._verify_connection()
        
        # Enhanced sector parameters (30+ sectors)
        self.sector_params = {
            # Technology
            'Information Technology': {'debt_equity_max': 0.3, 'pe_max': 45, 'interest_coverage': 4},
            'Software': {'debt_equity_max': 0.4, 'pe_max': 50, 'interest_coverage': 5},
            'Semiconductors': {'debt_equity_max': 0.5, 'pe_max': 40, 'interest_coverage': 3},
            
            # Financials
            'Banking': {'debt_equity_max': 10, 'pe_max': 25, 'interest_coverage': 1.5},
            'Financial Services': {'debt_equity_max': 3, 'pe_max': 30, 'interest_coverage': 2},
            'Insurance': {'debt_equity_max': 0.8, 'pe_max': 28, 'interest_coverage': 3},
            
            # Healthcare
            'Pharmaceuticals': {'debt_equity_max': 0.6, 'pe_max': 35, 'interest_coverage': 4},
            'Biotechnology': {'debt_equity_max': 0.7, 'pe_max': 60, 'interest_coverage': 2},
            'Healthcare': {'debt_equity_max': 0.5, 'pe_max': 40, 'interest_coverage': 3},
            
            # Cyclicals
            'Automobile': {'debt_equity_max': 1.2, 'pe_max': 22, 'interest_coverage': 2.5},
            'Consumer Durables': {'debt_equity_max': 0.8, 'pe_max': 25, 'interest_coverage': 3},
            'Retail': {'debt_equity_max': 0.7, 'pe_max': 30, 'interest_coverage': 3},
            
            # Infrastructure
            'Construction': {'debt_equity_max': 1.5, 'pe_max': 20, 'interest_coverage': 2},
            'Metals & Mining': {'debt_equity_max': 1.2, 'pe_max': 18, 'interest_coverage': 2},
            'Oil & Gas': {'debt_equity_max': 1.3, 'pe_max': 15, 'interest_coverage': 2},
            
            # Defensives
            'Utilities': {'debt_equity_max': 1.8, 'pe_max': 20, 'interest_coverage': 2},
            'Telecom': {'debt_equity_max': 2.0, 'pe_max': 18, 'interest_coverage': 1.5},
            'FMCG': {'debt_equity_max': 0.6, 'pe_max': 35, 'interest_coverage': 4},
            
            'default': {'debt_equity_max': 0.8, 'pe_max': 25, 'interest_coverage': 2}
        }
        
        # ADX parameters
        self.adx_period = 14
        self.adx_threshold = 25
        
    def _verify_connection(self):
        """Verify API connection works"""
        try:
            response = requests.get(
                f"{self.base_url}/user/profile",
                headers=self.headers
            )
            if response.status_code != 200:
                raise ConnectionError(f"API connection failed: {response.text}")
            print("Successfully connected to Upstox API v2")
        except Exception as e:
            raise ConnectionError(f"API connection error: {str(e)}")
        
    def get_fundamentals(self, ticker):
        """Quick fundamental health check"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            sector = info.get('sector', 'default')
            params = self.sector_params.get(sector, self.sector_params['default'])
            
            return {
                'ticker': ticker,
                'sector': sector,
                'debt_ok': info.get('debtToEquity', 0) < params['debt_equity_max'],
                'pe_ok': info.get('trailingPE', 100) < params['pe_max'],
                'current_ratio_ok': info.get('currentRatio', 0) > 1.0,
                'quick_ratio_ok': info.get('quickRatio', 0) > 0.8
            }
        except:
            return None
    
    def get_ohlc_data(self, symbol, interval='day', days_back=100):
        """Get OHLC data from Upstox API v2"""
        try:
            instrument = self._get_instrument_details(symbol)
            if not instrument:
                return None
                
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/historical-candle/{instrument['exchange']}/{instrument['symbol']}/{interval}"
            params = {
                'to_date': to_date,
                'from_date': from_date
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                candles = response.json()['data']['candles']
                df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                return df
            else:
                print(f"Error fetching OHLC: {response.text}")
                return None
        except Exception as e:
            print(f"Error in get_ohlc_data: {str(e)}")
            return None

    def _get_instrument_details(self, symbol, exchange='NSE'):
        """Get instrument details for a symbol"""
        try:
            url = f"{self.base_url}/search/instruments"
            params = {'query': symbol, 'exchange': exchange}
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                instruments = response.json()['data']
                if instruments:
                    return {
                        'symbol': instruments[0]['symbol'],
                        'exchange': instruments[0]['exchange'],
                        'instrument_key': instruments[0]['instrument_key']
                    }
            return None
        except Exception as e:
            print(f"Error getting instrument details: {str(e)}")
            return None
    def get_technicals(self, ticker):
        """Comprehensive technical analysis with ADX"""
        try:
            # Get OHLC data from Upstox
            instrument = self.upstox.get_instrument_by_symbol('NSE', ticker)
            ohlc = self.upstox.get_ohlc(instrument, 'day', 
                                      datetime.now() - timedelta(days=100),
                                      datetime.now())
            df = pd.DataFrame(ohlc)
            
            # Calculate EMAs
            df['9_ema'] = df['close'].ewm(span=9).mean()
            df['21_ema'] = df['close'].ewm(span=21).mean()
            df['50_ema'] = df['close'].ewm(span=50).mean()
            
            # Calculate ADX
            df['tr'] = self._true_range(df)
            df['atr'] = df['tr'].rolling(self.adx_period).mean()
            
            # +DM and -DM
            df['plus_dm'] = df['high'].diff()
            df['minus_dm'] = -df['low'].diff()
            df['plus_dm'] = df.apply(lambda x: x['plus_dm'] if x['plus_dm'] > x['minus_dm'] and x['plus_dm'] > 0 else 0, axis=1)
            df['minus_dm'] = df.apply(lambda x: x['minus_dm'] if x['minus_dm'] > x['plus_dm'] and x['minus_dm'] > 0 else 0, axis=1)
            
            # Smoothed +DM, -DM, and TR
            df['plus_di'] = 100 * (df['plus_dm'].rolling(self.adx_period).mean() / df['atr'])
            df['minus_di'] = 100 * (df['minus_dm'].rolling(self.adx_period).mean() / df['atr'])
            df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
            df['adx'] = df['dx'].rolling(self.adx_period).mean()
            
            # Volume analysis
            df['20_day_vol'] = df['volume'].rolling(20).mean()
            df['rvol'] = df['volume'] / df['20_day_vol']
            
            latest = df.iloc[-1]
            
            return {
                'adx': latest['adx'],
                'plus_di': latest['plus_di'],
                'minus_di': latest['minus_di'],
                'ema_crossover': latest['9_ema'] > latest['21_ema'] > latest['50_ema'],
                'price_above_ema': latest['close'] > latest['9_ema'],
                'rvol': latest['rvol'],
                'atr': latest['atr'],
                'current_price': latest['close']
            }
        except Exception as e:
            print(f"Technical analysis error for {ticker}: {e}")
            return None
    
    def _true_range(self, df):
        """Calculate True Range for ADX"""
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    def evaluate_trade(self, ticker):
        """Composite evaluation with ADX momentum"""
        fundamentals = self.get_fundamentals(ticker)
        if not fundamentals or not all([
            fundamentals['debt_ok'],
            fundamentals['pe_ok'],
            fundamentals['current_ratio_ok']
        ]):
            return {'ticker': ticker, 'decision': 'REJECT', 'reason': 'Fundamentals'}
        
        technicals = self.get_technicals(ticker)
        if not technicals: 
            return {'ticker': ticker, 'decision': 'REJECT', 'reason': 'Technical data'}
        
        # ADX Momentum Rules
        adx_ok = technicals['adx'] > self.adx_threshold
        trend_strength = technicals['plus_di'] > technicals['minus_di']
        ema_alignment = technicals['ema_crossover']
        volume_ok = technicals['rvol'] > 1.5
        
        if all([adx_ok, trend_strength, ema_alignment, volume_ok]):
            # Calculate risk management
            stop_loss = technicals['current_price'] - (2 * technicals['atr'])
            target = technicals['current_price'] + (4 * technicals['atr'])
            
            return {
                'ticker': ticker,
                'decision': 'BUY',
                'entry': technicals['current_price'],
                'stop_loss': round(stop_loss, 2),
                'target': round(target, 2),
                'adx': round(technicals['adx'], 2),
                'rvol': round(technicals['rvol'], 2)
            }
        elif technicals['adx'] < 20:
            return {'ticker': ticker, 'decision': 'WAIT', 'reason': 'Weak trend (ADX < 20)'}
        else:
            return {'ticker': ticker, 'decision': 'HOLD', 'reason': 'Waiting for confirmation'}

# Example Usage
if __name__ == "__main__":
    # Initialize with your Upstox credentials
    trader = SwingTraderPro(
        client_id="5b0b5830-a3ed-4083-a6e3-c356b3d1e34e",
        access_token="eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NEFMNVoiLCJqdGkiOiI2N2VkYTY5Y2E4ZTMwMzUyMTRlMWIyMzciLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzQzNjI3OTMyLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDM2MzEyMDB9.mcnCJnGv8cQvQJWulIzCjJPjFn9zIEKObBHVVYMEDoQ"
        )
    
    watchlist = ['RELIANCE', 'TATASTEEL', 'HDFCBANK', 'INFY', 'BHARTIARTL']
    
    # Evaluate all stocks
    results = [trader.evaluate_trade(ticker) for ticker in watchlist]
    
    # Display actionable trades
    print("Actionable Trades:")
    for trade in results:
        if trade['decision'] == 'BUY':
            print(f"{trade['ticker']}:")
            print(f"  Entry: {trade['entry']}")
            print(f"  Stop Loss: {trade['stop_loss']}")
            print(f"  Target: {trade['target']}")
            print(f"  ADX: {trade['adx']}, RVOL: {trade['rvol']}\n")