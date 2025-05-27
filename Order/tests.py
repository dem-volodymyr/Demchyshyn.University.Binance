from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Order
from wallet.models import Wallet
from django.urls import reverse
from unittest.mock import patch, Mock

class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.wallet = Wallet.objects.create(address='testuser')
        self.order = Order.objects.create(
            user=self.user, order_type='buy', crypto='BTC', quantity=1, price=10000, usdt_amount=10000, wallet=self.wallet
        )

    def test_order_fields(self):
        self.assertEqual(self.order.user.username, 'testuser')
        self.assertEqual(self.order.crypto, 'BTC')

class OrderViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.wallet = Wallet.objects.create(address='testuser', btc=10, usdt=100000)
        self.client.login(username='testuser', password='pass')

    def test_order_history(self):
        response = self.client.get(reverse('order_history'))
        self.assertEqual(response.status_code, 200)

    def test_create_order_get(self):
        response = self.client.get(reverse('create_order'))
        self.assertEqual(response.status_code, 200)

    @patch('Order.views.requests.get')
    def test_create_order_post_valid(self, mock_get):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'bitcoin': {'usd': 10000}}
        mock_get.return_value = mock_resp
        data = {'order_type': 'buy', 'crypto': 'BTC', 'quantity': 1}
        response = self.client.post(reverse('create_order'), data)
        self.assertEqual(response.status_code, 302)

    @patch('Order.views.requests.get')
    def test_create_order_post_invalid_crypto(self, mock_get):
        data = {'order_type': 'buy', 'crypto': 'INVALID', 'quantity': 1}
        response = self.client.post(reverse('create_order'), data)
        self.assertContains(response, 'Invalid crypto or order type')

    @patch('Order.views.requests.get')
    def test_create_order_post_api_error(self, mock_get):
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.json.return_value = {}
        mock_get.return_value = mock_resp
        data = {'order_type': 'buy', 'crypto': 'BTC', 'quantity': 1}
        response = self.client.post(reverse('create_order'), data)
        self.assertContains(response, 'Ціна для цієї криптовалюти зараз недоступна')

    def test_execute_order_sell_success(self):
        order = Order.objects.create(user=self.user, order_type='sell', crypto='BTC', quantity=1, price=10000, usdt_amount=10000, wallet=self.wallet)
        response = self.client.get(reverse('execute_order', args=[order.id]))
        self.assertEqual(response.status_code, 302)

    def test_execute_order_sell_insufficient(self):
        order = Order.objects.create(user=self.user, order_type='sell', crypto='BTC', quantity=1000, price=10000, usdt_amount=10000, wallet=self.wallet)
        response = self.client.get(reverse('execute_order', args=[order.id]))
        self.assertContains(response, 'Insufficient crypto balance')

    def test_execute_order_buy_success(self):
        order = Order.objects.create(user=self.user, order_type='buy', crypto='BTC', quantity=1, price=10000, usdt_amount=10, wallet=self.wallet)
        response = self.client.get(reverse('execute_order', args=[order.id]))
        self.assertEqual(response.status_code, 302)

    def test_execute_order_buy_insufficient(self):
        order = Order.objects.create(user=self.user, order_type='buy', crypto='BTC', quantity=1, price=10000, usdt_amount=1000000, wallet=self.wallet)
        response = self.client.get(reverse('execute_order', args=[order.id]))
        self.assertContains(response, 'Insufficient USDT balance')

    def test_delete_order(self):
        order = Order.objects.create(user=self.user, order_type='buy', crypto='BTC', quantity=1, price=10000, usdt_amount=10, wallet=self.wallet)
        response = self.client.get(reverse('delete_order', args=[order.id]))
        self.assertEqual(response.status_code, 302)
