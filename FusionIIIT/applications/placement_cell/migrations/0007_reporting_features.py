from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("placement_cell", "0006_alumni_features"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlacementReportSchedule",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("report_type", models.CharField(choices=[("batch", "Batch Summary"), ("company", "Company Summary"), ("branch", "Branch Summary"), ("custom", "Custom Report")], default="custom", max_length=20)),
                ("frequency", models.CharField(choices=[("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")], default="weekly", max_length=20)),
                ("export_format", models.CharField(choices=[("excel", "Excel"), ("pdf", "PDF")], default="excel", max_length=20)),
                ("filters", models.JSONField(blank=True, default=dict)),
                ("recipients", models.TextField(blank=True, default="", max_length=500)),
                ("is_active", models.BooleanField(default=True)),
                ("last_run_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-updated_at", "-id"),
            },
        ),
    ]
