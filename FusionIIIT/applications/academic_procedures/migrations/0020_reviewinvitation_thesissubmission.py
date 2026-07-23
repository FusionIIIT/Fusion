import applications.academic_procedures.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('academic_procedures', '0018_auto_20260106_1355'),
        ('academic_procedures', '0019_committeemember_publicationcount_seminarcomment_seminarconsent_seminarentry_thesistopic'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThesisSubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)),
                ('synopsis', models.FileField(upload_to=applications.academic_procedures.models.upload_synopsis)),
                ('thesis_report', models.FileField(upload_to=applications.academic_procedures.models.upload_report)),
                ('submitted_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('supervisor_approved_at', models.DateTimeField(blank=True, null=True)),
                ('director_approved_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('submitted', 'Submitted'), ('supervisor_review', 'Supervisor Review'), ('director_review', 'Director Review'), ('in_review', 'In External Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='submitted', max_length=30, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('director', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='directed_subs', to=settings.AUTH_USER_MODEL)),
                ('supervisor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervised_subs', to=settings.AUTH_USER_MODEL)),
                ('thesis', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='submission', to='academic_procedures.thesistopic')),
            ],
            options={
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.CreateModel(
            name='ReviewInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prof_name', models.CharField(max_length=255, db_index=True)),
                ('prof_position', models.CharField(max_length=255)),
                ('prof_address', models.TextField()),
                ('prof_phone', models.CharField(max_length=20)),
                ('prof_email', models.EmailField(max_length=254, db_index=True)),
                ('prof_time_ranking', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('priority', models.PositiveSmallIntegerField(default=0, db_index=True)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('completed', 'Completed'), ('expired', 'Expired')], default='pending', max_length=20, db_index=True)),
                ('last_sent', models.DateTimeField(blank=True, null=True)),
                ('review_form_sent', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='academic_procedures.thesissubmission')),
            ],
            options={
                'ordering': ['submission', 'priority'],
                'unique_together': {('submission', 'priority')},
            },
        ),
        migrations.AddIndex(
            model_name='reviewinvitation',
            index=models.Index(fields=['submission', 'status'], name='academic_pr_submiss_858405_idx'),
        ),
        migrations.AddIndex(
            model_name='reviewinvitation',
            index=models.Index(fields=['status', 'last_sent'], name='academic_pr_status_7509a8_idx'),
        ),
        migrations.AddIndex(
            model_name='thesissubmission',
            index=models.Index(fields=['status', 'submitted_at'], name='academic_pr_status_953719_idx'),
        ),
    ]
