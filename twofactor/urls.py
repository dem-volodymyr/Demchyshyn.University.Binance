from django.urls import path
from. import views

urlpatterns = [
    path('two_factor_auth_setup/', views.two_factor_auth_setup, name='two_factor_auth_setup'),
    path('two_factor_auth_login/', views.two_factor_auth_login, name='two_factor_auth_login'),
    path('sent_new_code/', views.sent_new_code, name ='sent_new_code')
]