from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class test_logout_view(TestCase):
    def setUp(self):
        self.client = Client()

    def test_logout_view(self):
        user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_login(user)
        # Make a GET request to the logout view
        response = self.client.get(reverse('logout_view'))
        # Check if the response status code is 302 (redirect)
        self.assertEqual(response.status_code, 302)
