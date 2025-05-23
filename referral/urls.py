from django.urls import path
from . import views

urlpatterns = [
    path('referral-program/', views.referral_program, name='referral_program'),
]