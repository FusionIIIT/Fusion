# Generated migration for T14/T16 (Escalation and Audit functionality)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('otheracademic', '0002_t22_t23_t24_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_name', models.CharField(max_length=100, db_index=True)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('action', models.CharField(choices=[('CREATE', 'Created'), ('UPDATE', 'Updated'), ('DELETE', 'Deleted')], max_length=10, db_index=True)),
                ('changed_by', models.CharField(max_length=255)),
                ('changed_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('old_values', models.JSONField(default=dict, blank=True)),
                ('new_values', models.JSONField(default=dict, blank=True)),
                ('reason', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name_plural': 'Audit logs',
                'ordering': ['-changed_at'],
            },
        ),
        migrations.CreateModel(
            name='NoDuesEscalation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=20, db_index=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending Approval'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('REMOVED', 'Removed from Escalation')], default='PENDING', max_length=15, db_index=True)),
                ('escalation_reason', models.CharField(max_length=255)),
                ('approval_chain', models.CharField(choices=[('HOD', 'Department HOD'), ('DEAN', 'Dean of Students'), ('DIRECTOR', 'Director')], default='HOD', max_length=15)),
                ('escalated_by', models.CharField(max_length=255)),
                ('escalated_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('approved_by', models.CharField(blank=True, default='', max_length=255)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True, default='')),
                ('notes', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name_plural': 'No Dues Escalations',
                'ordering': ['-escalated_at'],
            },
        ),
        migrations.CreateModel(
            name='NoDuesClearanceHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=20, db_index=True)),
                ('status_before', models.CharField(choices=[('CLEARED', 'Cleared'), ('NOT_CLEARED', 'Not Cleared'), ('ESCALATED', 'Escalated')], max_length=15)),
                ('status_after', models.CharField(choices=[('CLEARED', 'Cleared'), ('NOT_CLEARED', 'Not Cleared'), ('ESCALATED', 'Escalated')], max_length=15)),
                ('changed_by', models.CharField(max_length=255)),
                ('changed_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('reason', models.TextField(blank=True, default='')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name_plural': 'No Dues Clearance History',
                'ordering': ['-timestamp'],
            },
        ),
    ]
