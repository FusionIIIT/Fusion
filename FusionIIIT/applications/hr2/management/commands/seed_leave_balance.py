from django.core.management.base import BaseCommand

from applications.hr2.services import seed_leave_balances


class Command(BaseCommand):
    help = "Seed leave balances for testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--employee-id",
            dest="employee_id",
            default="EMP1001",
            help="ExtraInfo ID to seed (default: EMP1001)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            dest="seed_all",
            help="Seed balances for all ExtraInfo records",
        )

    def handle(self, *args, **options):
        result = seed_leave_balances(
            employee_id=options.get("employee_id"),
            seed_all=options.get("seed_all"),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Leave balances seeded for {result['seeded_count']} employee(s) (year {result['year']})."
            )
        )
