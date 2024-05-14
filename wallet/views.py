from django.shortcuts import render
from django.shortcuts import render, redirect
from django.urls import reverse
import requests
from .models import Wallet, Transaction
import re
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required


@login_required
def sent_alert(request, user, receiver_wallet, amount, currency):
    subject = 'Wallet transaction successful!'
    message = f'{user.username}, you sent to {receiver_wallet}, {amount}{currency}!'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


@login_required
def wallet(request):
    if request.method == 'POST':
        user = request.user
        sender_wallet_id = user.username
        receiver_wallet_id = request.POST.get('receiver_wallet_id')
        amount = float(request.POST.get('amount'))
        currency = request.POST.get('currency')

        sender_wallet = Wallet.objects.get(address=sender_wallet_id)
        receiver_wallet = Wallet.objects.get(address=receiver_wallet_id)

        # Перевірка наявності коштів на гаманці
        if sender_wallet.__dict__[currency.lower()] >= amount:
            sent_alert(request, user, receiver_wallet.address, amount, currency)
            transaction = Transaction(sender_wallet=sender_wallet, receiver_wallet=receiver_wallet, amount=amount,
                                      currency=currency)
            transaction.save_it()
            return redirect('success', transaction_id=transaction.id)
        else:
            return render(request, 'error.html', {'message': 'Insufficient balance.'})
    user = request.user
    sender_wallet_id = user.username
    wallets = Wallet.objects.get(address=sender_wallet_id)
    return render(request, 'wallet.html', {'wallets': wallets})


def callback_view(request):
    return redirect(reverse('wallet'))


@login_required
def wallet_history(request):
    user = request.user
    sender_wallet = user.id
    print(sender_wallet)
    transactions = Transaction.objects.filter(receiver_wallet_id=sender_wallet)
    return render(request, 'wallet_history.html', {'transactions': transactions})


def view_wallet(request):
    user = request.user
    sender_wallet_id = user.username
    user = request.user
    sender_wallet_id = user.username
    wallets = Wallet.objects.get(address=sender_wallet_id)
    return render(request, 'wallet.html', {'wallets': wallets})


@login_required
def success(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        return render(request, 'success.html', {'transaction': transaction})
    except Transaction.DoesNotExist:
        return render(request, 'error.html', {'error_message': 'Transaction not found'})
