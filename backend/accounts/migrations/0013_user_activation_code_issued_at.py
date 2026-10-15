from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_withdrawal_activation'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='activation_code_issued_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
