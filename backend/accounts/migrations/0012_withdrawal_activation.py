from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_user_two_factor_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='activation_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='activation_code',
            field=models.CharField(blank=True, help_text="Issued by admin (action 'Generate activation code'). Give it to the user.", max_length=12),
        ),
        migrations.AddField(
            model_name='user',
            name='withdrawals_activated',
            field=models.BooleanField(default=False),
        ),
    ]
