from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('hr2', '0002_leave_nominee'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='document_request_message',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='document_request_status',
            field=models.CharField(
                choices=[('NOT_REQUESTED', 'Not Requested'), ('REQUESTED', 'Requested'), ('SUBMITTED', 'Submitted')],
                default='NOT_REQUESTED',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='document_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='document_submission',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='document_submitted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
