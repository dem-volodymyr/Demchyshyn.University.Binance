from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from .views import welcome_email


# Signal receiver for post_save
@receiver(post_save, sender=User)
def check_new_user(sender, instance, created, **kwargs):
    if created:
        instance._newly_created = True
    elif not hasattr(instance, '_newly_created'):
        instance._newly_created = False


@receiver(user_logged_in)
def send_welcome_email_if_new(sender, request, user, **kwargs):
    if (getattr(user, '_newly_created') and
            user.backend == 'allauth.account.auth_backends.AuthenticationBackend'):
        welcome_email(request)
