from django.db import models
from django.contrib.auth.models import User
from wallet.models import Wallet


class Referral(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    referral_code = models.CharField(max_length=20, unique=True)
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='referrals')


class ReferralReward(models.Model):
    referral_wallet = models.ForeignKey(Wallet, related_name='referral_wallet', on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)

    def add_points(self, *args, **kwargs):
        referral_wallet = self.referral_wallet
        referral_wallet.usdt += self.amount
        referral_wallet.save()
        super().save(*args, **kwargs)
