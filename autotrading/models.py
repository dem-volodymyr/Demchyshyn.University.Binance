from django.db import models
from django.contrib.auth.models import User


class AutoTradeLog(models.Model):
    SIGNAL_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('HOLD', 'Hold'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auto_trade_logs')
    symbol = models.CharField(max_length=10)
    signal = models.CharField(max_length=4, choices=SIGNAL_CHOICES)
    predicted_price = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    market_price = models.DecimalField(max_digits=18, decimal_places=8)
    quantity = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    action_taken = models.CharField(max_length=64)
    reason = models.CharField(max_length=64, blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.symbol} {self.signal} @ {self.created_at:%Y-%m-%d %H:%M}'


class AutoPosition(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auto_positions')
    symbol = models.CharField(max_length=10)
    quantity = models.DecimalField(max_digits=18, decimal_places=8)
    entry_price = models.DecimalField(max_digits=18, decimal_places=8)
    stop_loss = models.DecimalField(max_digits=18, decimal_places=8)
    take_profit = models.DecimalField(max_digits=18, decimal_places=8)
    is_open = models.BooleanField(default=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-opened_at']

    def __str__(self):
        status = 'open' if self.is_open else 'closed'
        return f'{self.symbol} {status} qty={self.quantity}'


class AutoTradeSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auto_trade_settings')
    is_active = models.BooleanField(default=False)
    symbol = models.CharField(max_length=10, default='BTC')
    stop_loss_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.02)
    take_profit_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.05)
    trade_amount_usdt = models.DecimalField(max_digits=18, decimal_places=2, default=100.00)

    class Meta:
        unique_together = ('user', 'symbol')

    def __str__(self):
        return f"{self.user.username} - {self.symbol} (Active: {self.is_active})"
