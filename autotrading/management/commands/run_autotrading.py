from django.core.management.base import BaseCommand

from autotrading.config import get_auto_trading_config
from autotrading.services import build_auto_trading_service


class Command(BaseCommand):
    help = 'Run one auto-trading cycle: ML signals, risk exits, market orders, DB logs.'

    def handle(self, *args, **options):
        config = get_auto_trading_config()
        if not config.get('enabled'):
            self.stdout.write(self.style.WARNING('AUTO_TRADING.enabled is False — skipping.'))
            return

        from autotrading.models import AutoTradeSettings
        from autotrading.services.auto_trading_service import run_all_cycles

        if AutoTradeSettings.objects.filter(is_active=True).exists():
            run_all_cycles()
            self.stdout.write(self.style.SUCCESS('Cycles complete for active AutoTradeSettings.'))
            return

        service = build_auto_trading_service()
        logs = service.run_cycle()

        for log in logs:
            self.stdout.write(
                f'{log.symbol} {log.signal} -> {log.action_taken} '
                f'@ {log.market_price} ({log.reason})'
            )
        self.stdout.write(self.style.SUCCESS(f'Cycle complete: {len(logs)} log entries.'))
