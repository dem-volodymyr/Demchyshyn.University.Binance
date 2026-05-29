from decimal import Decimal

from django.contrib.auth.models import User

from wallet.models import Wallet, Transaction

from autotrading.config import DEFAULT_TRADABLE_PAIRS
from Order.models import Order


class InsufficientBalanceError(Exception):
    pass


class MarketPriceUnavailableError(Exception):
    pass


class OrderExecutor:
    """Executes market orders against the internal wallet (same rules as Order/views.execute_order)."""

    WALLET_FIELDS = {s.lower() for s in DEFAULT_TRADABLE_PAIRS}

    def execute_market_order(
        self,
        *,
        user: User | None = None,
        wallet: Wallet,
        order_type: str,
        crypto: str,
        quantity: Decimal,
        price: Decimal,
    ) -> dict:
        crypto = crypto.upper()
        field = crypto.lower()
        if field not in self.WALLET_FIELDS:
            raise ValueError(f'Crypto {crypto} is not supported for auto trading')

        usdt_amount = quantity * price
        order_type = order_type.lower()

        if order_type == 'sell':
            balance = wallet.get_available_balance(crypto)
            if balance < quantity:
                raise InsufficientBalanceError(
                    f'Insufficient {crypto} balance: have {balance}, need {quantity}'
                )
            setattr(wallet, field, getattr(wallet, field) - quantity)
            wallet.usdt += usdt_amount
            wallet.save()
            Transaction.objects.create(
                sender_wallet=wallet,
                receiver_wallet=wallet,
                amount=quantity,
                currency=crypto,
            )
        elif order_type == 'buy':
            available_usdt = wallet.get_available_balance('USDT')
            if available_usdt < usdt_amount:
                raise InsufficientBalanceError(
                    f'Insufficient available USDT: have {available_usdt}, need {usdt_amount}'
                )
            wallet.usdt -= usdt_amount
            setattr(wallet, field, getattr(wallet, field) + quantity)
            wallet.save()
            Transaction.objects.create(
                sender_wallet=wallet,
                receiver_wallet=wallet,
                amount=quantity,
                currency=crypto,
            )
        else:
            raise ValueError(f'Invalid order_type: {order_type}')

        if user is not None:
            Order.objects.create(
                user=user,
                wallet=wallet,
                order_type=order_type,
                order_mode=Order.ORDER_MODE_MARKET,
                crypto=crypto,
                quantity=quantity,
                price=price,
                usdt_amount=usdt_amount,
                status='executed',
            )

        return {
            'order_type': order_type,
            'crypto': crypto,
            'quantity': quantity,
            'price': price,
            'usdt_amount': usdt_amount,
        }
