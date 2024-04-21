from django.core import mail
from django.conf import settings
from django.shortcuts import redirect
from tracker.views import welcome_email
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User


class WelcomeEmailTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')

    def test_welcome_email_sent(self):
        request = self.factory.get('/')
        request.user = self.user

        response = welcome_email(request)

        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Welcome to BinanceXchange!')
        self.assertEqual(mail.outbox[0].body, f'{self.user.username}, thanks for becoming a part of our community!')
        self.assertEqual(mail.outbox[0].from_email, settings.EMAIL_HOST_USER)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_welcome_email_not_sent_missing_user_email(self):
        # Creating a user without an email address
        user_without_email = User.objects.create_user(username='noemailuser', password='password123')

        request = self.factory.get('/')
        request.user = user_without_email

        response = welcome_email(request)

        # Asserting that no email is sent as the user doesn't have an email address
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(response.status_code, 302)  # Redirect status code

    def test_welcome_email_not_sent_fail_silently(self):
        # Modifying settings to fail silently
        settings.EMAIL_FAIL_SILENTLY = True

        request = self.factory.get('/')
        request.user = self.user

        response = welcome_email(request)

        # Asserting that no email is sent when fail_silently is set to True
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(response.status_code, 302)  # Redirect status code

        # Resetting settings
        settings.EMAIL_FAIL_SILENTLY = False


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_view(self):
        user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_login(user)
        # Make a GET request to the home view
        response = self.client.get(reverse('home'))
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        # Check if the correct template is used
        self.assertTemplateUsed(response, 'homepage/homepage.html')

    def test_profile_view_authenticated(self):
        # Create a test user and log in
        user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_login(user)
        # Make a GET request to the profile.html view
        response = self.client.get(reverse('profile.html'))
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        # Check if the correct template is used
        self.assertTemplateUsed(response, 'homepage/profile.html.html')
        # Check if the username is passed to the template context
        self.assertEqual(response.context['username'], 'testuser')

    def test_profile_view_not_authenticated(self):
        # Make a GET request to the profile.html view without logging in
        response = self.client.get(reverse('profile.html'))
        # Check if the response status code is 302 (redirect to homepage)
        self.assertEqual(response.status_code, 302)
        # Check if the username context variable is None
        self.assertIsNone(response.context and response.context.get('username'))
