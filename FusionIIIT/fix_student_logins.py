import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
django.setup()

from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, DepartmentInfo, Designation, HoldsDesignation
from applications.academic_information.models import Student

def fix_all_students():
    NEW_PASSWORD = 'user@123'
    
    # Ensure 'student' designation exists
    student_desig, created = Designation.objects.get_or_create(
        name='student',
        defaults={'full_name': 'Student', 'type': 'academic'}
    )
    
    # Default department
    default_dept = DepartmentInfo.objects.filter(name='Computer Science and Engineering').first()
    if not default_dept:
        default_dept = DepartmentInfo.objects.first()

    # Define the ranges
    def get_usernames(prefix, start, end, padding=3):
        return [f"{prefix}{str(i).zfill(padding)}" for i in range(start, end + 1)]

    ranges = [
        ('23BCS', 1, 10, 3),
        ('23BEC', 1, 10, 3),
        ('23BSM', 1, 10, 3),
        ('23BME', 1, 10, 3),
        ('23BDS', 1, 10, 3),
        ('25MCSA', 1, 10, 2),
        ('25MCSS', 1, 10, 2),
        ('25MDS', 1, 7, 2),
    ]

    all_usernames = []
    for prefix, start, end, padding in ranges:
        all_usernames.extend(get_usernames(prefix, start, end, padding))

    print(f"Repairing {len(all_usernames)} student logins...")

    count = 0
    for username in all_usernames:
        try:
            # Case insensitive check for username
            user = User.objects.filter(username__iexact=username).first()
            if not user:
                print(f"  [SKIP] User {username} not found")
                continue
            
            # 1. Reset password
            user.set_password(NEW_PASSWORD)
            user.save()

            # 2. ExtraInfo
            extra, created_extra = ExtraInfo.objects.get_or_create(
                user=user,
                defaults={
                    'id': user.username.upper(),
                    'user_type': 'student',
                    'department': default_dept,
                }
            )
            if not created_extra and extra.user_type != 'student':
                extra.user_type = 'student'
                extra.save()

            # 3. Student model
            prog = 'B.Tech'
            if 'BDS' in username.upper(): prog = 'B.Des'
            elif 'MCS' in username.upper(): prog = 'M.Tech'
            elif 'MDS' in username.upper(): prog = 'M.Des'

            batch = 2023 if '23' in username else 2025

            student, created_student = Student.objects.get_or_create(
                id=extra,
                defaults={
                    'programme': prog,
                    'batch': batch,
                    'category': 'GEN',
                }
            )

            # 4. HoldsDesignation
            HoldsDesignation.objects.get_or_create(
                user=user,
                working=user,
                designation=student_desig
            )

            print(f"  [FIXED] {user.username}")
            count += 1
        except Exception as e:
            print(f"  [ERROR] {username}: {e}")

    print(f"\nSuccessfully repaired {count} student logins.")

if __name__ == '__main__':
    fix_all_students()
