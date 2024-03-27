from django.shortcuts import render
from .models import CryptoCurrency, PriceData


def crypto_market_analysis(request):
    cryptocurrencies = CryptoCurrency.objects.all()
    return render(request, 'analysis.html', {'cryptocurrencies': cryptocurrencies})
