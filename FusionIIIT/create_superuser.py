import os
import sys
import django

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')

# Setup Django
django.setup()

from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo

# Create superuser
username = 'test1'
email = 'test1@example.com'
password = 'test123'

if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(username=username, email=email, password=password)
    # Create ExtraInfo
    ExtraInfo.objects.create(
        id=username,
        user=user,
        user_type='staff'
    )
    print(f'Superuser {username} created successfully with ExtraInfo.')
else:
    print(f'Superuser {username} already exists.')
