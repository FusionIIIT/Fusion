from django.db import migrations


CENTRAL_MESS_DESIGNATIONS = [
    'mess_committee',
    'mess_warden',
    'mess_convener',
    'mess_manager',
    'mess_committee_mess1',
    'mess_committee_mess2',
    'mess_convener_mess1',
    'mess_convener_mess2',
]


def remove_central_mess_designations(apps, schema_editor):
    alias = schema_editor.connection.alias
    designation = apps.get_model('globals', 'Designation')
    module_access = apps.get_model('globals', 'ModuleAccess')

    module_access.objects.using(alias).filter(
        designation__in=CENTRAL_MESS_DESIGNATIONS
    ).delete()
    designation.objects.using(alias).filter(
        name__in=CENTRAL_MESS_DESIGNATIONS
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0015_remove_moduleaccess_mess_management'),
    ]

    operations = [
        migrations.RunPython(remove_central_mess_designations),
    ]
