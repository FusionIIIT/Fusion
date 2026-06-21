from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('placement_cell', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='companydetails',
            name='address',
            field=models.TextField(blank=True, default='', max_length=1000),
        ),
        migrations.AddField(
            model_name='companydetails',
            name='description',
            field=models.TextField(blank=True, default='', max_length=1000),
        ),
        migrations.AddField(
            model_name='companydetails',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='documents/placement/company_logos'),
        ),
        migrations.AddField(
            model_name='companydetails',
            name='website',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.CreateModel(
            name='PlacementField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('type', models.CharField(choices=[('text', 'Text'), ('number', 'Number'), ('decimal', 'Decimal'), ('date', 'Date'), ('time', 'Time')], default='text', max_length=20)),
                ('required', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='placementschedule',
            name='branch',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='placementschedule',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='placement_cell.CompanyDetails'),
        ),
        migrations.AddField(
            model_name='placementschedule',
            name='cpi',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='placementschedule',
            name='eligibility',
            field=models.TextField(blank=True, default='', max_length=1000),
        ),
        migrations.AddField(
            model_name='placementschedule',
            name='end_date',
            field=models.DateField(blank=True, null=True, verbose_name='Date'),
        ),
        migrations.AddField(
            model_name='placementschedule',
            name='end_datetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='placementschedule',
            name='gender',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='placementschedule',
            name='passoutyr',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='placementschedule',
            name='fields',
            field=models.ManyToManyField(blank=True, to='placement_cell.PlacementField'),
        ),
        migrations.AddField(
            model_name='studentplacement',
            name='debar_reason',
            field=models.TextField(blank=True, default='', max_length=1000),
        ),
        migrations.CreateModel(
            name='PlacementRestriction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criteria', models.CharField(max_length=50)),
                ('condition', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='', max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='PlacementRound',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_no', models.IntegerField(default=0)),
                ('test_date', models.DateField(blank=True, null=True)),
                ('description', models.TextField(blank=True, default='', max_length=1000)),
                ('test_type', models.CharField(blank=True, default='', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='placement_cell.PlacementSchedule')),
            ],
            options={
                'ordering': ('round_no', 'created_at'),
            },
        ),
        migrations.CreateModel(
            name='PlacementApplication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accept', 'Accept'), ('reject', 'Reject')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='placement_cell.PlacementSchedule')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.Student')),
            ],
            options={
                'unique_together': {('schedule', 'student')},
            },
        ),
        migrations.CreateModel(
            name='PlacementApplicationResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.TextField(blank=True, default='', max_length=5000)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='placement_cell.PlacementApplication')),
                ('field', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='placement_cell.PlacementField')),
            ],
        ),
    ]
