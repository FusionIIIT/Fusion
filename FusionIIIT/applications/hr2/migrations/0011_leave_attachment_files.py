from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("hr2", "0010_appraisal_assignment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="leaveapplicationnew",
            name="medical_certificate",
            field=models.FileField(blank=True, null=True, upload_to="hr/leave/"),
        ),
        migrations.AlterField(
            model_name="leaveapplicationnew",
            name="attachment_file",
            field=models.FileField(blank=True, null=True, upload_to="hr/leave/"),
        ),
    ]
