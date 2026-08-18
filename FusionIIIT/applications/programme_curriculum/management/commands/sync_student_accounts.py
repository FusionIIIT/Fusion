"""Push every admission record onto the account it created.

Upcoming Batches is the source of truth for the batches it covers, but until
now its details were only copied at account creation, so later edits never
reached the account. Editing a record now syncs it; this command catches up
the records that were edited before that existed. Students with no admission
record (the pre-2025 batches) are not touched.

    python manage.py sync_student_accounts --dry-run   # report only
    python manage.py sync_student_accounts             # apply
"""

from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from applications.programme_curriculum.api.account_sync import (
    sync_account_from_admission,
)
from applications.programme_curriculum.models_student_management import (
    PhdStudentBatchUpload,
    StudentBatchUpload,
)


class Command(BaseCommand):
    help = "Copy admission records onto their User / ExtraInfo / Student rows."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what would change without writing to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fields = Counter()
        touched = []
        checked = 0

        class Rollback(Exception):
            pass

        def run():
            nonlocal checked
            for model in (StudentBatchUpload, PhdStudentBatchUpload):
                records = model.objects.exclude(user=None).select_related('user')
                for record in records.iterator():
                    checked += 1
                    changed = sync_account_from_admission(record)
                    if changed:
                        touched.append((record.roll_number, changed))
                        fields.update(changed)

        try:
            with transaction.atomic():
                run()
                if dry_run:
                    raise Rollback()
        except Rollback:
            pass

        self.stdout.write("admission records checked: {}".format(checked))
        self.stdout.write("accounts out of date: {}".format(len(touched)))
        for field, count in fields.most_common():
            self.stdout.write("   {:16} {}".format(field, count))
        for roll, changed in touched[:10]:
            self.stdout.write("   e.g. {:12} {}".format(roll, ", ".join(changed)))

        if dry_run:
            self.stdout.write(self.style.WARNING("dry run - nothing was written"))
        else:
            self.stdout.write(self.style.SUCCESS(
                "synced {} accounts".format(len(touched))))
