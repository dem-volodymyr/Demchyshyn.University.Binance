from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cryptocurrency',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='cryptocurrency',
            name='symbol',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
