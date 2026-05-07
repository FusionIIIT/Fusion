from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, DepartmentInfo

# Get the first superuser
su = User.objects.filter(is_superuser=True).first()

if su:
    print(f"Processing superuser: {su.username}")
    
    # Check if extrainfo already exists
    extra = ExtraInfo.objects.filter(user=su).first()
    
    if not extra:
        # Create a default department
        dept, _ = DepartmentInfo.objects.get_or_create(name='Administration')
        
        # Create ExtraInfo for this user
        # Use username as the ID
        try:
            ExtraInfo.objects.create(
                id=su.username,
                user=su,
                user_type='admin',
                department=dept,
                title='Dr.',
                sex='M',
                phone_no=9999999999,
                user_status='PRESENT',
                address='Administration',
                about_me='System Administrator'
            )
            print(f"✓ ExtraInfo created for {su.username}")
        except Exception as e:
            print(f"✗ Error creating ExtraInfo: {e}")
    else:
        print(f"✓ ExtraInfo already exists for {su.username}")
else:
    print("No superuser found. Create one first with: python manage.py createsuperuser")
