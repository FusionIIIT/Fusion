import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

def verify():
    test_user = '23BCS007'
    test_pass = 'user@123'
    
    print(f"Verifying login for {test_user}...")
    user = authenticate(username=test_user, password=test_pass)
    
    if user:
        print(f"[SUCCESS] Successfully authenticated {test_user}")
        try:
            print(f"  User Type: {user.extrainfo.user_type}")
            print(f"  Programme: {user.extrainfo.student.programme}")
        except Exception as e:
            print(f"  [WARNING] Profile verification failed: {e}")
    else:
        print(f"[FAILED] Could not authenticate {test_user}")
        # Try finding the user
        try:
            u = User.objects.get(username__iexact=test_user)
            print(f"  User exists: {u.username}")
        except User.DoesNotExist:
            print(f"  User does not exist")

if __name__ == '__main__':
    verify()
