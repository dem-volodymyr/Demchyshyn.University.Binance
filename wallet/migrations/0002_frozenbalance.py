from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('wallet', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FrozenBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(max_length=10)),
                ('amount', models.DecimalField(decimal_places=8, default=0, max_digits=18)),
                ('reason', models.CharField(choices=[('order', 'Order')], default='order', max_length=20)),
                ('reference', models.CharField(max_length=64)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='frozen_balances', to='wallet.wallet')),
            ],
            options={
                'unique_together': {('wallet', 'currency', 'reason', 'reference')},
            },
        ),
    ]
