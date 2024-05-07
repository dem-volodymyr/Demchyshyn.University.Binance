from django.urls import path
from .views import referral_program, refer_friend

urlpatterns = [
    path('referral-program/', referral_program, name='referral_program'),
    path('refer_friend/', refer_friend, name='refer_friend'),
    # Other URLs for referral-related features
]