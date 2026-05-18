from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

SEQUENCE_LEN = 60


class MLModelLoader:
    """Loads Keras models and scalers from /models and produces trading signals."""

    def __init__(self, models_dir: Path, sequence_length: int = SEQUENCE_LEN):
        self.models_dir = Path(models_dir)
        self.sequence_length = sequence_length

    def model_paths(self, symbol: str) -> tuple[Path, Path]:
        key = symbol.lower()
        model_path = self.models_dir / f'{key}_usd_model.keras'
        scaler_path = self.models_dir / f'{key}_usd_scaler.gz'
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

    @lru_cache(maxsize=16)
    def _load_pair(self, symbol: str):
        from tensorflow.keras.models import load_model

        model_path, scaler_path = self.model_paths(symbol)
        model = load_model(model_path)
        scaler = joblib.load(scaler_path)
        return model, scaler

    def predict_price(self, symbol: str, features: np.ndarray) -> float:
        if len(features) < self.sequence_length:
            raise ValueError(
                f'Need at least {self.sequence_length} features, got {len(features)}'
            )
        model, scaler = self._load_pair(symbol.upper())
        window = features[-self.sequence_length :]
        scaled = scaler.transform(window)
        # Model expects input shape (batch, sequence_length, num_features)
        X = np.reshape(np.array([scaled]), (1, self.sequence_length, 11))
        pred_scaled = model.predict(X, verbose=0)
        
        # In the training script, 'Close' is the 0-th column in the 11 feature columns.
        # We need a dummy array to properly inverse transform the predicted target.
        dummy = np.zeros((1, 11))
        dummy[0, 0] = pred_scaled[0][0]
        return float(scaler.inverse_transform(dummy)[0][0])

    def get_signal(
        self,
        symbol: str,
        features: np.ndarray,
        current_price: float,
        *,
        has_usdt: bool,
        has_crypto: bool,
        buy_threshold: float = 1.005,
        min_usdt_for_buy: float = 10,
    ) -> tuple[str, float]:
        predicted = self.predict_price(symbol, features)
        if predicted > current_price * buy_threshold and has_usdt:
            return 'BUY', predicted
        if predicted < current_price and has_crypto:
            return 'SELL', predicted
        return 'HOLD', predicted
