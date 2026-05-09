from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0008_station_leave_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='resumption_status',
            field=models.CharField(
                choices=[('NOT_REQUESTED', 'Not Requested'), ('SUBMITTED', 'Submitted'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
                default='NOT_REQUESTED',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='resumption_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='resumption_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='resumption_submitted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='resumption_decided_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='resumption_current_approver_role',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='resumption_decision_remarks',
            field=models.TextField(blank=True),
        ),
    ]
