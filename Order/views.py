from decimal import Decimal

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from autotrading.models import AutoTradeSettings
from wallet.models import Transaction, Wallet

from .models import Order

SUPPORTED_CRYPTOS = ['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'XRP', 'AVAX', 'ADA', 'MATIC', 'DOT']
COINGECKO_IDS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'USDT': 'tether',
    'BNB': 'binancecoin',
    'SOL': 'solana',
    'XRP': 'ripple',
    'AVAX': 'avalanche-2',
    'ADA': 'cardano',
    'MATIC': 'matic-network',
    'DOT': 'polkadot',
}


def _model_reserved_usdt(user) -> Decimal:
    return (
        AutoTradeSettings.objects
        .filter(user=user, is_active=True)
        .aggregate(total=models.Sum('trade_amount_usdt'))['total']
        or Decimal('0')
    )


def _balance_level(total: Decimal, available: Decimal) -> str:
    if available <= 0:
        return 'danger'
    if total > 0 and available / total < Decimal('0.20'):
        return 'warning'
    return 'ok'


def _wallet_balances_with_frozen(
    wallet: Wallet,
    *,
    model_reserved_usdt: Decimal = Decimal('0'),
    hide_zero: bool = True,
):
    rows = []
    for currency in SUPPORTED_CRYPTOS:
        total = wallet.get_balance(currency)
        frozen = wallet.get_frozen(currency)
        if currency == 'USDT':
            frozen = frozen + Decimal(model_reserved_usdt)
        available = total - frozen
        if hide_zero and total == 0 and frozen == 0 and available == 0:
            continue
        rows.append(
            {
                'currency': currency,
                'total': total,
                'frozen': frozen,
                'available': available,
                'level': _balance_level(total, available),
            }
        )
    return rows


def _get_market_price(crypto: str) -> Decimal:
    cg_id = COINGECKO_IDS[crypto]
    url = 'https://api.coingecko.com/api/v3/simple/price'
    headers = {}
    if getattr(settings, 'COINGECKO_API_KEY', None):
        headers['x-cg-pro-api-key'] = settings.COINGECKO_API_KEY
    params = {'ids': cg_id, 'vs_currencies': 'usd'}
    resp = requests.get(url, headers=headers, params=params, timeout=20)
    data = resp.json()
    if resp.status_code != 200 or cg_id not in data or 'usd' not in data[cg_id]:
        raise ValueError('Ціна для цієї криптовалюти зараз недоступна.')
    return Decimal(str(data[cg_id]['usd']))


def _execute_wallet_transfer(order: Order, wallet: Wallet):
    if order.order_type == 'sell':
        if wallet.get_available_balance(order.crypto) < order.quantity:
            raise ValueError('Insufficient available crypto balance')
        setattr(wallet, order.crypto.lower(), getattr(wallet, order.crypto.lower()) - order.quantity)
        wallet.usdt += Decimal(order.usdt_amount)
    else:
        if wallet.get_available_balance('USDT') < order.usdt_amount:
            raise ValueError('Insufficient available USDT balance')
        wallet.usdt -= Decimal(order.usdt_amount)
        setattr(wallet, order.crypto.lower(), getattr(wallet, order.crypto.lower()) + order.quantity)
    wallet.save()
    Transaction.objects.create(
        sender_wallet=wallet,
        receiver_wallet=wallet,
        amount=order.quantity,
        currency=order.crypto,
    )


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
    wallet = Wallet.objects.get(address=request.user.username)
    balances = _wallet_balances_with_frozen(wallet, model_reserved_usdt=_model_reserved_usdt(request.user))
    return render(request, 'order_history.html', {'orders': orders, 'balances': balances})


