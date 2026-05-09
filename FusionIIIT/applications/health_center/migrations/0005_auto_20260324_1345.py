from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health_center', '0004_add_patient_name_to_hospital_admit'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='prescribedmedicine',
            options={'ordering': ['prescription', 'created_at']},
        ),
        migrations.AlterModelOptions(
            name='prescription',
            options={'ordering': ['-issued_date']},
        ),
        migrations.AddField(
            model_name='expiry',
            name='return_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='prescribedmedicine',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='hospitaladmit',
            name='patient_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
