import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BinanceXchange.settings")
django.setup()

from django.contrib.auth.models import User
from wallet.models import Wallet

username = 'valdemarmalyna'
amount_to_add = 1

try:
    user = User.objects.get(username=username)
    wallet = Wallet.objects.get(address=user.username)  # Якщо address = username, інакше змініть цю логіку
    wallet.btc += amount_to_add
    wallet.save()
    print(f"Added {amount_to_add} BTC to {username}. New BTC balance: {wallet.btc}")
except User.DoesNotExist:
    print(f"User with username '{username}' does not exist.")
except Wallet.DoesNotExist:
    print(f"Wallet for user '{username}' does not exist.") 