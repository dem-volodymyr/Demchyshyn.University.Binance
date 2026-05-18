from django.urls import path

from . import views

urlpatterns = [
    path('autotrading/', views.dashboard, name='autotrading_dashboard'),
]
