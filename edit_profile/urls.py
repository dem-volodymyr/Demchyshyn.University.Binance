from django.urls import path
from edit_profile import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
]