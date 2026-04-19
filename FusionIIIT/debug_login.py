"""
debug_login.py - Test login logic for a dummy student to diagnose the 500 error
"""
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings.development'
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from applications.globals.models import ExtraInfo, HoldsDesignation

# Test login for top student
ROLL_NO = '23bme020'
PASSWORD = 'student@123'

print(f"Testing login for: {ROLL_NO}")
print("="*60)

# Step 1: Check user exists
try:
    user = User.objects.get(username=ROLL_NO)
    print(f"[OK] User found: {user.username} | active: {user.is_active}")
except User.DoesNotExist:
    print(f"[FAIL] User {ROLL_NO} not found in auth_user")
    exit(1)

# Step 2: Check password
auth_user = authenticate(username=ROLL_NO, password=PASSWORD)
if auth_user:
    print(f"[OK] Password correct")
else:
    print(f"[FAIL] Password wrong - let's try to fix it")
    user.set_password(PASSWORD)
    user.save()
    print(f"[FIXED] Password reset to '{PASSWORD}'")

# Step 3: Check ExtraInfo
try:
    extra = ExtraInfo.objects.get(user=user)
    print(f"[OK] ExtraInfo found: id={extra.id}, user_type={extra.user_type}, dept={extra.department}")
except ExtraInfo.DoesNotExist:
    print(f"[FAIL] ExtraInfo missing for {ROLL_NO}")
    exit(1)

# Step 4: What the login view does
print(f"\n[STEP 4] Simulating login view logic...")
try:
    desig = list(HoldsDesignation.objects.select_related('user','working','designation').filter(working=user).values_list('designation'))
    b = [i for sub in desig for i in sub]
    designation = []
    if str(user.extrainfo.user_type) == "student":
        designation.append(str(user.extrainfo.user_type))
    print(f"[OK] Designation: {designation}")
except Exception as e:
    print(f"[FAIL] Error in login view logic: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Check if auth token works
print(f"\n[STEP 5] Checking token generation...")
try:
    from rest_framework.authtoken.models import Token
    token, created = Token.objects.get_or_create(user=user)
    print(f"[OK] Token: {token.key[:20]}...")
except Exception as e:
    print(f"[FAIL] Token error: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*60}")
print(f"To login via API:")
print(f"  URL: POST http://127.0.0.1:8000/api/auth/login/")
print(f"  Body: username={ROLL_NO}, password={PASSWORD}")
print(f"{'='*60}")
