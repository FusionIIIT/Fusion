import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
django.setup()

from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, DepartmentInfo, Designation, HoldsDesignation, Staff
from applications.academic_information.models import Student

def fix_all_users():
    NEW_PASSWORD = 'user@123'
    
    # Ensure designations
    student_desig, _ = Designation.objects.get_or_create(
        name='student', 
        defaults={'full_name': 'Student', 'type': 'academic'}
    )
    asst_desig, _ = Designation.objects.get_or_create(
        name='spacsassistant', 
        defaults={'full_name': 'SPACS Assistant', 'type': 'administrative'}
    )
    conv_desig, _ = Designation.objects.get_or_create(
        name='spacsconvenor', 
        defaults={'full_name': 'SPACS Convenor', 'type': 'administrative'}
    )
    
    default_dept = DepartmentInfo.objects.filter(name='Computer Science and Engineering').first() or DepartmentInfo.objects.first()

    print("--- Phase 1: Creating/Repairing Special Users ---")
    special_users = [
        ('spacs_asst', asst_desig, 'SPACS Assistant'), 
        ('spacs_conv', conv_desig, 'SPACS Convenor')
    ]
    
    for uname, desig, full_name in special_users:
        user, created = User.objects.get_or_create(
            username=uname, 
            defaults={
                'email': f'{uname}@iiitdmj.ac.in', 
                'first_name': full_name.split()[0],
                'last_name': full_name.split()[-1]
            }
        )
        user.set_password(NEW_PASSWORD)
        user.save()
        
        extra, _ = ExtraInfo.objects.get_or_create(
            user=user, 
            defaults={
                'id': uname.upper()[:20], 
                'user_type': 'staff', 
                'department': default_dept
            }
        )
        
        # Ensure Staff record for staff types
        if extra.user_type == 'staff':
            Staff.objects.get_or_create(id=extra)
        
        # Ensure Designation linkage
        HoldsDesignation.objects.get_or_create(
            user=user, 
            working=user, 
            designation=desig
        )
        print(f"  [OK] Profile ensured for: {uname}")

    print("\n--- Phase 2: Resetting All Users (3500+) ---")
    users = User.objects.all()
    total = users.count()
    print(f"Total users to process: {total}")

    count = 0
    for i, user in enumerate(users):
        try:
            # 1. Reset Password
            user.set_password(NEW_PASSWORD)
            user.save()
            
            # 2. Ensure ExtraInfo exists
            extra, created_extra = ExtraInfo.objects.get_or_create(
                user=user,
                defaults={
                    'id': user.username.upper()[:20],
                    'user_type': 'student', # Default to student
                    'department': default_dept,
                }
            )
            
            # 3. If student, ensure Student model and designation
            is_probably_student = any(c.isdigit() for c in user.username[:2]) or extra.user_type == 'student'
            
            if is_probably_student:
                # Basic student repair
                Student.objects.get_or_create(
                    id=extra,
                    defaults={
                        'programme': 'B.Tech', 
                        'batch': 2023, 
                        'category': 'GEN'
                    }
                )
                HoldsDesignation.objects.get_or_create(
                    user=user, 
                    working=user, 
                    designation=student_desig
                )

            count += 1
            if count % 100 == 0:
                print(f"  [Progress] {count}/{total} users processed...")
                
        except Exception as e:
            # We skip errors to ensure the rest of the users are processed
            print(f"  [ERROR] Failed to process {user.username}: {e}")

    print(f"\n--- MISSION COMPLETE ---")
    print(f"Total users processed: {count}")

if __name__ == '__main__':
    fix_all_users()
