import secrets
import string

from django.db import migrations, models


def reissue_old_format_codes(apps, schema_editor):
    """Rewrite pre-8-digit codes so they fit the narrowed column.

    The first release generated grouped alphanumeric codes (STC-KYDP-87FT-DZ9F,
    18 chars). Any of those still in the table would break the AlterField below,
    so they are reissued as 8-digit codes here. An admin who already sent one out
    has to send the new number — hence the deactivation, so a stale code can
    never authorise a withdrawal.
    """
    WithdrawalAccessCode = apps.get_model('transactions', 'WithdrawalAccessCode')
    stale = WithdrawalAccessCode.objects.exclude(code__regex=r'^\d{8}$')

    taken = set(WithdrawalAccessCode.objects.values_list('code', flat=True))
    for obj in stale:
        while True:
            fresh = ''.join(secrets.choice(string.digits) for _ in range(8))
            if fresh not in taken:
                break
        taken.add(fresh)
        obj.code = fresh
        obj.is_active = False
        obj.save(update_fields=['code', 'is_active'])


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0006_withdrawalaccesscode'),
    ]

    operations = [
        migrations.RunPython(reissue_old_format_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='withdrawalaccesscode',
            name='code',
            field=models.CharField(db_index=True, max_length=16, unique=True),
        ),
    ]
