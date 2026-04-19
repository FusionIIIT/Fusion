import os
import django
import sys

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Fusion.settings.development")
django.setup()

from django.db import connection

CREATE_SCHOLARSHIP_SETTINGS_SQL = """
CREATE TABLE IF NOT EXISTS scholarships_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);
"""

# Seed default deadline if not exists
SEED_DEADLINE_SQL = """
INSERT INTO scholarships_settings (setting_key, setting_value)
VALUES ('application_deadline', '2026-05-01 23:59:59')
ON CONFLICT (setting_key) DO NOTHING;
"""

def create_tables():
    print("Creating scholarship tables...")
    with connection.cursor() as cursor:
        cursor.execute(CREATE_SCHOLARSHIP_SETTINGS_SQL)
        print("  [+] scholarships_settings - OK")
        cursor.execute(SEED_DEADLINE_SQL)
        print("  [+] default deadline seeded - OK")

if __name__ == "__main__":
    try:
        create_tables()
        print("\n[DONE] Scholarship tables ready.")
    except Exception as e:
        print(f"\n[ERROR] Failed to create tables: {e}")
        sys.exit(1)
