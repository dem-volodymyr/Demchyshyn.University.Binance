from django.db import models
from django.contrib.auth.models import User


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


FAQ.objects.bulk_create([
    FAQ(question="What is a cryptocurrency?",
        answer="A cryptocurrency is a digital or virtual currency that uses cryptography for security and is decentralized, meaning it's not controlled by any government or financial institution."),
    FAQ(question="How do I create an account on your exchange?",
        answer="To create an account, simply click on the 'Sign Up' button on our homepage and follow the registration process. You will need to provide some basic information such as your name, email address, and password."),
    FAQ(question="What are the fees for trading on your exchange?",
        answer="Our fees are competitive and transparent. We charge a maker fee of 0.1% and a taker fee of 0.2% for most trades. You can find more information on our fees page."),
    FAQ(question="How do I deposit funds into my account?",
        answer="You can deposit funds into your account using a variety of methods, including bank transfer, credit card, and cryptocurrency deposits. Please see our deposit page for more information."),
    FAQ(question="Is my personal and financial information secure?",
        answer="Yes, we take the security of your personal and financial information very seriously. We use state-of-the-art encryption and security measures to protect your data."),
    FAQ(question="How do I withdraw my funds?",
        answer="To withdraw your funds, simply log in to your account and go to the withdrawal page. You will need to enter the amount you wish to withdraw and select your preferred withdrawal method."),
    FAQ(question="What are the minimum and maximum trade amounts?",
        answer="The minimum trade amount is 0.001 BTC and the maximum trade amount is 10 BTC. Please note that these limits may be subject to change."),
    FAQ(question="How do I contact customer support?",
        answer="You can contact our customer support team by submitting a ticket through our support page or by emailing us at support@example.com. We are available 24/7 to assist you."),
    FAQ(question="What are the trading hours for your exchange?",
        answer="Our exchange is open for trading 24 hours a day, 7 days a week. However, please note that some markets may be closed or have limited hours during holidays or maintenance."),
])


class Ticket(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed')
    ])


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.text[:20]}'
