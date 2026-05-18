from decimal import Decimal

from django.utils import timezone

from autotrading.models import AutoPosition


class RiskManager:
    def __init__(self, user, stop_loss_pct: float, take_profit_pct: float):
        self.user = user
        self.stop_loss_pct = Decimal(str(stop_loss_pct))
        self.take_profit_pct = Decimal(str(take_profit_pct))

    def get_open_position(self, symbol: str) -> AutoPosition | None:
        return AutoPosition.objects.filter(
            user=self.user,
            symbol=symbol.upper(),
            is_open=True,
        ).first()

    def check_exit(self, symbol: str, current_price: float) -> str | None:
        """Returns 'stop_loss' or 'take_profit' if position should be closed."""
        pos = self.get_open_position(symbol)
        if not pos:
            return None
        price = Decimal(str(current_price))
        if price <= pos.stop_loss:
            return 'stop_loss'
        if price >= pos.take_profit:
            return 'take_profit'
        return None

    def open_position(self, symbol: str, entry_price: float, quantity: Decimal) -> AutoPosition:
        entry = Decimal(str(entry_price))
        sl = entry * (Decimal('1') - self.stop_loss_pct)
        tp = entry * (Decimal('1') + self.take_profit_pct)
        AutoPosition.objects.filter(
            user=self.user,
            symbol=symbol.upper(),
            is_open=True,
        ).update(is_open=False, closed_at=timezone.now())
        return AutoPosition.objects.create(
            user=self.user,
            symbol=symbol.upper(),
            quantity=quantity,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            is_open=True,
        )

    def close_position(self, symbol: str) -> None:
        AutoPosition.objects.filter(
            user=self.user,
            symbol=symbol.upper(),
            is_open=True,
        ).update(is_open=False, closed_at=timezone.now())
