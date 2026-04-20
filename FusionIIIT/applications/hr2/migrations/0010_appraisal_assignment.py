from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("hr2", "0009_leave_resumption"),
    ]

    operations = [
        migrations.AddField(
            model_name="appraisalformnew",
            name="assigned_reviewer_role",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="appraisalformnew",
            name="assigned_reviewer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_appraisals_new",
                to="globals.extrainfo",
            ),
        ),
        migrations.AddField(
            model_name="appraisalformnew",
            name="assigned_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="appraisal_assignments_made",
                to="globals.extrainfo",
            ),
        ),
        migrations.AddField(
            model_name="appraisalformnew",
            name="assigned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
