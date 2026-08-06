from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("placement_cell", "0008_round_datetime_conflicts"),
    ]

    operations = [
        migrations.AddField(
            model_name="placementapplication",
            name="remarks",
            field=models.TextField(blank=True, default="", max_length=1000),
        ),
        migrations.AddField(
            model_name="placementapplication",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="placementapplication",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("shortlisted", "Shortlisted"),
                    ("interview_scheduled", "Interview Scheduled"),
                    ("interview_completed", "Interview Completed"),
                    ("offer_released", "Offer Released"),
                    ("accept", "Accept"),
                    ("reject", "Reject"),
                    ("withdrawn", "Withdrawn"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="PlacementApplicationTimeline",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stage", models.CharField(default="", max_length=100)),
                ("remarks", models.TextField(blank=True, default="", max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="timeline_entries", to="placement_cell.PlacementApplication")),
            ],
            options={"ordering": ("created_at", "id")},
        ),
        migrations.CreateModel(
            name="PlacementInterviewSchedule",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("round_no", models.IntegerField(default=1)),
                ("title", models.CharField(blank=True, default="", max_length=100)),
                ("scheduled_at", models.DateTimeField()),
                ("end_datetime", models.DateTimeField(blank=True, null=True)),
                ("mode", models.CharField(blank=True, default="", max_length=30)),
                ("location", models.CharField(blank=True, default="", max_length=255)),
                ("meeting_link", models.CharField(blank=True, default="", max_length=255)),
                ("remarks", models.TextField(blank=True, default="", max_length=1000)),
                ("outcome", models.CharField(choices=[("pending", "Pending"), ("passed", "Passed"), ("failed", "Failed"), ("selected", "Selected")], default="pending", max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interview_schedules", to="placement_cell.PlacementApplication")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-scheduled_at", "-id")},
        ),
    ]
