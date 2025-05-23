from django.urls import path
from . import views

urlpatterns = [
    path('order_history/', views.order_history, name='order_history'),
    path('create_order/', views.create_order, name='create_order'),
    path('execute_order/<int:order_id>/', views.execute_order, name='execute_order'),
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),
]
