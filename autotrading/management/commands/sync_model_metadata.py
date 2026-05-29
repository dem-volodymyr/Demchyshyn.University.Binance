"""Write *_meta.gz for models (Log_Return + quality from metrics CSV)."""

from pathlib import Path

import numpy as np
import yfinance as yf
from django.core.management.base import BaseCommand

from autotrading.config import get_auto_trading_config
from autotrading.services.model_metadata import (
    META_VERSION,
    TARGET_LOG_RETURN,
    ModelMetadata,
    save_metadata,
)
from autotrading.services.quality_gate import ModelQualityGate


class Command(BaseCommand):
    help = (
        'Sync models/*_meta.gz with Log_Return target stats and quality gate '
        'metrics from reports/metrics_extended.csv.'
    )

    def handle(self, *args, **options):
        config = get_auto_trading_config()
        models_dir = Path(config['models_dir'])
        gate = ModelQualityGate(config)

        model_files = sorted(models_dir.glob('*_usd_model.keras'))
        if not model_files:
            self.stdout.write(self.style.WARNING(f'No models in {models_dir}'))
            return

        for model_path in model_files:
            key = model_path.stem.replace('_model', '')
            symbol = key.replace('_usd', '').upper()
            y_mean, y_std = self._return_stats(symbol)

            meta = ModelMetadata(
                version=META_VERSION,
                target=TARGET_LOG_RETURN,
                y_mean=y_mean,
                y_std=y_std,
                sequence_length=config['sequence_length'],
            )
            updated = gate.sync_metadata_from_csv(symbol)
            if updated:
                meta.quality = updated.quality
                meta.quality_pass = updated.quality_pass

            path = save_metadata(models_dir, symbol, meta)
            ok, reason = gate.passes(symbol)
            self.stdout.write(
                f'{symbol}: meta -> {path.name} | gate={"PASS" if ok else "FAIL"} ({reason})'
            )

    def _return_stats(self, symbol: str) -> tuple[float, float]:
        ticker = f'{symbol}-USD'
        import pandas as pd

        df = yf.download(ticker, period='2y', interval='1d', auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        log_ret = np.log(df['Close'] / df['Close'].shift(1)).dropna().values
        return float(log_ret.mean()), float(log_ret.std() + 1e-8)
