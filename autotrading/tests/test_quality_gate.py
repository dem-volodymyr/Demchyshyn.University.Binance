from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings

from autotrading.services.model_metadata import (
    META_VERSION,
    TARGET_LOG_RETURN,
    ModelMetadata,
    save_metadata,
)
from autotrading.services.quality_gate import ModelQualityGate


@override_settings(
    AUTO_TRADING={
        'gate_enabled': True,
        'gate_min_r2': 0.0,
        'gate_min_directional_acc': 51.5,
        'gate_max_mape': 15.0,
        'gate_require_log_return': True,
        'gate_metrics_csv': None,
        'models_dir': None,
    }
)
class ModelQualityGateTest(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.models_dir = Path(self.tmp.name)
        self.config = {
            'gate_enabled': True,
            'gate_min_r2': 0.0,
            'gate_min_directional_acc': 51.5,
            'gate_max_mape': 15.0,
            'gate_require_log_return': True,
            'models_dir': self.models_dir,
            'gate_metrics_csv': None,
        }
        self.gate = ModelQualityGate(self.config)

    def tearDown(self):
        self.tmp.cleanup()

    def test_passes_with_quality_pass_flag(self):
        save_metadata(
            self.models_dir,
            'ETH',
            ModelMetadata(
                version=META_VERSION,
                target=TARGET_LOG_RETURN,
                y_mean=0.0,
                y_std=0.02,
                quality_pass=True,
            ),
        )
        ok, reason = self.gate.passes('ETH')
        self.assertTrue(ok)
        self.assertEqual(reason, 'metadata_quality_pass')

    def test_fails_without_metadata(self):
        ok, reason = self.gate.passes('BTC')
        self.assertFalse(ok)
        self.assertEqual(reason, 'missing_metadata')

    def test_evaluate_metrics_rejects_negative_r2(self):
        ok, reason = self.gate.evaluate_metrics(
            'BTC',
            {'r2': -0.1, 'mape': 5.0, 'directional_acc': 55.0},
        )
        self.assertFalse(ok)
        self.assertIn('R2', reason)
