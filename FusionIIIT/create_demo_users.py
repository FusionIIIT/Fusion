import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
django.setup()

from django.contrib.auth.models import User

from applications.globals.models import (
    DepartmentInfo,
    Designation,
    ExtraInfo,
    HoldsDesignation,
)
from applications.academic_information.models import Student

# --- Departments -----------------------------------------------------------
dept_cse, _ = DepartmentInfo.objects.get_or_create(name='CSE')
dept_ece, _ = DepartmentInfo.objects.get_or_create(name='ECE')
dept_admin, _ = DepartmentInfo.objects.get_or_create(name='Administration')

# --- Designations ---------------------------------------------------------
desig_student, _ = Designation.objects.get_or_create(
    name='student',
    defaults={'full_name': 'Student', 'type': 'academic'},
)
desig_faculty, _ = Designation.objects.get_or_create(
    name='Associate Professor',
    defaults={'full_name': 'Associate Professor', 'type': 'academic'},
)
desig_staff, _ = Designation.objects.get_or_create(
    name='office_staff',
    defaults={'full_name': 'Office Staff', 'type': 'administrative'},
)
desig_compounder, _ = Designation.objects.get_or_create(
    name='compounder',
    defaults={'full_name': 'Compounder', 'type': 'administrative'},
)

print("Creating users for all roles...\n")

# ============ 1. STUDENT USER ============
if not User.objects.filter(username='student1').exists() and not ExtraInfo.objects.filter(id='2021002').exists():
    user_student = User.objects.create_user(
        username='student1',
        password='student@123',
        first_name='Rahul',
        last_name='Kumar',
        email='student1@iiitdmj.ac.in',
    )

    extra_student = ExtraInfo.objects.create(
        id='2021002',
        user=user_student,
        title='Mr.',
        sex='M',
        user_type='student',
        department=dept_cse,
        phone_no=9876543210,
        address='Student Hostel 1, Room A-101',
    )

    HoldsDesignation.objects.create(
        user=user_student,
        working=user_student,
        designation=desig_student,
    )

    Student.objects.create(
        id=extra_student,
        programme='B.Tech',
        batch=2021,
        batch_id=None,
        cpi=8.5,
        category='GEN',
        father_name='Rajesh Kumar',
        mother_name='Sunita Kumar',
        hall_no=1,
        room_no='A-101',
        specialization='CSE',
        curr_semester_no=6,
    )
    print('✓ Student created: student1 / student@123')
else:
    print('→ Student user already exists')

# ============ 2. FACULTY USER ============
if not User.objects.filter(username='faculty1').exists() and not ExtraInfo.objects.filter(id='FAC001').exists():
    user_faculty = User.objects.create_user(
        username='faculty1',
        password='faculty@123',
        first_name='Priya',
        last_name='Sharma',
        email='faculty1@iiitdmj.ac.in',
    )

    extra_faculty = ExtraInfo.objects.create(
        id='FAC001',
        user=user_faculty,
        title='Dr.',
        sex='F',
        user_type='faculty',
        department=dept_cse,
        phone_no=9876543211,
        address='Faculty Quarters, Block B',
    )

    HoldsDesignation.objects.create(
        user=user_faculty,
        working=user_faculty,
        designation=desig_faculty,
    )

    # Faculty is just an ExtraInfo wrapper; create only if model exists
    try:
        from applications.globals.models import Faculty

        Faculty.objects.get_or_create(id=extra_faculty)
    except Exception:
        pass

    print('✓ Faculty created: faculty1 / faculty@123')
else:
    print('→ Faculty user already exists')

# ============ 3. STAFF USER ============
if not User.objects.filter(username='staff1').exists() and not ExtraInfo.objects.filter(id='STF001').exists():
    user_staff = User.objects.create_user(
        username='staff1',
        password='staff@123',
        first_name='Amit',
        last_name='Verma',
        email='staff1@iiitdmj.ac.in',
    )

    extra_staff = ExtraInfo.objects.create(
        id='STF001',
        user=user_staff,
        title='Mr.',
        sex='M',
        user_type='staff',
        department=dept_admin,
        phone_no=9876543212,
        address='Staff Quarters, Block C',
    )

    HoldsDesignation.objects.create(
        user=user_staff,
        working=user_staff,
        designation=desig_staff,
    )

    # Staff is just an ExtraInfo wrapper; create only if model exists
    try:
        from applications.globals.models import Staff

        Staff.objects.get_or_create(id=extra_staff)
    except Exception:
        pass

    print('✓ Staff created: staff1 / staff@123')
else:
    print('→ Staff user already exists')

# ============ 4. COMPOUNDER USER ============
if not User.objects.filter(username='compounder1').exists() and not ExtraInfo.objects.filter(id='CMP001').exists():
    user_compounder = User.objects.create_user(
        username='compounder1',
        password='compounder@123',
        first_name='Suresh',
        last_name='Patel',
        email='compounder1@iiitdmj.ac.in',
    )

    extra_compounder = ExtraInfo.objects.create(
        id='CMP001',
        user=user_compounder,
        title='Mr.',
        sex='M',
        user_type='compounder',
        department=dept_admin,
        phone_no=9876543213,
        address='Health Center',
    )

    HoldsDesignation.objects.create(
        user=user_compounder,
        working=user_compounder,
        designation=desig_compounder,
    )

    print('✓ Compounder created: compounder1 / compounder@123')
else:
    print('→ Compounder user already exists')

print('\n' + '='*50)
print('All users created successfully!')
print('='*50)
print('\nLogin Credentials Summary:')
print('-' * 50)
print('Role         | Username      | Password')
print('-' * 50)
print('Student      | student1      | student@123')
print('Faculty      | faculty1      | faculty@123')
print('Staff        | staff1        | staff@123')
print('Compounder   | compounder1   | compounder@123')
print('-' * 50)
print('\nAccess the application at: http://localhost:8000')
