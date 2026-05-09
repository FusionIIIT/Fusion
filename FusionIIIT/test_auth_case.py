import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings.development'
django.setup()
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

user_val = '23BCS010'
pass_val = 'user@123'

print(f"Testing Auth for {user_val}...")
u1 = authenticate(username=user_val, password=pass_val)
print(f"  Exact CASE match: {u1 is not None}")

u2 = authenticate(username=user_val.lower(), password=pass_val)
print(f"  Lower CASE match: {u2 is not None}")

u3 = User.objects.filter(username__iexact=user_val).first()
if u3:
    print(f"  Found user via iexact: {u3.username}")
    check = u3.check_password(pass_val)
    print(f"  Password check: {check}")
else:
    print("  User NOT found even with iexact")
