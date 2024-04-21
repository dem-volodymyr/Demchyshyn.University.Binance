from django.urls import path
from edit_profile import views

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
]
