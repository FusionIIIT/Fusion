from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("placement_cell", "0009_application_detail_features"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlacementAppeal",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.TextField(max_length=2000)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("reviewed", "Reviewed"), ("accepted", "Accepted"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("response", models.TextField(blank=True, default="", max_length=2000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("placement_status", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="placement_cell.PlacementStatus")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="academic_information.Student")),
            ],
            options={
                "unique_together": {("student", "placement_status")},
            },
        ),
    ]
