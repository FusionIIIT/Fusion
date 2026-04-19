import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings')

import django
from django.conf import settings

# Temporary fix to bypass AccountMiddleware issue during migration
if 'allauth.account.middleware.AccountMiddleware' not in settings.MIDDLEWARE:
    settings.MIDDLEWARE.append('allauth.account.middleware.AccountMiddleware')

django.setup()

from django.core.management import call_command

def run_migrations():
    try:
        print("Running makemigrations...")
        call_command('makemigrations')
        print("Running migrate...")
        call_command('migrate')
        print("Migrations applied successfully.")
        
        # Retroactively create CPDABalance for existing ExtraInfo records
        from applications.hr2.models import CPDABalance
        from applications.globals.models import ExtraInfo
        
        count = 0
        for extra in ExtraInfo.objects.all():
            bal, created = CPDABalance.objects.get_or_create(
                employeeId=extra,
                defaults={'cpda_allotted': 300000.00, 'cpda_used': 0.00}
            )
            if created:
                count += 1
                
        print(f"Created CPDABalance for {count} ExtraInfo records.")
        print("All existing users now have a CPDABalance record.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    run_migrations()
