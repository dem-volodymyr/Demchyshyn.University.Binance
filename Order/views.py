from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Order
from wallet.models import Wallet


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
        return redirect('order_history')
    return render(request, 'create_order.html')
