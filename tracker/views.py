from .models import Cryptocurrency, CryptocurrencyPrice
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
import requests


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
    # api_url = 'https://api.coingecko.com/api/v3/coins/markets'
    import requests

    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=USD&order=market_cap_desc&per_page=100&page=1&sparkline=false"

    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-L2LFhe4vEhqN8aLH2seaVAh1"
    }

    response = requests.get(url, headers=headers)

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
    print("API_Data", response.json())

    if response.status_code == 200:
        print("If Case")
        cryptos_data = response.json()
        for crypto_data in cryptos_data:
            symbol = crypto_data['symbol'].upper()
            name = crypto_data['name']
            market_cap = crypto_data['market_cap']
            market_cap_rank = crypto_data['market_cap_rank']
            total_volume = crypto_data['total_volume']
            high_24h = crypto_data['high_24h']
            low_24h = crypto_data['low_24h']
            price_change_24h = crypto_data['price_change_24h']
            max_supply = crypto_data['max_supply']
            total_supply = crypto_data['total_supply']
            last_updated = crypto_data['last_updated']
            image = crypto_data['image']
            circulating_supply = crypto_data['circulating_supply']

            # Update or create cryptocurrency records in the database
            crypto, created = Cryptocurrency.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'name': name,
                    'market_cap': market_cap,
                    'market_cap_rank': market_cap_rank,
                    'total_volume': total_volume,
                    'high_24h': high_24h,
                    'low_24h': low_24h,
                    'price_change_24h': price_change_24h,
                    'max_supply': max_supply,
                    'total_supply': total_supply,
                    'last_updated': last_updated,
                    'image': image,
                    'circulating_supply': circulating_supply,
                }
            )
            CryptocurrencyPrice.objects.create(
                cryptocurrency=crypto,
                price=crypto_data['current_price'],
            )
    else:
        # Handle API request failure
        error_message = f"Failed to fetch cryptocurrency data. Status code: {response.status_code}"
        return render(request, 'error.html', {'error_message': error_message})

    # Retrieve and pass the cryptocurrencies to the template
    cryptocurrencies = Cryptocurrency.objects.all()
    return render(request, 'crypto_list.html', {'cryptocurrencies': cryptocurrencies})
