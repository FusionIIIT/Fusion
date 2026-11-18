"""examination takes over Student_grades from online_cms.

Only Django's record of which app owns the model changes. The grades stay
in the same table (online_cms_student_grades) with every row, column and
index as they are; no table is created, copied or altered on a database
that already has it.

online_cms/0007 removed the model from online_cms's side, also without
touching the table. online_cms itself has since been removed, so this
migration no longer depends on it: on a new database it creates the table
itself (create_table_if_missing), and examination/0006 then renames it.
"""

from django.db import migrations, models
import django.db.models.deletion


def create_table_if_missing(apps, schema_editor):
    """Create the grades table only where it does not exist yet.

    On every existing database online_cms already created it, so this does
    nothing there. It is for a brand-new database once online_cms is gone.
    """
    Student_grades = apps.get_model('examination', 'Student_grades')
    with schema_editor.connection.cursor() as cursor:
        tables = schema_editor.connection.introspection.table_names(cursor)
    if Student_grades._meta.db_table not in tables:
        schema_editor.create_model(Student_grades)


def move_content_type(apps, schema_editor):
    """Relabel the model's content type, so its permissions carry over."""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    if not ContentType.objects.filter(app_label='examination', model='student_grades').exists():
        ContentType.objects.filter(app_label='online_cms', model='student_grades').update(app_label='examination')


def move_content_type_back(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    if not ContentType.objects.filter(app_label='online_cms', model='student_grades').exists():
        ContentType.objects.filter(app_label='examination', model='student_grades').update(app_label='online_cms')


class Migration(migrations.Migration):

    dependencies = [
        ('examination', '0004_auto_20260625_1637'),
        ('programme_curriculum', '0058_teaching_credit_versions'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Student_grades',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('semester', models.IntegerField(default=1)),
                        ('year', models.IntegerField(default=2016)),
                        ('roll_no', models.TextField(max_length=2000)),
                        ('grade', models.TextField(max_length=2000)),
                        ('batch', models.IntegerField(default=2021)),
                        ('remarks', models.CharField(max_length=500, null=True)),
                        ('verified', models.BooleanField(default=False)),
                        ('reSubmit', models.BooleanField(default=True)),
                        ('academic_year', models.CharField(max_length=9, null=True)),
                        ('semester_type', models.CharField(choices=[('Odd Semester', 'Odd Semester'), ('Even Semester', 'Even Semester'), ('Summer Semester', 'Summer Semester')], max_length=20, null=True)),
                        ('course_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.course')),
                        ('course_instructor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='programme_curriculum.courseinstructor')),
                    ],
                    options={
                        'db_table': 'online_cms_student_grades',
                    },
                ),
                migrations.AddIndex(
                    model_name='student_grades',
                    index=models.Index(fields=['roll_no'], name='student_grades_roll_no_idx'),
                ),
            ],
            database_operations=[],
        ),
        migrations.RunPython(create_table_if_missing, migrations.RunPython.noop),
        migrations.RunPython(move_content_type, move_content_type_back),
    ]
