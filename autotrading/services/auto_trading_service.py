from decimal import Decimal

import requests
from django.contrib.auth.models import User

from autotrading.config import get_auto_trading_config
from autotrading.models import AutoTradeLog
from wallet.models import Wallet

from .market_data_client import MarketDataClient
from .ml_model_loader import MLModelLoader
from .order_executor import InsufficientBalanceError, OrderExecutor
from .risk_manager import RiskManager


class AutoTradingService:
    def __init__(
        self,
        *,
        user: User,
        config: dict,
        market_client: MarketDataClient,
        ml_loader: MLModelLoader,
        order_executor: OrderExecutor,
        risk_manager: RiskManager,
    ):
        self.user = user
        self.config = config
        self.market_client = market_client
        self.ml_loader = ml_loader
        self.order_executor = order_executor
        self.risk_manager = risk_manager

    def run_cycle(self) -> list[AutoTradeLog]:
        logs = []
        for symbol in self.config['pairs']:
            symbol = symbol.upper()
            if not self.ml_loader.has_model(symbol):
                continue
            try:
                log = self._process_symbol(symbol)
                if log:
                    logs.append(log)
            except Exception as exc:
                logs.append(self._log(
                    symbol=symbol,
                    signal='HOLD',
                    market_price=Decimal('0'),
                    predicted_price=None,
                    action_taken='error',
                    reason='exception',
                    error_message=str(exc),
                ))
        return logs

    def _process_symbol(self, symbol: str) -> AutoTradeLog | None:
        current_price = self.market_client.get_current_price(symbol)
        market_price = Decimal(str(current_price))

        exit_reason = self.risk_manager.check_exit(symbol, current_price)
        if exit_reason:
            return self.execute_trade(
                'SELL',
                symbol,
                current_price,
                reason=exit_reason,
            )

        features = self.market_client.get_ml_features(
            symbol,
            limit=self.config['sequence_length'],
        )
        wallet = Wallet.objects.get(address=self.user.username)
        field = symbol.lower()
        has_usdt = wallet.usdt >= Decimal(str(self.config['min_usdt_for_buy']))
        has_crypto = getattr(wallet, field, Decimal('0')) > 0

        signal, predicted = self.ml_loader.get_signal(
            symbol,
            features,
            current_price,
            has_usdt=has_usdt,
            has_crypto=has_crypto,
            buy_threshold=self.config['buy_threshold'],
            min_usdt_for_buy=self.config['min_usdt_for_buy'],
        )
        predicted_dec = Decimal(str(predicted))

        if signal == 'HOLD':
            return self._log(
                symbol=symbol,
                signal=signal,
                market_price=market_price,
                predicted_price=predicted_dec,
                action_taken='hold',
                reason='model',
            )

        if signal == 'BUY' and self.risk_manager.get_open_position(symbol):
            return self._log(
                symbol=symbol,
                signal=signal,
                market_price=market_price,
                predicted_price=predicted_dec,
                action_taken='skipped_already_in_position',
                reason='model',
            )

        return self.execute_trade(
            signal,
            symbol,
            current_price,
            predicted_price=predicted_dec,
            reason='model',
        )

    def execute_trade(
        self,
        signal: str,
        symbol: str,
        price: float,
        *,
        predicted_price: Decimal | None = None,
        reason: str = 'model',
    ) -> AutoTradeLog:
        wallet = Wallet.objects.get(address=self.user.username)
        market_price = Decimal(str(price))
        quantity = self._calc_quantity(signal, symbol, wallet, price)

        if quantity <= 0:
            return self._log(
                symbol=symbol,
                signal=signal,
                market_price=market_price,
                predicted_price=predicted_price,
                quantity=quantity,
                action_taken='skipped_zero_quantity',
                reason=reason,
            )

        order_type = 'buy' if signal == 'BUY' else 'sell'
        try:
            self.order_executor.execute_market_order(
                wallet=wallet,
                order_type=order_type,
                crypto=symbol,
                quantity=quantity,
                price=market_price,
            )
            if signal == 'BUY':
                self.risk_manager.open_position(symbol, price, quantity)
            else:
                self.risk_manager.close_position(symbol)

            return self._log(
                symbol=symbol,
                signal=signal,
                market_price=market_price,
                predicted_price=predicted_price,
                quantity=quantity,
                action_taken=f'executed_{order_type}',
                reason=reason,
            )
        except InsufficientBalanceError as exc:
            return self._log(
                symbol=symbol,
                signal=signal,
                market_price=market_price,
                predicted_price=predicted_price,
                quantity=quantity,
                action_taken='skipped_insufficient_balance',
                reason=reason,
                error_message=str(exc),
            )
        except requests.RequestException as exc:
            return self._log(
                symbol=symbol,
                signal=signal,
                market_price=market_price,
                predicted_price=predicted_price,
                quantity=quantity,
                action_taken='api_unavailable',
                reason=reason,
                error_message=str(exc),
            )

    def _calc_quantity(
        self,
        signal: str,
        symbol: str,
        wallet: Wallet,
        price: float,
    ) -> Decimal:
        field = symbol.lower()
        if signal == 'BUY':
            usdt = min(
                wallet.usdt,
                Decimal(str(self.config['position_size_usdt'])),
            )
            if usdt <= 0 or price <= 0:
                return Decimal('0')
            return (usdt / Decimal(str(price))).quantize(Decimal('0.00000001'))
        balance = getattr(wallet, field, Decimal('0'))
        return balance

    def _log(
        self,
        *,
        symbol: str,
        signal: str,
        market_price: Decimal,
        predicted_price: Decimal | None,
        action_taken: str,
        reason: str = '',
        quantity: Decimal | None = None,
        error_message: str = '',
    ) -> AutoTradeLog:
        return AutoTradeLog.objects.create(
            user=self.user,
            symbol=symbol.upper(),
            signal=signal,
            predicted_price=predicted_price,
            market_price=market_price,
            quantity=quantity,
            action_taken=action_taken,
            reason=reason,
            error_message=error_message,
        )


def build_auto_trading_service(setting: 'AutoTradeSettings') -> AutoTradingService:
    config = get_auto_trading_config()

    # Override config with user settings
    config['pairs'] = [setting.symbol]
    config['position_size_usdt'] = float(setting.trade_amount_usdt)
    config['stop_loss_pct'] = float(setting.stop_loss_pct)
    config['take_profit_pct'] = float(setting.take_profit_pct)

    return AutoTradingService(
        user=setting.user,
        config=config,
        market_client=MarketDataClient(sequence_length=config['sequence_length']),
        ml_loader=MLModelLoader(
            models_dir=config['models_dir'],
            sequence_length=config['sequence_length'],
        ),
        order_executor=OrderExecutor(),
        risk_manager=RiskManager(
            user=setting.user,
            stop_loss_pct=config['stop_loss_pct'],
            take_profit_pct=config['take_profit_pct'],
        ),
    )


def run_all_cycles():
    import logging
    from autotrading.models import AutoTradeSettings
    
    logger = logging.getLogger(__name__)
    active_settings = AutoTradeSettings.objects.filter(is_active=True)
    
    for setting in active_settings:
        try:
            service = build_auto_trading_service(setting)
            service.run_cycle()
        except Exception as e:
            logger.error(f"Error running autotrading for {setting.user.username} ({setting.symbol}): {e}")
