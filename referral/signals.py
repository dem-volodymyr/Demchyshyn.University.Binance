from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Referral
import uuid

@receiver(post_save, sender=User)
def create_referral(sender, instance, created, **kwargs):
    if created:
        Referral.objects.create(user=instance, code=str(uuid.uuid4())[:12])