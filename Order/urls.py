from django.urls import path
from. import views

urlpatterns = [
    path('order_history/', views.order_history, name='order_history'),
    path('create_order/', views.create_order, name='create_order'),
]
