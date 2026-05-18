from datetime import timedelta

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from django.conf import settings
from django.utils import timezone

from tracker.models import Cryptocurrency, CryptocurrencyPrice

COINGECKO_IDS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'BNB': 'binancecoin',
    'SOL': 'solana',
    'XRP': 'ripple',
    'ADA': 'cardano',
    'MATIC': 'matic-network',
    'DOT': 'polkadot',
    'AVAX': 'avalanche-2',
}


class MarketDataClient:
    """Fetches current price and feature history for ML inference."""

    def __init__(self, sequence_length=60):
        self.sequence_length = sequence_length

    def _headers(self):
        headers = {'accept': 'application/json'}
        api_key = getattr(settings, 'COINGECKO_API_KEY', None)
        if api_key:
            headers['x-cg-pro-api-key'] = api_key
        return headers

    def get_current_price(self, symbol: str) -> float:
        cg_id = COINGECKO_IDS.get(symbol.upper())
        if not cg_id:
            raise ValueError(f'Unsupported symbol for market data: {symbol}')

        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {'ids': cg_id, 'vs_currencies': 'usd'}
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if cg_id not in data or 'usd' not in data[cg_id]:
            raise ValueError(f'Price unavailable for {symbol}')
        return float(data[cg_id]['usd'])

    def get_ml_features(self, symbol: str, limit: int | None = None) -> np.ndarray:
        limit = limit or self.sequence_length
        ticker = f"{symbol.upper()}-USD"
        
        # Download sufficient history to calculate SMA_50 (need at least limit + 50 + some buffer)
        df = yf.download(ticker, period='150d', interval='1d', auto_adjust=True, progress=False)
        if df.empty:
            raise ValueError(f"No data fetched for {ticker} from yfinance")
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.dropna(inplace=True)
        close = df['Close']
        df['SMA_20'] = close.rolling(window=20).mean()
        df['SMA_50'] = close.rolling(window=50).mean()
        
        # RSI 14
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_fast = close.ewm(span=12, adjust=False).mean()
        ema_slow = close.ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Daily Return & Volatility
        df['Daily_Return'] = close.pct_change()
        df['Volatility_10'] = df['Daily_Return'].rolling(window=10).std()
        
        feature_cols = ['Close', 'High', 'Low', 'Volume', 'SMA_20', 'SMA_50', 
                        'RSI_14', 'MACD', 'MACD_Signal', 'Daily_Return', 'Volatility_10']
                        
        df = df[feature_cols].dropna()
        if len(df) < limit:
            raise ValueError(f'Not enough feature history for {symbol}: need {limit}, got {len(df)}')
            
        return df.values[-limit:]
