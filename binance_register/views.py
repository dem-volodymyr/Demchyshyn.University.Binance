from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from wallet.models import Wallet


@login_required
def welcome_email(request):
    user = request.user
    wallet = Wallet.objects.create(address=user.username, btc=1, eth=1, usdt=200, bnb=1000, sol=100, xrp=20, avax=15,
                                   ada=10, matic=10, dot=10)
    subject = 'Welcome to Xchange!'
    message = f'{user.username}, thanks for becoming a part of our community!'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    return redirect('home')


def logout_view(request):
    logout(request)
    return redirect("home")
