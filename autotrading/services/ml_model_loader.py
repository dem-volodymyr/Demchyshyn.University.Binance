from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yfinance as yf

from autotrading.services.model_metadata import (
    DEFAULT_FEATURE_COLS,
    TARGET_CLOSE_LEGACY,
    TARGET_LOG_RETURN,
    ModelMetadata,
    load_metadata,
)

SEQUENCE_LEN = 60


class MLModelLoader:
    """Loads Keras models from /models and produces trading signals."""

    def __init__(self, models_dir: Path, sequence_length: int = SEQUENCE_LEN):
        self.models_dir = Path(models_dir)
        self.sequence_length = sequence_length

    def model_paths(self, symbol: str) -> tuple[Path, Path]:
        key = symbol.upper().replace('-', '_').lower()
        if not key.endswith('_usd'):
            key = f'{key}_usd'
        model_path = self.models_dir / f'{key}_model.keras'
        scaler_path = self.models_dir / f'{key}_scaler.gz'
        if not model_path.exists():
            raise FileNotFoundError(f'Model not found: {model_path}')
        if not scaler_path.exists():
            raise FileNotFoundError(f'Scaler not found: {scaler_path}')
        return model_path, scaler_path

    def has_model(self, symbol: str) -> bool:
        try:
            self.model_paths(symbol)
            return True
        except FileNotFoundError:
            return False

    def has_inference_bundle(self, symbol: str) -> bool:
        if not self.has_model(symbol):
            return False
        meta = load_metadata(self.models_dir, symbol)
        if meta is None:
            return False
        if meta.target == TARGET_LOG_RETURN:
            return meta.y_mean is not None and meta.y_std is not None
        return True

    @lru_cache(maxsize=16)
    def _load_pair(self, symbol: str):
        from tensorflow.keras.models import load_model

        model_path, scaler_path = self.model_paths(symbol)
        model = load_model(model_path)
        scaler = joblib.load(scaler_path)
        meta = load_metadata(self.models_dir, symbol)
        return model, scaler, meta

    def _resolve_metadata(self, symbol: str, meta: ModelMetadata | None) -> ModelMetadata:
        if meta is not None:
            return meta
        loaded = load_metadata(self.models_dir, symbol)
        if loaded is not None:
            return loaded
        return ModelMetadata(target=TARGET_CLOSE_LEGACY, feature_cols=list(DEFAULT_FEATURE_COLS))

    def _estimate_return_stats(self, symbol: str) -> tuple[float, float]:
        ticker = f'{symbol.upper()}-USD'
        df = yf.download(ticker, period='2y', interval='1d', auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        log_ret = np.log(df['Close'] / df['Close'].shift(1)).dropna().values
        return float(log_ret.mean()), float(log_ret.std() + 1e-8)

    def predict_price(
        self,
        symbol: str,
        features: np.ndarray,
        current_price: float,
    ) -> float:
        if len(features) < self.sequence_length:
            raise ValueError(
                f'Need at least {self.sequence_length} feature rows, got {len(features)}'
            )

        model, scaler, meta = self._load_pair(symbol.upper())
        meta = self._resolve_metadata(symbol, meta)
        feature_cols = meta.feature_cols or list(DEFAULT_FEATURE_COLS)
        n_features = len(feature_cols)

        window = np.asarray(features[-self.sequence_length :], dtype=np.float64)
        if window.shape[1] != n_features:
            raise ValueError(
                f'Feature width mismatch for {symbol}: expected {n_features}, got {window.shape[1]}'
            )

        scaled = scaler.transform(window)
        X = np.reshape(scaled, (1, self.sequence_length, n_features))
        pred_scaled = float(model.predict(X, verbose=0)[0][0])

        if meta.target == TARGET_LOG_RETURN:
            y_mean = meta.y_mean
            y_std = meta.y_std
            if y_mean is None or y_std is None:
                y_mean, y_std = self._estimate_return_stats(symbol)
            pred_log_return = pred_scaled * y_std + y_mean
            return float(current_price * np.exp(pred_log_return))

        # Legacy: model predicted scaled Close column
        close_idx = feature_cols.index('Close')
        dummy = np.zeros((1, n_features))
        dummy[0, close_idx] = pred_scaled
        return float(scaler.inverse_transform(dummy)[0, close_idx])

    def predict_log_return(self, symbol: str, features: np.ndarray) -> float:
        """Raw model output in log-return space (before signal bias correction)."""
        if len(features) < self.sequence_length:
            raise ValueError(
                f'Need at least {self.sequence_length} feature rows, got {len(features)}'
            )

        model, scaler, meta = self._load_pair(symbol.upper())
        meta = self._resolve_metadata(symbol, meta)
        feature_cols = meta.feature_cols or list(DEFAULT_FEATURE_COLS)
        n_features = len(feature_cols)

        window = np.asarray(features[-self.sequence_length :], dtype=np.float64)
        scaled = scaler.transform(window)
        X = np.reshape(scaled, (1, self.sequence_length, n_features))
        pred_scaled = float(model.predict(X, verbose=0)[0][0])

        if meta.target == TARGET_LOG_RETURN:
            y_mean = meta.y_mean
            y_std = meta.y_std
            if y_mean is None or y_std is None:
                y_mean, y_std = self._estimate_return_stats(symbol)
            return float(pred_scaled * y_std + y_mean)

        predicted_price = self.predict_price(symbol, features, float(window[-1, 0]))
        ref = float(window[-1, 0])
        return float(np.log(predicted_price / ref)) if ref > 0 else 0.0

    def predict_return(self, symbol: str, features: np.ndarray, current_price: float) -> float:
        if current_price <= 0:
            return 0.0
        pred_log = self.predict_log_return(symbol, features)
        return pred_log

    def get_signal(
        self,
        symbol: str,
        features: np.ndarray,
        current_price: float,
        *,
        has_usdt: bool,
        has_crypto: bool,
        buy_return_threshold: float = 0.003,
        sell_return_threshold: float = -0.003,
        buy_threshold: float | None = None,
        min_usdt_for_buy: float = 10,
        signal_centering: bool = True,
        centered_buy_return_threshold: float = 0.0,
        centered_sell_return_threshold: float = 0.0,
    ) -> tuple[str, float]:
        # buy_threshold kept for backward compatibility (price ratio, e.g. 1.005)
        if buy_threshold is not None and buy_return_threshold == 0.003:
            buy_return_threshold = float(np.log(buy_threshold))

        _, _, meta = self._load_pair(symbol.upper())
        meta = self._resolve_metadata(symbol, meta)
        pred_log_return = self.predict_log_return(symbol, features)
        predicted_price = (
            float(current_price * np.exp(pred_log_return))
            if current_price > 0
            else 0.0
        )

        signal_return = pred_log_return
        buy_thr = buy_return_threshold
        sell_thr = sell_return_threshold
        if signal_centering and meta.target == TARGET_LOG_RETURN:
            signal_return = pred_log_return - float(meta.signal_bias or 0.0)
            buy_thr = centered_buy_return_threshold
            sell_thr = centered_sell_return_threshold

        if signal_return > buy_thr and has_usdt:
            return 'BUY', predicted_price
        if signal_return < sell_thr and has_crypto:
            return 'SELL', predicted_price
        return 'HOLD', predicted_price
