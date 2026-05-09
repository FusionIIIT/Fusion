from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from applications.globals.models import ExtraInfo

class Command(BaseCommand):
    help = 'Setup or regenerate auditor authentication token'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='test_auditor', help='Username of auditor')
        parser.add_argument('--regenerate', action='store_true', help='Regenerate token if exists')

    def handle(self, *args, **options):
        username = options['username']
        regenerate = options['regenerate']

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("AUDITOR TOKEN SETUP")
        self.stdout.write(f"{'='*60}\n")

        try:
            # Get user
            user = User.objects.get(username=username)
            self.stdout.write(f"✓ Found user: {username}")

            # Check ExtraInfo
            try:
                extra_info = ExtraInfo.objects.get(user=user)
                if extra_info.user_type != 'AUDITOR':
                    self.stdout.write(self.style.WARNING(f"⚠ User has user_type='{extra_info.user_type}', not 'AUDITOR'"))
                    extra_info.user_type = 'AUDITOR'
                    extra_info.save()
                    self.stdout.write(self.style.SUCCESS(f"✓ Updated user_type to 'AUDITOR'"))
                else:
                    self.stdout.write(f"✓ User has correct user_type='AUDITOR'")
            except ExtraInfo.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠ No ExtraInfo found - creating one"))
                ExtraInfo.objects.create(user=user, user_type='AUDITOR')
                self.stdout.write(self.style.SUCCESS(f"✓ Created ExtraInfo with user_type='AUDITOR'"))

            # Handle token
            if regenerate:
                Token.objects.filter(user=user).delete()
                self.stdout.write(self.style.SUCCESS(f"✓ Deleted existing token"))

            token, created = Token.objects.get_or_create(user=user)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ Created new authentication token"))
            else:
                self.stdout.write(f"✓ Using existing authentication token")

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"USERNAME: {username}")
            self.stdout.write(f"TOKEN: {token.key}")
            self.stdout.write(f"{'='*60}\n")
            
            self.stdout.write(self.style.SUCCESS("\n✓ Setup complete! Use this token in requests:"))
            self.stdout.write(f"Authorization: Token {token.key}\n")

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ User not found: {username}"))
