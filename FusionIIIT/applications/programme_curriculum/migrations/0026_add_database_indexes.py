# Database Optimization Migration for Student List Generation

from django.db import migrations

class Migration(migrations.Migration):
    """
    Add database indexes to optimize student list generation queries
    """
    
    dependencies = [
        ('programme_curriculum', '0025_update_minority_values'),
    ]

    operations = [
        # Add database indexes for optimized query performance
        migrations.RunSQL(
            sql=[
                # Main composite index for course registration queries
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'course_registration'
                    ) THEN
                        CREATE INDEX IF NOT EXISTS idx_course_reg_main_query
                        ON course_registration(session, semester_type, course_id_id, registration_type, student_id_id);
                    END IF;
                END $$;
                """,
                
                # Individual indexes for course registration
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'course_registration'
                    ) THEN
                        CREATE INDEX IF NOT EXISTS idx_course_reg_session_semester_course
                        ON course_registration(session, semester_type, course_id_id);
                    END IF;
                END $$;
                """,
                
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'course_registration'
                    ) THEN
                        CREATE INDEX IF NOT EXISTS idx_course_reg_student
                        ON course_registration(student_id_id);
                    END IF;
                END $$;
                """,
                
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'course_registration'
                    ) THEN
                        CREATE INDEX IF NOT EXISTS idx_course_reg_type
                        ON course_registration(registration_type);
                    END IF;
                END $$;
                """
            ],
            
            # Reverse migration to drop indexes
            reverse_sql=[
                "DROP INDEX IF EXISTS idx_course_reg_main_query;",
                "DROP INDEX IF EXISTS idx_course_reg_session_semester_course;",
                "DROP INDEX IF EXISTS idx_course_reg_student;",
                "DROP INDEX IF EXISTS idx_course_reg_type;"
            ]
        )
    ]
