# Generated by Django 3.1.5 on 2024-04-20 00:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('globals', '__first__'),
        ('academic_information', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Club_info',
            fields=[
                ('club_name', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('club_website', models.CharField(default='hello', max_length=150, null=True)),
                ('category', models.CharField(choices=[('Technical', 'Technical'), ('Sports', 'Sports'), ('Cultural', 'Cultural')], max_length=50)),
                ('club_file', models.FileField(null=True, upload_to='gymkhana/club_poster')),
                ('activity_calender', models.FileField(default=' ', null=True, upload_to='gymkhana/activity_calender')),
                ('description', models.TextField(max_length=256, null=True)),
                ('alloted_budget', models.IntegerField(default=0, null=True)),
                ('spent_budget', models.IntegerField(default=0, null=True)),
                ('avail_budget', models.IntegerField(default=0, null=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')], default='open', max_length=50)),
                ('head_changed_on', models.DateField(default=django.utils.timezone.now, null=True)),
                ('created_on', models.DateField(default=django.utils.timezone.now, null=True)),
                ('co_coordinator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coco_of', to='academic_information.student')),
                ('co_ordinator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='co_of', to='academic_information.student')),
                ('faculty_incharge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='faculty_incharge_of', to='globals.faculty')),
            ],
            options={
                'db_table': 'Club_info',
            },
        ),
        migrations.CreateModel(
            name='Fest_budget',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('fest', models.CharField(choices=[('Abhikalpan', 'Abhikalpan'), ('Gusto', 'Gusto'), ('Tarang', 'Tarang')], max_length=50)),
                ('budget_amt', models.IntegerField(default=0)),
                ('budget_file', models.FileField(upload_to='uploads/')),
                ('year', models.CharField(max_length=10, null=True)),
                ('description', models.TextField(max_length=256)),
                ('status', models.CharField(choices=[('open', 'Open'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')], default='open', max_length=50)),
                ('remarks', models.CharField(max_length=256, null=True)),
            ],
            options={
                'db_table': 'Fest_budget',
            },
        ),
        migrations.CreateModel(
            name='Form_available',
            fields=[
                ('roll', models.CharField(default=2016001, max_length=7, primary_key=True, serialize=False)),
                ('status', models.BooleanField(default=True, max_length=5)),
                ('form_name', models.CharField(default='senate_registration', max_length=30)),
            ],
            options={
                'db_table': 'Form_available',
            },
        ),
        migrations.CreateModel(
            name='Registration_form',
            fields=[
                ('roll', models.CharField(default='20160017', max_length=8, primary_key=True, serialize=False)),
                ('user_name', models.CharField(default='Student', max_length=40)),
                ('branch', models.CharField(default='open', max_length=20)),
                ('cpi', models.FloatField(default=6.0, max_length=3)),
                ('programme', models.CharField(default='B.tech', max_length=20)),
            ],
            options={
                'db_table': 'Registration_form',
            },
        ),
        migrations.CreateModel(
            name='Voting_polls',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.CharField(max_length=5000)),
                ('pub_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('exp_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.CharField(max_length=100, null=True)),
                ('groups', models.CharField(default='{}', max_length=500)),
            ],
            options={
                'ordering': ['-pub_date'],
            },
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('club_name', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='club_inventory', serialize=False, to='gymkhana.club_info')),
                ('inventory', models.FileField(upload_to='gymkhana/inventory')),
            ],
            options={
                'db_table': 'Inventory',
            },
        ),
        migrations.CreateModel(
            name='Voting_voters',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=50)),
                ('poll_event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gymkhana.voting_polls')),
            ],
        ),
        migrations.CreateModel(
            name='Voting_choices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.CharField(default='', max_length=500)),
                ('votes', models.IntegerField(default=0)),
                ('poll_event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gymkhana.voting_polls')),
            ],
            options={
                'get_latest_by': 'votes',
            },
        ),
        migrations.CreateModel(
            name='Session_info',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('venue', models.CharField(choices=[('Classroom', (('CR101', 'CR101'), ('CR102', 'CR102'))), ('Lecturehall', (('L101', 'L101'), ('L102', 'L102')))], max_length=50)),
                ('date', models.DateField(default=None)),
                ('start_time', models.TimeField(default=None)),
                ('end_time', models.TimeField(default=None)),
                ('session_poster', models.ImageField(null=True, upload_to='gymkhana/session_poster')),
                ('details', models.TextField(max_length=256, null=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')], default='open', max_length=50)),
                ('club', models.ForeignKey(max_length=50, null=True, on_delete=django.db.models.deletion.CASCADE, to='gymkhana.club_info')),
            ],
            options={
                'db_table': 'Session_info',
            },
        ),
        migrations.CreateModel(
            name='Other_report',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('event_name', models.CharField(max_length=50)),
                ('date', models.DateTimeField(blank=True, default=django.utils.timezone.now, max_length=50)),
                ('event_details', models.FileField(upload_to='uploads/')),
                ('description', models.TextField(max_length=256, null=True)),
                ('incharge', models.ForeignKey(max_length=256, on_delete=django.db.models.deletion.CASCADE, to='globals.extrainfo')),
            ],
            options={
                'db_table': 'Other_report',
            },
        ),
        migrations.CreateModel(
            name='Event_info',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('event_name', models.CharField(max_length=256)),
                ('venue', models.CharField(choices=[('Classroom', (('CR101', 'CR101'), ('CR102', 'CR102'))), ('Lecturehall', (('L101', 'L101'), ('L102', 'L102')))], max_length=50)),
                ('incharge', models.CharField(max_length=256)),
                ('date', models.DateField(default=None)),
                ('start_time', models.TimeField(default=None)),
                ('end_time', models.TimeField(default=None, null=True)),
                ('event_poster', models.FileField(blank=True, upload_to='gymkhana/event_poster')),
                ('details', models.TextField(max_length=256, null=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')], default='open', max_length=50)),
                ('club', models.ForeignKey(max_length=50, null=True, on_delete=django.db.models.deletion.CASCADE, to='gymkhana.club_info')),
            ],
            options={
                'db_table': 'Event_info',
            },
        ),
        migrations.CreateModel(
            name='Core_team',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('team', models.CharField(max_length=50)),
                ('year', models.DateTimeField(max_length=6, null=True)),
                ('fest_name', models.CharField(choices=[('Abhikalpan', 'Abhikalpan'), ('Gusto', 'Gusto'), ('Tarang', 'Tarang')], max_length=256)),
                ('pda', models.TextField(max_length=256)),
                ('remarks', models.CharField(max_length=256, null=True)),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applied_for', to='academic_information.student')),
            ],
            options={
                'db_table': 'Core_team',
            },
        ),
        migrations.CreateModel(
            name='Club_report',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('event_name', models.CharField(max_length=50)),
                ('date', models.DateTimeField(blank=True, default=django.utils.timezone.now, max_length=50)),
                ('event_details', models.FileField(upload_to='uploads/')),
                ('description', models.TextField(max_length=256, null=True)),
                ('club', models.ForeignKey(max_length=50, on_delete=django.db.models.deletion.CASCADE, to='gymkhana.club_info')),
                ('incharge', models.ForeignKey(max_length=256, on_delete=django.db.models.deletion.CASCADE, to='globals.extrainfo')),
            ],
            options={
                'db_table': 'Club_report',
            },
        ),
        migrations.CreateModel(
            name='Club_member',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('description', models.TextField(max_length=256, null=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')], default='open', max_length=50)),
                ('remarks', models.CharField(max_length=256, null=True)),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='this_club', to='gymkhana.club_info')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='member_of', to='academic_information.student')),
            ],
            options={
                'db_table': 'Club_member',
            },
        ),
        migrations.CreateModel(
            name='Club_budget',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('budget_for', models.CharField(max_length=256)),
                ('budget_amt', models.IntegerField(default=0)),
                ('budget_file', models.FileField(upload_to='uploads/')),
                ('description', models.TextField(max_length=256)),
                ('status', models.CharField(choices=[('open', 'Open'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')], default='open', max_length=50)),
                ('remarks', models.CharField(max_length=256, null=True)),
                ('club', models.ForeignKey(max_length=50, on_delete=django.db.models.deletion.CASCADE, to='gymkhana.club_info')),
            ],
            options={
                'db_table': 'Club_budget',
            },
        ),
        migrations.CreateModel(
            name='Change_office',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('open', 'Open'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')], default='open', max_length=50)),
                ('date_request', models.DateTimeField(blank=True, default=django.utils.timezone.now, max_length=50)),
                ('date_approve', models.DateTimeField(blank=True, max_length=50)),
                ('remarks', models.CharField(max_length=256, null=True)),
                ('club', models.ForeignKey(max_length=50, on_delete=django.db.models.deletion.CASCADE, to='gymkhana.club_info')),
                ('co_coordinator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coco_of', to=settings.AUTH_USER_MODEL)),
                ('co_ordinator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='co_of', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'Change_office',
            },
        ),
    ]
