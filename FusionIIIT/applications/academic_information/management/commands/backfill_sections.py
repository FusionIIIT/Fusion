"""Backfill Student.section for existing undergraduate students.

Section is derived from (discipline, roll-number parity) via
``academic_information.models.compute_section``. This is a one-time,
idempotent backfill for students who predate the section feature; new
students get their section at onboarding and it is recomputed on branch
change, so this command can safely be re-run at any time.

    python manage.py backfill_sections            # apply
    python manage.py backfill_sections --dry-run  # report only
"""

from collections import Counter

from django.core.management.base import BaseCommand

from applications.academic_information.models import Student, compute_section


class Command(BaseCommand):
    help = "Backfill Student.section from discipline + roll parity (UG only)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what would change without writing to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        students = Student.objects.select_related('batch_id__discipline').all()

        to_update = []
        dist = Counter()
        no_discipline = 0
        non_ug = 0

        for student in students:
            discipline = None
            if student.batch_id and student.batch_id.discipline:
                discipline = student.batch_id.discipline.name

            section = compute_section(discipline, student.id_id, student.programme)

            if section is None:
                if str(student.programme or '').strip().upper() not in ('B.TECH', 'B.DES'):
                    non_ug += 1
                elif not discipline:
                    no_discipline += 1
                # leave section as-is (None) when unresolved
                if student.section is not None:
                    # UG student whose discipline no longer maps — clear stale value
                    student.section = None
                    to_update.append(student)
                continue

            dist[section] += 1
            if student.section != section:
                student.section = section
                to_update.append(student)

        self.stdout.write(f"Scanned {students.count()} students.")
        self.stdout.write(f"Section distribution (UG resolved): {dict(sorted(dist.items()))}")
        self.stdout.write(f"Non-UG (skipped): {non_ug}   UG without discipline (skipped): {no_discipline}")
        self.stdout.write(f"Rows needing update: {len(to_update)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes written."))
            return

        if to_update:
            Student.objects.bulk_update(to_update, ['section'], batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Updated {len(to_update)} students."))
