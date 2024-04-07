from django.urls import path
from . import views

urlpatterns = [
    path('', views.crypto_list, name='home'),
]