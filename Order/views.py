from django.shortcuts import render, redirect
from .models import Order
from wallet.models import Wallet
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
import requests


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
    if request.method == 'POST':
        product = request.POST.get('product')
        quantity = int(request.POST.get('quantity'))
        price = float(request.POST.get('price'))
        total = quantity * price
        wallet_address = user.username
        wallet = Wallet.objects.get(address=wallet_address)
        order = Order(user=request.user, product=product, quantity=quantity, price=price, total=total, wallet=wallet)
        order.save()
        order_alert(request, user, quantity, product, price, total)
        return redirect('order_history')

    return render(request, 'create_order.html')