@login_required
def create_order(request):
    user = request.user
    wallet = Wallet.objects.get(address=user.username)
    model_reserved_usdt = _model_reserved_usdt(user)
    balances = _wallet_balances_with_frozen(wallet, model_reserved_usdt=model_reserved_usdt)
    if request.method == 'POST':
        order_type = request.POST.get('order_type')
        order_mode = request.POST.get('order_mode', Order.ORDER_MODE_LIMIT)
        crypto = (request.POST.get('crypto') or '').upper()
        quantity_raw = request.POST.get('quantity')
        limit_price_raw = request.POST.get('limit_price')

        try:
            quantity = Decimal(quantity_raw)
        except Exception:
            quantity = Decimal('0')

        if quantity <= 0:
            return render(
                request,
                'create_order.html',
                {
                    'error': 'Quantity must be positive.',
                    'supported_cryptos': SUPPORTED_CRYPTOS,
                    'balances': balances,
                },
            )

        if crypto not in SUPPORTED_CRYPTOS or (order_type not in ['buy', 'sell']):
            return render(
                request,
                'create_order.html',
                {
                    'error': 'Invalid crypto or order type',
                    'supported_cryptos': SUPPORTED_CRYPTOS,
                    'balances': balances,
                },
            )
        if order_mode not in [Order.ORDER_MODE_MARKET, Order.ORDER_MODE_LIMIT]:
            return render(
                request,
                'create_order.html',
                {
                    'error': 'Invalid order mode',
                    'supported_cryptos': SUPPORTED_CRYPTOS,
                    'balances': balances,
                },
            )

        try:
            market_price = _get_market_price(crypto)
        except Exception as exc:
            return render(
                request,
                'create_order.html',
                {
                    'error': str(exc),
                    'supported_cryptos': SUPPORTED_CRYPTOS,
                    'balances': balances,
                },
            )

        if order_mode == Order.ORDER_MODE_MARKET:
            price = market_price
        else:
            try:
                price = Decimal(limit_price_raw)
            except Exception:
                price = Decimal('0')
            if price <= 0:
                return render(
                    request,
                    'create_order.html',
                    {
                        'error': 'Limit price must be positive for limit order.',
                        'supported_cryptos': SUPPORTED_CRYPTOS,
                        'balances': balances,
                    },
                )

        usdt_amount = quantity * price

        if order_type == 'buy':
            available_usdt = wallet.get_available_balance('USDT') - Decimal(model_reserved_usdt)
            if available_usdt < usdt_amount:
                return render(
                    request,
                    'create_order.html',
                    {
                        'error': (
                            f'Insufficient available USDT. '
                            f'Available: {available_usdt}, required: {usdt_amount} '
                            f'(part reserved for active auto bots: {model_reserved_usdt}).'
                        ),
                        'supported_cryptos': SUPPORTED_CRYPTOS,
                        'balances': balances,
                    },
                )
        else:
            available_crypto = wallet.get_available_balance(crypto)
            if available_crypto < quantity:
                return render(
                    request,
                    'create_order.html',
                    {
                        'error': (
                            f'Insufficient available {crypto}. '
                            f'Available: {available_crypto}, required: {quantity}.'
                        ),
                        'supported_cryptos': SUPPORTED_CRYPTOS,
                        'balances': balances,
                    },
                )

        order = Order(
            user=user,
            order_type=order_type,
            order_mode=order_mode,
            crypto=crypto,
            quantity=quantity,
            price=price,
            usdt_amount=usdt_amount,
            wallet=wallet,
        )
        if order_mode == Order.ORDER_MODE_MARKET:
            try:
                _execute_wallet_transfer(order, wallet)
                order.status = 'executed'
                order.save()
            except ValueError as exc:
                return render(
                    request,
                    'create_order.html',
                    {
                        'error': str(exc),
                        'supported_cryptos': SUPPORTED_CRYPTOS,
                        'balances': balances,
                    },
                )
        else:
            order.status = 'pending'
            order.save()
            lock_currency = 'USDT' if order_type == 'buy' else crypto
            lock_amount = usdt_amount if order_type == 'buy' else quantity
            wallet.freeze(
                currency=lock_currency,
                amount=lock_amount,
                reason='order',
                reference=f'order:{order.id}',
            )
            order_alert(request, user, quantity, crypto, price, usdt_amount)
        return redirect('order_history')

    return render(
        request,
        'create_order.html',
        {'supported_cryptos': SUPPORTED_CRYPTOS, 'balances': balances},
    )


