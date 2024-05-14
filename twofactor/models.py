from django.contrib.auth.models import User
from django.db import models

class UserTwoFactorAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    two_factor_auth_secret = models.CharField(max_length=255, null=True, blank=True)