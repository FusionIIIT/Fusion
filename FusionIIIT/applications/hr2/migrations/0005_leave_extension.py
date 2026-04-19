from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0004_leave_cancellation'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='extension_status',
            field=models.CharField(
                choices=[('NOT_REQUESTED', 'Not Requested'), ('REQUESTED', 'Requested'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
                default='NOT_REQUESTED',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='extension_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='extension_decided_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='extension_requested_by_role',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='extension_current_approver_role',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='extension_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='extension_new_end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='extension_new_total_days',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='extension_decision_remarks',
            field=models.TextField(blank=True),
        ),
    ]
