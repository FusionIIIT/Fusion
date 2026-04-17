import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')

try:
    import Fusion.settings.development as dev_settings
    if 'allauth.account.middleware.AccountMiddleware' not in dev_settings.MIDDLEWARE:
        dev_settings.MIDDLEWARE.append('allauth.account.middleware.AccountMiddleware')
except ImportError:
    pass

import django
django.setup()

from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation
from applications.filetracking.models import File, Tracking
from applications.hr2.models import CPDAAdvanceform
from applications.hr2.constants.form_types import FormType

def populate_test_data():
    professors = HoldsDesignation.objects.filter(designation__name__icontains='professor').select_related('user', 'designation')
    
    if not professors.exists():
        print("No users found with Professor designation.")
        return

    print(f"Found {professors.count()} professors. Inserting test data for each...")

    for hold_desig in professors:
        user = hold_desig.user
        designation = hold_desig.designation
        
        extrainfo, _ = ExtraInfo.objects.get_or_create(
            user=user, 
            defaults={'id': str(user.id), 'user_type': 'faculty'}
        )
        
        def create_workflow(form_instance, form_type_str, state):
            file_obj = File.objects.create(
                uploader=extrainfo,
                designation=designation,
                subject=f'{form_type_str} {state}',
                description='Test auto-generated',
                is_read=(state == 'archive'),
                src_module='HR',
                src_object_id=str(form_instance.id),
                file_extra_JSON={"type": form_type_str}
            )
            
            if state == 'inbox':
                Tracking.objects.create(
                    file_id=file_obj,
                    current_id=extrainfo,
                    current_design=hold_desig,
                    receiver_id=user,
                    receive_design=designation,
                    remarks='Inbox Test',
                    is_read=False
                )
            elif state == 'outbox':
                Tracking.objects.create(
                    file_id=file_obj,
                    current_id=extrainfo,
                    current_design=hold_desig,
                    receiver_id=User.objects.first(),
                    receive_design=Designation.objects.first(),
                    remarks='Outbox Test',
                    is_read=False
                )
            elif state == 'archive':
                Tracking.objects.create(
                    file_id=file_obj,
                    current_id=extrainfo,
                    current_design=hold_desig,
                    receiver_id=user,
                    receive_design=designation,
                    remarks='Archive Test',
                    is_read=True
                )

        # CPDA Advance ONLY (since other models have missing DB columns)
        for state in ['inbox', 'outbox', 'archive']:
            f = CPDAAdvanceform.objects.create(
                employeeId=user.id, name=user.username,
                purpose=f'Test {state.capitalize()}', amountRequired=10000
            )
            create_workflow(f, FormType.CPDA_ADVANCE, state)

    print("Successfully inserted targeted test data for CPDA Advance.")

if __name__ == '__main__':
    populate_test_data()
