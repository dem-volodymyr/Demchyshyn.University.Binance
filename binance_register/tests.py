from django.test import TestCase
from django.urls import reverse

class TestRegisterView(TestCase):
    def test_register_view(self):
        url = reverse('register')  # Assuming 'register' is the name of your URL pattern
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)  # Assuming 200 is the expected status code
        self.assertTemplateUsed(response, 'register.html')
