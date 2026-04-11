"""
Django migration file for T22, T23, T24 models.
This migration creates tables for:
- T22: Analytics, APICallLog, SystemHealthCheck  
- T23: Feedback, FeedbackHelpfulness
- T24: SystemHealthCheck (shared with T22)
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('otheracademic', '0001_initial'),  # Adjust to match your actual latest migration
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # T22: Analytics Model
        migrations.CreateModel(
            name='Analytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('metric_type', models.CharField(
                    choices=[
                        ('total_records', 'Total No Dues Records'),
                        ('cleared_count', 'Total Cleared'),
                        ('notclear_count', 'Total Not Clear'),
                        ('pending_count', 'Pending Clearance'),
                        ('avg_clearance_time', 'Average Days to Clear'),
                        ('escalation_rate', 'Escalation Rate (%)'),
                        ('department_clear_rate', 'Department Clear Rate (%)'),
                        ('7day_reminders_sent', '7-Day Reminders Sent'),
                        ('14day_reminders_sent', '14-Day Reminders Sent'),
                        ('21day_reminders_sent', '21-Day Reminders Sent'),
                        ('auto_marked_30day', 'Auto-Marked After 30 Days'),
                    ],
                    db_index=True,
                    max_length=50
                )),
                ('department', models.CharField(blank=True, db_index=True, max_length=100, null=True)),
                ('value', models.JSONField(default=dict)),
                ('period_start', models.DateField(blank=True, null=True)),
                ('period_end', models.DateField(blank=True, null=True)),
                ('aggregation_type', models.CharField(
                    choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
                    default='daily',
                    max_length=20
                )),
            ],
            options={
                'verbose_name_plural': 'Analytics',
                'db_table': 'otheracademic_analytics',
            },
        ),
        # Index for Analytics
        migrations.AddIndex(
            model_name='analytics',
            index=models.Index(fields=['metric_type', 'timestamp'], name='otheracad_metric_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='analytics',
            index=models.Index(fields=['department', 'timestamp'], name='otheracad_dept_timestamp_idx'),
        ),
        
        # T23: Feedback Model
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(
                    choices=[
                        ('process_clarity', 'Process Clarity'),
                        ('ease_of_use', 'Ease of Use'),
                        ('timeline', 'Timeline'),
                        ('communication', 'Communication'),
                        ('support', 'Support Quality'),
                        ('other', 'Other'),
                    ],
                    db_index=True,
                    max_length=50
                )),
                ('rating', models.IntegerField(
                    choices=[(1, 'Very Poor'), (2, 'Poor'), (3, 'Average'), (4, 'Good'), (5, 'Excellent')]
                )),
                ('title', models.CharField(max_length=200)),
                ('comment', models.TextField(max_length=5000)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('is_anonymous', models.BooleanField(default=False)),
                ('helpful_count', models.IntegerField(default=0)),
                ('admin_response', models.TextField(blank=True, null=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('responded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='feedback_responses', to='auth.user')),
                ('user', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='auth.user')),
            ],
            options={
                'db_table': 'otheracademic_feedback',
                'ordering': ['-created_at'],
            },
        ),
        # Index for Feedback
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(fields=['user', 'created_at'], name='otheracad_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(fields=['category', 'rating'], name='otheracad_cat_rating_idx'),
        ),
        
        # T23: FeedbackHelpfulness Model
        migrations.CreateModel(
            name='FeedbackHelpfulness',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_helpful', models.BooleanField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('feedback', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='helpfulness_votes', to='otheracademic.feedback')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
            options={
                'db_table': 'otheracademic_feedback_helpfulness',
                'unique_together': {('feedback', 'user')},
            },
        ),
        # Index for FeedbackHelpfulness
        migrations.AddIndex(
            model_name='feedbackhelpfulness',
            index=models.Index(fields=['feedback', 'user'], name='otheracad_feedback_user_idx'),
        ),
        
        # T24: SystemHealthCheck Model
        migrations.CreateModel(
            name='SystemHealthCheck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('check_type', models.CharField(db_index=True, max_length=100)),
                ('status', models.CharField(choices=[('success', 'Success'), ('warning', 'Warning'), ('error', 'Error')], max_length=20)),
                ('message', models.TextField()),
                ('details', models.JSONField(default=dict)),
            ],
            options={
                'db_table': 'otheracademic_health_check',
                'ordering': ['-timestamp'],
            },
        ),
        # Index for SystemHealthCheck
        migrations.AddIndex(
            model_name='systemhealthcheck',
            index=models.Index(fields=['check_type', 'status'], name='otheracad_check_status_idx'),
        ),
        
        # T24: APICallLog Model
        migrations.CreateModel(
            name='APICallLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('endpoint', models.CharField(db_index=True, max_length=200)),
                ('method', models.CharField(max_length=10)),
                ('status_code', models.IntegerField(db_index=True)),
                ('response_time_ms', models.IntegerField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('ip_address', models.CharField(blank=True, max_length=255, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={
                'db_table': 'otheracademic_api_call_log',
            },
        ),
        # Index for APICallLog
        migrations.AddIndex(
            model_name='apicalllog',
            index=models.Index(fields=['endpoint', 'method'], name='otheracad_endpoint_method_idx'),
        ),
        migrations.AddIndex(
            model_name='apicalllog',
            index=models.Index(fields=['user', 'timestamp'], name='otheracad_user_ts_idx'),
        ),
    ]
