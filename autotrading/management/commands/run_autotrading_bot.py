import time
import logging
from django.core.management.base import BaseCommand
from autotrading.services.auto_trading_service import run_all_cycles

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs the autotrading bot in an infinite loop'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Autotrading Bot...'))
        while True:
            try:
                run_all_cycles()
            except Exception as e:
                logger.error(f"Error in autotrading bot loop: {e}")
            
            # Wait for 60 seconds before next cycle
            time.sleep(60)
