from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse

from Order.models import Order
from .models import Transaction, Wallet
from .verification import (
    clear_pending_operation,
    get_pending_operation,
    send_verification_email,
    set_pending_operation,
    verify_email_code,
    verify_otp,
)


def _get_wallet(user):
    return Wallet.objects.get_or_create(address=user.username)[0]


def _log_usd_order(user, wallet, order_type: str, amount: Decimal):
    Order.objects.create(
        user=user,
        order_type=order_type,
        crypto='USDT',
        quantity=amount,
        price=Decimal('1'),
        usdt_amount=amount,
        status='executed',
        wallet=wallet,
    )


def _require_email(user):
    if not user.email:
        return False
    return True


@login_required
def wallet(request):
    wallets = _get_wallet(request.user)
    if request.method == 'POST':
        if not _require_email(request.user):
            return render(
                request,
                'wallet_error.html',
                {'message': 'Для переказу потрібно вказати email у профілі.'},
            )

        receiver_wallet_id = request.POST.get('receiver_wallet_id')
        currency = request.POST.get('currency')
        try:
            amount = Decimal(str(request.POST.get('amount')))
        except (InvalidOperation, TypeError):
            return render(request, 'wallet_error.html', {'message': 'Некоректна сума переказу.'})
        if amount <= 0:
            return render(request, 'wallet_error.html', {'message': 'Сума має бути більшою за 0.'})

        try:
            sender_wallet = Wallet.objects.get(address=request.user.username)
        except Wallet.DoesNotExist:
            return render(request, 'wallet_error.html', {'message': 'Ваш гаманець не знайдено.'})
        try:
            receiver_wallet = Wallet.objects.get(address=receiver_wallet_id)
        except Wallet.DoesNotExist:
            return render(
                request,
                'wallet_error.html',
                {'message': 'Гаманець отримувача не знайдено. Перевірте адресу.'},
            )

        if sender_wallet.__dict__[currency.lower()] < amount:
            return render(request, 'wallet_error.html', {'message': 'Недостатньо коштів.'})

        email_code = send_verification_email(request.user, 'transfer')
        set_pending_operation(
            request,
            {
                'type': 'transfer',
                'user_id': request.user.id,
                'receiver_wallet_id': receiver_wallet_id,
                'amount': str(amount),
                'currency': currency,
                'email_code': email_code,
            },
        )
        messages.info(request, 'На вашу пошту надіслано код підтвердження.')
        return redirect('wallet_confirm')

    return render(request, 'wallet.html', {'wallets': wallets})


