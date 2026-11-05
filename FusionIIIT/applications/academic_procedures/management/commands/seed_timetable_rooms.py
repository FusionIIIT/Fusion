"""Seed the timetable room inventory from the institute seating-capacity data.

The timetable solver has one hard ``capacity`` field, so class scheduling uses
the physical capacity from the source.  Exam capacity and the raw layout are
kept in this payload for traceability, but are not timetable model fields.

Usage::

    python manage.py seed_timetable_rooms
    python manage.py seed_timetable_rooms --replace --clear-timetables
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.deletion import ProtectedError

from applications.academic_procedures.models import Classroom, TimetableVersion


ROOM_SEED_DATA = [
    {
        "room_no": "CR-101",
        "type": "CR",
        "physical_capacity": 81,
        "exam_capacity": 45,
        "layout_raw": "ROWS COLS",
    },
    {
        "room_no": "CR-102",
        "type": "CR",
        "physical_capacity": 81,
        "exam_capacity": 45,
        "layout_raw": "ROWS COLS",
    },
    {
        "room_no": "CR-103",
        "type": "CR",
        "physical_capacity": 81,
        "exam_capacity": 45,
        "layout_raw": "9 ROWS COLS",
    },
    {
        "room_no": "CR-104",
        "type": "CR",
        "physical_capacity": 81,
        "exam_capacity": 45,
        "layout_raw": "ROWS COLS",
    },
    {
        "room_no": "CR-107",
        "type": "CR",
        "physical_capacity": 45,
        "exam_capacity": 36,
        "layout_raw": "9 ROWS COLS",
    },
    {
        "room_no": "CR-108",
        "type": "CR",
        "physical_capacity": 45,
        "exam_capacity": 36,
        "layout_raw": "9 ROWS 5 COLS",
    },
    {
        "room_no": "CR-109",
        "type": "CR",
        "physical_capacity": 45,
        "exam_capacity": 36,
        "layout_raw": "ROWS 5 COLS",
    },
    {
        "room_no": "CR-201",
        "type": "CR",
        "physical_capacity": 81,
        "exam_capacity": 45,
        "layout_raw": "ROWS 9 COLS",
    },
    {
        "room_no": "CR-202",
        "type": "CR",
        "physical_capacity": 81,
        "exam_capacity": 45,
        "layout_raw": "9 ROWS COLS",
    },
    {
        "room_no": "CR-208",
        "type": "CR",
        "physical_capacity": 45,
        "exam_capacity": 36,
        "layout_raw": "ROWS 5 COLS",
    },
    {
        "room_no": "L-102",
        "type": "L",
        "physical_capacity": 126,
        "exam_capacity": 126,
        "layout_raw": "14 ROWS 9 COLS",
    },
    {
        "room_no": "L-104",
        "type": "L",
        "physical_capacity": 240,
        "exam_capacity": 120,
        "layout_raw": "15 ROWS 16 COLS",
    },
    {
        "room_no": "L-105",
        "type": "L",
        "physical_capacity": 240,
        "exam_capacity": 120,
        "layout_raw": "15 ROWS 16 COLS",
    },
    {
        "room_no": "L-106",
        "type": "L",
        "physical_capacity": 114,
        "exam_capacity": 114,
        "layout_raw": "STEPPED (9-12 ROWS) - 10 COLS",
    },
    {
        "room_no": "L-107",
        "type": "L",
        "physical_capacity": 68,
        "exam_capacity": 65,
        "layout_raw": "STEPPED (7-9 ROWS & COLS",
    },
    {
        "room_no": "L-201",
        "type": "L",
        "physical_capacity": 70,
        "exam_capacity": 70,
        "layout_raw": "10 ROWS 7 COLS",
    },
    {
        "room_no": "L-202",
        "type": "L",
        "physical_capacity": 126,
        "exam_capacity": 126,
        "layout_raw": "14 ROWS COLS",
    },
    {
        "room_no": "L-206",
        "type": "L",
        "physical_capacity": 104,
        "exam_capacity": 104,
        "layout_raw": "STEPPED (9-11 ROWS) 10 COLS",
    },
    {
        "room_no": "L-207",
        "type": "L",
        "physical_capacity": 54,
        "exam_capacity": 54,
        "layout_raw": "STEPPED (6-7 ROWS) 8 COLS",
    },
]


ROOM_TYPE_DEFAULTS = {
    "CR": {"building": "Core Lab", "room_type": "Tutorial Room"},
    "L": {"building": "LHTC", "room_type": "Lecture Hall"},
}


def classroom_from_seed(room):
    """Translate the source payload to the fields used by the class solver."""
    try:
        type_defaults = ROOM_TYPE_DEFAULTS[room["type"]]
    except KeyError as exc:
        raise CommandError(f"Unsupported room type in seed data: {exc.args[0]}")
    return Classroom(
        room_id=room["room_no"],
        building=type_defaults["building"],
        capacity=room["physical_capacity"],
        room_type=type_defaults["room_type"],
        has_projector=True,
        is_active=True,
    )


class Command(BaseCommand):
    help = "Seed the exact CR/L room inventory used by timetable generation."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete every existing timetable classroom before seeding.",
        )
        parser.add_argument(
            "--clear-timetables",
            action="store_true",
            help=(
                "Delete generated timetable versions first. Required when old "
                "slots protect classrooms being replaced."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report the seed operation without writing.",
        )

    def handle(self, *args, **options):
        replace = options["replace"]
        clear_timetables = options["clear_timetables"]
        dry_run = options["dry_run"]

        if clear_timetables and not replace:
            raise CommandError("--clear-timetables may only be used with --replace.")

        room_ids = [room["room_no"] for room in ROOM_SEED_DATA]
        if len(room_ids) != len(set(room_ids)):
            raise CommandError("Duplicate room_no found in ROOM_SEED_DATA.")

        # Construct every object before opening the transaction so malformed
        # source data cannot partially alter the inventory.
        classrooms = [classroom_from_seed(room) for room in ROOM_SEED_DATA]
        current_room_count = Classroom.objects.count()
        version_count = TimetableVersion.objects.count()

        self.stdout.write(
            f"Rooms: {current_room_count} existing -> {len(classrooms)} seeded | "
            f"timetable versions: {version_count}"
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))
            return

        if current_room_count and not replace:
            raise CommandError(
                f"{current_room_count} rooms already exist. Use --replace for "
                "an exact reset."
            )

        with transaction.atomic():
            if clear_timetables:
                TimetableVersion.objects.all().delete()
            if replace:
                try:
                    Classroom.objects.all().delete()
                except ProtectedError as exc:
                    raise CommandError(
                        "Existing rooms are referenced by timetable slots. Re-run "
                        "with --replace --clear-timetables."
                    ) from exc
            Classroom.objects.bulk_create(classrooms)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(classrooms)} active rooms using physical capacity."
            )
        )
