from django.db import models


class Cryptocurrency(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10, unique=True)
    market_cap = models.FloatField(null=True, blank=True)
    market_cap_rank = models.IntegerField(null=True, blank=True)
    total_volume = models.FloatField(null=True, blank=True)
    high_24h = models.FloatField(null=True, blank=True)
    low_24h = models.FloatField(null=True, blank=True)
    price_change_24h = models.FloatField(null=True, blank=True)
    max_supply = models.FloatField(null=True, blank=True)
    total_supply = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    image = models.CharField(max_length=1600, null=True, blank=True)
    circulating_supply = models.CharField(max_length=1600, null=True, blank=True)


class CryptocurrencyPrice(models.Model):
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    price = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']  # Order by timestamp in descending order
        get_latest_by = 'timestamp'  # Specify the field for get_latest_by

    @classmethod
    def latest(cls):
        # Custom method to get the latest record
        return cls.objects.latest()

    @classmethod
    def earliest(cls):
        # Custom method to get the earliest record
        return cls.objects.earliest()
