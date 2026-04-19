#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from applications.globals.models import Designation, HoldsDesignation
from django.contrib.auth.models import User

try:
    # Get the user 23BCS226
    user = User.objects.get(username='23BCS226')
    print(f"✓ Found user: {user.username} (ID: {user.id})")
    
    # Get Director designation
    director = Designation.objects.get(name='Director')
    print(f"✓ Found Director designation (ID: {director.id})")
    
    # Create PCC Admin designation if it doesn't exist
    pcc_admin, created = Designation.objects.get_or_create(
        name='PCC Admin',
        defaults={
            'full_name': 'PCC Admin',
            'type': 'administrative',
            'basic': False
        }
    )
    print(f"✓ PCC Admin designation {'created' if created else 'already exists'}")
    
    # Check if user already has a working entry to use
    existing_holds = HoldsDesignation.objects.filter(user=user).first()
    if existing_holds and existing_holds.working_id:
        working_id = existing_holds.working_id
        print(f"✓ Using existing working_id: {working_id}")
    else:
        # Try to find any working record
        any_working = HoldsDesignation.objects.filter(working_id__isnull=False).first()
        if any_working:
            working_id = any_working.working_id
            print(f"✓ Using working_id from another record: {working_id}")
        else:
            # If no working_id found, create a default one
            working_id = 1
            print(f"✓ Using default working_id: {working_id}")
    
    # Assign Director role
    director_hold, dir_created = HoldsDesignation.objects.get_or_create(
        user=user, 
        designation=director,
        defaults={'working_id': working_id}
    )
    print(f"✓ Director role {'assigned' if dir_created else 'already assigned'}")
    
    # Assign PCC Admin role
    pcc_hold, pcc_created = HoldsDesignation.objects.get_or_create(
        user=user, 
        designation=pcc_admin,
        defaults={'working_id': working_id}
    )
    print(f"✓ PCC Admin role {'assigned' if pcc_created else 'already assigned'}")
    
    print("\n✅ All roles successfully assigned to 23BCS226!")
    print(f"   - Director: {director.id}")
    print(f"   - PCC Admin: {pcc_admin.id}")
    
except User.DoesNotExist:
    print("❌ Error: User 23BCS226 not found")
    sys.exit(1)
except Designation.DoesNotExist as e:
    print(f"❌ Error: Designation not found - {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
