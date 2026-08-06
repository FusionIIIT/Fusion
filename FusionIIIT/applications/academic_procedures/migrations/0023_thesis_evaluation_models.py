# Manually authored migration — 0023_thesis_evaluation_models
# Creates ThesisEvaluation and ProgressSeminarEvaluation tables.
# Generated to match models added in academic_procedures/models.py.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic_procedures', '0022_thesis_registration_add_credits'),
        ('globals', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ------------------------------------------------------------------ #
        # ThesisEvaluation                                                    #
        # ------------------------------------------------------------------ #
        migrations.CreateModel(
            name='ThesisEvaluation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('block_number', models.PositiveSmallIntegerField(
                    help_text='Sequential block index starting at 1 (max = registration.credits ÷ 3)',
                )),
                ('grade', models.CharField(
                    blank=True, choices=[('S', 'Satisfactory'), ('X', 'Unsatisfactory')],
                    max_length=1, null=True,
                )),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('remarks', models.TextField(blank=True)),
                ('verified', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('announced', models.BooleanField(default=False)),
                ('announced_at', models.DateTimeField(blank=True, null=True)),
                ('registration', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluations',
                    to='academic_procedures.ThesisRegistration',
                )),
                ('submitted_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='thesis_grades_submitted',
                    to='globals.Faculty',
                )),
                ('verified_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='thesis_grades_verified',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'ThesisEvaluation',
                'ordering': ['registration', 'block_number'],
                'unique_together': {('registration', 'block_number')},
            },
        ),
        # ------------------------------------------------------------------ #
        # ProgressSeminarEvaluation                                           #
        # ------------------------------------------------------------------ #
        migrations.CreateModel(
            name='ProgressSeminarEvaluation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grade', models.CharField(
                    blank=True, choices=[('S', 'Satisfactory'), ('X', 'Unsatisfactory')],
                    max_length=1, null=True,
                )),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('remarks', models.TextField(blank=True)),
                ('verified', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('announced', models.BooleanField(default=False)),
                ('announced_at', models.DateTimeField(blank=True, null=True)),
                ('registration', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluation',
                    to='academic_procedures.ProgressSeminarRegistration',
                )),
                ('submitted_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='seminar_grades_submitted',
                    to='globals.Faculty',
                )),
                ('verified_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='seminar_grades_verified',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'ProgressSeminarEvaluation',
            },
        ),
    ]
