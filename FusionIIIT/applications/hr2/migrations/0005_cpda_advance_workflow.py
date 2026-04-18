from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr2", "0004_add_hr2_leavebalance_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="cpdaadvanceform",
            name="workflow_status",
            field=models.CharField(
                choices=[
                    ("submitted", "Submitted"),
                    ("hod_verified", "Verified by HOD"),
                    ("hod_not_verified", "Not verified by HOD"),
                    ("forwarded_to_director", "Forwarded to Director"),
                    ("director_approved", "Approved by Director"),
                    ("director_rejected", "Rejected by Director"),
                    ("accountant_processed", "Processed by Accountant"),
                ],
                db_index=True,
                default="submitted",
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name="cpdaadvanceform",
            name="workflow_history",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
