from django.shortcuts import render, redirect
from .models import Referral
from django.contrib.auth.models import User
from wallet.models import Wallet, Transaction
from decimal import Decimal

def referral_program(request):
    if not request.user.is_authenticated:
        return redirect('home')

    # Створити Referral, якщо ще немає
    referral, _ = Referral.objects.get_or_create(user=request.user)

    # Якщо вже є invited_by — просто показати код і історію
    if referral.invited_by:
        ref_list = request.user.referrals.all()
        return render(request, 'referral_program.html', {
            'referral_code': referral.code,
            'referrals': ref_list,
            'bonus': referral.bonus,
            'invited_by': referral.invited_by,
        })

    # Якщо ще не вводив код — показати форму
    if request.method == 'POST':
        referral_code = request.POST.get('referral')
        referrer = Referral.objects.filter(code=referral_code).first()
        if referrer and referrer.user != request.user:
            referral.invited_by = referrer.user
            referral.save()
            # Нараховуємо бонуси обом
            referrer.bonus += 10
            referrer.save()
            referral.bonus += 10
            referral.save()
            # --- Транзакції на гаманець ---
            system_wallet, _ = Wallet.objects.get_or_create(address='Xchange')
            referrer_wallet, _ = Wallet.objects.get_or_create(address=referrer.user.username)
            referred_wallet, _ = Wallet.objects.get_or_create(address=request.user.username)
            # Для реферера
            referrer_wallet.usdt += Decimal(10)
            referrer_wallet.save()
            Transaction.objects.create(
                sender_wallet=system_wallet,
                receiver_wallet=referrer_wallet,
                amount=10,
                currency='USDT'
            )
            # Для запрошеного
            referred_wallet.usdt += Decimal(10)
            referred_wallet.save()
            Transaction.objects.create(
                sender_wallet=system_wallet,
                receiver_wallet=referred_wallet,
                amount=10,
                currency='USDT'
            )
            return redirect('referral_program')
        else:
            error = "Реферальний код не знайдено або ви не можете запросити самі себе!"
            return render(request, 'referral_program.html', {
                'referral_code': referral.code,
                'referrals': request.user.referrals.all(),
                'bonus': referral.bonus,
                'error': error,
                'invited_by': referral.invited_by,
            })

    return render(request, 'referral_program.html', {
        'referral_code': referral.code,
        'referrals': request.user.referrals.all(),
        'bonus': referral.bonus,
        'invited_by': referral.invited_by,
    })