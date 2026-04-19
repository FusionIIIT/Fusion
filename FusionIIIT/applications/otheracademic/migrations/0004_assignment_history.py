from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("otheracademic", "0003_pgfacultysupervisorassignment"),
    ]

    operations = [
        migrations.CreateModel(
            name="PGTAAssignmentHistory",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="pg_ta_assignment_history_assigned_by",
                        to="auth.user",
                    ),
                ),
                (
                    "pg_student",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="globals.extrainfo"),
                ),
                (
                    "subject",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="programme_curriculum.course"),
                ),
            ],
            options={"db_table": "PGTAAssignmentHistory"},
        ),
        migrations.CreateModel(
            name="PGFacultySupervisorAssignmentHistory",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="pg_faculty_supervisor_assignment_history_assigned_by",
                        to="auth.user",
                    ),
                ),
                (
                    "faculty_supervisor",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="auth.user"),
                ),
                (
                    "pg_student",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="globals.extrainfo"),
                ),
            ],
            options={"db_table": "PGFacultySupervisorAssignmentHistory"},
        ),
    ]
