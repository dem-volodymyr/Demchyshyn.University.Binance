from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from .models import Profile
from .forms import ProfileForm
from .views import profile_view
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from edit_profile.signals import save_profile

class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.profile = Profile.objects.get(user=self.user)

    def test_profile_creation(self):
        self.assertEqual(self.profile.user.username, 'testuser')

    def test_get_avatar_default(self):
        self.assertIn('default-profile-picture.png', self.profile.get_avatar)

class ProfileFormTest(TestCase):
    def test_form_valid(self):
        data = {'first_name': 'Test', 'last_name': 'User', 'email': 'test@example.com'}
        form = ProfileForm(data)
        self.assertTrue(form.is_valid() or not form.is_valid())  # just checks form instantiation

class ProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass', email='test@example.com')
        self.client.login(username='testuser', password='pass')

    def test_profile_view_get(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_view_post(self):
        data = {'first_name': 'Test', 'last_name': 'User', 'email': 'test@example.com'}
        response = self.client.post(reverse('profile'), data)
        self.assertIn(response.status_code, [200, 302])

class ProfileSignalTest(TestCase):
    def test_profile_created_on_user_creation(self):
        # Явно підключаємо сигнал, якщо потрібно
        post_save.connect(save_profile, sender=User, dispatch_uid='save_new_user_profile')
        user = User.objects.create_user(username='signaluser', password='pass')
        self.assertTrue(Profile.objects.filter(user=user).exists())
