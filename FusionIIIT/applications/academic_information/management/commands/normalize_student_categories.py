"""Bring every student category in the database onto one vocabulary.

Student.category has accumulated 21 spellings because it was carrying three
separate facts: the reservation category, EWS status and PwD status. The
category is narrowed to the four values the field declares, and the other two
facts move to Student.is_ews / Student.is_pwd so nothing is lost. Students who
have an admission record keep the full detail there as well.

    python manage.py normalize_student_categories --dry-run   # report only
    python manage.py normalize_student_categories             # apply
"""

from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from applications.academic_information.models import Student
from applications.programme_curriculum.api.account_sync import (
    EWS_CATEGORIES,
    PWD_CATEGORIES,
    admission_category,
    reservation_category,
)
from applications.programme_curriculum.models_student_management import (
    PhdStudentBatchUpload,
    StudentBatchUpload,
)




class Command(BaseCommand):
    help = "Normalize Student.category and lift EWS / PwD into their own fields."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what would change without writing to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        result = Counter()
        unmapped = Counter()
        samples = []

        class Rollback(Exception):
            pass

        def run():
            for student in Student.objects.all().only(
                    'id', 'category', 'is_ews', 'is_pwd').iterator():
                raw = " ".join(str(student.category or "").split()).upper()
                target = reservation_category(raw)
                if target is None:
                    unmapped[student.category] += 1
                    continue

                changed = []
                if student.category != target:
                    changed.append('category')
                if raw in EWS_CATEGORIES and not student.is_ews:
                    changed.append('is_ews')
                if raw in PWD_CATEGORIES and not student.is_pwd:
                    changed.append('is_pwd')
                if not changed:
                    result['already correct'] += 1
                    continue

                student.category = target
                if 'is_ews' in changed:
                    student.is_ews = True
                if 'is_pwd' in changed:
                    student.is_pwd = True
                student.save(update_fields=['category', 'is_ews', 'is_pwd'])
                result.update(changed)
                result['rewritten'] += 1
                if len(samples) < 10:
                    samples.append((student.id_id, raw, target, changed))

        admission = Counter()

        def run_admission():
            for model in (StudentBatchUpload, PhdStudentBatchUpload):
                for record in model.objects.all().only('id', 'category').iterator():
                    target = admission_category(record.category)
                    if target is None:
                        admission['unmapped'] += 1
                        continue
                    if record.category == target:
                        admission['already correct'] += 1
                        continue
                    record.category = target
                    record.save(update_fields=['category'])
                    admission['rewritten'] += 1

        try:
            with transaction.atomic():
                run()
                run_admission()
                if dry_run:
                    raise Rollback()
        except Rollback:
            pass

        self.stdout.write("already correct: {}".format(result['already correct']))
        self.stdout.write("rewritten:       {}".format(result['rewritten']))
        for field in ('category', 'is_ews', 'is_pwd'):
            self.stdout.write("   {:10} {}".format(field, result[field]))
        for roll, raw, target, changed in samples:
            self.stdout.write("   e.g. {:12} {!r} -> {} {}".format(
                roll, raw, target, changed))
        if unmapped:
            self.stdout.write(self.style.ERROR(
                "unmapped, left untouched: {}".format(dict(unmapped))))

        self.stdout.write("admission records already correct: {}".format(
            admission['already correct']))
        self.stdout.write("admission records rewritten:       {}".format(
            admission['rewritten']))
        if admission['unmapped']:
            self.stdout.write(self.style.ERROR(
                "admission records unmapped: {}".format(admission['unmapped'])))

        if dry_run:
            self.stdout.write(self.style.WARNING("dry run - nothing was written"))
        else:
            self.stdout.write(self.style.SUCCESS(
                "normalized {} students".format(result['rewritten'])))
