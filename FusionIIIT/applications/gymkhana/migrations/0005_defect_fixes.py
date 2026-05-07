# Generated migration for defect fixes
# DEF-007: MinValueValidator on Club_budget and Fest_budget (validators don't create DB migrations)
# DEF-011: unique_together on Voting_voters (poll_event, student_id) — creates DB constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gymkhana', '0004_yearlyplan_yearlyplanevents'),
    ]

    operations = [
        # DEF-011 FIX: Enforce one vote per student per poll at the database level.
        # Adds a UNIQUE constraint on (poll_event_id, student_id) in the Voting_voters table.
        migrations.AlterUniqueTogether(
            name='voting_voters',
            unique_together={('poll_event', 'student_id')},
        ),
        # Note: MinValueValidator (DEF-007) is enforced at the application layer only.
        # Django validators do not generate database constraints; they run during model
        # full_clean() and form validation. No schema change is needed for that fix.
    ]