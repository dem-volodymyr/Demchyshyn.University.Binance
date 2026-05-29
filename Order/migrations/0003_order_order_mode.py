from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('Order', '0002_remove_order_product_remove_order_total_order_crypto_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_mode',
            field=models.CharField(
                choices=[('market', 'Market'), ('limit', 'Limit')],
                default='limit',
                max_length=10,
            ),
        ),
    ]
