from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('programme_curriculum', '0044_teachingcredit_teachingcreditslot'),
        # academic_procedures 0021 creates FKs to ProgressSeminarSlot/ProgressSeminar
        # under their pre-rename names; it must apply before this rename runs, or
        # migration state-building fails with a lazy-reference error.
        ('academic_procedures', '0021_thesis_registration_models'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ProgressSeminar',
            new_name='Seminar',
        ),
        migrations.RenameField(
            model_name='seminar',
            old_name='working_progress_seminar',
            new_name='working_seminar',
        ),
        migrations.RenameModel(
            old_name='ProgressSeminarSlot',
            new_name='SeminarSlot',
        ),
        migrations.RenameField(
            model_name='seminarslot',
            old_name='progress_seminar_slot_info',
            new_name='seminar_slot_info',
        ),
        migrations.RenameField(
            model_name='seminarslot',
            old_name='progress_seminars',
            new_name='seminars',
        ),
    ]
