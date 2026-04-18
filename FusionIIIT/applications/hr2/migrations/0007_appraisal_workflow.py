from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr2", "0006_ltc_workflow"),
    ]

    operations = [
        migrations.AddField(
            model_name="appraisalform",
            name="workflow_status",
            field=models.CharField(
                choices=[
                    ("submitted", "Submitted"),
                    ("hr_approved", "Approved by HR"),
                    ("hr_rejected", "Rejected by HR"),
                ],
                db_index=True,
                default="submitted",
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name="appraisalform",
            name="workflow_history",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
