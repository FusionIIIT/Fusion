from django.db import migrations

from applications.scholarships.models_assistantship import STAFF_DISCIPLINES


def add_roles(apps, schema_editor):
    Designation = apps.get_model('globals', 'Designation')
    for role, (_code, disciplines) in STAFF_DISCIPLINES.items():
        Designation.objects.get_or_create(
            name=role,
            defaults={'full_name': '{} Office Staff'.format(disciplines[0]),
                      'type': 'administrative'},
        )


def drop_roles(apps, schema_editor):
    Designation = apps.get_model('globals', 'Designation')
    Designation.objects.filter(name__in=list(STAFF_DISCIPLINES)).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('scholarships', '0004_assistantship'),
        ('globals', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_roles, drop_roles),
    ]
