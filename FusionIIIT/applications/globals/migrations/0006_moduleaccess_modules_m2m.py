from django.db import migrations, models


MODULE_DEFINITIONS = [
    ('program_and_curriculum', 'Program and Curriculum'),
    ('course_registration', 'Course Registration'),
    ('course_management', 'Course Management'),
    ('other_academics', 'Other Academics'),
    ('spacs', 'SPACS'),
    ('department', 'Department'),
    ('database', 'Database'),
    ('examinations', 'Examinations'),
    ('hr', 'HR'),
    ('iwd', 'IWD'),
    ('complaint_management', 'Complaint Management'),
    ('fts', 'File Tracking System'),
    ('purchase_and_store', 'Purchase and Store'),
    ('rspc', 'RSPC'),
    ('hostel_management', 'Hostel Management'),
    ('mess_management', 'Mess Management'),
    ('gymkhana', 'Gymkhana'),
    ('placement_cell', 'Placement Cell'),
    ('visitor_hostel', 'Visitor Hostel'),
    ('phc', 'PHC'),
]


def migrate_moduleaccess_to_m2m(apps, schema_editor):
    Module = apps.get_model('globals', 'Module')
    ModuleAccess = apps.get_model('globals', 'ModuleAccess')

    module_map = {}
    for key, label in MODULE_DEFINITIONS:
        module_obj, _ = Module.objects.get_or_create(key=key, defaults={'label': label})
        module_map[key] = module_obj

    for access in ModuleAccess.objects.all():
        enabled_keys = [
            key for key, _ in MODULE_DEFINITIONS
            if getattr(access, key, False)
        ]
        if enabled_keys:
            access.modules.add(*[module_map[key] for key in enabled_keys])


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0005_moduleaccess_database'),
    ]

    operations = [
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=64, unique=True)),
                ('label', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['label'],
            },
        ),
        migrations.AddField(
            model_name='moduleaccess',
            name='modules',
            field=models.ManyToManyField(blank=True, related_name='designation_accesses', to='globals.Module'),
        ),
        migrations.RunPython(migrate_moduleaccess_to_m2m, migrations.RunPython.noop),
        migrations.RemoveField(model_name='moduleaccess', name='complaint_management'),
        migrations.RemoveField(model_name='moduleaccess', name='course_management'),
        migrations.RemoveField(model_name='moduleaccess', name='course_registration'),
        migrations.RemoveField(model_name='moduleaccess', name='database'),
        migrations.RemoveField(model_name='moduleaccess', name='department'),
        migrations.RemoveField(model_name='moduleaccess', name='examinations'),
        migrations.RemoveField(model_name='moduleaccess', name='fts'),
        migrations.RemoveField(model_name='moduleaccess', name='gymkhana'),
        migrations.RemoveField(model_name='moduleaccess', name='hostel_management'),
        migrations.RemoveField(model_name='moduleaccess', name='hr'),
        migrations.RemoveField(model_name='moduleaccess', name='iwd'),
        migrations.RemoveField(model_name='moduleaccess', name='mess_management'),
        migrations.RemoveField(model_name='moduleaccess', name='other_academics'),
        migrations.RemoveField(model_name='moduleaccess', name='phc'),
        migrations.RemoveField(model_name='moduleaccess', name='placement_cell'),
        migrations.RemoveField(model_name='moduleaccess', name='program_and_curriculum'),
        migrations.RemoveField(model_name='moduleaccess', name='purchase_and_store'),
        migrations.RemoveField(model_name='moduleaccess', name='rspc'),
        migrations.RemoveField(model_name='moduleaccess', name='spacs'),
        migrations.RemoveField(model_name='moduleaccess', name='visitor_hostel'),
    ]
