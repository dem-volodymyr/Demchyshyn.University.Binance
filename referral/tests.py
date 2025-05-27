from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Referral
from django.urls import reverse
from wallet.models import Wallet

class ReferralModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.referral = Referral.objects.get(user=self.user)

    def test_referral_str(self):
        self.assertIn(self.user.username, str(self.referral))

class ReferralViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')
        self.referral = Referral.objects.get(user=self.user)

    def test_referral_program_get(self):
        response = self.client.get(reverse('referral_program'))
        self.assertEqual(response.status_code, 200)

    def test_referral_program_get_with_invited_by(self):
        inviter = User.objects.create_user(username='inviter', password='pass')
        inviter_ref = Referral.objects.get(user=inviter)
        self.referral.invited_by = inviter
        self.referral.save()
        response = self.client.get(reverse('referral_program'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, inviter.username)

    def test_referral_program_post_valid(self):
        inviter = User.objects.create_user(username='inviter', password='pass')
        inviter_ref = Referral.objects.get(user=inviter)
        Wallet.objects.create(address='Xchange')
        Wallet.objects.create(address='inviter')
        Wallet.objects.create(address='testuser')
        data = {'referral': inviter_ref.code}
        response = self.client.post(reverse('referral_program'), data)
        self.assertEqual(response.status_code, 302)

    def test_referral_program_post_invalid(self):
        data = {'referral': 'invalidcode'}
        response = self.client.post(reverse('referral_program'), data)
        self.assertContains(response, 'Реферальний код не знайдено')

    def test_referral_program_post_self_invite(self):
        data = {'referral': self.referral.code}
        response = self.client.post(reverse('referral_program'), data)
        self.assertContains(response, 'Реферальний код не знайдено')
