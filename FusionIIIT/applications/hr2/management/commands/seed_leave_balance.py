import datetime

from django.core.management.base import BaseCommand, CommandError

from applications.globals.models import ExtraInfo
from applications.hr2.models import EmployeeLeaveBalance, LeaveType


DEFAULT_BALANCES = [
    ("Casual", "CL", 10),
    ("Restricted", "RL", 5),
    ("Medical", "ML", 12),
    ("Earned", "EL", 18),
    ("Vacation", "VL", 20),
    ("Sabbatical", "SL", 0),
]

ROLE_BALANCES = {
    "EMP1002": {"CL": 12, "RL": 6, "ML": 15, "EL": 25, "VL": 30, "SL": 10},
    "EMP1003": {"CL": 15, "RL": 8, "ML": 20, "EL": 30, "VL": 35, "SL": 15},
    "EMP1004": {"CL": 12, "RL": 6, "ML": 15, "EL": 22, "VL": 28, "SL": 5},
    "EMP1005": {"CL": 10, "RL": 5, "ML": 12, "EL": 20, "VL": 25, "SL": 0},
    "EMP1006": {"CL": 10, "RL": 5, "ML": 12, "EL": 18, "VL": 22, "SL": 0},
    "EMP1007": {"CL": 12, "RL": 6, "ML": 15, "EL": 25, "VL": 30, "SL": 12},
}


class Command(BaseCommand):
    help = "Seed leave balances for testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--employee-id",
            dest="employee_id",
            default="EMP1001",
            help="ExtraInfo ID to seed (default: EMP1001)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            dest="seed_all",
            help="Seed balances for all ExtraInfo records",
        )

    def handle(self, *args, **options):
        year = datetime.date.today().year

        for name, code, _value in DEFAULT_BALANCES:
            LeaveType.objects.get_or_create(
                name=name,
                code=code,
                defaults={"is_active": True},
            )

        if options.get("seed_all"):
            employees = ExtraInfo.objects.all()
        else:
            employee_id = options.get("employee_id")
            try:
                employees = [ExtraInfo.objects.get(id=employee_id)]
            except ExtraInfo.DoesNotExist as exc:
                raise CommandError(f"Employee not found: {employee_id}") from exc

        for employee in employees:
            balance_map = ROLE_BALANCES.get(employee.id, {})
            for name, code, default_value in DEFAULT_BALANCES:
                value = balance_map.get(code, default_value)
                leave_type = LeaveType.objects.get(code=code)
                EmployeeLeaveBalance.objects.update_or_create(
                    employee=employee,
                    leave_type=leave_type,
                    year=year,
                    defaults={
                        "opening_balance": value,
                        "accrued": 0,
                        "availed": 0,
                        "current_balance": value,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Leave balances seeded."))
