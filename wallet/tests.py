from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Wallet, Transaction
from django.urls import reverse
from unittest.mock import patch

class WalletModelTest(TestCase):
    def setUp(self):
        self.wallet = Wallet.objects.create(address='testwallet')

    def test_wallet_creation(self):
        self.assertEqual(self.wallet.address, 'testwallet')

class TransactionModelTest(TestCase):
    def setUp(self):
        self.wallet1 = Wallet.objects.create(address='w1')
        self.wallet2 = Wallet.objects.create(address='w2')
        self.tx = Transaction.objects.create(sender_wallet=self.wallet1, receiver_wallet=self.wallet2, amount=1, currency='BTC')

    def test_transaction_fields(self):
        self.assertEqual(self.tx.currency, 'BTC')

class WalletViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.wallet = Wallet.objects.create(address='testuser', btc=10, usdt=1000)
        self.wallet2 = Wallet.objects.create(address='receiver', btc=0, usdt=0)
        self.client.login(username='testuser', password='pass')

    def test_wallet_get(self):
        response = self.client.get(reverse('wallet'))
        self.assertEqual(response.status_code, 200)

    @patch('wallet.views.sent_alert')
    def test_wallet_post_success(self, mock_alert):
        data = {'receiver_wallet_id': 'receiver', 'amount': 1, 'currency': 'BTC'}
        response = self.client.post(reverse('wallet'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Transaction.objects.filter(sender_wallet=self.wallet, receiver_wallet=self.wallet2).exists())

    def test_wallet_history(self):
        response = self.client.get(reverse('wallet_history'))
        self.assertEqual(response.status_code, 200)

    def test_success_view_found(self):
        tx = Transaction.objects.create(sender_wallet=self.wallet, receiver_wallet=self.wallet2, amount=1, currency='BTC')
        response = self.client.get(reverse('success', args=[tx.id]))
        self.assertEqual(response.status_code, 200)
