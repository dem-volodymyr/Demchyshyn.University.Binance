from django.urls import path
from. import views

urlpatterns = [
    path('wallet/', views.wallet, name='wallet'),
    path('wallet_history/', views.wallet_history, name='wallet_history'),
]