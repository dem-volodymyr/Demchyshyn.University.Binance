# models.py
from django.db import models


class CryptoCurrency(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class PriceData(models.Model):
    cryptocurrency = models.ForeignKey(CryptoCurrency, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    price = models.DecimalField(max_digits=20, decimal_places=10)

    def __str__(self):
        return f"{self.cryptocurrency} - {self.timestamp}"
