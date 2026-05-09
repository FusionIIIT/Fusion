# Generated migration for UC-NT-01 and UC-NT-03 models

import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications_extension", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationEventType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("event_name", models.CharField(max_length=100)),
                ("module", models.CharField(
                    choices=[
                        ("Leave Module", "Leave Module"),
                        ("Placement Cell", "Placement Cell"),
                        ("Academic's Module", "Academic's Module"),
                        ("Central Mess", "Central Mess"),
                        ("Visitor's Hostel", "Visitor's Hostel"),
                        ("Healthcare Center", "Healthcare Center"),
                        ("File Tracking", "File Tracking"),
                        ("Scholarship Portal", "Scholarship Portal"),
                        ("Complaint System", "Complaint System"),
                        ("Office of Dean PnD Module", "Office of Dean PnD Module"),
                        ("Office Module", "Office Module"),
                        ("Gymkhana Module", "Gymkhana Module"),
                        ("Assistantship Request", "Assistantship Request"),
                        ("department", "Department"),
                        ("Research Procedures", "Research Procedures"),
                    ],
                    max_length=60,
                )),
                ("default_priority", models.CharField(
                    choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
                    default="medium",
                    max_length=10,
                )),
                ("description", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("registered_by", models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="registered_event_types",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "verbose_name": "Notification Event Type",
                "verbose_name_plural": "Notification Event Types",
                "ordering": ["module", "event_name"],
                "unique_together": {("event_name", "module")},
            },
        ),
        migrations.CreateModel(
            name="Announcement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("message", models.TextField()),
                ("audience_type", models.CharField(
                    choices=[
                        ("all", "All Users"),
                        ("students", "All Students"),
                        ("faculty", "All Faculty"),
                        ("staff", "All Staff"),
                        ("group", "Specific Group"),
                    ],
                    default="all",
                    max_length=20,
                )),
                ("audience_value", models.CharField(blank=True, default="", max_length=100)),
                ("expiry_date", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("sender", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="sent_announcements",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "verbose_name": "Announcement",
                "verbose_name_plural": "Announcements",
                "ordering": ["-created_at"],
            },
        ),
    ]
