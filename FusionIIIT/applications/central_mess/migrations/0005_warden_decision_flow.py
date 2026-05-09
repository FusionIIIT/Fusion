# Generated manually for mess warden escalation workflow support.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('central_mess', '0004_special_request_rules'),
    ]

    operations = [
        migrations.AddField(
            model_name='deregistrationrequest',
            name='escalated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deregistrationrequest',
            name='escalation_remark',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='deregistrationrequest',
            name='override_conditions',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='deregistrationrequest',
            name='warden_decided_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deregistrationrequest',
            name='warden_remark',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='paymentupdaterequest',
            name='escalated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paymentupdaterequest',
            name='escalation_remark',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='paymentupdaterequest',
            name='override_conditions',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='paymentupdaterequest',
            name='warden_decided_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paymentupdaterequest',
            name='warden_remark',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='rebate',
            name='escalated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rebate',
            name='escalation_remark',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='rebate',
            name='override_conditions',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='rebate',
            name='warden_decided_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rebate',
            name='warden_remark',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='registrationrequest',
            name='escalated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='registrationrequest',
            name='escalation_remark',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='registrationrequest',
            name='override_conditions',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='registrationrequest',
            name='warden_decided_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='registrationrequest',
            name='warden_remark',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='special_request',
            name='escalated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='special_request',
            name='escalation_remark',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='special_request',
            name='override_conditions',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='special_request',
            name='warden_decided_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='special_request',
            name='warden_remark',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='deregistrationrequest',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('escalated', 'Escalated'), ('accept', 'Accepted'), ('reject', 'Rejected'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='paymentupdaterequest',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('escalated', 'Escalated'), ('accept', 'Accepted'), ('reject', 'Rejected'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='rebate',
            name='status',
            field=models.CharField(choices=[('0', 'rejected'), ('1', 'pending'), ('2', 'accepted'), ('3', 'escalated')], default='1', max_length=20),
        ),
        migrations.AlterField(
            model_name='registrationrequest',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('escalated', 'Escalated'), ('accept', 'Accepted'), ('reject', 'Rejected'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='special_request',
            name='status',
            field=models.CharField(choices=[('0', 'rejected'), ('1', 'pending'), ('2', 'accepted'), ('3', 'escalated')], default='1', max_length=20),
        ),
    ]
