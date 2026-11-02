from django.db import migrations


FORWARD_SQL = """
CREATE OR REPLACE FUNCTION public.enforce_single_basic_designation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        IF NEW.designation_id IS NOT NULL AND (
            SELECT basic
            FROM public.globals_designation
            WHERE id = NEW.designation_id
        ) = TRUE THEN
            IF EXISTS (
                SELECT 1
                FROM public.globals_holdsdesignation h
                JOIN public.globals_designation d
                  ON h.designation_id = d.id
                WHERE h.user_id = NEW.user_id
                  AND d.basic = TRUE
                  AND h.id <> COALESCE(NEW.id, -1)
            ) THEN
                RAISE EXCEPTION 'A user can only have one basic designation.';
            END IF;
        END IF;

        RETURN NEW;
    END;
    $$;
"""


class Migration(migrations.Migration):
    dependencies = [
        ('globals', '0014_user_activity_log'),
    ]

    operations = [
        migrations.RunSQL(FORWARD_SQL, migrations.RunSQL.noop),
    ]
