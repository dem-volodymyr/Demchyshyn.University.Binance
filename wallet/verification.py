import random

from django.conf import settings
from django.core.mail import send_mail

from edit_profile.models import Profile

SESSION_KEY = 'pending_wallet_operation'


def send_verification_email(user, purpose: str) -> str:
    code = f'{random.randint(100000, 999999)}'
    send_mail(
        subject=f'Xchange {purpose} verification code',
        message=f'Your verification code is: {code}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return code


def set_pending_operation(request, payload: dict):
    request.session[SESSION_KEY] = payload


def get_pending_operation(request):
    return request.session.get(SESSION_KEY)


def clear_pending_operation(request):
    request.session.pop(SESSION_KEY, None)


def verify_email_code(pending: dict, code: str) -> bool:
    return (code or '').strip() == pending.get('email_code')


def verify_otp(user, token: str) -> tuple[bool, str]:
    profile, _ = Profile.objects.get_or_create(user=user)
    if not profile.otp_enabled or not profile.otp_secret:
        return False, 'Спочатку увімкніть 2FA в профілі.'

    import pyotp

    normalized = (token or '').strip().replace(' ', '')
    if not pyotp.TOTP(profile.otp_secret).verify(normalized, valid_window=1):
        return False, 'Невірний 2FA токен.'
    return True, ''
