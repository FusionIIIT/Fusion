"""globals takes over the student profile models from placement_cell.

Skill, Has, Education, Experience, Project, Course, Publication, Patent,
Achievement and StudentBankDetails: the records the dashboard profile shows
and edits through globals' /api/profile endpoints.

Only Django's record of which app owns these models changes. The ten tables
keep their placement_cell names and every row, column, index and constraint
as they are; nothing is created, copied or altered on a database that
already has them. Renaming the tables is a separate change.

placement_cell/0017 removes them from placement_cell's side, also without
touching the tables.
"""

import datetime
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


PROFILE_MODELS = ['Skill', 'StudentBankDetails', 'Publication', 'Project', 'Patent',
                  'Experience', 'Education', 'Course', 'Achievement', 'Has']


def create_tables_if_missing(apps, schema_editor):
    """Create a profile table only where it does not exist yet.

    Every existing database already has them (placement_cell created them),
    so this does nothing there. It is for a brand-new database once
    placement_cell is gone. Skill comes before Has, which points at it.
    """
    with schema_editor.connection.cursor() as cursor:
        tables = set(schema_editor.connection.introspection.table_names(cursor))
    for name in PROFILE_MODELS:
        model = apps.get_model('globals', name)
        if model._meta.db_table not in tables:
            schema_editor.create_model(model)


def move_content_types(apps, schema_editor):
    """Relabel the models' content types, so their permissions carry over."""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    for name in PROFILE_MODELS:
        model = name.lower()
        if not ContentType.objects.filter(app_label='globals', model=model).exists():
            ContentType.objects.filter(app_label='placement_cell', model=model).update(app_label='globals')


def move_content_types_back(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    for name in PROFILE_MODELS:
        model = name.lower()
        if not ContentType.objects.filter(app_label='placement_cell', model=model).exists():
            ContentType.objects.filter(app_label='globals', model=model).update(app_label='placement_cell')


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0012_acad_role_module_access'),
        ('academic_information', '0010_normalize_phd_programme'),
        ('placement_cell', '0016_studentbankdetails'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Skill',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('skill', models.CharField(default='', max_length=30)),
                    ],
                    options={
                        'db_table': 'placement_cell_skill',
                    },
                ),
                migrations.CreateModel(
                    name='StudentBankDetails',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('account_holder_name', models.CharField(default='', max_length=200)),
                        ('bank_name', models.CharField(default='', max_length=200)),
                        ('branch_name', models.CharField(blank=True, default='', max_length=200)),
                        ('account_number', models.CharField(default='', max_length=30)),
                        ('ifsc_code', models.CharField(default='', max_length=20)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('unique_id', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bank_details', to='academic_information.student')),
                    ],
                    options={
                        'db_table': 'placement_cell_studentbankdetails',
                    },
                ),
                migrations.CreateModel(
                    name='Publication',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('publication_title', models.CharField(default='', max_length=100)),
                        ('description', models.TextField(blank=True, default='', max_length=250, null=True)),
                        ('publisher', models.TextField(default='', max_length=250)),
                        ('publication_date', models.DateField(default=datetime.date.today, verbose_name='Date')),
                        ('unique_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                    ],
                    options={
                        'db_table': 'placement_cell_publication',
                    },
                ),
                migrations.CreateModel(
                    name='Project',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('project_name', models.CharField(default='', max_length=50)),
                        ('project_status', models.CharField(choices=[('ONGOING', 'Ongoing'), ('COMPLETED', 'Completed')], default='COMPLETED', max_length=20)),
                        ('summary', models.TextField(blank=True, default='', max_length=1000, null=True)),
                        ('project_link', models.CharField(blank=True, default='', max_length=200, null=True)),
                        ('sdate', models.DateField(default=datetime.date.today, verbose_name='Date')),
                        ('edate', models.DateField(blank=True, null=True)),
                        ('unique_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                    ],
                    options={
                        'db_table': 'placement_cell_project',
                    },
                ),
                migrations.CreateModel(
                    name='Patent',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('patent_name', models.CharField(default='', max_length=100)),
                        ('description', models.TextField(blank=True, default='', max_length=250, null=True)),
                        ('patent_office', models.TextField(default='', max_length=250)),
                        ('patent_date', models.DateField()),
                        ('unique_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                    ],
                    options={
                        'db_table': 'placement_cell_patent',
                    },
                ),
                migrations.CreateModel(
                    name='Experience',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('title', models.CharField(default='', max_length=100)),
                        ('status', models.CharField(choices=[('ONGOING', 'Ongoing'), ('COMPLETED', 'Completed')], default='COMPLETED', max_length=20)),
                        ('description', models.TextField(blank=True, default='', max_length=500, null=True)),
                        ('company', models.CharField(default='', max_length=200)),
                        ('location', models.CharField(default='', max_length=200)),
                        ('sdate', models.DateField(default=datetime.date.today, verbose_name='Date')),
                        ('edate', models.DateField(blank=True, null=True)),
                        ('unique_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                    ],
                    options={
                        'db_table': 'placement_cell_experience',
                    },
                ),
                migrations.CreateModel(
                    name='Education',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('degree', models.CharField(default='', max_length=40)),
                        ('grade', models.CharField(default='', max_length=10)),
                        ('institute', models.TextField(default='', max_length=250)),
                        ('stream', models.CharField(blank=True, default='', max_length=150, null=True)),
                        ('sdate', models.DateField(default=datetime.date.today, verbose_name='Date')),
                        ('edate', models.DateField(blank=True, null=True)),
                        ('unique_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                    ],
                    options={
                        'db_table': 'placement_cell_education',
                    },
                ),
                migrations.CreateModel(
                    name='Course',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('course_name', models.CharField(default='', max_length=100)),
                        ('description', models.TextField(blank=True, default='', max_length=250, null=True)),
                        ('license_no', models.CharField(blank=True, default='', max_length=100, null=True)),
                        ('sdate', models.DateField(default=datetime.date.today, verbose_name='Date')),
                        ('edate', models.DateField(blank=True, null=True)),
                        ('unique_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                    ],
                    options={
                        'db_table': 'placement_cell_course',
                    },
                ),
                migrations.CreateModel(
                    name='Achievement',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('achievement', models.CharField(default='', max_length=100)),
                        ('achievement_type', models.CharField(choices=[('EDUCATIONAL', 'Educational'), ('OTHER', 'Other')], default='OTHER', max_length=20)),
                        ('description', models.TextField(blank=True, default='', max_length=1000, null=True)),
                        ('issuer', models.CharField(default='', max_length=200)),
                        ('date_earned', models.DateField(default=datetime.date.today, verbose_name='Date')),
                        ('unique_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                    ],
                    options={
                        'db_table': 'placement_cell_achievement',
                    },
                ),
                migrations.CreateModel(
                    name='Has',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('skill_rating', models.IntegerField(default=80, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                        ('skill_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='globals.skill')),
                        ('unique_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                    ],
                    options={
                        'db_table': 'placement_cell_has',
                        'unique_together': {('skill_id', 'unique_id')},
                    },
                ),
            ],
            database_operations=[],
        ),
        migrations.RunPython(create_tables_if_missing, migrations.RunPython.noop),
        migrations.RunPython(move_content_types, move_content_types_back),
    ]
