import os
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from django.conf import settings
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam

logger = logging.getLogger(__name__)

class CryptoModelTrainer:
    """
    Service for fine-tuning existing LSTM models on fresh market data.
    """
    def __init__(self, symbol: str, window_size: int = 60):
        self.symbol = symbol.upper()
        self.window_size = window_size
        self.models_dir = Path(settings.BASE_DIR) / 'models'
        
        # Resolving model path
        key = self.symbol.lower()
        if not key.endswith('-usd') and not key.endswith('_usd'):
            key = f"{key}_usd"
        key = key.replace('-', '_')
        
        self.model_path = self.models_dir / f"{key}_model.keras"
        self.scaler_path = self.models_dir / f"{key}_scaler.gz"

    def retrain_model(self, period='3mo', epochs=5, learning_rate=1e-5):
        if not self.model_path.exists() or not self.scaler_path.exists():
            raise FileNotFoundError(f"Model or scaler for {self.symbol} not found in {self.models_dir}. Cannot retrain.")
            
        logger.info(f"Loading existing model for {self.symbol}...")
        model = load_model(str(self.model_path))
        scaler = joblib.load(str(self.scaler_path))
        
        # Determine correct yfinance ticker format (e.g. BTC-USD)
        yf_ticker = self.symbol
        if not yf_ticker.endswith('-USD'):
            yf_ticker = f"{yf_ticker}-USD"
            
        logger.info(f"Downloading recent {period} data for {yf_ticker}...")
        df = yf.download(yf_ticker, period=period, interval='1h', auto_adjust=True, progress=False)
        
        if df.empty:
            return False, f"No data returned from yfinance for {yf_ticker}."
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.dropna(inplace=True)
        
        # Feature Engineering (must match exact logic)
        close = df['Close']
        df['SMA_20'] = close.rolling(window=20).mean()
        df['SMA_50'] = close.rolling(window=50).mean()
        df['RSI_14'] = self._calc_rsi(close)
        df['MACD'], df['MACD_Signal'] = self._calc_macd(close)
        df['Daily_Return'] = close.pct_change()
        df['Volatility_10'] = df['Daily_Return'].rolling(window=10).std()
        
        feature_cols = ['Close', 'High', 'Low', 'Volume', 'SMA_20', 'SMA_50', 'RSI_14', 'MACD', 'MACD_Signal', 'Daily_Return', 'Volatility_10']
        df = df[feature_cols].dropna()
        
        if len(df) <= self.window_size:
            return False, f"Not enough valid data points ({len(df)}) after feature engineering."
            
        close_col_idx = feature_cols.index('Close')
        dataset = df.values
        
        # Fine-tune the scaler using partial_fit to adapt to new highs/lows
        scaler.partial_fit(dataset)
        scaled_data = scaler.transform(dataset)
        
        X, y = [], []
        for i in range(self.window_size, len(scaled_data)):
            X.append(scaled_data[i - self.window_size:i])
            y.append(scaled_data[i, close_col_idx])
            
        X, y = np.array(X), np.array(y)
        
        logger.info(f"Recompiling model for {self.symbol} with lower learning rate ({learning_rate}) to prevent catastrophic forgetting.")
        model.compile(optimizer=Adam(learning_rate=learning_rate), loss='huber')
        
        callbacks = [
            EarlyStopping(monitor='loss', patience=3, restore_best_weights=True),
        ]
        
        logger.info(f"Fine-tuning {self.symbol} model for {epochs} epochs on {len(X)} samples...")
        model.fit(X, y, epochs=epochs, batch_size=32, callbacks=callbacks, verbose=0)
        
        logger.info(f"Saving updated model and scaler to {self.models_dir}...")
        model.save(str(self.model_path))
        joblib.dump(scaler, str(self.scaler_path))
        
        return True, f"Successfully retrained on {len(X)} recent hourly samples."
        
    def _calc_rsi(self, series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        return 100 - (100 / (1 + rs))

    def _calc_macd(self, series):
        ema_fast = series.ewm(span=12, adjust=False).mean()
        ema_slow = series.ewm(span=26, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        return macd_line, signal_line
