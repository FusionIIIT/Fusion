import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
django.setup()

from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation, ModuleAccess, DepartmentInfo

# 1. Create or get dummy department (if needed for extrainfo)
dept, _ = DepartmentInfo.objects.get_or_create(name='CSE')

# 2. Create users
print('Creating Users...')
asst_user, created1 = User.objects.get_or_create(username='spacs_asst_login')
if created1:
    asst_user.set_password('user@123')
    asst_user.first_name = 'SPACS'
    asst_user.last_name = 'Assistant'
    asst_user.save()

conv_user, created2 = User.objects.get_or_create(username='spacs_conv_login')
if created2:
    conv_user.set_password('user@123')
    conv_user.first_name = 'SPACS'
    conv_user.last_name = 'Convenor'
    conv_user.save()

# 3. Create ExtraInfo
print('Creating ExtraInfo Profiles...')
ExtraInfo.objects.get_or_create(user=asst_user, defaults={'user_type': 'staff', 'id': 'asst1', 'department': dept})
ExtraInfo.objects.get_or_create(user=conv_user, defaults={'user_type': 'faculty', 'id': 'conv1', 'department': dept})

# 4. Create Designations
print('Creating Designations...')
desig_asst, _ = Designation.objects.get_or_create(name='spacsassistant')
desig_conv, _ = Designation.objects.get_or_create(name='spacsconvenor')

# 5. Connect Users to Designations
print('Mapping Users to Designations (HoldsDesignation)...')
HoldsDesignation.objects.get_or_create(user=asst_user, working=asst_user, designation=desig_asst)
HoldsDesignation.objects.get_or_create(user=conv_user, working=conv_user, designation=desig_conv)

# 6. Grant Frontend Module Access (Redux)
print('Configuring ModuleAccess...')
acc_asst, _ = ModuleAccess.objects.get_or_create(designation=desig_asst)
acc_asst.spacs = True
acc_asst.save()

acc_conv, _ = ModuleAccess.objects.get_or_create(designation=desig_conv)
acc_conv.spacs = True
acc_conv.save()

print('SUCCESS: Created spacs_asst_login and spacs_conv_login with password user@123 !')
