#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
sys.path.insert(0, r'C:\Users\saumi\OneDrive\Desktop\FUSION-FINAL\fusion\Fusion\FusionIIIT')

django.setup()

from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo

# Get the admin user
admin_user = User.objects.get(username='admin')

# Create ExtraInfo for admin user if it doesn't exist
extra_info, created = ExtraInfo.objects.get_or_create(
    user=admin_user,
    defaults={
        'roll_no': 'admin',
        'phone_number': '0000000000',
        'sex': 'U'  # Unknown
    }
)

if created:
    print("✅ ExtraInfo created for admin user")
else:
    print("✅ ExtraInfo already exists for admin user")

print(f"Admin user: {admin_user.username}")
print(f"Email: {admin_user.email}")
print(f"Is Staff: {admin_user.is_staff}")
print(f"Is Superuser: {admin_user.is_superuser}")
