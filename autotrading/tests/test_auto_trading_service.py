from decimal import Decimal
from unittest.mock import MagicMock, patch

import numpy as np
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from autotrading.models import AutoTradeLog, AutoPosition
from autotrading.services.auto_trading_service import AutoTradingService
from autotrading.services.order_executor import InsufficientBalanceError
from autotrading.services.risk_manager import RiskManager
from wallet.models import Wallet


@override_settings(
    AUTO_TRADING={
        'enabled': True,
        'username': 'botuser',
        'pairs': ['BTC'],
        'position_size_usdt': 100,
        'buy_threshold': 1.005,
        'min_usdt_for_buy': 10,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.05,
        'sequence_length': 60,
    }
)
class AutoTradingServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='botuser', password='pass')
        self.wallet = Wallet.objects.create(address='botuser', usdt=Decimal('1000'), btc=Decimal('0'))

        self.market = MagicMock()
        self.market.get_current_price.return_value = 65000.0
        self.market.get_hourly_closes.return_value = np.linspace(60000, 65000, 60)

        self.ml = MagicMock()
        self.ml.has_model.return_value = True
        self.ml.get_signal.return_value = ('BUY', 66000.0)

        self.executor = MagicMock()
        self.risk = RiskManager(self.user, stop_loss_pct=0.02, take_profit_pct=0.05)

        self.service = AutoTradingService(
            user=self.user,
            config={
                'pairs': ['BTC'],
                'position_size_usdt': 100,
                'buy_threshold': 1.005,
                'min_usdt_for_buy': 10,
                'sequence_length': 60,
            },
            market_client=self.market,
            ml_loader=self.ml,
            order_executor=self.executor,
            risk_manager=self.risk,
        )

    def test_execute_trade_buy_creates_log_and_position(self):
        log = self.service.execute_trade('BUY', 'BTC', 65000.0, predicted_price=Decimal('66000'))

        self.executor.execute_market_order.assert_called_once()
        self.assertEqual(log.action_taken, 'executed_buy')
        self.assertEqual(AutoTradeLog.objects.count(), 1)
        self.assertTrue(AutoPosition.objects.filter(symbol='BTC', is_open=True).exists())

    def test_execute_trade_insufficient_balance(self):
        self.executor.execute_market_order.side_effect = InsufficientBalanceError('no usdt')
        log = self.service.execute_trade('BUY', 'BTC', 65000.0)

        self.assertEqual(log.action_taken, 'skipped_insufficient_balance')

    def test_run_cycle_hold_signal(self):
        self.ml.get_signal.return_value = ('HOLD', 64000.0)
        logs = self.service.run_cycle()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action_taken, 'hold')
        self.executor.execute_market_order.assert_not_called()

    def test_run_cycle_buy_executes_order(self):
        logs = self.service.run_cycle()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action_taken, 'executed_buy')
        self.executor.execute_market_order.assert_called_once()

    def test_risk_stop_loss_triggers_sell(self):
        AutoPosition.objects.create(
            user=self.user,
            symbol='BTC',
            quantity=Decimal('0.001'),
            entry_price=Decimal('65000'),
            stop_loss=Decimal('63700'),
            take_profit=Decimal('68250'),
            is_open=True,
        )
        self.market.get_current_price.return_value = 63000.0

        logs = self.service.run_cycle()

        self.assertEqual(logs[0].action_taken, 'executed_sell')
        self.assertEqual(logs[0].reason, 'stop_loss')

    @patch('autotrading.services.ml_model_loader.MLModelLoader.get_signal')
    def test_ml_signal_buy_threshold(self, mock_get_signal):
        mock_get_signal.return_value = ('BUY', 70000.0)
        closes = np.linspace(60000, 65000, 60)
        signal, _ = mock_get_signal(
            'BTC', closes, 65000.0, has_usdt=True, has_crypto=False
        )
        self.assertEqual(signal, 'BUY')
