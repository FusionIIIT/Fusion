"""
Migration: Remove Central Mess application tables and migration history.

The central_mess application has been removed from the codebase.
This migration drops all its database tables and cleans up the
django_migrations table so Django is unaware of the removed app.

Safe to run on production: uses IF EXISTS so it is a no-op if
tables were never created or have already been removed.
"""

from django.db import migrations


# Tables created by central_mess migrations (child tables first to
# respect FK constraints, though DROP … CASCADE handles it anyway).
DROP_CENTRAL_MESS_TABLES = """
DROP TABLE IF EXISTS central_mess_mess_minutes             CASCADE;
DROP TABLE IF EXISTS central_mess_menu_change_request      CASCADE;
DROP TABLE IF EXISTS central_mess_vacation_food            CASCADE;
DROP TABLE IF EXISTS central_mess_update_payment           CASCADE;
DROP TABLE IF EXISTS central_mess_special_request          CASCADE;
DROP TABLE IF EXISTS central_mess_registration_request     CASCADE;
DROP TABLE IF EXISTS central_mess_reg_records              CASCADE;
DROP TABLE IF EXISTS central_mess_reg_main                 CASCADE;
DROP TABLE IF EXISTS central_mess_rebate                   CASCADE;
DROP TABLE IF EXISTS central_mess_payments                 CASCADE;
DROP TABLE IF EXISTS central_mess_feedback                 CASCADE;
DROP TABLE IF EXISTS central_mess_deregistration_request   CASCADE;
DROP TABLE IF EXISTS central_mess_monthly_bill             CASCADE;
DROP TABLE IF EXISTS central_mess_messinfo                 CASCADE;
DROP TABLE IF EXISTS central_mess_mess_meeting             CASCADE;
DROP TABLE IF EXISTS central_mess_menu                     CASCADE;
DROP TABLE IF EXISTS central_mess_mess_reg                 CASCADE;
DROP TABLE IF EXISTS central_mess_messbillbase             CASCADE;
DROP TABLE IF EXISTS central_mess_semdates                 CASCADE;
"""

# Remove central_mess migration history so Django does not complain
# about missing migrations for a removed app.
CLEAN_MIGRATION_HISTORY = """
DELETE FROM django_migrations WHERE app = 'central_mess';
"""

# Reverse: nothing to restore — tables are intentionally deleted.
NOOP = ""


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0012_acad_role_module_access'),
    ]

    operations = [
        migrations.RunSQL(
            sql=DROP_CENTRAL_MESS_TABLES,
            reverse_sql=NOOP,
        ),
        migrations.RunSQL(
            sql=CLEAN_MIGRATION_HISTORY,
            reverse_sql=NOOP,
        ),
    ]
