from django.core.management.base import BaseCommand
from applications.coursemanagement.services import release_due


class Command(BaseCommand):
    help = 'Release due scheduled course materials and assignments.'

    def handle(self, *args, **options):
        self.stdout.write(str(release_due()) + ' scheduled items released')
