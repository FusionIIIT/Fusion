from django.core.management.base import BaseCommand
from applications.hr2.services import seed_hr2_demo_data


class Command(BaseCommand):
    help = "Seed HR2 demo data (employee, access, leave balance)."

    def handle(self, *args, **options):
        result = seed_hr2_demo_data()
        self.stdout.write(
            self.style.SUCCESS(
                f"HR2 seed data created/updated for employee {result['employee_id']}."
            )
        )
