#!/usr/bin/env python3
"""
Test script to verify login endpoint is working correctly
"""
import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development_local')
sys.path.insert(0, '/home/divyeshtechs/Desktop/Fusion/FusionIIIT')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Test 1: Verify test users have tokens
print("=" * 60)
print("TEST 1: Checking if test users have authentication tokens")
print("=" * 60)

test_users = ['teststudent', 'testteacher', 'admin']

for username in test_users:
    try:
        user = User.objects.get(username=username)
        token, created = Token.objects.get_or_create(user=user)
        status = "CREATED" if created else "EXISTS"
        print(f"✓ {username}: Token {status}")
        print(f"  Token: {token.key}")
    except User.DoesNotExist:
        print(f"✗ {username}: User not found")
    except Exception as e:
        print(f"✗ {username}: Error - {e}")

print("\n" + "=" * 60)
print("TEST 2: Testing login via API")
print("=" * 60)

# Test login endpoint
login_url = "http://127.0.0.1:8000/api/auth/login/"
credentials = {
    "username": "teststudent",
    "password": "password123"  # Default test password
}

try:
    response = requests.post(login_url, json=credentials)
    if response.status_code == 200:
        print(f"✓ Login successful!")
        data = response.json()
        print(f"  Response: {data}")
        if 'token' in data:
            print(f"  ✓ Token in response: {data['token'][:10]}...")
        else:
            print(f"  ⚠ No token in response")
    else:
        print(f"✗ Login failed with status {response.status_code}")
        print(f"  Response: {response.text}")
except Exception as e:
    print(f"✗ Error testing login: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("If users don't have tokens, run:")
print("  python manage.py drf_create_token admin")
print("  python manage.py drf_create_token teststudent")
print("  python manage.py drf_create_token testteacher")
print("\nThen log in with credentials:")
print("  Student: username='teststudent', password='password123'")
print("  Teacher: username='testteacher', password='password123'")
