from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login/otp/', views.login_otp_view, name='login_otp'),
    path('signup/', views.signup_view, name='signup'),
    path('signup/verify/', views.signup_verify_view, name='signup_verify'),
    path('logout/', views.logout_view, name='logout_view'),
    path('profile/otp/', views.otp_setup_view, name='otp_setup'),
]
