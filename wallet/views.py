from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
import requests
from .models import Wallet, Transaction
import re


def wallet(request):
    if request.method == 'POST':
        user = request.user
        sender_wallet_id = user.username
        receiver_wallet_id = request.POST.get('receiver_wallet_id')
        amount = float(request.POST.get('amount'))
        currency = request.POST.get('currency')

        sender_wallet = Wallet.objects.get(address=sender_wallet_id)
        receiver_wallet = Wallet.objects.get(id=receiver_wallet_id)

        # Перевірка наявності коштів на гаманці
        if sender_wallet.__dict__[currency.lower()] >= amount:
            # Створення транзакції
            transaction = Transaction(sender_wallet=sender_wallet, receiver_wallet=receiver_wallet, amount=amount,
                                      currency=currency)
            transaction.save()
            return redirect('success', transaction_id=transaction.id)
        else:
            return render(request, 'error.html', {'message': 'Insufficient balance.'})

    wallets = Wallet.objects.all()
    return render(request, 'wallet.html', {'wallets': wallets})


def callback_view(request):
    return redirect(reverse('wallet'))


def success(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        return render(request, 'success.html', {'transaction': transaction})
    except Transaction.DoesNotExist:
        return render(request, 'error.html', {'error_message': 'Transaction not found'})
