from django.conf import settings

# Wallet-aligned tradable assets (USDT is quote currency, so not included as a pair).
DEFAULT_TRADABLE_PAIRS = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'AVAX', 'ADA', 'MATIC', 'DOT']

DEFAULT_AUTO_TRADING = {
    'enabled': False,
    'username': None,
    'pairs': DEFAULT_TRADABLE_PAIRS,
    'position_size_usdt': 100,
    'buy_threshold': 1.005,
    'buy_return_threshold': 0.003,
    'sell_return_threshold': -0.003,
    'min_usdt_for_buy': 10,
    'stop_loss_pct': 0.02,
    'take_profit_pct': 0.05,
    'sequence_length': 60,
    'models_dir': None,
    'gate_enabled': False,
    'gate_min_r2': 0.0,
    'gate_min_directional_acc': 51.5,
    'gate_max_mape': 15.0,
    'gate_require_log_return': True,
    'gate_metrics_csv': None,
    'signal_centering': True,
  # After subtracting signal_bias, trade direction vs bias (0 = BUY if above bias, SELL if below)
    'centered_buy_return_threshold': 0.0,
    'centered_sell_return_threshold': 0.0,
}


def get_auto_trading_config():
    user_config = getattr(settings, 'AUTO_TRADING', {})
    config = {**DEFAULT_AUTO_TRADING, **user_config}
    if config['models_dir'] is None:
        config['models_dir'] = settings.BASE_DIR / 'models'
    if config['gate_metrics_csv'] is None:
        config['gate_metrics_csv'] = settings.BASE_DIR / 'reports' / 'metrics_extended.csv'
    return config
