from django.shortcuts import render, redirect
from .models import Order
from wallet.models import Wallet, Transaction
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
import requests
from decimal import Decimal
from django.http import HttpResponseRedirect
from django.urls import reverse


@login_required
def order_alert(request, user, quantity, product, price, total):
    subject = 'You have just placed an order!'
    message = f'{user.username}, you place order for {quantity}{product} at price {price}USDT/{product}. Your {total}USDT frozen.  !'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'order_history.html', {'orders': orders})


@login_required
def create_order(request):
    user = request.user
    # Список підтримуваних валют з Wallet
    SUPPORTED_CRYPTOS = ['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'XRP', 'AVAX', 'ADA', 'MATIC', 'DOT']
    if request.method == 'POST':
        order_type = request.POST.get('order_type')  # 'buy' або 'sell'
        crypto = request.POST.get('crypto')
        quantity = float(request.POST.get('quantity'))
        if crypto not in SUPPORTED_CRYPTOS or (order_type not in ['buy', 'sell']):
            return render(request, 'create_order.html', {'error': 'Invalid crypto or order type', 'supported_cryptos': SUPPORTED_CRYPTOS})

        # CoinGecko API: отримати ціну
        coingecko_ids = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'USDT': 'tether', 'BNB': 'binancecoin', 'SOL': 'solana',
            'XRP': 'ripple', 'AVAX': 'avalanche-2', 'ADA': 'cardano', 'MATIC': 'matic-network', 'DOT': 'polkadot'
        }
        cg_id = coingecko_ids[crypto]
        url = f'https://api.coingecko.com/api/v3/simple/price'
        headers = {}
        if hasattr(settings, 'COINGECKO_API_KEY') and settings.COINGECKO_API_KEY:
            headers['x-cg-pro-api-key'] = settings.COINGECKO_API_KEY
        params = {
            "ids": cg_id,
            "vs_currencies": "usd"
        }
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        if resp.status_code != 200 or cg_id not in data or 'usd' not in data[cg_id]:
            return render(request, 'create_order.html', {
                'error': 'Ціна для цієї криптовалюти зараз недоступна. Спробуйте пізніше або виберіть іншу валюту.',
                'supported_cryptos': SUPPORTED_CRYPTOS
            })
        price = float(data[cg_id]['usd'])

        # Розрахунок суми в USDT
        if order_type == 'sell':
            usdt_amount = quantity * price  # продаємо crypto, отримуємо USDT
        else:  # buy
            usdt_amount = quantity * price  # купуємо crypto, платимо USDT

        wallet_address = user.username
        wallet = Wallet.objects.get(address=wallet_address)
        order = Order(user=user, order_type=order_type, crypto=crypto, quantity=quantity, price=price, usdt_amount=usdt_amount, wallet=wallet)
        order.save()
        order_alert(request, user, quantity, crypto, price, usdt_amount)
        return redirect('order_history')

    return render(request, 'create_order.html', {'supported_cryptos': SUPPORTED_CRYPTOS})


@login_required
def execute_order(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    wallet = order.wallet
    # Перевірка балансу
    if order.order_type == 'sell':
        if getattr(wallet, order.crypto.lower()) < order.quantity:
            return render(request, 'order_history.html', {'orders': Order.objects.filter(user=request.user), 'error': 'Insufficient crypto balance'})
        setattr(wallet, order.crypto.lower(), getattr(wallet, order.crypto.lower()) - order.quantity)
        wallet.usdt += Decimal(order.usdt_amount)
        wallet.save()
        Transaction.objects.create(sender_wallet=wallet, receiver_wallet=wallet, amount=order.quantity, currency=order.crypto)
    else:
        if wallet.usdt < order.usdt_amount:
            return render(request, 'order_history.html', {'orders': Order.objects.filter(user=request.user), 'error': 'Insufficient USDT balance'})
        wallet.usdt -= Decimal(order.usdt_amount)
        setattr(wallet, order.crypto.lower(), getattr(wallet, order.crypto.lower()) + order.quantity)
        wallet.save()
        Transaction.objects.create(sender_wallet=wallet, receiver_wallet=wallet, amount=order.quantity, currency=order.crypto)
    # Видалити ордер
    order.delete()
    return HttpResponseRedirect(reverse('order_history'))


@login_required
def delete_order(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    order.delete()
    return HttpResponseRedirect(reverse('order_history'))
