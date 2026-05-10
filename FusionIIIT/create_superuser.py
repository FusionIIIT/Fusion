#!/usr/bin/env python
import os
import sys
import django

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')

# Add project to path
sys.path.insert(0, r'C:\Users\saumi\OneDrive\Desktop\FUSION-FINAL\fusion\Fusion\FusionIIIT')

# Setup Django
django.setup()

from django.contrib.auth.models import User

# Delete existing admin user if it exists
User.objects.filter(username='admin').delete()

# Create superuser
user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
print("✅ Superuser created successfully!")
print("Username: admin")
print("Password: admin123")
