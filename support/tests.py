from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import FAQ, Ticket, Comment
from django.urls import reverse
from unittest.mock import patch

class FAQModelTest(TestCase):
    def test_faq_str(self):
        faq = FAQ.objects.create(question='Q', answer='A')
        self.assertEqual(str(faq), 'Q')

class TicketModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.ticket = Ticket.objects.create(title='T', description='D', user=self.user, status='open')

    def test_ticket_fields(self):
        self.assertEqual(self.ticket.title, 'T')

class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.ticket = Ticket.objects.create(title='T', description='D', user=self.user, status='open')
        self.comment = Comment.objects.create(ticket=self.ticket, user=self.user, text='text')

    def test_comment_str(self):
        self.assertIn(self.user.username, str(self.comment))

class SupportViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass', email='test@example.com')
        self.client.login(username='testuser', password='pass')
        self.ticket = Ticket.objects.create(title='T', description='D', user=self.user, status='open')
        self.faq = FAQ.objects.create(question='Q', answer='A')

    def test_ticket_list(self):
        response = self.client.get(reverse('ticket_list'))
        self.assertEqual(response.status_code, 200)

    def test_faq_list(self):
        response = self.client.get(reverse('faq_list'))
        self.assertEqual(response.status_code, 200)

    @patch('support.views.generate_ai_response')
    def test_ticket_detail_get(self, mock_ai):
        response = self.client.get(reverse('ticket_detail', args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 200)

    @patch('support.views.generate_ai_response')
    def test_ticket_detail_post_valid(self, mock_ai):
        data = {'text': 'Test comment'}
        response = self.client.post(reverse('ticket_detail', args=[self.ticket.pk]), data)
        self.assertEqual(response.status_code, 302)

    @patch('support.views.generate_ai_response')
    def test_ticket_detail_post_invalid(self, mock_ai):
        data = {'text': ''}  # invalid, required field
        response = self.client.post(reverse('ticket_detail', args=[self.ticket.pk]), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ticket')

    @patch('support.views.generate_ai_response')
    def test_create_ticket_get(self, mock_ai):
        response = self.client.get(reverse('create_ticket'))
        self.assertEqual(response.status_code, 200)

    @patch('support.views.generate_ai_response')
    def test_create_ticket_post(self, mock_ai):
        data = {'title': 'New', 'description': 'Desc'}
        response = self.client.post(reverse('create_ticket'), data)
        self.assertEqual(response.status_code, 302)

    @patch('support.views.send_mail')
    def test_contact_get(self, mock_mail):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)

    @patch('support.views.send_mail')
    def test_contact_post(self, mock_mail):
        response = self.client.post(reverse('contact'), {'message': 'Help!'}, follow=True)
        self.assertEqual(response.status_code, 200)
