"""
Management command to create test users for notification system testing.
Usage: python manage.py create_test_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, DepartmentInfo


class Command(BaseCommand):
    help = 'Create test users for notification system'

    def handle(self, *args, **options):
        """Create 3 test users: 1 student, 1 faculty, 1 staff"""
        
        # Try to get existing departments, or None if not found
        try:
            dept_cse = DepartmentInfo.objects.filter(name__icontains='cse').first()
            if not dept_cse:
                dept_cse = DepartmentInfo.objects.first()  # Use first available dept
        except:
            dept_cse = None
            
        try:
            dept_admin = DepartmentInfo.objects.filter(name__icontains='admin').first()
            if not dept_admin:
                dept_admin = DepartmentInfo.objects.first()  # Use first available dept
        except:
            dept_admin = None
        
        test_users = [
            {'username': 'student1', 'email': 'student1@test.com', 'type': 'student'},
            {'username': 'faculty1', 'email': 'faculty1@test.com', 'type': 'faculty'},
            {'username': 'staff1', 'email': 'staff1@test.com', 'type': 'staff'},
        ]
        
        created_count = 0
        
        for user_data in test_users:
            try:
                # Create user
                user, user_created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults={
                        'email': user_data['email'],
                        'first_name': user_data['username'].replace('1', ' Test').title(),
                        'is_active': True,
                    }
                )
                
                # Create ExtraInfo if doesn't exist
                if not hasattr(user, 'extrainfo'):
                    ExtraInfo.objects.create(
                        user=user,
                        user_type=user_data['type'],
                        department=dept_cse or dept_admin,
                    )
                    info_created = True
                else:
                    info_created = False
                
                if user_created or info_created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Created {user_data["type"]}: {user.username} ({user.email})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'- User already exists: {user.username}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error creating {user_data["username"]}: {str(e)}')
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Done! Created {created_count} test users.')
        )
        self.stdout.write('Now publish an announcement targeting "All Users" to see notifications!')
