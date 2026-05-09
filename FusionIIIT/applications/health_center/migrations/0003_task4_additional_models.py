# Generated migration for Task 4: Additional Health Center Models
# Adds ComplaintV2, HospitalAdmit, and AmbulanceRecordsV2 models

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('health_center', '0002_task3_pharmacy_models'),
        ('globals', '0005_moduleaccess_database'),
    ]

    operations = [
        # 1. Create ComplaintV2 model
        migrations.CreateModel(
            name='ComplaintV2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('category', models.CharField(
                    choices=[
                        ('SERVICE', 'Service Quality'),
                        ('STAFF', 'Staff Behavior'),
                        ('FACILITIES', 'Facilities'),
                        ('MEDICAL', 'Medical Care'),
                        ('OTHER', 'Other'),
                    ],
                    max_length=20
                )),
                ('status', models.CharField(
                    choices=[
                        ('SUBMITTED', 'Submitted'),
                        ('IN_PROGRESS', 'In Progress'),
                        ('RESOLVED', 'Resolved'),
                        ('CLOSED', 'Closed'),
                    ],
                    default='SUBMITTED',
                    max_length=20
                )),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('resolved_date', models.DateTimeField(blank=True, null=True)),
                ('resolution_notes', models.TextField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints', to='globals.extrainfo')),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_complaints', to='globals.extrainfo')),
            ],
            options={
                'db_table': 'health_center_complaint_v2',
                'ordering': ['-created_date'],
            },
        ),

        # 2. Create HospitalAdmit model
        migrations.CreateModel(
            name='HospitalAdmit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hospital_id', models.CharField(max_length=100)),
                ('hospital_name', models.CharField(max_length=255)),
                ('admission_date', models.DateField()),
                ('discharge_date', models.DateField(blank=True, null=True)),
                ('reason', models.TextField()),
                ('summary', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hospital_admissions', to='globals.extrainfo')),
                ('referred_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals', to='health_center.doctor')),
            ],
            options={
                'db_table': 'health_center_hospital_admit',
                'ordering': ['-admission_date'],
            },
        ),

        # 3. Create AmbulanceRecordsV2 model
        migrations.CreateModel(
            name='AmbulanceRecordsV2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vehicle_type', models.CharField(max_length=50)),
                ('registration_number', models.CharField(max_length=50, unique=True)),
                ('driver_name', models.CharField(max_length=255)),
                ('driver_contact', models.CharField(max_length=15)),
                ('driver_license', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(
                    choices=[
                        ('AVAILABLE', 'Available'),
                        ('ASSIGNED', 'Assigned'),
                        ('IN_TRANSIT', 'In Transit'),
                        ('MAINTENANCE', 'Maintenance'),
                        ('OUT_OF_SERVICE', 'Out of Service'),
                    ],
                    default='AVAILABLE',
                    max_length=20
                )),
                ('current_assignment', models.CharField(blank=True, max_length=255, null=True)),
                ('last_maintenance_date', models.DateField(blank=True, null=True)),
                ('next_maintenance_due', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'health_center_ambulance_records_v2',
                'ordering': ['registration_number'],
            },
        ),
    ]
