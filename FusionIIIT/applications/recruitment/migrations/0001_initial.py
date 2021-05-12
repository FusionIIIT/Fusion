# Generated by Django 3.1.5 on 2021-05-01 09:50

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EducationalDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('university', models.CharField(max_length=200)),
                ('board', models.CharField(max_length=200)),
                ('year_of_passing', models.IntegerField()),
                ('division', models.CharField(max_length=6)),
            ],
        ),
        migrations.CreateModel(
            name='Experience',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration', models.IntegerField(null=True)),
                ('organization', models.CharField(max_length=100, null=True)),
                ('area', models.CharField(max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Vacancy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('advertisement_number', models.IntegerField()),
                ('job_description', models.TextField()),
                ('job_notification', models.FileField(upload_to='')),
                ('number_of_vacancy', models.IntegerField(default=1)),
                ('job_type', models.CharField(choices=[('T', 'Teaching'), ('NT', 'Non-Teaching')], max_length=15)),
                ('last_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='ThesisSupervision',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_of_student', models.CharField(max_length=200)),
                ('masters_or_phd', models.CharField(choices=[('Masters', 'Masters'), ('PhD', 'PhD')], max_length=20)),
                ('year_of_completion', models.IntegerField()),
                ('title_of_thesis', models.CharField(max_length=100)),
                ('co_guides', models.CharField(max_length=200, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TeachingExperience',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teaching_experience', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recruitment.experience')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SponsoredProjects',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.CharField(max_length=10)),
                ('sponsoring_organisation', models.CharField(max_length=200)),
                ('title_of_project', models.CharField(max_length=200)),
                ('grant_amount', models.IntegerField(null=True)),
                ('co_investigators', models.CharField(max_length=200, null=True)),
                ('status', models.CharField(choices=[('Ongoing', 'Ongoing'), ('Completed', 'Completed')], max_length=20)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ResearchExperience',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('research_experience', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recruitment.experience')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='References',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('address', models.TextField(null=True)),
                ('email', models.EmailField(max_length=254)),
                ('mobile_number', models.BigIntegerField()),
                ('department', models.CharField(max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='QualifiedExams',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('net', models.BooleanField()),
                ('gate', models.BooleanField()),
                ('jrf', models.BooleanField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Publications',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('referred_journal', models.CharField(max_length=100)),
                ('sci_index_journal', models.CharField(max_length=100)),
                ('international_conferences', models.CharField(max_length=100, null=True)),
                ('national_conferences', models.CharField(max_length=100, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PersonalDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='Dr.', max_length=20)),
                ('sex', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], default='M', max_length=2)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='')),
                ('marital_status', models.CharField(choices=[('M', 'Married'), ('U', 'Unmarried')], max_length=10)),
                ('discipline', models.CharField(max_length=50)),
                ('specialization', models.CharField(choices=[('MA', 'Major'), ('MI', 'Minor')], max_length=10)),
                ('category', models.CharField(choices=[('PH', 'Physically Handicapped'), ('UR', 'Unreserved'), ('OBC', 'Other Backward Classes'), ('SC', 'Scheduled Castes'), ('ST', 'Scheduled Tribes'), ('EWS', 'Economic Weaker Section')], max_length=20)),
                ('father_name', models.CharField(default='', max_length=40)),
                ('address_correspondence', models.TextField(max_length=1000)),
                ('address_permanent', models.TextField(default='', max_length=1000)),
                ('email_alternate', models.EmailField(default='', max_length=50, null=True)),
                ('phone_no', models.BigIntegerField(default=9999999999, null=True)),
                ('mobile_no_first', models.BigIntegerField(default=9999999999)),
                ('mobile_no_second', models.BigIntegerField(default=9999999999, null=True)),
                ('date_of_birth', models.DateField(default=datetime.date(1970, 1, 1))),
                ('nationality', models.CharField(max_length=30)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Patent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filed_national', models.CharField(max_length=200, null=True)),
                ('filed_international', models.CharField(max_length=200, null=True)),
                ('award_national', models.CharField(max_length=200, null=True)),
                ('award_international', models.CharField(max_length=200, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PapersInReferredJournal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author', models.CharField(max_length=100)),
                ('year', models.IntegerField()),
                ('published', models.BooleanField()),
                ('accepted', models.BooleanField()),
                ('title', models.CharField(max_length=100)),
                ('reference_of_journal', models.CharField(max_length=100)),
                ('impact_factor', models.CharField(max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='NationalConference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author', models.CharField(max_length=100)),
                ('year', models.IntegerField()),
                ('title', models.CharField(max_length=100)),
                ('name_and_place_of_conference', models.CharField(max_length=200)),
                ('presented', models.BooleanField()),
                ('published', models.BooleanField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='InternationalConference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author', models.CharField(max_length=100)),
                ('year', models.IntegerField()),
                ('title', models.CharField(max_length=100)),
                ('name_and_place_of_conference', models.CharField(max_length=200)),
                ('presented', models.BooleanField()),
                ('published', models.BooleanField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='IndustrialExperience',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.IntegerField(null=True)),
                ('organization', models.CharField(max_length=200, null=True)),
                ('title_of_post', models.CharField(max_length=200, null=True)),
                ('nature_of_work', models.TextField(null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ExperienceDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_experience_months', models.IntegerField(null=True)),
                ('member_of_professional_body', models.CharField(max_length=200, null=True)),
                ('employer', models.CharField(max_length=100, null=True)),
                ('position_held', models.CharField(max_length=100, null=True)),
                ('date_of_joining', models.DateField(null=True)),
                ('date_of_leaving', models.DateField(null=True)),
                ('pay_in_payband', models.CharField(max_length=20, null=True)),
                ('payband', models.CharField(max_length=20, null=True)),
                ('AGP', models.CharField(max_length=20, null=True)),
                ('reasons_for_leaving', models.TextField(null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CoursesTaught',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, null=True)),
                ('level', models.CharField(choices=[('UG', 'UnderGraduate'), ('PG', 'PostGraduate')], max_length=20, null=True)),
                ('number_of_times', models.IntegerField(null=True)),
                ('developed_by_you', models.BooleanField(null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Consultancy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.CharField(max_length=10)),
                ('sponsoring_organisation', models.CharField(max_length=200)),
                ('title_of_project', models.CharField(max_length=200)),
                ('grant_amount', models.IntegerField(null=True)),
                ('co_investigators', models.CharField(max_length=200, null=True)),
                ('status', models.CharField(choices=[('Ongoing', 'Ongoing'), ('Completed', 'Completed')], max_length=20)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Books',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_of_book', models.CharField(max_length=100)),
                ('year', models.IntegerField()),
                ('published', models.BooleanField()),
                ('title', models.CharField(max_length=100)),
                ('publisher', models.CharField(max_length=200)),
                ('co_author', models.CharField(max_length=100, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BankDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_reference_number', models.CharField(max_length=20)),
                ('payment_date', models.DateField()),
                ('bank_name', models.CharField(max_length=100)),
                ('bank_branch', models.CharField(max_length=200)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='applied',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('advertisement_number', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recruitment.vacancy')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AdministrativeExperience',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.IntegerField(null=True)),
                ('organization', models.CharField(max_length=200, null=True)),
                ('title_of_post', models.CharField(max_length=200, null=True)),
                ('nature_of_work', models.TextField(null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AcademicDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area_of_specialization', models.TextField()),
                ('current_area_of_research', models.TextField()),
                ('date_of_enrollment_in_phd', models.DateField()),
                ('date_of_phd_defence', models.DateField()),
                ('date_of_award_of_phd', models.DateField()),
                ('XIIth', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='XIIth_details', to='recruitment.educationaldetails')),
                ('Xth', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='Xth_details', to='recruitment.educationaldetails')),
                ('graduation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='graduation_details', to='recruitment.educationaldetails')),
                ('phd', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='phd_details', to='recruitment.educationaldetails')),
                ('post_graduation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='post_graduations_details', to='recruitment.educationaldetails')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
