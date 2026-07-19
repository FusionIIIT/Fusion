# Renames for consistency (see project decision log, 2026-07-16):
#   SeminarEntry/SeminarConsent/SeminarComment -> ProgressSeminarEntry/Consent/Comment
#     (these are unambiguously progress-seminar-only; the bare "Seminar" prefix
#     was ambiguous against OpenSeminar in this same app)
#   TeachingCreditPreRegistration -> TeachingCreditAllocation
#     ("Pre-Registration" stopped making sense once the legacy
#     TeachingCreditRegistration table below became the real enrollment step
#     that happens *before* this one)
# and repurposing the legacy, dead TeachingCreditRegistration table into a
# semester-enrollment record mirroring ThesisRegistration/ProgressSeminarRegistration.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('programme_curriculum', '0045_rename_progress_seminar_to_seminar'),
        ('academic_procedures', '0035_teachingcreditevaluationresponse_teachingcreditpreregistration'),
    ]

    operations = [
        migrations.RenameModel(old_name='SeminarEntry', new_name='ProgressSeminarEntry'),
        migrations.RenameModel(old_name='SeminarConsent', new_name='ProgressSeminarConsent'),
        migrations.RenameModel(old_name='SeminarComment', new_name='ProgressSeminarComment'),
        migrations.RenameModel(old_name='TeachingCreditPreRegistration', new_name='TeachingCreditAllocation'),
        migrations.AlterField(
            model_name='teachingcreditallocation',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teaching_credit_allocations', to='academic_information.student'),
        ),

        # Repurpose the legacy TeachingCreditRegistration table (previously an
        # admin-entered, 4-choice teaching-credit record predating
        # TeachingCreditAllocation) into a lightweight semester-enrollment
        # record, matching ThesisRegistration / ProgressSeminarRegistration.
        # It was dead (only reachable via a retired Django-template admin
        # page, never used by the React frontend), so its existing rows carry
        # no data worth preserving under the new schema -- clear it first so
        # the new NOT NULL fields below don't need throwaway defaults.
        migrations.RunSQL(
            sql='DELETE FROM "TeachingCreditRegistration";',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveField(model_name='teachingcreditregistration', name='approved_course'),
        migrations.RemoveField(model_name='teachingcreditregistration', name='course_completion'),
        migrations.RemoveField(model_name='teachingcreditregistration', name='curr_1'),
        migrations.RemoveField(model_name='teachingcreditregistration', name='curr_2'),
        migrations.RemoveField(model_name='teachingcreditregistration', name='curr_3'),
        migrations.RemoveField(model_name='teachingcreditregistration', name='curr_4'),
        migrations.RemoveField(model_name='teachingcreditregistration', name='req_pending'),
        migrations.RemoveField(model_name='teachingcreditregistration', name='supervisor_id'),
        migrations.RemoveField(model_name='teachingcreditregistration', name='student_id'),
        migrations.AddField(
            model_name='teachingcreditregistration',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teaching_credit_registrations', to='academic_information.student'),
        ),
        migrations.AddField(
            model_name='teachingcreditregistration',
            name='teaching_credit_slot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='programme_curriculum.teachingcreditslot'),
        ),
        migrations.AddField(
            model_name='teachingcreditregistration',
            name='semester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.semester'),
        ),
        migrations.AddField(
            model_name='teachingcreditregistration',
            name='working_year',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='teachingcreditregistration',
            name='academic_session',
            field=models.CharField(blank=True, max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='teachingcreditregistration',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending Verification'), ('verified', 'Verified'), ('rejected', 'Rejected')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='teachingcreditregistration',
            name='registered_on',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='teachingcreditregistration',
            name='remarks',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterUniqueTogether(
            name='teachingcreditregistration',
            unique_together={('student', 'semester')},
        ),
    ]
