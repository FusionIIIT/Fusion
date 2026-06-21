# Generated migration for Assignment 7 implementation
# This migration adds new fields and models for T-NT-01, T-NT-02, T-NT-04, T-NT-05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0001_initial'),  # Update if different
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # T-NT-04: Create RegisteredModule model for module authorization
        migrations.CreateModel(
            name='RegisteredModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module_name', models.CharField(help_text='Name of the registered module', max_length=100, unique=True)),
                ('api_key', models.CharField(help_text='API key for module authentication', max_length=255, unique=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this module is allowed to send notifications')),
                ('default_priority', models.IntegerField(choices=[(1, 'Critical'), (2, 'High'), (3, 'Medium'), (4, 'Low')], default=3, help_text='Default priority for notifications from this module')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='registered_modules', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Registered Module',
                'verbose_name_plural': 'Registered Modules',
                'ordering': ['module_name'],
            },
        ),
        
        # T-NT-05: Add priority field to Announcements model
        migrations.AddField(
            model_name='announcements',
            name='priority',
            field=models.IntegerField(choices=[(1, 'Critical'), (2, 'High'), (3, 'Medium'), (4, 'Low')], default=3, help_text='Priority level (1=Critical, 4=Low)'),
        ),
        
        # T-NT-02: Add expiry_date field to Announcements model
        migrations.AddField(
            model_name='announcements',
            name='expiry_date',
            field=models.DateTimeField(blank=True, help_text='Announcement automatically expires at this date/time', null=True),
        ),
        
        # T-NT-05: Update model ordering to include priority
        migrations.AlterModelOptions(
            name='announcements',
            options={
                'ordering': ['-priority', '-created_at'],
                'verbose_name_plural': 'Announcements',
            },
        ),
        
        # T-NT-05 & T-NT-02: Add indexes for performance
        migrations.AddIndex(
            model_name='announcements',
            index=models.Index(fields=['is_active', 'is_published'], name='notification_announ_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='announcements',
            index=models.Index(fields=['expiry_date'], name='notification_announ_expiry_idx'),
        ),
    ]
