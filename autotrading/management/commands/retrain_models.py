import logging
from django.core.management.base import BaseCommand
from autotrading.models import AutoTradeSettings
from autotrading.services.model_trainer import CryptoModelTrainer

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Retrains LSTM models on fresh data for all active autotrading pairs."

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Specific symbol to retrain (e.g. BTC). If not provided, retrains all active pairs.',
        )
        parser.add_argument(
            '--period',
            type=str,
            default='3mo',
            help='Data period to fetch from Yahoo Finance (default: 3mo).',
        )
        parser.add_argument(
            '--epochs',
            type=int,
            default=5,
            help='Number of epochs to train (default: 5).',
        )

    def handle(self, *args, **options):
        symbol = options.get('symbol')
        period = options.get('period')
        epochs = options.get('epochs')
        
        if symbol:
            symbols_to_train = [symbol.upper()]
        else:
            active_settings = AutoTradeSettings.objects.filter(is_active=True)
            symbols_to_train = list(set(setting.symbol.upper() for setting in active_settings))
            
        if not symbols_to_train:
            self.stdout.write(self.style.WARNING("No active autotrading settings found. Nothing to retrain."))
            return
            
        self.stdout.write(self.style.SUCCESS(f"Found {len(symbols_to_train)} symbols to retrain: {', '.join(symbols_to_train)}"))
        
        for sym in symbols_to_train:
            self.stdout.write(f"\n[START] Start fine-tuning for {sym} (period: {period}, epochs: {epochs})...")
            trainer = CryptoModelTrainer(symbol=sym)
            try:
                success, msg = trainer.retrain_model(period=period, epochs=epochs)
                if success:
                    self.stdout.write(self.style.SUCCESS(f"[SUCCESS] [{sym}] {msg}"))
                else:
                    self.stdout.write(self.style.WARNING(f"[WARNING] [{sym}] {msg}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[ERROR] [{sym}] Error: {e}"))
                logger.error(f"Error retraining {sym}: {e}")
                
        self.stdout.write(self.style.SUCCESS("\nAll retraining processes have completed!"))
