"""Schema and I/O for per-model training metadata (Log_Return models)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import joblib

# Must match LSTM_Predictor_Master.CryptoPredictor.feature_cols
DEFAULT_FEATURE_COLS = [
    'Close', 'High', 'Low', 'Volume', 'SMA_20', 'SMA_50',
    'RSI_14', 'MACD', 'MACD_Signal', 'Daily_Return', 'Volatility_10',
]

META_VERSION = 2
TARGET_LOG_RETURN = 'log_return'
TARGET_CLOSE_LEGACY = 'close_legacy'


@dataclass
class ModelMetadata:
    version: int = META_VERSION
    target: str = TARGET_LOG_RETURN
    feature_cols: list[str] = field(default_factory=lambda: list(DEFAULT_FEATURE_COLS))
    y_mean: float | None = None
    y_std: float | None = None
    sequence_length: int = 60
    quality: dict[str, float] = field(default_factory=dict)
    quality_pass: bool = False
    # Mean predicted log-return on validation; subtract in get_signal to avoid always-BUY bias
    signal_bias: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ModelMetadata':
        return cls(
            version=int(data.get('version', 1)),
            target=data.get('target', TARGET_CLOSE_LEGACY),
            feature_cols=list(data.get('feature_cols', DEFAULT_FEATURE_COLS)),
            y_mean=data.get('y_mean'),
            y_std=data.get('y_std'),
            sequence_length=int(data.get('sequence_length', 60)),
            quality={k: float(v) for k, v in (data.get('quality') or {}).items()},
            quality_pass=bool(data.get('quality_pass', False)),
            signal_bias=float(data.get('signal_bias', 0.0)),
        )


def symbol_to_model_key(symbol: str) -> str:
    return symbol.upper().replace('-', '_').lower().replace('_usd', '')


def meta_path(models_dir: Path, symbol: str) -> Path:
    key = symbol_to_model_key(symbol)
    if not key.endswith('_usd'):
        key = f'{key}_usd'
    return Path(models_dir) / f'{key}_meta.gz'


def load_metadata(models_dir: Path, symbol: str) -> ModelMetadata | None:
    path = meta_path(models_dir, symbol)
    if not path.exists():
        return None
    data = joblib.load(path)
    return ModelMetadata.from_dict(data)


def save_metadata(models_dir: Path, symbol: str, metadata: ModelMetadata) -> Path:
    path = meta_path(models_dir, symbol)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(metadata.to_dict(), path)
    return path
