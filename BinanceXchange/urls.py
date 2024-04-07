from django.contrib import admin
from django.urls import path, include
from wallet.views import wallet, success

urlpatterns = [
    path('accounts/', include("allauth.urls")),
    path('', include('binance_register.urls')),
    path('', include('tracker.urls')),
    path('wallet/', wallet, name='wallet'),
    path('success/<int:transaction_id>/', success, name='success'),





    #path('', crypto_list, name='crypto_list'),
    #path('accounts/', include("allauth.urls")),
    #path('register/', views.register, name='register'),
    #path('binance_register/', include("allauth.urls")),
    #path('accounts/google/login/callback/', views.callback_view, name='google_callback'),
    #path('tables/', exchange_view, name='table'),
]

