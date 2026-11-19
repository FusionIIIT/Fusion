"""Store the curriculum semester represented by each timetable version."""

from django.db import migrations, models


def backfill_semester_number(apps, schema_editor):
    TimetableSlot = apps.get_model('academic_procedures', 'TimetableSlot')
    TimetableVersion = apps.get_model('academic_procedures', 'TimetableVersion')

    for version in TimetableVersion.objects.all().iterator():
        semesters = list(
            TimetableSlot.objects.filter(version_id=version.pk)
            .values_list('curriculum__sem', flat=True)
            .distinct()[:2]
        )
        if len(semesters) == 1 and semesters[0] in range(1, 9):
            version.semester_number = semesters[0]
            version.save(update_fields=['semester_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('academic_procedures', '0061_timetable_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetableversion',
            name='semester_number',
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, 'Semester 1'),
                    (2, 'Semester 2'),
                    (3, 'Semester 3'),
                    (4, 'Semester 4'),
                    (5, 'Semester 5'),
                    (6, 'Semester 6'),
                    (7, 'Semester 7'),
                    (8, 'Semester 8'),
                ],
                help_text='Curriculum semester scheduled by this run (1-8)',
                null=True,
            ),
        ),
        migrations.RunPython(backfill_semester_number, migrations.RunPython.noop),
    ]
