# Generated migration for adding patient_name field to HospitalAdmit
# Task 14: Add patient name denormalization for audit trail and performance

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health_center', '0003_task4_additional_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospitaladmit',
            name='patient_name',
            field=models.CharField(blank=True, max_length=255, help_text='Denormalized patient name for audit trail'),
        ),
    ]
