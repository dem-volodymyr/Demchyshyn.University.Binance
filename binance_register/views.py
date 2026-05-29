import base64
import io
import random

import pyotp
import qrcode
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import SignUpForm
from edit_profile.models import Profile


def _send_email_code(email: str, code: str, purpose: str):
    send_mail(
        subject=f"Xchange {purpose} verification code",
        message=f"Your verification code is: {code}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


@login_required
def welcome_email(request):
    user = request.user
    subject = 'Welcome to Xchange!'
    message = f'{user.username}, thanks for becoming a part of our community!'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    return redirect('home')


def logout_view(request):
    logout(request)
    return redirect("home")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        identifier = request.POST.get("login", "").strip()
        password = request.POST.get("password", "")
        matched_user = None

        if "@" in identifier:
            matched_user = User.objects.filter(email__iexact=identifier).first()
        else:
            matched_user = User.objects.filter(username=identifier).first()

        if matched_user and not matched_user.is_active:
            messages.error(request, "Email is not verified yet. Please complete signup verification.")
            return redirect("signup_verify")

        user = authenticate(request, username=identifier, password=password)
        if user is None and "@" in identifier:
            matched_user = User.objects.filter(email__iexact=identifier).first()
            if matched_user:
                user = authenticate(request, username=matched_user.username, password=password)

        if user is not None:
            profile, _ = Profile.objects.get_or_create(user=user)
            if profile.otp_enabled and profile.otp_secret:
                request.session["pending_login_user_id"] = user.id
                request.session["pending_login_next"] = request.POST.get("next") or "home"
                return redirect("login_otp")

            login(request, user)
            request.session["force_otp_setup"] = True
            messages.warning(request, "You must enable 2FA before using your account.")
            return redirect("otp_setup")

        messages.error(request, "Invalid username/email or password.")

    return render(request, "account/login.html")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            verification_code = f"{random.randint(100000, 999999)}"
            request.session["pending_signup"] = {
                "username": form.cleaned_data["username"],
                "email": form.cleaned_data["email"],
                "password": form.cleaned_data["password1"],
                "code": verification_code,
            }
            _send_email_code(form.cleaned_data["email"], verification_code, "signup")
            messages.info(request, "Verification code sent to your email.")
            return redirect("signup_verify")
    else:
        form = SignUpForm()

    return render(request, "account/signup.html", {"form": form})


def signup_verify_view(request):
    pending = request.session.get("pending_signup")
    if not pending:
        messages.error(request, "Signup session expired. Please register again.")
        return redirect("signup")

    if request.method == "POST":
        code = request.POST.get("verification_code", "").strip()
        if code != pending.get("code"):
            messages.error(request, "Invalid verification code.")
            return redirect("signup_verify")

        if User.objects.filter(username=pending["username"]).exists():
            messages.error(request, "Username already exists. Please register again.")
            request.session.pop("pending_signup", None)
            return redirect("signup")
        if User.objects.filter(email__iexact=pending["email"]).exists():
            messages.error(request, "Email already exists. Please register again.")
            request.session.pop("pending_signup", None)
            return redirect("signup")

        user = User.objects.create_user(
            username=pending["username"],
            email=pending["email"],
            password=pending["password"],
            is_active=True,
        )
        request.session.pop("pending_signup", None)
        login(request, user)
        request.session["force_otp_setup"] = True
        messages.success(request, "Email verified. Now enable 2FA to finish registration.")
        return redirect("otp_setup")

    return render(request, "account/signup_verify.html", {"email": pending.get("email")})


def _build_qr_data_uri(data: str) -> str:
    qr_img = qrcode.make(data)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def login_otp_view(request):
    pending_user_id = request.session.get("pending_login_user_id")
    if not pending_user_id:
        messages.error(request, "OTP session expired. Please sign in again.")
        return redirect("login")

    try:
        user = User.objects.get(id=pending_user_id)
    except User.DoesNotExist:
        request.session.pop("pending_login_user_id", None)
        request.session.pop("pending_login_next", None)
        messages.error(request, "User not found. Please sign in again.")
        return redirect("login")

    profile, _ = Profile.objects.get_or_create(user=user)
    if not profile.otp_enabled or not profile.otp_secret:
        request.session.pop("pending_login_user_id", None)
        login(request, user)
        return redirect(request.session.pop("pending_login_next", "home"))

    if request.method == "POST":
        token = request.POST.get("otp_token", "").strip().replace(" ", "")
        totp = pyotp.TOTP(profile.otp_secret)
        if totp.verify(token, valid_window=1):
            request.session.pop("pending_login_user_id", None)
            next_url = request.session.pop("pending_login_next", "home")
            login(request, user)
            return redirect(next_url)
        messages.error(request, "Invalid OTP token.")

    return render(request, "account/login_otp.html")


@login_required
def otp_setup_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    force_otp_setup = bool(request.session.get("force_otp_setup"))

    if request.method == "POST" and request.POST.get("action") == "disable":
        if force_otp_setup:
            messages.error(request, "You must enable 2FA to continue.")
            return redirect("otp_setup")
        profile.otp_enabled = False
        profile.otp_secret = ""
        profile.save(update_fields=["otp_enabled", "otp_secret"])
        request.session.pop("otp_setup_secret", None)
        messages.success(request, "OTP disabled.")
        return redirect("otp_setup")

    secret = request.session.get("otp_setup_secret")
    if profile.otp_enabled and profile.otp_secret and not secret:
        secret = profile.otp_secret
    if not secret:
        secret = pyotp.random_base32()
        request.session["otp_setup_secret"] = secret

    if request.method == "POST" and request.POST.get("action") == "enable":
        token = request.POST.get("otp_token", "").strip().replace(" ", "")
        totp = pyotp.TOTP(secret)
        if totp.verify(token, valid_window=1):
            profile.otp_secret = secret
            profile.otp_enabled = True
            profile.save(update_fields=["otp_secret", "otp_enabled"])
            request.session.pop("otp_setup_secret", None)
            request.session.pop("force_otp_setup", None)
            messages.success(request, "OTP enabled successfully.")
            return redirect("home")
        messages.error(request, "Invalid OTP token. Please try again.")

    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
        name=request.user.email or request.user.username,
        issuer_name="Xchange",
    )
    qr_data_uri = _build_qr_data_uri(provisioning_uri)
    return render(
        request,
        "account/otp_setup.html",
        {
            "otp_enabled": profile.otp_enabled,
            "qr_data_uri": qr_data_uri,
            "secret": secret,
            "force_otp_setup": force_otp_setup,
        },
    )
