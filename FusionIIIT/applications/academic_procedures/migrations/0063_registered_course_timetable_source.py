"""Allow timetable slots generated from modern registered course offerings."""

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic_procedures', '0062_timetable_version_semester_number'),
        ('programme_curriculum', '0057_batch_unique_with_curriculum'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetableversion',
            name='course_source',
            field=models.CharField(
                choices=[
                    ('legacy', 'Legacy floated curriculum'),
                    ('registered', 'Registered term courses'),
                ],
                default='legacy',
                max_length=15,
            ),
        ),
        migrations.AlterField(
            model_name='timetableslot',
            name='curriculum',
            field=models.ForeignKey(
                blank=True,
                db_column='curriculum_id',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='timetable_slots',
                to='academic_information.curriculum',
            ),
        ),
        migrations.AlterField(
            model_name='timetableslot',
            name='classroom',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='timetable_slots',
                to='academic_procedures.classroom',
            ),
        ),
        migrations.AddField(
            model_name='timetableslot',
            name='course',
            field=models.ForeignKey(
                blank=True,
                db_column='modern_course_id',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='timetable_slots',
                to='programme_curriculum.course',
            ),
        ),
        migrations.AddField(
            model_name='timetableslot',
            name='course_instructor',
            field=models.ForeignKey(
                blank=True,
                db_column='modern_course_instructor_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='timetable_slots',
                to='programme_curriculum.courseinstructor',
            ),
        ),
        migrations.AddField(
            model_name='timetableslot',
            name='room_label',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Display-only room for unallocated facilities such as LAB',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='timetableslot',
            name='enrollment_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='timetableslot',
            name='student_ids',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=20),
                blank=True,
                default=list,
                help_text='Students represented by a registered-course timetable slot',
                size=None,
            ),
        ),
    ]
