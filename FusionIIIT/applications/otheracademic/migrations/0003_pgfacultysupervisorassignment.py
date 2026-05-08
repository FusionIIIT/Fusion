from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("otheracademic", "0002_pgtaassignment"),
    ]

    operations = [
        migrations.CreateModel(
            name="PGFacultySupervisorAssignment",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="pg_faculty_supervisor_assigned_by",
                        to="auth.user",
                    ),
                ),
                (
                    "faculty_supervisor",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="auth.user"),
                ),
                (
                    "pg_student",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="globals.extrainfo"),
                ),
            ],
            options={"db_table": "PGFacultySupervisorAssignment"},
        ),
    ]
