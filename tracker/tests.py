from django.test import TestCase, Client
from .models import Cryptocurrency, CryptocurrencyPrice
from django.urls import reverse
from django.contrib.auth.models import User

class CryptocurrencyModelTest(TestCase):
    def test_crypto_creation(self):
        crypto = Cryptocurrency.objects.create(name='Bitcoin', symbol='BTC')
        self.assertEqual(crypto.symbol, 'BTC')

class CryptocurrencyPriceModelTest(TestCase):
    def setUp(self):
        self.crypto = Cryptocurrency.objects.create(name='Bitcoin', symbol='BTC')
        self.price = CryptocurrencyPrice.objects.create(cryptocurrency=self.crypto, price=100)

    def test_latest(self):
        self.assertEqual(CryptocurrencyPrice.latest(), self.price)

class TrackerViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass', email='test@example.com')
        self.client.login(username='testuser', password='pass')

    def test_logout_view(self):
        response = self.client.get(reverse('logout_view'))
        self.assertEqual(response.status_code, 302)
