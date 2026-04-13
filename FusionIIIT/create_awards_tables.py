"""
create_awards_tables.py
========================
Creates the two new awards tables directly in the PostgreSQL DB.
Run once to set up the awards module tables.

USAGE:
  cd FusionIIIT
  python create_awards_tables.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
django.setup()

from django.db import connection

CREATE_AUTO_AWARD_SQL = """
CREATE TABLE IF NOT EXISTS awards_auto_award_result (
    id              SERIAL PRIMARY KEY,
    award_name      VARCHAR(100) NOT NULL,
    award_code      VARCHAR(30)  NOT NULL DEFAULT 'CGM',
    student_id      VARCHAR(20)  NOT NULL REFERENCES globals_extrainfo(id) ON DELETE CASCADE,
    cpi             DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    programme       VARCHAR(20)  NOT NULL DEFAULT '',
    branch          VARCHAR(100) NOT NULL DEFAULT '',
    batch           INTEGER      NOT NULL DEFAULT 2023,
    generated_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);
"""

CREATE_AWARD_APPLICATION_SQL = """
CREATE TABLE IF NOT EXISTS awards_award_application (
    id          SERIAL PRIMARY KEY,
    student_id  VARCHAR(20)  NOT NULL REFERENCES globals_extrainfo(id) ON DELETE CASCADE,
    award_type  VARCHAR(30)  NOT NULL,
    form_data   JSONB        NOT NULL DEFAULT '{}',
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, award_type)
);
"""

def main():
    print("Creating awards tables...")
    with connection.cursor() as cursor:
        cursor.execute(CREATE_AUTO_AWARD_SQL)
        print("  [+] awards_auto_award_result — OK")
        cursor.execute(CREATE_AWARD_APPLICATION_SQL)
        print("  [+] awards_award_application — OK")
    print("\n[DONE] Awards tables ready.")

if __name__ == '__main__':
    main()
