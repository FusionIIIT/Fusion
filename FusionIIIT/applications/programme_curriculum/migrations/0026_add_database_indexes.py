# Database Optimization Migration for Student List Generation

from django.db import migrations


class Migration(migrations.Migration):
    """
    Add database indexes to optimize student list generation queries.
    The underlying table is not guaranteed to exist in every setup, so this
    migration is intentionally defensive.
    """

    dependencies = [
        ('programme_curriculum', '0025_update_minority_values'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF to_regclass('public.course_registration') IS NOT NULL THEN
                    CREATE INDEX IF NOT EXISTS idx_course_reg_main_query
                    ON course_registration(session, semester_type, course_id_id, registration_type, student_id_id);

                    CREATE INDEX IF NOT EXISTS idx_course_reg_session_semester_course
                    ON course_registration(session, semester_type, course_id_id);

                    CREATE INDEX IF NOT EXISTS idx_course_reg_student
                    ON course_registration(student_id_id);

                    CREATE INDEX IF NOT EXISTS idx_course_reg_type
                    ON course_registration(registration_type);
                END IF;
            END $$;
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS idx_course_reg_main_query;
            DROP INDEX IF EXISTS idx_course_reg_session_semester_course;
            DROP INDEX IF EXISTS idx_course_reg_student;
            DROP INDEX IF EXISTS idx_course_reg_type;
            """,
        )
    ]