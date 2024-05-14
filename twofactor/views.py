from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserTwoFactorAuth
from .forms import TwoFactorAuthForm
import pyotp
from django.conf import settings
from django.core.mail import send_mail


@login_required
def sent_new_code(request):
    user = request.user
    user_id = request.user.id
    try:
        two_factor_auth = UserTwoFactorAuth.objects.get(user_id=user_id)
        two_factor_secret = two_factor_auth.two_factor_auth_secret
        subject = 'Reset your two-factor authentication'
        message = f'{user.username}, your new token {two_factor_secret}!'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return redirect('/two_factor_auth_login')

    except UserTwoFactorAuth.DoesNotExist:
        subject = 'Reset your two-factor authentication'
        message = f'{user.username}, you have not registered 2FA before, please click the button <I dont have 2FA> on the website !'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return redirect('/two_factor_auth_login')



@login_required
def two_factor_auth_setup(request):
    if not UserTwoFactorAuth.objects.filter(user=request.user).exists():
        # Generate a secret key and store it in the user's profile
        user_two_factor_auth = UserTwoFactorAuth(user=request.user)
        user_two_factor_auth.two_factor_auth_secret = pyotp.random_base32()
        user_two_factor_auth.save()
        # Generate a QR code URL to be scanned by the authenticator app
        qr_code_url = pyotp.totp.TOTP(user_two_factor_auth.two_factor_auth_secret).provisioning_uri(
            name=request.user.username, issuer_name="Xchange")
        return render(request, 'two_factor_auth_qr_code.html', {'qr_code_url': qr_code_url})
    else:
        return render(request, 'error.html', {'message': 'Insufficient balance.'})


@login_required
def two_factor_auth_login(request):
    if request.method == 'POST':
        form = TwoFactorAuthForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            user_two_factor_auth = UserTwoFactorAuth.objects.get(user=request.user)
            if pyotp.totp.TOTP(user_two_factor_auth.two_factor_auth_secret).verify(token):
                # Login successful, redirect to dashboard
                return redirect('/')
            else:
                # Invalid token, show error message
                return render(request, 'two_factor_auth_login.html', {'error': 'Invalid token'})
    return render(request, 'two_factor_auth_login.html')
