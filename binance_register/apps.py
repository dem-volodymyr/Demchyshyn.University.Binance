from django.apps import AppConfig


class BinanceRegisterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'binance_register'

    def ready(self):
        import binance_register.signals
