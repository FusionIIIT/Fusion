from django.core.management.base import BaseCommand
from applications.hr2.services import convert_vl_to_earned


class Command(BaseCommand):
    help = "Convert unavailed Vacation Leave (VL) to Earned Leave (EL) for faculty at 2:1 for the next year."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            default=datetime.date.today().year,
            help="Source year to convert from (default: current year).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Show changes without updating balances.",
        )

    def handle(self, *args, **options):
        result = convert_vl_to_earned(
            source_year=options.get("year"),
            dry_run=options.get("dry_run", False),
        )

        if result["dry_run"]:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run: would convert VL to EL for "
                    f"{result['converted_count']} faculty (total EL added: {result['total_converted']})"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "Converted VL to EL for "
                    f"{result['converted_count']} faculty (total EL added: {result['total_converted']})"
                )
            )
