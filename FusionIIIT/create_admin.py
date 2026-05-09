from django.contrib.auth.models import User
from applications.globals.models import Designation, HoldsDesignation, ModuleAccess

try:
    # Get the user
    user = User.objects.get(username='23bcs201')
    
    # Create or get the designation
    designation, _ = Designation.objects.get_or_create(
        name='complaint_admin',
        defaults={'full_name': 'Complaint System Admin', 'type': 'administrative'}
    )
    
    # Create module access so it appears in UI if necessary
    ModuleAccess.objects.get_or_create(
        designation='complaint_admin',
        defaults={'complaint_management': True}
    )
    
    # Assign the designation to the user
    HoldsDesignation.objects.get_or_create(
        user=user,
        working=user,
        designation=designation
    )
    
    print("Successfully assigned complaint_admin to 23bcs201")
except User.DoesNotExist:
    print("User 23bcs201 does not exist.")
except Exception as e:
    print(f"Error occurred: {e}")
