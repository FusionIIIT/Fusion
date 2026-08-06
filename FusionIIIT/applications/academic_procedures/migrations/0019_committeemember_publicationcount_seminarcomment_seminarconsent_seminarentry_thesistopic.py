from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academic_information', '0001_initial'),
        ('globals', '0004_extrainfo_last_selected_role'),
        ('academic_procedures', '0015_auto_20250709_1240'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThesisTopic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('supervisor_consented', models.BooleanField(default=False)),
                ('co_supervisor_consented', models.BooleanField(default=False)),
                ('category', models.CharField(choices=[('Regular', 'Regular'), ('Sponsored', 'Sponsored'), ('External', 'External')], max_length=20)),
                ('broad_area', models.CharField(max_length=200)),
                ('research_theme', models.TextField()),
                ('external_name', models.CharField(blank=True, max_length=100)),
                ('external_email', models.EmailField(blank=True, max_length=254)),
                ('external_discipline', models.CharField(blank=True, max_length=100)),
                ('external_institution', models.CharField(blank=True, max_length=200)),
                ('pg_single', models.PositiveIntegerField(default=0)),
                ('pg_shared', models.PositiveIntegerField(default=0)),
                ('phd_single', models.PositiveIntegerField(default=0)),
                ('phd_shared', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(choices=[('supervisor_pending', 'Pending with Supervisor'), ('hod_pending', 'Approved by Supervisor, Pending with HOD'), ('hod_rejected', 'Rejected by HOD, Returned to Supervisor'), ('dean_pending', 'Approved by HOD, Pending with Dean'), ('dean_rejected', 'Rejected by Dean, Returned to HOD'), ('dean_approved', 'Approved by Dean')], default='supervisor_pending', max_length=30)),
                ('hod_remarks', models.TextField(blank=True)),
                ('dean_remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('co_supervisor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='theses_cosupervised', to='globals.faculty')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                ('supervisor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='theses_supervised', to='globals.faculty')),
            ],
        ),
        migrations.CreateModel(
            name='SeminarEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveSmallIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('rpc_pending', 'Pending RPC Consent'), ('rpc_approved', 'Approved')], default='draft', max_length=20)),
                ('seminar_date', models.DateField(blank=True, null=True)),
                ('seminar_time', models.TimeField(blank=True, null=True)),
                ('seminar_venue', models.CharField(blank=True, max_length=200)),
                ('summary_prev', models.TextField(blank=True)),
                ('summary_curr', models.TextField(blank=True)),
                ('future_plan', models.TextField(blank=True)),
                ('upload_doc', models.FileField(blank=True, null=True, upload_to='seminar_docs/')),
                ('quality', models.CharField(blank=True, choices=[('Excellent', 'Excellent'), ('Good', 'Good'), ('Sat', 'Satisfactory'), ('Unsat', 'Unsatisfactory')], max_length=20)),
                ('quantity', models.CharField(blank=True, choices=[('Enough', 'Enough'), ('Just', 'Just Sufficient'), ('Insuff', 'Insufficient')], max_length=20)),
                ('overall_grade', models.CharField(blank=True, choices=[('S', 'S'), ('X', 'X')], max_length=2)),
                ('expected_period', models.CharField(blank=True, choices=[('1', '1 year'), ('2', '2 years'), ('3', '3 years'), ('4', '4 years')], max_length=2)),
                ('rec_assist', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No'), ('NA', 'Not Applicable')], max_length=3)),
                ('rec_enhance', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No'), ('NA', 'Not Applicable')], max_length=3)),
                ('rec_repeat', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('NA', 'Not Applicable')], max_length=3)),
                ('rec_open', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No')], max_length=3)),
                ('thesis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seminars', to='academic_procedures.thesistopic')),
            ],
        ),
        migrations.CreateModel(
            name='SeminarConsent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('consented', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='globals.faculty')),
                ('seminar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consents', to='academic_procedures.seminarentry')),
            ],
            options={
                'unique_together': {('seminar', 'member')},
            },
        ),
        migrations.CreateModel(
            name='SeminarComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='globals.faculty')),
                ('seminar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='academic_procedures.seminarentry')),
            ],
            options={
                'ordering': ['-timestamp'],
                'unique_together': {('seminar', 'member')},
            },
        ),
        migrations.CreateModel(
            name='PublicationCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('Journal', 'Journal'), ('Conference', 'Conference'), ('Submitted', 'Submitted')], max_length=50)),
                ('submitted', models.PositiveIntegerField(default=0)),
                ('accepted', models.PositiveIntegerField(default=0)),
                ('published', models.PositiveIntegerField(default=0)),
                ('seminar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pub_counts', to='academic_procedures.seminarentry')),
            ],
            options={
                'unique_together': {('seminar', 'category')},
            },
        ),
        migrations.CreateModel(
            name='CommitteeMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='globals.faculty')),
                ('thesis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='committee', to='academic_procedures.thesistopic')),
            ],
            options={
                'unique_together': {('thesis', 'member')},
            },
        ),
    ]
