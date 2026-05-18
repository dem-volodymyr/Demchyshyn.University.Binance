from decimal import Decimal

from wallet.models import Wallet, Transaction

from autotrading.config import DEFAULT_TRADABLE_PAIRS


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
            balance = getattr(wallet, field)
            if balance < quantity:
                raise InsufficientBalanceError(
                    f'Insufficient {crypto} balance: have {balance}, need {quantity}'
                )
            setattr(wallet, field, balance - quantity)
            wallet.usdt += usdt_amount
            wallet.save()
            Transaction.objects.create(
                sender_wallet=wallet,
                receiver_wallet=wallet,
                amount=quantity,
                currency=crypto,
            )
        elif order_type == 'buy':
            if wallet.usdt < usdt_amount:
                raise InsufficientBalanceError(
                    f'Insufficient USDT: have {wallet.usdt}, need {usdt_amount}'
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

        return {
            'order_type': order_type,
            'crypto': crypto,
            'quantity': quantity,
            'price': price,
            'usdt_amount': usdt_amount,
        }
