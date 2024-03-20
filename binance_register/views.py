from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from wallet.models import Wallet
import requests

# Create your views here.


# Create your views here.
def home(request):
    return render(request, "home.html")


def register(request):
    wallet = Wallet.objects.create(address='', btc=0.0001, eth=0.000001, usdt=100, bnb=1000, sol=100, xrp=20, avax=15, ada=10,
                                    matic=10, dot=10)
    return render(request, "register.html")


def callback_view(request):
    return redirect(reverse('table'))

