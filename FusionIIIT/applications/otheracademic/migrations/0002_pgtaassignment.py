from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("otheracademic", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PGTAAssignment",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="auth.user"),
                ),
                (
                    "pg_student",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="globals.extrainfo"),
                ),
                (
                    "subject",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="programme_curriculum.course"),
                ),
            ],
            options={"db_table": "PGTAAssignment"},
        ),
    ]
