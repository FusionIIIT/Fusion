from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('programme_curriculum', '0032_auto_20260210_1820'),
        ('academic_information', '0002_auto_20260210_1820'),
        ('academic_procedures', '0018_auto_20260106_1355'),
    ]

    operations = [
        migrations.CreateModel(
            name='SwayamReplacementRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('academic_year', models.CharField(max_length=9)),
                ('semester_type', models.CharField(choices=[('Odd Semester', 'Odd Semester'), ('Even Semester', 'Even Semester'), ('Summer Semester', 'Summer Semester')], max_length=20)),
                ('request_type', models.CharField(choices=[('Extra_Credits', 'Extra Credits'), ('Swayam_Replace', 'Swayam Replace')], default='Extra_Credits', max_length=20)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending', max_length=20)),
                ('is_current_semester', models.BooleanField(default=False, help_text='True if the old course is an SW course in an OE slot in the current semester (DROP + REGISTER on approval)')),
                ('submitted_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('course_slot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='swayam_course_slot_reqs', to='programme_curriculum.courseslot')),
                ('new_course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='swayam_new_course_reqs', to='programme_curriculum.course')),
                ('new_course_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='swayam_new_course_slot_reqs', to='programme_curriculum.courseslot')),
                ('old_course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='swayam_old_course_reqs', to='programme_curriculum.course')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.semester')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'academic_procedures_swayamreplacementrequest',
                'ordering': ['-submitted_at'],
            },
        ),
    ]
