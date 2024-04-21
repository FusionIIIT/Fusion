# Generated by Django 3.1.5 on 2024-04-21 17:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academic_information', '0002_auto_20240421_1716'),
        ('programme_curriculum', '0002_auto_20240421_1716'),
        ('academic_procedures', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assistantshipclaim',
            name='year',
            field=models.IntegerField(choices=[(2024, 2024), (2023, 2023)]),
        ),
        migrations.AlterField(
            model_name='course_registration',
            name='working_year',
            field=models.IntegerField(blank=True, choices=[(2024, 2024), (2023, 2023)], null=True),
        ),
        migrations.AlterField(
            model_name='finalregistrations',
            name='batch',
            field=models.IntegerField(default=2024),
        ),
        migrations.AlterField(
            model_name='messdue',
            name='year',
            field=models.IntegerField(choices=[(2024, 2024), (2023, 2023)]),
        ),
        migrations.AlterField(
            model_name='register',
            name='year',
            field=models.IntegerField(default=2024),
        ),
        migrations.CreateModel(
            name='backlog_course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_summer_course', models.BooleanField(default=False)),
                ('course_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.course')),
                ('semester_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.semester')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
        ),
    ]