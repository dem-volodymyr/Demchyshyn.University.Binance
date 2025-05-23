from django.db import models
from django.contrib.auth.models import User
from wallet.models import Wallet


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=4, choices=[('buy', 'Buy'), ('sell', 'Sell')], default='sell')  # buy or sell
    crypto = models.CharField(max_length=10, default='BTC')  # e.g. BTC, ETH, etc.
    quantity = models.DecimalField(max_digits=18, decimal_places=8)
    price = models.DecimalField(max_digits=18, decimal_places=8)  # price per 1 crypto in USDT
    usdt_amount = models.DecimalField(max_digits=18, decimal_places=8, default=0)  # total USDT to pay/receive
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
