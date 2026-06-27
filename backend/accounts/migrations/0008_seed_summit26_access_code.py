from django.db import migrations


def create_default_code(apps, schema_editor):
    AccessCode = apps.get_model('accounts', 'AccessCode')
    AccessCode.objects.get_or_create(
        code='SUMMIT26',
        defaults={'label': 'Default launch access code', 'is_active': True},
    )


def remove_default_code(apps, schema_editor):
    AccessCode = apps.get_model('accounts', 'AccessCode')
    AccessCode.objects.filter(code='SUMMIT26').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_user_course_access_unlocked_and_more'),
    ]

    operations = [
        migrations.RunPython(create_default_code, remove_default_code),
    ]
