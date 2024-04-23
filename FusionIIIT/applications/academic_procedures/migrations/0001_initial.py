# Generated by Django 3.1.5 on 2024-04-15 23:58

import datetime
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('globals', '0001_initial'),
        ('academic_information', '0001_initial'),
        ('programme_curriculum', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assistantship_status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_status', models.BooleanField()),
                ('hod_status', models.BooleanField()),
                ('account_status', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='MinimumCredits',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.IntegerField()),
                ('credits', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ThesisTopicProcess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('research_area', models.CharField(max_length=50)),
                ('thesis_topic', models.CharField(max_length=1000)),
                ('submission_by_student', models.BooleanField(default=False)),
                ('pending_supervisor', models.BooleanField(default=True)),
                ('approval_supervisor', models.BooleanField(default=False)),
                ('forwarded_to_hod', models.BooleanField(default=False)),
                ('pending_hod', models.BooleanField(default=True)),
                ('approval_by_hod', models.BooleanField(default=False)),
                ('date', models.DateField(default=datetime.datetime.now)),
                ('co_supervisor_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='thesistopicprocess_co_supervisor', to='globals.faculty')),
                ('curr_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='academic_information.curriculum')),
                ('member1', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='thesistopicprocess_member1', to='globals.faculty')),
                ('member2', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='thesistopicprocess_member2', to='globals.faculty')),
                ('member3', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='thesistopicprocess_member3', to='globals.faculty')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                ('supervisor_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='thesistopicprocess_supervisor', to='globals.faculty')),
            ],
            options={
                'db_table': 'ThesisTopicProcess',
            },
        ),
        migrations.CreateModel(
            name='Thesis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=1000)),
                ('reg_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='globals.extrainfo')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                ('supervisor_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='globals.faculty')),
            ],
            options={
                'db_table': 'Thesis',
            },
        ),
        migrations.CreateModel(
            name='TeachingCreditRegistration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('req_pending', models.BooleanField(default=True)),
                ('course_completion', models.BooleanField(default=False)),
                ('approved_course', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='teachingcreditregistration_approved_course', to='academic_information.curriculum')),
                ('curr_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teachingcreditregistration_curr1', to='academic_information.curriculum')),
                ('curr_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teachingcreditregistration_curr2', to='academic_information.curriculum')),
                ('curr_3', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teachingcreditregistration_curr3', to='academic_information.curriculum')),
                ('curr_4', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teachingcreditregistration_curr4', to='academic_information.curriculum')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                ('supervisor_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='teachingcreditregistration_supervisor_id', to='globals.faculty')),
            ],
            options={
                'db_table': 'TeachingCreditRegistration',
            },
        ),
        migrations.CreateModel(
            name='StudentRegistrationChecks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pre_registration_flag', models.BooleanField(default=False)),
                ('final_registration_flag', models.BooleanField(default=False)),
                ('semester_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.semester')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'StudentRegistrationChecks',
            },
        ),
        migrations.CreateModel(
            name='StudentRegistrationCheck',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pre_registration_flag', models.BooleanField(default=False)),
                ('final_registration_flag', models.BooleanField(default=False)),
                ('semester', models.IntegerField(default=1)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'StudentRegistrationCheck',
            },
        ),
        migrations.CreateModel(
            name='SemesterMarks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('q1', models.FloatField(default=None)),
                ('mid_term', models.FloatField(default=None)),
                ('q2', models.FloatField(default=None)),
                ('end_term', models.FloatField(default=None)),
                ('other', models.FloatField(default=None)),
                ('grade', models.CharField(choices=[('O', 'O'), ('A+', 'A+'), ('A', 'A'), ('B+', 'B+'), ('B', 'B'), ('C+', 'C+'), ('C', 'C'), ('D+', 'D+'), ('D', 'D'), ('F', 'F'), ('S', 'S'), ('X', 'X')], max_length=5, null=True)),
                ('curr_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.course')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'SemesterMarks',
            },
        ),
        migrations.CreateModel(
            name='PhDProgressExamination',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('theme', models.CharField(max_length=50)),
                ('seminar_date_time', models.DateTimeField()),
                ('place', models.CharField(max_length=30)),
                ('work_done', models.TextField()),
                ('specific_contri_curr_semester', models.TextField()),
                ('future_plan', models.TextField()),
                ('details', models.FileField(upload_to='academic_procedure/Uploaded_document/PhdProgressDetails/')),
                ('papers_published', models.IntegerField()),
                ('presented_papers', models.IntegerField()),
                ('papers_submitted', models.IntegerField()),
                ('quality_of_work', models.CharField(choices=[('Excellent', 'Excellent'), ('Good', 'Good'), ('Satisfactory', 'Satisfactory'), ('Unsatisfactory', 'Unsatisfactory')], max_length=20)),
                ('quantity_of_work', models.CharField(choices=[('Enough', 'Enough'), ('Just Sufficient', 'Just Sufficient'), ('Insufficient', 'Insufficient')], max_length=15)),
                ('Overall_grade', models.CharField(choices=[('A+', 'A+'), ('A', 'A'), ('B+', 'B+'), ('B', 'B'), ('C+', 'C+'), ('C', 'C'), ('D+', 'D'), ('D', 'D'), ('F', 'F')], max_length=2)),
                ('completion_period', models.IntegerField(null=True)),
                ('panel_report', models.TextField(null=True)),
                ('continuation_enhancement_assistantship', models.CharField(choices=[('yes', 'yes'), ('no', 'no'), ('not applicable', 'not applicable')], max_length=20, null=True)),
                ('enhancement_assistantship', models.CharField(choices=[('yes', 'yes'), ('no', 'no'), ('not applicable', 'not applicable')], max_length=15, null=True)),
                ('annual_progress_seminar', models.CharField(choices=[('Give again', 'Give again'), ('Not Applicable', 'Not Applicable'), ('Approved', 'Approved')], max_length=20, null=True)),
                ('commments', models.TextField(null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
        ),
        migrations.CreateModel(
            name='MTechGraduateSeminarReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('theme_of_work', models.TextField()),
                ('date', models.DateField()),
                ('place', models.CharField(max_length=30)),
                ('time', models.TimeField()),
                ('work_done_till_previous_sem', models.TextField()),
                ('specific_contri_in_cur_sem', models.TextField()),
                ('future_plan', models.TextField()),
                ('brief_report', models.FileField(upload_to='academic_procedure/Uploaded_document/GraduateSeminarReport/')),
                ('publication_submitted', models.IntegerField()),
                ('publication_accepted', models.IntegerField()),
                ('paper_presented', models.IntegerField()),
                ('papers_under_review', models.IntegerField()),
                ('quality_of_work', models.CharField(choices=[('Excellent', 'Excellent'), ('Good', 'Good'), ('Satisfactory', 'Satisfactory'), ('Unsatisfactory', 'Unsatisfactory')], max_length=20)),
                ('quantity_of_work', models.CharField(choices=[('Enough', 'Enough'), ('Just Sufficient', 'Just Sufficient'), ('Insufficient', 'Insufficient')], max_length=15)),
                ('Overall_grade', models.CharField(choices=[('A+', 'A+'), ('A', 'A'), ('B+', 'B+'), ('B', 'B'), ('C+', 'C+'), ('C', 'C'), ('D+', 'D'), ('D', 'D'), ('F', 'F')], max_length=2)),
                ('panel_report', models.CharField(choices=[('Give again', 'Give again'), ('Not Applicable', 'Not Applicable'), ('Approved', 'Approved')], max_length=15)),
                ('suggestion', models.TextField(null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
        ),
        migrations.CreateModel(
            name='MessDue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.CharField(choices=[('Jan', 'January'), ('Feb', 'Febuary'), ('Mar', 'March'), ('Apr', 'April'), ('May', 'May'), ('Jun', 'June'), ('Jul', 'July'), ('Aug', 'August'), ('Sep', 'September'), ('Oct', 'October'), ('Nov', 'November'), ('Dec', 'December')], max_length=10)),
                ('year', models.IntegerField(choices=[(2024, 2024), (2023, 2023)])),
                ('description', models.CharField(choices=[('Stu_paid', 'Paid'), ('Stu_due', 'Due')], max_length=15)),
                ('amount', models.IntegerField()),
                ('remaining_amount', models.IntegerField()),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
        ),
        migrations.CreateModel(
            name='MarkSubmissionCheck',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verified', models.BooleanField(default=False)),
                ('submitted', models.BooleanField(default=False)),
                ('announced', models.BooleanField(default=False)),
                ('curr_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.course')),
            ],
            options={
                'db_table': 'MarkSubmissionCheck',
            },
        ),
        migrations.CreateModel(
            name='InitialRegistrations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('priority', models.IntegerField(blank=True, null=True)),
                ('course_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.course')),
                ('course_slot_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='programme_curriculum.courseslot')),
                ('semester_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.semester')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'InitialRegistrations',
            },
        ),
        migrations.CreateModel(
            name='InitialRegistration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('priority', models.IntegerField(blank=True, null=True)),
                ('course_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.course')),
                ('course_slot_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='programme_curriculum.courseslot')),
                ('semester_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.semester')),
                ('student_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'InitialRegistration',
            },
        ),
        migrations.CreateModel(
            name='FinalRegistrations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.IntegerField()),
                ('batch', models.IntegerField(default=2024)),
                ('verified', models.BooleanField(default=False)),
                ('curr_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.curriculum')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'FinalRegistrations',
            },
        ),
        migrations.CreateModel(
            name='FinalRegistration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verified', models.BooleanField(default=False)),
                ('course_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.course')),
                ('course_slot_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='programme_curriculum.courseslot')),
                ('semester_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.semester')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'FinalRegistration',
            },
        ),
        migrations.CreateModel(
            name='FeePayments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode', models.CharField(choices=[('Axis Easypay', 'Axis Easypay'), ('Subpaisa', 'Subpaisa'), ('NEFT', 'NEFT'), ('RTGS', 'RTGS'), ('Bank Challan', 'Bank Challan'), ('Edu Loan', 'Edu Loan')], max_length=20)),
                ('transaction_id', models.CharField(max_length=40)),
                ('fee_receipt', models.FileField(null=True, upload_to='fee_receipt/')),
                ('deposit_date', models.DateField(default=datetime.date.today)),
                ('utr_number', models.CharField(max_length=40, null=True)),
                ('fee_paid', models.IntegerField(default=0)),
                ('reason', models.CharField(max_length=20, null=True)),
                ('actual_fee', models.IntegerField(default=0)),
                ('semester_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.semester')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'FeePayments',
            },
        ),
        migrations.CreateModel(
            name='FeePayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.IntegerField(default=1)),
                ('batch', models.IntegerField(default=2016)),
                ('mode', models.CharField(choices=[('Axis Easypay', 'Axis Easypay'), ('Subpaisa', 'Subpaisa'), ('NEFT', 'NEFT'), ('RTGS', 'RTGS'), ('Bank Challan', 'Bank Challan'), ('Edu Loan', 'Edu Loan')], max_length=20)),
                ('transaction_id', models.CharField(max_length=40)),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
        ),
        migrations.CreateModel(
            name='Dues',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mess_due', models.IntegerField()),
                ('hostel_due', models.IntegerField()),
                ('library_due', models.IntegerField()),
                ('placement_cell_due', models.IntegerField()),
                ('academic_due', models.IntegerField()),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'Dues',
            },
        ),
        migrations.CreateModel(
            name='CoursesMtech',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('specialization', models.CharField(choices=[('Power and Control', 'Power and Control'), ('Microwave and Communication Engineering', 'Microwave and Communication Engineering'), ('Micro-nano Electronics', 'Micro-nano Electronics'), ('CAD/CAM', 'CAD/CAM'), ('Design', 'Design'), ('Manufacturing', 'Manufacturing'), ('CSE', 'CSE'), ('Mechatronics', 'Mechatronics'), ('MDes', 'MDes'), ('all', 'all')], max_length=40)),
                ('c_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.course')),
            ],
        ),
        migrations.CreateModel(
            name='CourseRequested',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.course')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'CourseRequested',
            },
        ),
        migrations.CreateModel(
            name='course_registration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('working_year', models.IntegerField(blank=True, choices=[(2024, 2024), (2023, 2023)], null=True)),
                ('course_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.course')),
                ('course_slot_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='programme_curriculum.courseslot')),
                ('semester_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.semester')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'course_registration',
            },
        ),
        migrations.CreateModel(
            name='BranchChange',
            fields=[
                ('c_id', models.AutoField(primary_key=True, serialize=False)),
                ('applied_date', models.DateField(default=datetime.datetime.now)),
                ('branches', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='globals.departmentinfo')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
        ),
        migrations.CreateModel(
            name='Bonafide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(max_length=50)),
                ('purpose', models.CharField(max_length=100)),
                ('academic_year', models.CharField(max_length=15)),
                ('enrolled_course', models.CharField(max_length=10)),
                ('complaint_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'Bonafide',
            },
        ),
        migrations.CreateModel(
            name='AssistantshipClaim',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('month', models.CharField(choices=[('Jan', 'January'), ('Feb', 'Febuary'), ('Mar', 'March'), ('Apr', 'April'), ('May', 'May'), ('Jun', 'June'), ('Jul', 'July'), ('Aug', 'August'), ('Sep', 'September'), ('Oct', 'October'), ('Nov', 'November'), ('Dec', 'December')], max_length=10)),
                ('year', models.IntegerField(choices=[(2024, 2024), (2023, 2023)])),
                ('bank_account', models.CharField(max_length=11)),
                ('applicability', models.CharField(choices=[('GATE', 'GATE'), ('NET', 'NET'), ('CEED', 'CEED')], max_length=5)),
                ('ta_supervisor_remark', models.BooleanField(default=False)),
                ('thesis_supervisor_remark', models.BooleanField(default=False)),
                ('hod_approval', models.BooleanField(default=False)),
                ('acad_approval', models.BooleanField(default=False)),
                ('account_approval', models.BooleanField(default=False)),
                ('stipend', models.IntegerField(default=0)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
                ('ta_supervisor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='TA_SUPERVISOR', to='globals.faculty')),
                ('thesis_supervisor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='THESIS_SUPERVISOR', to='globals.faculty')),
            ],
        ),
        migrations.CreateModel(
            name='Register',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(default=2024)),
                ('semester', models.IntegerField()),
                ('curr_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.curriculum')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.student')),
            ],
            options={
                'db_table': 'Register',
                'unique_together': {('curr_id', 'student_id')},
            },
        ),
    ]