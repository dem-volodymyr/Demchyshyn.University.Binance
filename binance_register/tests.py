from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
from .views import welcome_email, logout_view
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.test.utils import override_settings

class BinanceRegisterViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass', email='test@example.com')
        self.client.login(username='testuser', password='pass')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_welcome_email_view(self):
        request = RequestFactory().get('/')
        request.user = self.user
        response = welcome_email(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Welcome to Xchange!', mail.outbox[0].subject)

    def test_logout_view(self):
        response = self.client.get(reverse('logout_view'))
        self.assertEqual(response.status_code, 302)