@login_required
def wallet_usd(request):
    wallets = _get_wallet(request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            usd_amount = Decimal(str(request.POST.get('usd_amount')))
        except (InvalidOperation, TypeError):
            messages.error(request, 'Некоректна сума USD.')
            return redirect('wallet_usd')

        if usd_amount <= 0:
            messages.error(request, 'Сума має бути більшою за 0.')
            return redirect('wallet_usd')

        if action == 'usd_deposit':
            wallets.usdt += usd_amount
            wallets.save(update_fields=['usdt'])
            _log_usd_order(request.user, wallets, 'buy', usd_amount)
            messages.success(
                request,
                f'Псевдо-поповнення на {usd_amount} USD виконано. Нараховано {usd_amount} USDT.',
            )
            return redirect('wallet_usd')

        if action == 'usd_withdraw':
            if not _require_email(request.user):
                messages.error(request, 'Для виведення потрібно вказати email у профілі.')
                return redirect('wallet_usd')
            if wallets.usdt < usd_amount:
                messages.error(request, 'Недостатньо USDT для виведення USD.')
                return redirect('wallet_usd')

            email_code = send_verification_email(request.user, 'USD withdraw')
            set_pending_operation(
                request,
                {
                    'type': 'usd_withdraw',
                    'user_id': request.user.id,
                    'amount': str(usd_amount),
                    'email_code': email_code,
                },
            )
            messages.info(request, 'На вашу пошту надіслано код підтвердження виведення.')
            return redirect('wallet_confirm')

    return render(request, 'wallet_usd.html', {'wallets': wallets})


@login_required
def wallet_confirm(request):
    pending = get_pending_operation(request)
    if not pending or pending.get('user_id') != request.user.id:
        messages.error(request, 'Немає операції для підтвердження.')
        return redirect('wallet')

    operation_label = _operation_label(pending)

    if request.method == 'POST':
        if request.POST.get('action') == 'cancel':
            clear_pending_operation(request)
            messages.info(request, 'Операцію скасовано.')
            return redirect(_cancel_redirect(pending))

        email_ok = verify_email_code(pending, request.POST.get('email_code', ''))
        otp_ok, otp_error = verify_otp(request.user, request.POST.get('otp_token', ''))

        if not email_ok:
            messages.error(request, 'Невірний код з email.')
            return redirect('wallet_confirm')
        if not otp_ok:
            messages.error(request, otp_error)
            return redirect('wallet_confirm')

        try:
            _execute_pending(request, pending)
        except ValueError as exc:
            messages.error(request, str(exc))
            clear_pending_operation(request)
            return redirect(_cancel_redirect(pending))

        clear_pending_operation(request)
        messages.success(request, 'Операцію успішно підтверджено.')
        return redirect(_success_redirect(request, pending))

    return render(
        request,
        'wallet_confirm.html',
        {
            'pending': pending,
            'operation_label': operation_label,
            'operation_details': _operation_details(pending),
        },
    )


def _operation_label(pending: dict) -> str:
    if pending['type'] == 'transfer':
        return 'Підтвердження переказу криптовалюти'
    if pending['type'] == 'usd_withdraw':
        return 'Підтвердження виведення USD'
    return 'Підтвердження операції'


def _operation_details(pending: dict) -> list[tuple[str, str]]:
    if pending['type'] == 'transfer':
        return [
            ('Отримувач', pending['receiver_wallet_id']),
            ('Валюта', pending['currency']),
            ('Сума', pending['amount']),
        ]
    if pending['type'] == 'usd_withdraw':
        return [
            ('Операція', 'Виведення USD (1 USDT = 1 USD)'),
            ('Сума', f"{pending['amount']} USD"),
            ('Буде списано', f"{pending['amount']} USDT"),
        ]
    return []


def _cancel_redirect(pending: dict) -> str:
    if pending['type'] == 'usd_withdraw':
        return 'wallet_usd'
    return 'wallet'


def _success_redirect(request, pending: dict):
    if pending['type'] == 'transfer':
        transaction_id = request.session.pop('last_transfer_transaction_id', None)
        if transaction_id:
            return reverse('success', kwargs={'transaction_id': transaction_id})
        return reverse('wallet')
    return reverse('wallet_usd')


def _execute_pending(request, pending: dict):
    user = request.user
    if pending['type'] == 'transfer':
        amount = Decimal(pending['amount'])
        currency = pending['currency']
        sender_wallet = Wallet.objects.get(address=user.username)
        receiver_wallet = Wallet.objects.get(address=pending['receiver_wallet_id'])
        if sender_wallet.__dict__[currency.lower()] < amount:
            raise ValueError('Недостатньо коштів.')
        transaction = Transaction(
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=amount,
            currency=currency,
        )
        transaction.save_it()
        request.session['last_transfer_transaction_id'] = transaction.id
        return

    if pending['type'] == 'usd_withdraw':
        amount = Decimal(pending['amount'])
        wallet = _get_wallet(user)
        if wallet.usdt < amount:
            raise ValueError('Недостатньо USDT для виведення USD.')
        wallet.usdt -= amount
        wallet.save(update_fields=['usdt'])
        _log_usd_order(user, wallet, 'sell', amount)
        return

    raise ValueError('Невідомий тип операції.')


@login_required
def wallet_history(request):
    wallet = Wallet.objects.get(address=request.user.username)
    transactions = Transaction.objects.filter(
        Q(sender_wallet=wallet) | Q(receiver_wallet=wallet)
    )
    return render(request, 'wallet_history.html', {'transactions': transactions})


@login_required
def success(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        return render(request, 'success.html', {'transaction': transaction})
    except Transaction.DoesNotExist:
        return render(request, 'error.html', {'error_message': 'Transaction not found'})
