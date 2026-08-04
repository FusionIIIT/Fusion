"""Bind course_registration rows to their CourseInstructor offering.

For each registration that isn't yet bound, resolve the offering from
(course, working_year, semester_type, student.section) and set course_instructor.
Resolution mirrors academic_information.models.resolve_offering:
  1. core: offering whose section_label matches the student's section
  2. elective / single-offering: the offering with no section (NULL)
  3. if exactly one offering exists for the term, use it

All offerings are preloaded into memory so this scales to 100k+ registrations
without a per-row query. Registrations whose offering can't be resolved (e.g. a
sectioned course whose offerings aren't labelled yet, or an ambiguous
multi-offering term) are left unbound and reported. Idempotent / re-runnable.

    python manage.py bind_course_offerings            # apply
    python manage.py bind_course_offerings --dry-run  # report only
"""

from collections import defaultdict

from django.core.management.base import BaseCommand

from applications.academic_procedures.models import course_registration
from applications.programme_curriculum.models import CourseInstructor


class Command(BaseCommand):
    help = "Bind course_registration rows to their CourseInstructor offering."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would change without writing.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Preload offerings into memory: {(course_id, year, semester_type): [CI, ...]}
        offerings = defaultdict(list)
        for ci in CourseInstructor.objects.all().only(
                'id', 'course_id', 'year', 'semester_type', 'section_label'):
            offerings[(ci.course_id_id, ci.year, ci.semester_type)].append(ci)

        def resolve(course_id, year, semester_type, section):
            group = offerings.get((course_id, year, semester_type))
            if not group:
                return None
            if section:
                for o in group:
                    if o.section_label == section:
                        return o
            nulls = [o for o in group if o.section_label is None]
            if len(nulls) == 1:
                return nulls[0]
            if not nulls and len(group) == 1:
                return group[0]
            return None

        qs = (course_registration.objects
              .filter(course_instructor__isnull=True, working_year__isnull=False)
              .exclude(semester_type__isnull=True)
              .exclude(semester_type='')
              .select_related('student_id')
              .only('id', 'course_id', 'working_year', 'semester_type', 'student_id__section',
                    'course_instructor'))

        total = bound = unresolved = 0
        batch = []
        for reg in qs.iterator(chunk_size=2000):
            total += 1
            offering = resolve(reg.course_id_id, reg.working_year, reg.semester_type,
                               reg.student_id.section)
            if offering is None:
                unresolved += 1
                continue
            reg.course_instructor = offering
            batch.append(reg)
            bound += 1
            if not dry_run and len(batch) >= 1000:
                course_registration.objects.bulk_update(batch, ['course_instructor'])
                batch = []

        if not dry_run and batch:
            course_registration.objects.bulk_update(batch, ['course_instructor'])

        self.stdout.write(f"Unbound registrations scanned: {total}")
        self.stdout.write(f"Resolved & bound: {bound}   Unresolved (no matching offering): {unresolved}")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Bound {bound} registrations."))
