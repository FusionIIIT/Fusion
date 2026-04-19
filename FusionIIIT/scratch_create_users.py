import datetime
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, DepartmentInfo
from applications.hr2.models import Employee
from dateutil.relativedelta import relativedelta

def setup_user(username, password, doj_offset):
    # Get or create User
    user, created = User.objects.get_or_create(username=username)
    user.set_password(password)
    user.save()
    
    # Check if ExtraInfo exists
    extrainfo = ExtraInfo.objects.filter(user=user).first()
    if not extrainfo:
        # Create department just in case it's needed for ExtraInfo
        dept, _ = DepartmentInfo.objects.get_or_create(name="CSE")
        extrainfo = ExtraInfo.objects.create(
            id=username,
            user=user,
            user_type='faculty',
            department=dept
        )

    # Get or create Employee
    employee, emp_created = Employee.objects.get_or_create(extra_info=extrainfo)

    doj = datetime.date.today() - doj_offset
    employee.date_of_joining = doj
    employee.save()

    print(f"Set up {username} with doj {employee.date_of_joining}")

setup_user('faculty1', 'faculty@123', relativedelta(years=2))
setup_user('faculty2', 'faculty@123', relativedelta(months=6))
