from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation, ModuleAccess
from applications.hr2.models import Employee, EmployeeLeaveBalance, LeaveType

try:
    from notifications.signals import notify
except ImportError:  # pragma: no cover - optional dependency
    notify = None


class Command(BaseCommand):
    help = "Seed HR2 demo data (employee, access, leave balance)."

    def handle(self, *args, **options):
        User = get_user_model()
        now = timezone.now()

        department, _ = DepartmentInfo.objects.get_or_create(name="Computer Science")

        designation, _ = Designation.objects.get_or_create(
            name="Faculty",
            defaults={"full_name": "Faculty", "type": "academic"},
        )

        module_access, _ = ModuleAccess.objects.get_or_create(designation="Faculty")
        if not module_access.hr:
            module_access.hr = True
            module_access.save()

        user, created = User.objects.get_or_create(
            username="rahul123",
            defaults={
                "first_name": "Rahul",
                "last_name": "Sharma",
                "email": "rahul.sharma@iiitdmj.ac.in",
            },
        )
        if created:
            user.set_password("user@123")
            user.save()
        else:
            user.email = "rahul.sharma@iiitdmj.ac.in"
            user.first_name = user.first_name or "Rahul"
            user.last_name = user.last_name or "Sharma"
            user.set_password("user@123")
            user.save()

        extra_info, _ = ExtraInfo.objects.get_or_create(
            id="EMP001",
            defaults={
                "user": user,
                "title": "Dr.",
                "sex": "M",
                "date_of_birth": "1990-05-12",
                "user_status": "PRESENT",
                "address": "IIITDMJ Campus",
                "phone_no": 9876543210,
                "user_type": "faculty",
                "department": department,
                "about_me": "Faculty member",
                "last_selected_role": "Faculty",
            },
        )
        if extra_info.user_id != user.id:
            extra_info.user = user
        extra_info.department = department
        extra_info.phone_no = 9876543210
        extra_info.last_selected_role = "Faculty"
        extra_info.save()

        HoldsDesignation.objects.get_or_create(
            user=user,
            working=user,
            designation=designation,
        )

        Employee.objects.get_or_create(
            id=user,
            defaults={
                "father_name": "Rajesh Sharma",
                "mother_name": "Sunita Sharma",
                "category": "General",
                "caste": "N/A",
                "home_state": "Madhya Pradesh",
                "home_district": "Jabalpur",
                "full_address": "IIITDMJ Campus, Dumna Airport Road",
                "date_of_joining": "2021-08-01",
                "date_of_birth": "1990-05-12",
                "blood_group": "O+",
                "phone_number": "9876543210",
                "personal_email": "rahul.sharma@iiitdmj.ac.in",
                "emergency_contact_number": "9876543211",
                "emergency_contact_name": "Rajesh Sharma",
                "employee_type": "Faculty",
            },
        )

        leave_type_map = {
            "Casual": ("CL", Decimal("10")),
            "Earned": ("EL", Decimal("18")),
            "Medical": ("ML", Decimal("12")),
            "Restricted": ("RL", Decimal("5")),
            "Vacation": ("VL", Decimal("25")),
            "Sabbatical": ("SL", Decimal("0")),
        }

        current_year = now.year
        for name, (code, balance) in leave_type_map.items():
            leave_type, _ = LeaveType.objects.get_or_create(
                name=name,
                defaults={"code": code, "is_active": True},
            )
            EmployeeLeaveBalance.objects.get_or_create(
                employee=extra_info,
                leave_type=leave_type,
                year=current_year,
                defaults={
                    "opening_balance": balance,
                    "accrued": Decimal("0"),
                    "availed": Decimal("0"),
                    "current_balance": balance,
                },
            )

        if notify:
            notify.send(
                sender=user,
                recipient=user,
                verb="Welcome to HR Portal",
                description="Welcome to HR Portal",
            )

        self.stdout.write(self.style.SUCCESS("HR2 seed data created/updated."))
