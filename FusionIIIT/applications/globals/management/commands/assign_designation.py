from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from applications.globals.models import HoldsDesignation, Designation


class Command(BaseCommand):
    help = 'Assign specific designations to a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to assign designations to')
        parser.add_argument('--designations', type=str, help='Comma-separated list of designations (e.g., student,acadadmin,Professor)')

    def handle(self, *args, **options):
        username = options['username']
        designations_input = options.get('designations', '')

        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f'Found user: {username}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} not found'))
            return

        if not designations_input:
            self.stdout.write(self.style.ERROR('Please provide --designations argument'))
            self.stdout.write('Example: python manage.py assign_designation penguin --designations student,acadadmin,dept_admin,Professor')
            return

        # Parse designated designations
        designation_names = [d.strip() for d in designations_input.split(',')]

        assigned = []
        failed = []

        for designation_name in designation_names:
            try:
                designation = Designation.objects.get(name=designation_name)

                # Check if already assigned
                if HoldsDesignation.objects.filter(working=user, designation=designation).exists():
                    self.stdout.write(f'  ⊘ {designation_name} (already assigned)')
                else:
                    # Create HoldsDesignation record
                    HoldsDesignation.objects.create(
                        user=user,
                        working=user,
                        designation=designation
                    )
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {designation_name}'))
                    assigned.append(designation_name)

            except Designation.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  ✗ {designation_name} (not found)'))
                failed.append(designation_name)

        self.stdout.write(f'\n{len(assigned)} designation(s) assigned to {username}')

        if failed:
            self.stdout.write(self.style.ERROR(f'{len(failed)} designation(s) not found. Available:'))
            for des in Designation.objects.all().values_list('name', flat=True):
                self.stdout.write(f'  - {des}')
