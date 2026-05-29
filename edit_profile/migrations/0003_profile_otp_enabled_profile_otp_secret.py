from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edit_profile', '0002_alter_profile_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='otp_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='otp_secret',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
