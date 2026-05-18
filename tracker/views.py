from .models import Cryptocurrency, CryptocurrencyPrice
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.db.models import Avg
from django.utils import timezone
from dateutil.relativedelta import relativedelta


@login_required
def welcome_email(request):
    user = request.user
    subject = 'Welcome to BinanceXchange!'
    message = f'{user.username}, thanks for becoming a part of our community!'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    return redirect('home')


def logout_view(request):
    logout(request)
    return redirect("home")


def crypto_list(request):
    import logging

    import requests

    logger = logging.getLogger(__name__)

    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=USD&order=market_cap_desc&per_page=100&page=1&sparkline=false"

    headers = {"accept": "application/json"}
    api_key = getattr(settings, 'COINGECKO_API_KEY', None)
    if api_key:
        headers['x-cg-pro-api-key'] = api_key

    response = requests.get(url, headers=headers, timeout=30)

    """
    api_url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=USD&order=market_cap_desc&per_page=100&page=1&sparkline=false'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 10,
        'page': 1,
        'sparkline': False,
    }
    response = requests.get(api_url, params=params)
    """
    print("API_Data")

    if response.status_code == 200:
        print("Success")
        cryptos_data = response.json()
        for crypto_data in cryptos_data:
            symbol = str(crypto_data.get('symbol', '')).upper()[:20]
            if not symbol:
                continue
            name = str(crypto_data.get('name', symbol))[:255]
            circulating = crypto_data.get('circulating_supply')
            if circulating is not None:
                circulating = str(circulating)[:1600]

            defaults = {
                'name': name,
                'market_cap': crypto_data.get('market_cap'),
                'market_cap_rank': crypto_data.get('market_cap_rank'),
                'total_volume': crypto_data.get('total_volume'),
                'high_24h': crypto_data.get('high_24h'),
                'low_24h': crypto_data.get('low_24h'),
                'price_change_24h': crypto_data.get('price_change_24h'),
                'max_supply': crypto_data.get('max_supply'),
                'total_supply': crypto_data.get('total_supply'),
                'last_updated': crypto_data.get('last_updated'),
                'image': (crypto_data.get('image') or '')[:1600] or None,
                'circulating_supply': circulating,
            }

            try:
                crypto, _ = Cryptocurrency.objects.update_or_create(
                    symbol=symbol,
                    defaults=defaults,
                )
                CryptocurrencyPrice.objects.create(
                    cryptocurrency=crypto,
                    price=crypto_data['current_price'],
                )
            except Exception as exc:
                logger.warning('Skip crypto %s: %s', symbol, exc)
    else:
        # Handle API request failure
        error_message = f"Failed to fetch cryptocurrency data. Status code: {response.status_code}"
        return render(request, 'error.html', {'error_message': error_message})

    # Get hourly price data for each crypto for today (last price per hour for 24 hours)
    from django.db.models import F
    cryptocurrencies = Cryptocurrency.objects.all().order_by(F('market_cap_rank').asc(nulls_last=True))
    now = timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    for crypto in cryptocurrencies:
        hourly_prices = []
        for h in range(24):
            hour_start = today + timedelta(hours=h)
            hour_end = hour_start + timedelta(hours=1)
            price_obj = CryptocurrencyPrice.objects.filter(
                cryptocurrency=crypto,
                timestamp__gte=hour_start,
                timestamp__lt=hour_end
            ).order_by('-timestamp').first()
            label = hour_start.strftime('%H:00')  # Наприклад, 09:00
            hourly_prices.append({'hour': label, 'price': price_obj.price if price_obj else None})
        crypto.hourly_prices = hourly_prices
    return render(request, 'crypto_list.html', {'cryptocurrencies': cryptocurrencies})
