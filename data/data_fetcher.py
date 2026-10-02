import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import numpy as np

class CryptoDataFetcher:
    def __init__(self):
        self.symbols = {
            'BTC': 'BTC-USD',
            'ETH': 'ETH-USD',
            'SOL': 'SOL-USD',
            'BNB': 'BNB-USD',
            'XRP': 'XRP-USD',
            'DOGE': 'DOGE-USD',
            'ADA': 'ADA-USD',
            'AVAX': 'AVAX-USD',
            'LINK': 'LINK-USD',
            'DOT': 'DOT-USD',
            'LTC': 'LTC-USD'
        }
        self.fallback_prices = {
            'BTC': 115000.0,
            'ETH': 4500.0,
            'SOL': 235.0,
            'BNB': 925.0,
            'XRP': 3.0,
            'DOGE': 0.26,
            'ADA': 0.87,
            'AVAX': 30.5,
            'LINK': 23.5,
            'DOT': 4.23,
            'LTC': 115.0
        }
    
    def fetch_historical_data(self, symbol='BTC', period='1y'):
        """Fetch historical crypto data"""
        try:
            ticker_symbol = self.symbols.get(symbol, f'{symbol}-USD')
            ticker = yf.Ticker(ticker_symbol)
            
            # Get historical data
            hist = ticker.history(period=period)
            
            if hist.empty:
                # Fallback: generate sample data if API fails
                return self.generate_sample_data(symbol)
            
            # Clean and prepare data
            hist = hist.reset_index()
            hist['Date'] = pd.to_datetime(hist['Date'])
            
            return hist[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        except Exception as e:
            print(f"Error fetching data: {e}")
            return self.generate_sample_data(symbol)
    
    def get_current_price(self, symbol='BTC'):
        """Get current crypto price"""
        try:
            ticker_symbol = self.symbols.get(symbol, f'{symbol}-USD')
            ticker = yf.Ticker(ticker_symbol)
            
            # Get recent data
            hist = ticker.history(period='1d', interval='1m')
            
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            else:
                # Fallback price
                return self.fallback_prices.get(symbol, 100.0)
        
        except Exception as e:
            print(f"Error fetching current price: {e}")
            return self.fallback_prices.get(symbol, 100.0)
    
    def generate_sample_data(self, symbol='BTC'):
        """Generate sample crypto data for demonstration"""
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        
        # Generate realistic price data based on symbol
        np.random.seed(42)  # For reproducibility
        prices = []
        start_price = self.fallback_prices.get(symbol, 100.0)
        current_price = start_price
        
        for i in range(len(dates)):
            # Add some trend and volatility
            trend = 0.0002 * i  # Slight upward trend
            volatility = np.random.normal(0, 0.02)  # 2% daily volatility
            
            current_price = current_price * (1 + trend + volatility)
            prices.append(current_price)
        
        # Create OHLC data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            high = close * (1 + abs(np.random.normal(0, 0.01)))
            low = close * (1 - abs(np.random.normal(0, 0.01)))
            open_price = prices[i-1] if i > 0 else close
            volume = np.random.randint(1000000, 10000000)
            
            data.append({
                'Date': date,
                'Open': open_price,
                'High': max(open_price, high, close),
                'Low': min(open_price, low, close),
                'Close': close,
                'Volume': volume
            })
        
        return pd.DataFrame(data)