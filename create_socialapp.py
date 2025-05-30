import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BinanceXchange.settings")
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Створюємо Site з коротшим доменом
site, created = Site.objects.get_or_create(
    id=1,
    defaults={
        "domain": "xchange-production-ua.up.railway.app",
        "name": "xchange-production-ua.up.railway.app"
    }
)

client_id = os.environ.get('GOOGLE_CLIENT_ID')
secret = os.environ.get('GOOGLE_SECRET')

if not client_id or not secret:
    raise Exception("GOOGLE_CLIENT_ID or GOOGLE_SECRET not set in environment variables.")

app, created = SocialApp.objects.get_or_create(
    provider='google',
    name='Google',
    client_id=client_id,
    secret=secret,
)
app.sites.add(site)
print("SocialApp created:", app, "Created:", created)