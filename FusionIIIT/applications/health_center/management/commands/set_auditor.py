"""
Django management command to set a user as auditor.
Usage: python manage.py set_auditor <username>
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo


class Command(BaseCommand):
    help = 'Set a user as auditor with auditor designation'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to set as auditor')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            # Get user
            user = User.objects.get(username=username)
            self.stdout.write(f"Found user: {user.username} ({user.get_full_name()})")
            
            # Get or create ExtraInfo
            extra_info, created = ExtraInfo.objects.get_or_create(user=user)
            
            if created:
                self.stdout.write(f"✓ Created new ExtraInfo for {username}")
            else:
                self.stdout.write(f"✓ Using existing ExtraInfo for {username}")
            
            # Set as auditor
            extra_info.user_type = 'AUDITOR'
            extra_info.designation = 'Auditor'
            extra_info.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully set {username} as auditor'
            ))
            self.stdout.write(f"  - user_type: {extra_info.user_type}")
            self.stdout.write(f"  - designation: {extra_info.designation}")
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'✗ User "{username}" not found'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'✗ Error: {str(e)}'
            ))
