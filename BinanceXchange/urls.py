from django.contrib import admin
from django.urls import path, include
from wallet.views import success
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include("allauth.urls")),
    path('qr_code/', include('qr_code.urls', namespace="qr_code")),
    path('', include('binance_register.urls')),
    path('', include('tracker.urls')),
    path('', include('Order.urls')),
    path('', include('wallet.urls')),
    path('success/<int:transaction_id>/', success, name='success'),
    path('', include("edit_profile.urls")),
    path('', include("support.urls")),
    path('', include("referral.urls")),
    path('', include("twofactor.urls")),


    #path('', crypto_list, name='crypto_list'),
    #path('accounts/', include("allauth.urls")),
    #path('register/', views.register, name='register'),
    #path('binance_register/', include("allauth.urls")),
    #path('accounts/google/login/callback/', views.callback_view, name='google_callback'),
    #path('tables/', exchange_view, name='table'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)