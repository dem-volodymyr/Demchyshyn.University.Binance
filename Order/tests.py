from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from myapp.models import Order, Wallet

class OrderViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.wallet = Wallet.objects.create(address='test_wallet_address', user=self.user)

    def test_order_history_view_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('order_history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order_history.html')

    def test_order_history_view_unauthenticated_user(self):
        response = self.client.get(reverse('order_history'))
        self.assertRedirects(response, '/accounts/login/?next=/order/history/', target_status_code=302)

    def test_create_order_view_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('create_order'), {'product': 'test_product', 'quantity': 10, 'price': 20.0})
        self.assertEqual(response.status_code, 302)  # Redirects to order_history on successful order creation

        # Check if the order is created
        self.assertTrue(Order.objects.filter(user=self.user).exists())

    def test_create_order_view_unauthenticated_user(self):
        response = self.client.post(reverse('create_order'), {'product': 'test_product', 'quantity': 10, 'price': 20.0})
        self.assertRedirects(response, '/accounts/login/?next=/create/order/', target_status_code=302)
