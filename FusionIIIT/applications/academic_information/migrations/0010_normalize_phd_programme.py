from django.db import migrations


def normalize_phd_programme(apps, schema_editor):
    Student = apps.get_model('academic_information', 'Student')
    Student.objects.filter(
        programme__in=('Ph.D', 'Ph.D.', 'PHD', 'phd')
    ).update(programme='PhD')


class Migration(migrations.Migration):

    dependencies = [
        ('academic_information', '0009_alphanumeric_sections'),
    ]

    operations = [
        migrations.RunPython(normalize_phd_programme, migrations.RunPython.noop),
    ]
