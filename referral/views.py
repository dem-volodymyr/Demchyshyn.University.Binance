from django.shortcuts import render, redirect
from .models import Referral, ReferralReward
from django.contrib.auth.models import User
import hashlib
from wallet.models import Wallet


def generate_referral_code(user):
    username_bytes = user.username.encode('utf-8')
    hash_object = hashlib.md5(username_bytes)
    referral_code = hash_object.hexdigest()[:8]  # Take first 8 characters of the hash
    return referral_code


def referral_program(request):
    if request.user.is_authenticated:
        if not hasattr(request.user, 'referral'):
            referral_code = generate_referral_code(request.user)
            referral = Referral.objects.create(user=request.user, referral_code=referral_code)
        else:
            referral = request.user.referral

        referred_by = referral.referred_by
        # TODO: something for input ref_code and test

        return render(request, 'referral_program.html', {'referral': referral.referral_code})
    else:
        return redirect('home')


def refer_friend(request):
    if request.method == 'POST':
        referral_code = request.POST.get('referral')
        user_referred_by = Referral.objects.filter(referral_code=referral_code)
        referred_by = User.objects.filter(referral__referral_code=referral_code).first()
        print(user_referred_by)

        if referred_by:
            referred_user = request.user
            referral_wallet_id = referred_user.username
            if not hasattr(referred_user, 'referral'):
                referral_code = generate_referral_code(referred_user)
                Referral.objects.create(user=referred_user, referral_code=referral_code,
                                        referred_by=referred_by)

            else:
                referral = referred_user.referral

            referral_wallet = Wallet.objects.get(address=referral_wallet_id)
            rr = ReferralReward(referral_wallet=referral_wallet, amount=100)
            rr.add_points()

            """
            # Reward the referrer
            referrer_reward, created = ReferralReward.objects.get_or_create(referral_wallet=referred_by)
            referrer_reward.add_points(100)  # Example: Give 100 points to the referrer

            # Reward the referred user
            referred_user_reward, created = ReferralReward.objects.get_or_create(referral_wallet=referred_user)
            referred_user_reward.add_points(50)  # Example: Give 50 points to the referred user
            """

            return redirect('referral_program')
        else:
            return render(request, 'error.html')
    else:
        return render(request, 'refer_friend.html')
