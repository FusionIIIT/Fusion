from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('academic_procedures', '0016_coursedroprequest'),
        ('programme_curriculum', '0031_add_curriculum_options_to_batch'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseAddRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('academic_year', models.CharField(max_length=9)),
                ('semester_type', models.CharField(choices=[('Odd Semester', 'Odd Semester'), ('Even Semester', 'Even Semester'), ('Summer Semester', 'Summer Semester')], max_length=20)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending', max_length=20)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='add_course_reqs', to='programme_curriculum.Course')),
                ('course_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.CourseSlot')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.Student')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='courseaddrequest',
            unique_together={('student', 'course_slot', 'academic_year', 'semester_type')},
        ),
    ]
