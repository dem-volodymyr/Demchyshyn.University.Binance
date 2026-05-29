from django.db import models
from decimal import Decimal


class Wallet(models.Model):
    address = models.CharField(max_length=255)
    btc = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    eth = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    usdt = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    bnb = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    sol = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    xrp = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    avax = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    ada = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    matic = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    dot = models.DecimalField(max_digits=18, decimal_places=8, default=0)

    def _field_for_currency(self, currency: str) -> str:
        field = currency.lower()
        if field not in {
            'usdt', 'btc', 'eth', 'bnb', 'sol', 'xrp', 'avax', 'ada', 'matic', 'dot'
        }:
            raise ValueError(f'Unsupported currency: {currency}')
        return field

    def get_balance(self, currency: str) -> Decimal:
        field = self._field_for_currency(currency)
        return Decimal(getattr(self, field))

    def get_frozen(self, currency: str, *, reason: str | None = None) -> Decimal:
        qs = FrozenBalance.objects.filter(wallet=self, currency=currency.upper(), is_active=True)
        if reason:
            qs = qs.filter(reason=reason)
        return Decimal(qs.aggregate(total=models.Sum('amount'))['total'] or Decimal('0'))

    def get_available_balance(self, currency: str, *, reason: str | None = None) -> Decimal:
        return self.get_balance(currency) - self.get_frozen(currency, reason=reason)

    def freeze(self, *, currency: str, amount: Decimal, reason: str, reference: str) -> 'FrozenBalance':
        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError('Freeze amount must be positive')
        available = self.get_available_balance(currency)
        if available < amount:
            raise ValueError(
                f'Insufficient available {currency}: have {available}, need {amount}'
            )
        frozen, _ = FrozenBalance.objects.get_or_create(
            wallet=self,
            currency=currency.upper(),
            reason=reason,
            reference=reference,
            defaults={'amount': Decimal('0'), 'is_active': True},
        )
        frozen.amount = Decimal(frozen.amount) + amount
        frozen.is_active = True
        frozen.save(update_fields=['amount', 'is_active', 'updated_at'])
        return frozen

    def unfreeze(self, *, currency: str, amount: Decimal, reason: str, reference: str) -> Decimal:
        amount = Decimal(amount)
        if amount <= 0:
            return Decimal('0')
        frozen = FrozenBalance.objects.filter(
            wallet=self,
            currency=currency.upper(),
            reason=reason,
            reference=reference,
            is_active=True,
        ).first()
        if not frozen:
            return Decimal('0')
        release = min(Decimal(frozen.amount), amount)
        frozen.amount = Decimal(frozen.amount) - release
        if frozen.amount <= 0:
            frozen.amount = Decimal('0')
            frozen.is_active = False
        frozen.save(update_fields=['amount', 'is_active', 'updated_at'])
        return release


class FrozenBalance(models.Model):
    REASON_ORDER = 'order'
    REASON_CHOICES = [
        (REASON_ORDER, 'Order'),
    ]

    wallet = models.ForeignKey(Wallet, related_name='frozen_balances', on_delete=models.CASCADE)
    currency = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default=REASON_ORDER)
    reference = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('wallet', 'currency', 'reason', 'reference')


class Transaction(models.Model):
    sender_wallet = models.ForeignKey(Wallet, related_name='sender_wallet', on_delete=models.CASCADE)
    receiver_wallet = models.ForeignKey(Wallet, related_name='receiver_wallet', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    currency = models.CharField(max_length=10)

    def save_it(self, *args, **kwargs):
        sender_wallet = self.sender_wallet
        receiver_wallet = self.receiver_wallet
        if self.currency == 'BTC':
            sender_wallet.btc -= Decimal(self.amount)
            receiver_wallet.btc += Decimal(self.amount)
        elif self.currency == 'ETH':
            sender_wallet.eth -= Decimal(self.amount)
            receiver_wallet.eth += Decimal(self.amount)
        elif self.currency == 'USDT':
            sender_wallet.usdt -= Decimal(self.amount)
            receiver_wallet.usdt += Decimal(self.amount)
        elif self.currency == 'BNB':
            sender_wallet.bnb -= Decimal(self.amount)
            receiver_wallet.bnb += Decimal(self.amount)
        elif self.currency == 'SOL':
            sender_wallet.sol -= Decimal(self.amount)
            receiver_wallet.sol += Decimal(self.amount)
        elif self.currency == 'XRP':
            sender_wallet.xrp -= Decimal(self.amount)
            receiver_wallet.xrp += Decimal(self.amount)
        elif self.currency == 'AVAX':
            sender_wallet.avax -= Decimal(self.amount)
            receiver_wallet.avax += Decimal(self.amount)
        elif self.currency == 'ADA':
            sender_wallet.ada -= Decimal(self.amount)
            receiver_wallet.ada += Decimal(self.amount)
        elif self.currency == 'MATIC':
            sender_wallet.matic -= Decimal(self.amount)
            receiver_wallet.matic += Decimal(self.amount)
        elif self.currency == 'DOT':
            sender_wallet.dot -= Decimal(self.amount)
            receiver_wallet.dot += Decimal(self.amount)
        sender_wallet.save()
        receiver_wallet.save()
        super().save(*args, **kwargs)
