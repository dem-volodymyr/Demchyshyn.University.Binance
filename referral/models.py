from django.db import models
from django.contrib.auth.models import User
import uuid

class Referral(models.Model):
    user = models.OneToOneField(User, related_name='referral', on_delete=models.CASCADE)
    invited_by = models.ForeignKey(User, related_name='referrals', null=True, blank=True, on_delete=models.SET_NULL)
    code = models.CharField(max_length=16, unique=True, default=uuid.uuid4)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username} (invited by {self.invited_by.username if self.invited_by else 'None'})"