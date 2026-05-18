import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoPosition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=10)),
                ('quantity', models.DecimalField(decimal_places=8, max_digits=18)),
                ('entry_price', models.DecimalField(decimal_places=8, max_digits=18)),
                ('stop_loss', models.DecimalField(decimal_places=8, max_digits=18)),
                ('take_profit', models.DecimalField(decimal_places=8, max_digits=18)),
                ('is_open', models.BooleanField(default=True)),
                ('opened_at', models.DateTimeField(auto_now_add=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auto_positions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-opened_at'],
            },
        ),
        migrations.CreateModel(
            name='AutoTradeLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=10)),
                ('signal', models.CharField(choices=[('BUY', 'Buy'), ('SELL', 'Sell'), ('HOLD', 'Hold')], max_length=4)),
                ('predicted_price', models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
                ('market_price', models.DecimalField(decimal_places=8, max_digits=18)),
                ('quantity', models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
                ('action_taken', models.CharField(max_length=64)),
                ('reason', models.CharField(blank=True, default='', max_length=64)),
                ('error_message', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auto_trade_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
