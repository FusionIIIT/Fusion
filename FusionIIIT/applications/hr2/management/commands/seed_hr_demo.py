from django.core.management.base import BaseCommand
from applications.hr2.services import seed_hr_demo_data


class Command(BaseCommand):
    help = "Seed HR demo data for form testing."

    def handle(self, *args, **options):
        result = seed_hr_demo_data()
        self.stdout.write(
            self.style.SUCCESS(
                f"HR demo data seeded for {result['employees_seeded']} employee(s)."
            )
        )
