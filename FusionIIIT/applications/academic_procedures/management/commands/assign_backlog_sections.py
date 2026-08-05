"""Bulk-assign a section to unsectioned backlog/improvement registrations (once per term)."""

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from applications.academic_procedures.models import course_registration
from applications.programme_curriculum.models import CourseInstructor


def _working_year(session, semester_type):
    # "2026-27" -> 2026; Even semester falls in the next calendar year.
    start = int(str(session).split("-")[0])
    return start + 1 if semester_type == "Even Semester" else start


class Command(BaseCommand):
    help = "Assign a section (course_instructor) to unsectioned backlog/improvement registrations."

    def add_arguments(self, parser):
        parser.add_argument("--year", required=True, help="Session, e.g. 2026-27")
        parser.add_argument("--sem", required=True, help='Semester type, e.g. "Odd Semester"')
        parser.add_argument("--course", help="Optional course code to limit to")
        parser.add_argument("--dry-run", action="store_true", help="Preview only, no writes")

    def handle(self, *args, **opts):
        session, sem, dry = opts["year"], opts["sem"], opts["dry_run"]
        working_year = _working_year(session, sem)

        regs = course_registration.objects.filter(
            session=session,
            semester_type=sem,
            registration_type__in=["Backlog", "Improvement"],
            course_instructor__isnull=True,
        ).select_related("student_id", "course_id")
        if opts.get("course"):
            regs = regs.filter(course_id__code=opts["course"])

        # Seed per-offering counts so "least-full" balances against those already placed.
        counts = defaultdict(int)
        for ci_id in course_registration.objects.filter(
            session=session, semester_type=sem, course_instructor__isnull=False,
        ).values_list("course_instructor_id", flat=True):
            counts[ci_id] += 1

        offerings_by_course = {}

        def offerings_for(course):
            if course.id not in offerings_by_course:
                offerings_by_course[course.id] = list(CourseInstructor.objects.filter(
                    course_id=course, year=working_year, semester_type=sem,
                ))
            return offerings_by_course[course.id]

        plan, skipped = [], 0
        for reg in regs:
            offs = offerings_for(reg.course_id)
            if not offs:
                skipped += 1
                continue
            if len(offs) == 1:
                chosen = offs[0]
            else:
                sec = getattr(reg.student_id, "section", None)
                chosen = next(
                    (o for o in offs if o.section_label and o.section_label == sec),
                    None,
                ) or min(offs, key=lambda o: counts[o.id])
            counts[chosen.id] += 1
            plan.append((reg, chosen))

        self.stdout.write(
            f"Unsectioned backlog/improvement regs: {regs.count()} | "
            f"to assign: {len(plan)} | skipped (course has no offering): {skipped}"
        )
        for reg, chosen in plan[:50]:
            self.stdout.write(
                f"   {reg.student_id_id}  {reg.course_id.code}  -> "
                f"section {chosen.section_label or '-'} (offering {chosen.id})"
            )
        if len(plan) > 50:
            self.stdout.write(f"   ... and {len(plan) - 50} more")

        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes written."))
            return

        with transaction.atomic():
            for reg, chosen in plan:
                reg.course_instructor = chosen
                reg.save(update_fields=["course_instructor"])
        self.stdout.write(self.style.SUCCESS(f"Assigned {len(plan)} registration(s)."))
