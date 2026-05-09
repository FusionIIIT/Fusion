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
        # Safe migration that checks if table exists before creating indexes
        migrations.RunSQL(
            sql=[
                # Check if course_registration table exists and create indexes only if it does
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = 'course_registration'
                    ) THEN
                        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_course_reg_main_query 
                            ON course_registration(session, semester_type, course_id_id, registration_type, student_id_id)';
                        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_course_reg_session_semester_course 
                            ON course_registration(session, semester_type, course_id_id)';
                        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_course_reg_student 
                            ON course_registration(student_id_id)';
                        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_course_reg_type 
                            ON course_registration(registration_type)';
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
