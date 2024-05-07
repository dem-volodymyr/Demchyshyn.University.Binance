from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from wallet.models import Wallet


@login_required
def welcome_email(request):
    user = request.user
    wallet = Wallet.objects.create(address=user.username, btc=0, eth=0, usdt=0, bnb=0, sol=0, xrp=0, avax=0,
                                   ada=0, matic=0, dot=0)
    subject = 'Welcome to Xchange!'
    message = f'{user.username}, thanks for becoming a part of our community!'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    return redirect('home')


def logout_view(request):
    logout(request)
    return redirect("home")
