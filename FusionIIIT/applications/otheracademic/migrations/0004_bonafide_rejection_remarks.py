# Migration to add missing rejection_remarks column to BonafideFormTableUpdated

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('otheracademic', '0003_t14_t16_audit_escalation'),
    ]

    operations = [
        migrations.AddField(
            model_name='bonafideformtableupdated',
            name='rejection_remarks',
            field=models.TextField(blank=True, help_text='Remarks provided when rejecting the bonafide request', null=True),
        ),
    ]
