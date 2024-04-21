from django.test import TestCase
from django.core import mail
from django.contrib.auth.models import User
from django.conf import settings
from wallet.views import sent_alert


class SentAlertTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.receiver_wallet = 'receiver_wallet_address'
        self.amount = 100
        self.currency = 'USD'

    def test_sent_alert_email_sent(self):
        sent_alert(self.request, self.user, self.receiver_wallet, self.amount, self.currency)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Wallet transaction successful!')
        self.assertEqual(mail.outbox[0].body,
                         f'{self.user.username}, you sent to {self.receiver_wallet}, {self.amount}{self.currency}!')
        self.assertEqual(mail.outbox[0].from_email, settings.EMAIL_HOST_USER)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_sent_alert_email_not_sent_missing_user_email(self):
        # Creating a user without an email address
        user_without_email = User.objects.create_user(username='noemailuser', password='password123')
        sent_alert(self.request, user_without_email, self.receiver_wallet, self.amount, self.currency)
        # Asserting that no email is sent as the user doesn't have an email address
        self.assertEqual(len(mail.outbox), 0)

    def test_sent_alert_email_not_sent_fail_silently(self):
        # Modifying settings to fail silently
        settings.EMAIL_FAIL_SILENTLY = True
        sent_alert(self.request, self.user, self.receiver_wallet, self.amount, self.currency)
        # Asserting that no email is sent when fail_silently is set to True
        self.assertEqual(len(mail.outbox), 0)
        # Resetting settings
        settings.EMAIL_FAIL_SILENTLY = False
