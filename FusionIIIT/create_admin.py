#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings')
django.setup()

from django.contrib.auth.models import User

# Check if superuser already exists
if User.objects.filter(username='admin').exists():
    print("⚠️ Superuser 'admin' already exists")
else:
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✅ Superuser created successfully!")

print("\n" + "="*50)
print("Django Admin Credentials:")
print("="*50)
print("Username: admin")
print("Password: admin123")
print("URL: http://localhost:8000/admin/")
print("="*50)
