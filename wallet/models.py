from django.db import models
from django.contrib.auth.models import User
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

