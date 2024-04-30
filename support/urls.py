from django.urls import path
from support import views

urlpatterns = [
    path('support/faq_list/', views.faq_list, name='faq_list'),
    path('support/contact/', views.contact, name='contact'),
    path('support/', views.ticket_list, name='ticket_list'),
    path('support/create_ticket/', views.create_ticket, name='create_ticket'),
    path('support/ticket/<int:pk>/', views.ticket_detail, name='ticket_detail'),
]
