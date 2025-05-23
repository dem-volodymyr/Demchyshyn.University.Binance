from django.core.management.base import BaseCommand
from tracker.models import Cryptocurrency, CryptocurrencyPrice
from django.utils import timezone
from django.conf import settings
import requests
from datetime import datetime, timedelta
import time

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/{id}/market_chart"

class Command(BaseCommand):
    help = 'Update hourly prices for all cryptocurrencies in the DB using CoinGecko API (for the last 24h)'

    def handle(self, *args, **options):
        cryptos = Cryptocurrency.objects.all()
        api_key = getattr(settings, 'COINGECKO_API', None)
        headers = {
            "accept": "application/json"
        }
        if api_key:
            headers["x-cg-demo-api-key"] = api_key
        for crypto in cryptos:
            cg_id = getattr(crypto, 'coingecko_id', None)
            if not cg_id:
                cg_id = crypto.name.lower().replace(' ', '-')
            url = COINGECKO_API_URL.format(id=cg_id)
            params = {
                'vs_currency': 'usd',
                'days': 1,
                'interval': 'hourly'
            }
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                self.stdout.write(self.style.WARNING(f"Failed to fetch {crypto.symbol} ({cg_id}): {resp.status_code}"))
                time.sleep(2)
                continue
            data = resp.json()
            prices = data.get('prices', [])
            for price_point in prices:
                ts = datetime.utcfromtimestamp(price_point[0] / 1000).replace(tzinfo=timezone.utc)
                price = price_point[1]
                CryptocurrencyPrice.objects.update_or_create(
                    cryptocurrency=crypto,
                    timestamp=ts,
                    defaults={'price': price}
                )
            self.stdout.write(self.style.SUCCESS(f"Updated {crypto.symbol}: {len(prices)} hourly points"))
            time.sleep(2) 