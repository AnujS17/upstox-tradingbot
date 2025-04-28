import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt
from config import sector_params, SYMBOL_TO_ISIN, base_url

class SwingTraderPro:
    def __init__(self, client_id, access_token):
        # Upstox API v2 configuration
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

    # Reverse mapping for lookup
        self.ISIN_TO_SYMBOL = {v: k for k, v in self.SYMBOL_TO_ISIN.items()}
            
        # Verify connection
        self._verify_connection()
        
        # Enhanced sector parameters (30+ sectors)
        self.sector_params = sector_params
        
    def _verify_connection(self):
        """Verify API connection works with proper client_id"""
        try:
            url = f"{self.base_url}/user/profile"
            params = {'client_id': self.client_id}
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params
            )
            
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
                # url = f"{self.base_url}/search/instruments"
                # params = {
                #     'query': isin,
                #     'exchange': 'NSE',
                #     'client_id': self.client_id
                # }
                
                # response = requests.get(url, headers=self.headers, params=params)
                # if response.status_code == 200:
                #     instruments = response.json()['data']
                #     if instruments:
                #         return {
                #             'symbol': symbol,
                #             'isin': isin,
                #             'exchange': instruments[0]['exchange'],
                #             'instrument_key': instrument_key,
                #         }
                return {
                'symbol': symbol,
                'isin': isin,
                'instrument_key': instrument_key,  # Upstox required format
                'exchange': 'NSE'
            }
                
            except Exception as e:
                print(f"Error getting instrument details: {str(e)}")
                return None

    def get_ohlc_data(self, symbol, interval='day', days_back=100):
        """Get OHLC data from Upstox API v2 with proper client_id"""
        try:
            instrument = self._get_instrument_details(symbol)
            if not instrument:
                print(f"Instrument details not found for {symbol}")
                return None

            # Format dates
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            # URL-encode the instrument key (replace | with %7C)
            encoded_key = instrument['instrument_key'].replace("|", "%7C")
            
            url = f"{self.base_url}/historical-candle/{encoded_key}/{interval}/{to_date}/{from_date}"
            
            response = requests.get(
                url,
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()
                candles = data['data']['candles']
                
                # Create DataFrame
                df = pd.DataFrame(candles, columns=[
                    'timestamp',
                    'open',
                    'high', 
                    'low',
                    'close',
                    'volume',
                    'oi'
                ])
                
                # Convert and sort timestamps
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
    
    def get_fundamentals(self, ticker):
       max_retries = 2
       for attempt in range(max_retries):
            try:
                yf_ticker = f"{ticker}.NS" if attempt == 0 else ticker
                stock = yf.Ticker(yf_ticker)
                info = stock.info
                
                if not info:
                    raise ValueError("Empty response from yfinance")
                
                # Get sector and clean it (remove extra spaces, handle None)
                sector = (info.get('sector') or 'default').strip().title()
                
                # Match sector to our parameters (with case-insensitive fallback)
                params = next(
                    (v for k, v in self.sector_params.items() 
                    if k.lower() == sector.lower()),
                    self.sector_params['default']
                )
                
                return {
                    'ticker': ticker,
                    'sector': sector,  # Actual sector from Yahoo
                    'debt_ok': info.get('debtToEquity', 0) < params['debt_equity_max'],
                    'pe_ok': info.get('trailingPE', 100) < params['pe_max'],
                    # 'current_ratio_ok': info.get('currentRatio', 0) > 0.5,
                    # 'quick_ratio_ok': info.get('quickRatio', 0) > 0.4
                }
                
            except Exception as e:
                print(f"Attempt {attempt+1} for {ticker}: {str(e)}")
                if attempt == max_retries - 1:
                    return self._fallback_fundamentals(ticker)
                time.sleep(1)

    def get_technicals(self, ticker):
        """Technical analysis with Upstox API v2 data"""
        try:
            df = self.get_ohlc_data(ticker)
            if df is None or len(df) < 50:  # Need sufficient data for indicators
                print(f"Insufficient data for {ticker}")
                return None
                
            # Calculate EMAs
            df['9_ema'] = df['close'].ewm(span=9).mean()
            df['21_ema'] = df['close'].ewm(span=21).mean()
            df['50_ema'] = df['close'].ewm(span=50).mean()
            
            # Calculate ADX (requires 14 periods minimum)
            df['tr'] = self._true_range(df)
            df['atr'] = df['tr'].rolling(14).mean()
            df['plus_dm'] = df['high'].diff()
            df['minus_dm'] = -df['low'].diff()
            df['plus_dm'] = df.apply(lambda x: x['plus_dm'] if x['plus_dm'] > x['minus_dm'] and x['plus_dm'] > 0 else 0, axis=1)
            df['minus_dm'] = df.apply(lambda x: x['minus_dm'] if x['minus_dm'] > x['plus_dm'] and x['minus_dm'] > 0 else 0, axis=1)
            df['plus_di'] = 100 * (df['plus_dm'].rolling(14).mean() / df['atr'])
            df['minus_di'] = 100 * (df['minus_dm'].rolling(14).mean() / df['atr'])
            df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
            df['adx'] = df['dx'].rolling(14).mean()
            
            # Volume analysis
            df['20_day_vol'] = df['volume'].rolling(20).mean()
            df['rvol'] = df['volume'] / df['20_day_vol']
            
            latest = df.iloc[-1]  # Get most recent data
            
            print(f"\n{ticker} Technicals:")
            print(f"- Current Price: {latest['close']}")
            print(f"- Volume: {latest['volume']} (RVOL: {latest['rvol']:.2f}x)")
            print(f"- ADX: {latest['adx']:.1f} (+DI: {latest['plus_di']:.1f}, -DI: {latest['minus_di']:.1f})")
            print(f"- EMAs: 9EMA={latest['9_ema']:.1f}, 21EMA={latest['21_ema']:.1f}, 50EMA={latest['50_ema']:.1f}")
                    
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
            print(f"Technical analysis error for {ticker}: {str(e)}")
            return None

    def _true_range(self, df):
        """Calculate True Range for ADX"""
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    def evaluate_trade(self, ticker, print_stats=True):
        fundamentals = self.get_fundamentals(ticker)
        if not fundamentals or not all([
            fundamentals['debt_ok'],
            fundamentals['pe_ok'],
            # fundamentals['current_ratio_ok']
        ]):
            rejection = {'ticker': ticker, 'decision': 'REJECT', 'reason': 'Fundamentals'}
            if print_stats:
                print(f"\n🔴 {ticker} REJECTED - Failed Fundamentals:")
                print(f"   Debt Ratio: {fundamentals.get('debt_ratio', 'N/A')}")
                print(f"   P/E: {fundamentals.get('pe_ratio', 'N/A')}")
            return rejection
            
        technicals = self.get_technicals(ticker)
        if not technicals:
            rejection = {'ticker': ticker, 'decision': 'REJECT', 'reason': 'Technical data'}
            if print_stats:
                print(f"\n🔴 {ticker} REJECTED - Missing Technical Data")
            return rejection
            
        # ADX Momentum Rules
        adx_ok = technicals['adx'] > 25
        trend_strength = technicals['plus_di'] > technicals['minus_di']
        ema_alignment = technicals['ema_crossover']
        volume_ok = technicals['rvol'] > 0.3
        
        if all([adx_ok, trend_strength, ema_alignment, volume_ok]):
            # Risk management calculations
            entry = technicals['current_price']
            stop_loss = entry - (2 * technicals['atr'])
            target = entry + (4 * technicals['atr'])
            risk_reward = (target - entry) / (entry - stop_loss)
            
            trade_stats = {
                'ticker': ticker,
                'decision': 'BUY',
                'entry': entry,
                'stop_loss': round(stop_loss, 2),
                'target': round(target, 2),
                'adx': round(technicals['adx'], 2),
                'rvol': round(technicals['rvol'], 2),
                'atr': round(technicals['atr'], 2),
                'risk_reward': round(risk_reward, 2)
            }
            
            if print_stats:
                print(f"\n✅ {ticker} BUY SIGNAL")
                print(f"   Entry Price: {entry}")
                print(f"   Stop Loss: {round(stop_loss, 2)} ({round((entry - stop_loss)/entry*100, 1)}% risk)")
                print(f"   Target: {round(target, 2)} ({round((target - entry)/entry*100, 1)}% gain)")
                print(f"   Risk/Reward: 1:{round(risk_reward, 1)}")
                print(f"   Trend Strength (ADX): {round(technicals['adx'], 1)}")
                print(f"   Volume (RVOL): {round(technicals['rvol'], 1)}x")
                print(f"   EMA Alignment: 9EMA > 21EMA > 50EMA")
                
            return trade_stats
            
        elif technicals['adx'] < 20:
            decision = {'ticker': ticker, 'decision': 'WAIT', 'reason': 'Weak trend (ADX < 20)'}
            if print_stats:
                print(f"\n🟡 {ticker} WAIT - Weak Trend (ADX: {round(technicals['adx'], 1)})")
            return decision
        else:
            decision = {'ticker': ticker, 'decision': 'HOLD', 'reason': 'Waiting for confirmation'}
            if print_stats:
                print(f"\n🟠 {ticker} HOLD - Insufficient Confirmation")
                print(f"   ADX: {round(technicals['adx'], 1)} (Needs >25)")
                print(f"   +DI/-DI: {round(technicals['plus_di'], 1)}/{round(technicals['minus_di'], 1)}")
                print(f"   RVOL: {round(technicals['rvol'], 1)}x (Needs >1.5x)")
            return decision

    def plot_technicals(self, ticker):
        df = self.get_ohlc_data(ticker)
        if df is None or df.empty:
            print(f"No data for {ticker}")
            return
        
        # Calculate all technical indicators
        df = self._calculate_technicals(df)
        
        # Create figure
        plt.figure(figsize=(12, 10))
        
        # Plot 1: Price and EMAs
        plt.subplot(3, 1, 1)
        plt.plot(df.index, df['close'], label='Price', color='black', linewidth=1.5)
        plt.plot(df.index, df['9_ema'], label='9 EMA', color='blue', alpha=0.8)
        plt.plot(df.index, df['21_ema'], label='21 EMA', color='orange', alpha=0.8)
        plt.plot(df.index, df['50_ema'], label='50 EMA', color='red', alpha=0.8)
        plt.title(f"{ticker} Price Analysis", fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Volume
        plt.subplot(3, 1, 2)
        plt.bar(df.index, df['volume'], color='purple', alpha=0.6, label='Daily Volume')
        plt.plot(df.index, df['20_day_vol'], color='red', linewidth=2, label='20D Avg Volume')
        plt.title("Volume Analysis", fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 3: ADX and DIs
        plt.subplot(3, 1, 3)
        plt.plot(df.index, df['adx'], label='ADX (Trend Strength)', color='green', linewidth=2)
        plt.plot(df.index, df['plus_di'], label='+DI', color='blue', linestyle='--')
        plt.plot(df.index, df['minus_di'], label='-DI', color='red', linestyle='--')
        plt.axhline(25, color='gray', linestyle=':', label='Trend Threshold (25)')
        plt.title("Trend Strength Analysis", fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        time.sleep(0.1)  # Prevent plot from closing immediately

    def _calculate_technicals(self, df):
        """Calculate all technical indicators for plotting"""
        # EMAs
        df['9_ema'] = df['close'].ewm(span=9, adjust=False).mean()
        df['21_ema'] = df['close'].ewm(span=21, adjust=False).mean()
        df['50_ema'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # Volume
        df['20_day_vol'] = df['volume'].rolling(20).mean()
        
        # ADX Calculation
        df['tr'] = self._true_range(df)
        df['atr'] = df['tr'].rolling(14).mean()
        df['plus_dm'] = df['high'].diff().clip(lower=0)
        df['minus_dm'] = (-df['low'].diff()).clip(lower=0)
        df['plus_di'] = 100 * (df['plus_dm'].rolling(14).mean() / df['atr'])
        df['minus_di'] = 100 * (df['minus_dm'].rolling(14).mean() / df['atr'])
        df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        df['adx'] = df['dx'].rolling(14).mean()
        
        return df
    
if __name__ == "__main__":
    # Initialize with your Upstox credentials
    trader = SwingTraderPro(
        client_id="your_client_id",  # From Upstox developer console
        access_token= "your_access_token"  # From Upstox login
        )

    watchlist = ['HDFCBANK']
    
    for symbol in watchlist:
        print(f"\nAnalyzing {symbol}...")
        fundamentals = trader.get_fundamentals(symbol)
    
        technicals = trader.get_technicals(symbol)
        
        trader.plot_technicals(symbol)
        
        decision = trader.evaluate_trade(symbol)
        print(decision)

    results = [trader.evaluate_trade(ticker) for ticker in watchlist]
    
    print("\nActionable Trades:")
    print(results)
    for trade in results:
        if trade['decision'] == 'BUY':
            print(f"\n{trade['ticker']}:")
            print(f"  Entry: {trade['entry']}")
            print(f"  Stop Loss: {trade['stop_loss']}")
            print(f"  Target: {trade['target']}")
            print(f"  ADX: {trade['adx']} (Trend Strength)")
            print(f"  Volume: {trade['rvol']:.2f}x average")