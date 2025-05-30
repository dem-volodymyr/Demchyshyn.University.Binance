import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BinanceXchange.settings")
django.setup()

from referral.models import Referral

# Отримати новий код з env
new_code = os.environ.get('REFERRAL_CODE')
if not new_code:
    raise Exception("REFERRAL_CODE not set in environment variables.")

# Знайти Referral з потрібним кодом
try:
    referral = Referral.objects.get(code="fb3d6c7f-9c6")
    referral.code = new_code
    referral.save()
    print(f"Referral code updated to: {new_code}")
except Referral.DoesNotExist:
    print("Referral with code 'fb3d6c7f-9c6' does not exist.")