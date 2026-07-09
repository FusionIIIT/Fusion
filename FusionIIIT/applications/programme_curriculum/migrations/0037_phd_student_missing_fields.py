from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adds fields present in StudentBatchUpload that were missing from PhdStudentBatchUpload:
      - allotted_gender
      - aadhar_number
      - category_rank
      - allocation_status
      - email_password
      - password_email_sent
      - password_generated_at
    """

    dependencies = [
        ('programme_curriculum', '0036_phd_student_batch_upload'),
    ]

    operations = [
        # Allotment tracking
        migrations.AddField(
            model_name='phdstudentbatchupload',
            name='allotted_gender',
            field=models.CharField(blank=True, max_length=50, null=True, help_text='Allotted Gender'),
        ),
        # Identity
        migrations.AddField(
            model_name='phdstudentbatchupload',
            name='aadhar_number',
            field=models.CharField(blank=True, max_length=12, null=True, help_text='Aadhaar Number (12 digits)'),
        ),
        # Rank
        migrations.AddField(
            model_name='phdstudentbatchupload',
            name='category_rank',
            field=models.IntegerField(blank=True, null=True, help_text='Category Rank in admission (GATE category rank or equivalent)'),
        ),
        # Allocation state
        migrations.AddField(
            model_name='phdstudentbatchupload',
            name='allocation_status',
            field=models.CharField(default='ALLOCATED', max_length=50, help_text='Allocation Status (e.g., ALLOCATED, PENDING)'),
        ),
        # Password / email notification workflow
        migrations.AddField(
            model_name='phdstudentbatchupload',
            name='email_password',
            field=models.CharField(
                blank=True, max_length=50, null=True,
                help_text='Temporary plain-text password storage for email notification (cleared after sending)',
            ),
        ),
        migrations.AddField(
            model_name='phdstudentbatchupload',
            name='password_email_sent',
            field=models.BooleanField(default=False, help_text='Whether the password email has been sent to the student'),
        ),
        migrations.AddField(
            model_name='phdstudentbatchupload',
            name='password_generated_at',
            field=models.DateTimeField(blank=True, null=True, help_text='Timestamp when the password was generated'),
        ),
    ]
