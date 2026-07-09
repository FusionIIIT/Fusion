from django.conf import settings
from django.db import migrations, models
import applications.programme_curriculum.models_student_management
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('programme_curriculum', '0035_progressseminarslot_thesisslot'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PhdStudentBatchUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                # Core identification
                ('application_no', models.CharField(
                    blank=True, max_length=50, null=True, unique=True,
                    help_text='PhD Application Number (col: Application No.)'
                )),
                ('roll_number', models.CharField(
                    blank=True, max_length=20, null=True, unique=True,
                    help_text='Institute Roll Number'
                )),
                ('institute_email', models.EmailField(
                    blank=True, max_length=254, null=True,
                    help_text='Institute Email ID'
                )),
                # Personal
                ('name', models.CharField(max_length=200, help_text='Full Name')),
                ('discipline', models.CharField(max_length=200, help_text='Discipline / Branch')),
                ('admission_type', models.CharField(
                    blank=True, max_length=100, null=True,
                    choices=[
                        ('FULL TIME with Institute Assistantship', 'FULL TIME with Institute Assistantship'),
                        ('FULL TIME with Govt. / Semi Govt. Fellowship Award', 'FULL TIME with Govt. / Semi Govt. Fellowship Award'),
                        ('FULL TIME Self Financed', 'FULL TIME Self Financed'),
                        ('PART TIME (External)', 'PART TIME (External)'),
                        ('QIP', 'QIP'),
                        ('Any other (remarks)', 'Any other (remarks)'),
                    ],
                    help_text='Admission Type'
                )),
                ('gender', models.CharField(
                    max_length=10,
                    choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
                )),
                ('category', models.CharField(
                    max_length=10,
                    choices=[
                        ('GEN', 'General'), ('OBC', 'Other Backward Class'),
                        ('SC', 'Scheduled Caste'), ('ST', 'Scheduled Tribe'),
                        ('EWS', 'Economically Weaker Section'),
                    ]
                )),
                ('minority', models.TextField(blank=True, null=True, help_text='Minority Status')),
                ('pwd', models.CharField(
                    default='NO', max_length=3,
                    choices=[('YES', 'Yes'), ('NO', 'No')]
                )),
                ('pwd_category', models.CharField(
                    blank=True, max_length=100, null=True,
                    choices=[
                        ('Locomotor Disability', 'Locomotor Disability'),
                        ('Visual Impairment', 'Visual Impairment'),
                        ('Hearing Impairment', 'Hearing Impairment'),
                        ('Speech and Language Disability', 'Speech and Language Disability'),
                        ('Intellectual Disability', 'Intellectual Disability'),
                        ('Autism Spectrum Disorder', 'Autism Spectrum Disorder'),
                        ('Multiple Disabilities', 'Multiple Disabilities'),
                        ('Any other (remarks)', 'Any other (remarks)'),
                    ]
                )),
                ('pwd_category_remarks', models.TextField(blank=True, null=True)),
                # Contact
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('personal_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('parent_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('address', models.TextField(blank=True, null=True, help_text='Full Address (with pincode)')),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                # Family
                ('father_name', models.CharField(blank=True, max_length=200, null=True)),
                ('father_occupation', models.CharField(blank=True, max_length=200, null=True)),
                ('father_mobile', models.CharField(blank=True, max_length=15, null=True)),
                ('mother_name', models.CharField(blank=True, max_length=200, null=True)),
                ('mother_occupation', models.CharField(blank=True, max_length=200, null=True)),
                ('mother_mobile', models.CharField(blank=True, max_length=15, null=True)),
                # Personal details
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('blood_group', models.CharField(
                    blank=True, max_length=10, null=True,
                    choices=[
                        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
                        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
                        ('Other', 'Other'),
                    ]
                )),
                ('blood_group_remarks', models.TextField(blank=True, null=True)),
                ('country', models.CharField(blank=True, default='India', max_length=100, null=True)),
                ('nationality', models.CharField(blank=True, default='Indian', max_length=100, null=True)),
                # Admission details
                ('admission_mode', models.CharField(
                    blank=True, max_length=50, null=True,
                    choices=[
                        ('Institute Level', 'Institute Level'), ('QIP', 'QIP'),
                        ('GATE', 'GATE'), ('Sponsored', 'Sponsored'),
                        ('Foreign National', 'Foreign National'),
                        ('Any other (remarks)', 'Any other (remarks)'),
                    ]
                )),
                ('admission_mode_remarks', models.TextField(blank=True, null=True)),
                ('income_group', models.CharField(
                    blank=True, max_length=30, null=True,
                    choices=[
                        ('Below 1 Lakh', 'Below 1 Lakh'),
                        ('Between 1 to 4 Lakh', 'Between 1 to 4 Lakh'),
                        ('Between 4 to 6 Lakh', 'Between 4 to 6 Lakh'),
                        ('Above 6 Lakh', 'Above 6 Lakh'),
                    ]
                )),
                ('income', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('allotted_category', models.CharField(blank=True, max_length=50, null=True)),
                # PhD / GATE specific
                ('gate_qualified', models.CharField(
                    blank=True, max_length=3, null=True,
                    choices=[('YES', 'Yes'), ('NO', 'No')],
                    help_text='GATE Qualified'
                )),
                ('gate_stream', models.CharField(blank=True, max_length=100, null=True)),
                ('gate_rank', models.IntegerField(blank=True, null=True)),
                # System / batch tracking
                ('admission_semester', models.CharField(
                    blank=True, max_length=10, null=True,
                    choices=[('Odd', 'Odd Semester'), ('Even', 'Even Semester')]
                )),
                ('year', models.IntegerField(
                    db_column='batch_year',
                    default=applications.programme_curriculum.models_student_management.get_current_academic_year,
                    help_text='Admission batch year (e.g., 2025)'
                )),
                ('academic_year', models.CharField(blank=True, max_length=20)),
                ('reported_status', models.CharField(
                    default='NOT_REPORTED', max_length=20,
                    choices=[
                        ('NOT_REPORTED', 'Not Reported'),
                        ('REPORTED', 'Reported'),
                        ('WITHDRAWAL', 'Withdrawal'),
                    ]
                )),
                ('source', models.CharField(default='admin_upload', max_length=50)),
                # Auth / metadata
                ('user', models.ForeignKey(
                    blank=True, db_column='user_account_id', null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='phd_student_profile',
                    to=settings.AUTH_USER_MODEL
                )),
                ('uploaded_by', models.ForeignKey(
                    blank=True, db_column='created_by_id', null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='uploaded_phd_students',
                    to=settings.AUTH_USER_MODEL
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'PhD Student Batch Upload',
                'verbose_name_plural': 'PhD Student Batch Uploads',
                'ordering': ['roll_number', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='phdstudentbatchupload',
            index=models.Index(fields=['year'], name='phd_stud_year_idx'),
        ),
        migrations.AddIndex(
            model_name='phdstudentbatchupload',
            index=models.Index(fields=['discipline'], name='phd_stud_disc_idx'),
        ),
        migrations.AddIndex(
            model_name='phdstudentbatchupload',
            index=models.Index(fields=['reported_status'], name='phd_stud_status_idx'),
        ),
        migrations.AddIndex(
            model_name='phdstudentbatchupload',
            index=models.Index(fields=['admission_semester'], name='phd_stud_sem_idx'),
        ),
        migrations.AddIndex(
            model_name='phdstudentbatchupload',
            index=models.Index(fields=['application_no'], name='phd_stud_appno_idx'),
        ),
        migrations.AddIndex(
            model_name='phdstudentbatchupload',
            index=models.Index(fields=['roll_number'], name='phd_stud_roll_idx'),
        ),
    ]