@login_required
def execute_order(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    if order.status != 'pending':
        return HttpResponseRedirect(reverse('order_history'))
    if order.order_mode != Order.ORDER_MODE_LIMIT:
        return HttpResponseRedirect(reverse('order_history'))

    wallet = order.wallet
    lock_ref = f'order:{order.id}'
    market_price = _get_market_price(order.crypto)

    if order.order_type == 'buy' and market_price > order.price:
        return render(
            request,
            'order_history.html',
            {
                'orders': Order.objects.filter(user=request.user),
                'balances': _wallet_balances_with_frozen(wallet, model_reserved_usdt=_model_reserved_usdt(request.user)),
                'error': f'Limit BUY not triggered yet. Market: {market_price}, limit: {order.price}',
            },
        )
    if order.order_type == 'sell' and market_price < order.price:
        return render(
            request,
            'order_history.html',
            {
                'orders': Order.objects.filter(user=request.user),
                'balances': _wallet_balances_with_frozen(wallet, model_reserved_usdt=_model_reserved_usdt(request.user)),
                'error': f'Limit SELL not triggered yet. Market: {market_price}, limit: {order.price}',
            },
        )

    if order.order_type == 'sell':
        locked_qty = wallet.get_frozen(order.crypto, reason='order')
        if locked_qty < order.quantity:
            return render(
                request,
                'order_history.html',
                {
                    'orders': Order.objects.filter(user=request.user),
                    'balances': _wallet_balances_with_frozen(wallet, model_reserved_usdt=_model_reserved_usdt(request.user)),
                    'error': 'Insufficient crypto balance',
                },
            )
        if getattr(wallet, order.crypto.lower()) < order.quantity:
            return render(
                request,
                'order_history.html',
                {
                    'orders': Order.objects.filter(user=request.user),
                    'balances': _wallet_balances_with_frozen(wallet, model_reserved_usdt=_model_reserved_usdt(request.user)),
                    'error': 'Insufficient crypto balance',
                },
            )
        wallet.unfreeze(
            currency=order.crypto,
            amount=Decimal(order.quantity),
            reason='order',
            reference=lock_ref,
        )
        setattr(wallet, order.crypto.lower(), getattr(wallet, order.crypto.lower()) - order.quantity)
        wallet.usdt += Decimal(order.usdt_amount)
        wallet.save()
        Transaction.objects.create(sender_wallet=wallet, receiver_wallet=wallet, amount=order.quantity, currency=order.crypto)
    else:
        locked_usdt = wallet.get_frozen('USDT', reason='order')
        if locked_usdt < order.usdt_amount:
            return render(
                request,
                'order_history.html',
                {
                    'orders': Order.objects.filter(user=request.user),
                    'balances': _wallet_balances_with_frozen(wallet, model_reserved_usdt=_model_reserved_usdt(request.user)),
                    'error': 'Insufficient USDT balance',
                },
            )
        if wallet.usdt < order.usdt_amount:
            return render(
                request,
                'order_history.html',
                {
                    'orders': Order.objects.filter(user=request.user),
                    'balances': _wallet_balances_with_frozen(wallet, model_reserved_usdt=_model_reserved_usdt(request.user)),
                    'error': 'Insufficient USDT balance',
                },
            )
        wallet.unfreeze(
            currency='USDT',
            amount=Decimal(order.usdt_amount),
            reason='order',
            reference=lock_ref,
        )
        wallet.usdt -= Decimal(order.usdt_amount)
        setattr(wallet, order.crypto.lower(), getattr(wallet, order.crypto.lower()) + order.quantity)
        wallet.save()
        Transaction.objects.create(sender_wallet=wallet, receiver_wallet=wallet, amount=order.quantity, currency=order.crypto)
    order.status = 'executed'
    order.save(update_fields=['status', 'updated_at'])
    return HttpResponseRedirect(reverse('order_history'))


@login_required
def delete_order(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    if order.status != 'pending':
        return HttpResponseRedirect(reverse('order_history'))
    lock_ref = f'order:{order.id}'
    if order.order_type == 'buy':
        order.wallet.unfreeze(
            currency='USDT',
            amount=Decimal(order.usdt_amount),
            reason='order',
            reference=lock_ref,
        )
    else:
        order.wallet.unfreeze(
            currency=order.crypto,
            amount=Decimal(order.quantity),
            reason='order',
            reference=lock_ref,
        )
    order.status = 'cancelled'
    order.save(update_fields=['status', 'updated_at'])
    return HttpResponseRedirect(reverse('order_history'))
