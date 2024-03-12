from django.shortcuts import render
import requests
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse


# Create your views here.

def exchange_view(request):
    url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=USD&order=market_cap_desc&per_page=100&page=1&sparkline=false'
    data = requests.get(url).json()

    # return HttpResponse(data)

    context = {'data': data}

    return render(request, 'main.html', context)


def callback_view(request):
    return redirect(reverse('exchange_view'))
