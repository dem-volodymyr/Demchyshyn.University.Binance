from django.conf import settings

# Pairs that have both ML models in /models and wallet balance fields.
DEFAULT_TRADABLE_PAIRS = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'MATIC', 'DOT']

DEFAULT_AUTO_TRADING = {
    'enabled': False,
    'username': None,
    'pairs': DEFAULT_TRADABLE_PAIRS,
    'position_size_usdt': 100,
    'buy_threshold': 1.005,
    'min_usdt_for_buy': 10,
    'stop_loss_pct': 0.02,
    'take_profit_pct': 0.05,
    'sequence_length': 60,
    'models_dir': None,
}


def get_auto_trading_config():
    user_config = getattr(settings, 'AUTO_TRADING', {})
    config = {**DEFAULT_AUTO_TRADING, **user_config}
    if config['models_dir'] is None:
        config['models_dir'] = settings.BASE_DIR / 'models'
    return config
