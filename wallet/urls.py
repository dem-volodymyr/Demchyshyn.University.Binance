from django.urls import path
from . import views

urlpatterns = [
    path('wallet/', views.wallet, name='wallet'),
    path('wallet/usd/', views.wallet_usd, name='wallet_usd'),
    path('wallet/confirm/', views.wallet_confirm, name='wallet_confirm'),
    path('wallet_history/', views.wallet_history, name='wallet_history'),
]
