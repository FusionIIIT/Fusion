from django.db import migrations


def backfill_session_and_semester_type(apps, schema_editor):
    """
    Fix all course_registration rows that were created by verify_registration
    without session or semester_type fields set.
    Derives them from semester_no parity + working_year.
    """
    CourseRegistration = apps.get_model('academic_procedures', 'course_registration')

    broken = CourseRegistration.objects.filter(
        session__isnull=True
    ).select_related('semester_id')

    to_update = []
    for reg in broken:
        sem_no = reg.semester_id.semester_no
        sem_type = "Odd Semester" if sem_no % 2 == 1 else "Even Semester"

        year = reg.working_year
        if not year:
            # Fallback: derive year from the semester's start date if available
            start = getattr(reg.semester_id, 'start_semester', None)
            if start:
                year = start.year
            else:
                continue  # Cannot determine year — skip; do not corrupt data

        if sem_type == "Odd Semester":
            session = f"{year}-{str(year + 1)[-2:]}"
        else:
            session = f"{year - 1}-{str(year)[-2:]}"

        reg.session = session
        reg.semester_type = sem_type
        to_update.append(reg)

    if to_update:
        CourseRegistration.objects.bulk_update(to_update, ['session', 'semester_type'], batch_size=500)


def reverse_backfill(apps, schema_editor):
    # Not reversible — we cannot safely infer which rows were NULL before.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('academic_procedures', '0019_swayamreplacementrequest'),
    ]

    operations = [
        migrations.RunPython(
            backfill_session_and_semester_type,
            reverse_code=reverse_backfill,
        ),
    ]
