"""Estimate signal_bias = mean predicted log-return on recent walk-forward window."""

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from django.core.management.base import BaseCommand

from autotrading.config import get_auto_trading_config
from autotrading.services.model_metadata import TARGET_LOG_RETURN, load_metadata, save_metadata
from autotrading.services.ml_model_loader import MLModelLoader

FEATURE_COLS = [
    'Close', 'High', 'Low', 'Volume', 'SMA_20', 'SMA_50',
    'RSI_14', 'MACD', 'MACD_Signal', 'Daily_Return', 'Volatility_10',
]


def _engineer(df: pd.DataFrame) -> pd.DataFrame:
    close = df['Close']
    out = df.copy()
    out['SMA_20'] = close.rolling(20).mean()
    out['SMA_50'] = close.rolling(50).mean()
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, min_periods=14).mean()
    avg_loss = loss.ewm(com=13, min_periods=14).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    out['RSI_14'] = 100 - (100 / (1 + rs))
    ema_fast = close.ewm(span=12, adjust=False).mean()
    ema_slow = close.ewm(span=26, adjust=False).mean()
    out['MACD'] = ema_fast - ema_slow
    out['MACD_Signal'] = out['MACD'].ewm(span=9, adjust=False).mean()
    out['Daily_Return'] = close.pct_change()
    out['Volatility_10'] = out['Daily_Return'].rolling(10).std()
    return out[FEATURE_COLS].dropna()


class Command(BaseCommand):
    help = 'Calibrate signal_bias in *_meta.gz from recent walk-forward predictions.'

    def add_arguments(self, parser):
        parser.add_argument('--symbol', default=None, help='Single symbol, e.g. BTC')
        parser.add_argument('--days', type=int, default=252, help='Calibration window')
        parser.add_argument('--all', action='store_true', help='All models in models/')

    def handle(self, *args, **options):
        config = get_auto_trading_config()
        models_dir = Path(config['models_dir'])
        loader = MLModelLoader(models_dir, sequence_length=config['sequence_length'])

        symbols = [options['symbol'].upper()] if options['symbol'] else []
        if options['all'] or not symbols:
            symbols = sorted({
                p.stem.replace('_usd_model', '').upper()
                for p in models_dir.glob('*_usd_model.keras')
            })

        for symbol in symbols:
            meta = load_metadata(models_dir, symbol)
            if meta is None or meta.target != TARGET_LOG_RETURN:
                self.stdout.write(self.style.WARNING(f'{symbol}: skip (no log_return meta)'))
                continue

            bias = self._calibrate_symbol(loader, symbol, options['days'])
            meta.signal_bias = bias
            save_metadata(models_dir, symbol, meta)
            self.stdout.write(
                self.style.SUCCESS(
                    f'{symbol}: signal_bias={bias:.6f} ({bias * 100:.3f}% log-return)'
                )
            )

    def _calibrate_symbol(self, loader: MLModelLoader, symbol: str, days: int) -> float:
        df = yf.download(
            f'{symbol}-USD', period='3y', interval='1d', auto_adjust=True, progress=False
        )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        feat = _engineer(df)
        preds = []
        test_idx = feat.index[-days:]
        for dt in test_idx:
            idx = df.index.get_loc(dt)
            if idx < 120:
                continue
            hist = df.iloc[:idx]
            fdf = _engineer(hist)
            if len(fdf) < loader.sequence_length:
                continue
            try:
                preds.append(loader.predict_log_return(symbol, fdf.values))
            except Exception:
                continue
        if not preds:
            return 0.0
        return float(np.mean(preds))
