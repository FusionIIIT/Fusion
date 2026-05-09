from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0003_leave_document_request'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='cancel_status',
            field=models.CharField(
                choices=[('NOT_REQUESTED', 'Not Requested'), ('REQUESTED', 'Requested'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
                default='NOT_REQUESTED',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='cancel_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='cancel_decided_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='cancel_requested_by_role',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='cancel_current_approver_role',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='cancel_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='cancel_decision_remarks',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='leaveapplicationnew',
            name='approval_status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('FORWARDED', 'Forwarded'),
                    ('APPROVED', 'Approved'),
                    ('REJECTED', 'Rejected'),
                    ('WITHDRAWN', 'Withdrawn'),
                    ('CANCELLED', 'Cancelled'),
                ],
                default='PENDING',
                max_length=20,
            ),
        ),
    ]
