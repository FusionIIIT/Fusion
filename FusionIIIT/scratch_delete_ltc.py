import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings')
django.setup()

from applications.hr2.models import LTCform
from django.contrib.auth.models import User

def delete_faculty1_ltc():
    try:
        user = User.objects.get(username='faculty1')
        deleted_count, _ = LTCform.objects.filter(created_by=user).delete()
        print(f"Successfully deleted {deleted_count} LTC form(s) for faculty1.")
    except User.DoesNotExist:
        print("User 'faculty1' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    delete_faculty1_ltc()
