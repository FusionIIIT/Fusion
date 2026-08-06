from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academic_information', '0001_initial'),
        ('placement_cell', '0005_auto_20260418_0906'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AlumniProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('graduation_year', models.IntegerField()),
                ('degree', models.CharField(blank=True, default='', max_length=100)),
                ('current_company', models.CharField(blank=True, default='', max_length=150)),
                ('current_designation', models.CharField(blank=True, default='', max_length=150)),
                ('linkedin_url', models.URLField(blank=True, default='')),
                ('verification_document', models.FileField(blank=True, null=True, upload_to='documents/placement/alumni_verification')),
                ('verification_notes', models.TextField(blank=True, default='', max_length=1000)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('topics', models.TextField(blank=True, default='', max_length=1000)),
                ('availability', models.CharField(blank=True, default='', max_length=200)),
                ('bio', models.TextField(blank=True, default='', max_length=1500)),
                ('mentorship_enabled', models.BooleanField(default=False)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_alumni_profiles', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-updated_at', '-id'),
            },
        ),
        migrations.CreateModel(
            name='AlumniReferral',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('company', models.CharField(max_length=150)),
                ('location', models.CharField(blank=True, default='', max_length=150)),
                ('application_url', models.URLField(blank=True, default='')),
                ('description', models.TextField(max_length=2000)),
                ('expires_at', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('alumni', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referrals', to='placement_cell.alumniprofile')),
            ],
            options={
                'ordering': ('-created_at', '-id'),
            },
        ),
        migrations.CreateModel(
            name='AlumniMentorshipSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=150)),
                ('agenda', models.TextField(blank=True, default='', max_length=1500)),
                ('scheduled_at', models.DateTimeField()),
                ('mode', models.CharField(blank=True, default='online', max_length=50)),
                ('meeting_link', models.CharField(blank=True, default='', max_length=300)),
                ('student_message', models.TextField(blank=True, default='', max_length=1500)),
                ('alumni_message', models.TextField(blank=True, default='', max_length=1500)),
                ('status', models.CharField(choices=[('requested', 'Requested'), ('scheduled', 'Scheduled'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='requested', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('alumni', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='placement_cell.alumniprofile')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alumni_sessions', to='academic_information.student')),
            ],
            options={
                'ordering': ('scheduled_at', '-id'),
            },
        ),
        migrations.CreateModel(
            name='AlumniConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('connected', 'Connected'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('message', models.TextField(blank=True, default='', max_length=1000)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('alumni', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connections', to='placement_cell.alumniprofile')),
                ('responded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alumni_connection_responses', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alumni_connections', to='academic_information.student')),
            ],
            options={
                'ordering': ('-created_at', '-id'),
                'unique_together': {('alumni', 'student')},
            },
        ),
    ]
