"""Production quality gate for ML models before live autotrading."""

from __future__ import annotations

import csv
from pathlib import Path

from autotrading.services.model_metadata import (
    META_VERSION,
    TARGET_LOG_RETURN,
    ModelMetadata,
    load_metadata,
    save_metadata,
)


class ModelQualityGate:
    """Decides whether a symbol's model is allowed to trade."""

    def __init__(self, config: dict):
        self.enabled = bool(config.get('gate_enabled', True))
        self.min_r2 = float(config.get('gate_min_r2', 0.0))
        self.min_directional_acc = float(config.get('gate_min_directional_acc', 51.5))
        self.max_mape = float(config.get('gate_max_mape', 15.0))
        self.require_log_return_target = bool(config.get('gate_require_log_return', True))
        self.models_dir = Path(config['models_dir'])
        metrics_csv = config.get('gate_metrics_csv')
        self.metrics_csv = Path(metrics_csv) if metrics_csv else None
        self._metrics_cache: dict[str, dict[str, float]] | None = None

    def _load_metrics_csv(self) -> dict[str, dict[str, float]]:
        if self._metrics_cache is not None:
            return self._metrics_cache

        self._metrics_cache = {}
        if not self.metrics_csv or not self.metrics_csv.exists():
            return self._metrics_cache

        with self.metrics_csv.open(newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                key = row.get('Криптовалюта') or row.get('symbol') or row.get('Symbol')
                if not key:
                    continue
                symbol = key.split('-')[0].upper()

                def _f(name: str, default: float = 0.0) -> float:
                    raw = row.get(name, '')
                    if raw in (None, ''):
                        return default
                    return float(str(raw).replace('%', '').strip())

                self._metrics_cache[symbol] = {
                    'mape': _f('MAPE (%)'),
                    'r2': _f('R2'),
                    'directional_acc': _f('Directional Acc (%)'),
                }
        return self._metrics_cache

    def evaluate_metrics(self, symbol: str, metrics: dict[str, float]) -> tuple[bool, str]:
        mape = metrics.get('mape')
        r2 = metrics.get('r2')
        directional = metrics.get('directional_acc')

        if r2 is not None and r2 < self.min_r2:
            return False, f'R2 {r2:.4f} < {self.min_r2}'
        if mape is not None and mape > self.max_mape:
            return False, f'MAPE {mape:.2f}% > {self.max_mape}%'
        if directional is not None and directional < self.min_directional_acc:
            return False, (
                f'Directional Acc {directional:.2f}% < {self.min_directional_acc}%'
            )
        return True, 'metrics_ok'

    def passes(self, symbol: str) -> tuple[bool, str]:
        if not self.enabled:
            return True, 'gate_disabled'

        meta = load_metadata(self.models_dir, symbol)
        if meta is None:
            return False, 'missing_metadata'

        if self.require_log_return_target and meta.target != TARGET_LOG_RETURN:
            return False, f'legacy_target:{meta.target}'

        if meta.version < META_VERSION:
            return False, f'old_meta_version:{meta.version}'

        if meta.quality_pass:
            return True, 'metadata_quality_pass'

        if meta.quality:
            return self.evaluate_metrics(symbol, meta.quality)

        csv_metrics = self._load_metrics_csv().get(symbol.upper())
        if csv_metrics:
            ok, reason = self.evaluate_metrics(symbol, csv_metrics)
            if ok:
                return True, f'csv_{reason}'
            return False, f'csv_{reason}'

        return False, 'no_quality_data'

    def sync_metadata_from_csv(self, symbol: str) -> ModelMetadata | None:
        """Attach CSV metrics to meta file (used after training export)."""
        csv_metrics = self._load_metrics_csv().get(symbol.upper())
        if not csv_metrics:
            return None

        meta = load_metadata(self.models_dir, symbol) or ModelMetadata()
        meta.quality = csv_metrics
        ok, _ = self.evaluate_metrics(symbol, csv_metrics)
        meta.quality_pass = ok
        save_metadata(self.models_dir, symbol, meta)
        return meta
