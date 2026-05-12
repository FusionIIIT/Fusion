# Generated migration to drop extraneous columns from Bill table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('visitor_hostel', '0007_auto_20260421_1005'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE visitor_hostel_bill DROP COLUMN IF EXISTS settlement_proof CASCADE;',
            reverse_sql='',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE visitor_hostel_bill DROP COLUMN IF EXISTS settled_at CASCADE;',
            reverse_sql='',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE visitor_hostel_bill DROP COLUMN IF EXISTS tariff_snapshot CASCADE;',
            reverse_sql='',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE visitor_hostel_bill DROP COLUMN IF EXISTS tariff_version_id CASCADE;',
            reverse_sql='',
        ),
    ]


