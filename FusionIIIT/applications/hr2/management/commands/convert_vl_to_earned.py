import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand

from applications.globals.models import ExtraInfo
from applications.hr2.models import EmployeeLeaveBalance, LeaveType


class Command(BaseCommand):
    help = "Convert unavailed Vacation Leave (VL) to Earned Leave (EL) for faculty at 2:1 for the next year."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            default=datetime.date.today().year,
            help="Source year to convert from (default: current year).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Show changes without updating balances.",
        )

    def handle(self, *args, **options):
        source_year = options["year"]
        target_year = source_year + 1
        dry_run = options.get("dry_run", False)

        vl_type = LeaveType.objects.filter(code__iexact="VL").first() or LeaveType.objects.filter(name__iexact="Vacation").first()
        el_type = LeaveType.objects.filter(code__iexact="EL").first() or LeaveType.objects.filter(name__iexact="Earned").first()

        if not vl_type or not el_type:
            self.stderr.write(self.style.ERROR("Leave types VL/Earned not found. Ensure LeaveType records exist."))
            return

        all_employees = ExtraInfo.objects.all()
        converted_count = 0
        total_converted = Decimal("0.0")

        next_year_defaults = {
            "CL": Decimal("8.0"),
            "RL": Decimal("2.0"),
            "VL": Decimal("60.0"),
        }
        leave_types = {lt.code.upper(): lt for lt in LeaveType.objects.all() if lt.code}

        for employee in all_employees:
            is_faculty = employee.user_type == "faculty"
            converted = Decimal("0.0")

            vl_balance = EmployeeLeaveBalance.objects.filter(
                employee=employee,
                leave_type=vl_type,
                year=source_year,
            ).first()
            if is_faculty and vl_balance:
                vl_current = Decimal(str(vl_balance.current_balance or 0))
                if vl_current > 0:
                    converted = (vl_current / Decimal("2")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                    if not dry_run:
                        vl_balance.current_balance = Decimal("0.0")
                        vl_balance.save(update_fields=["current_balance"])
                    if converted > 0:
                        converted_count += 1
                        total_converted += converted

            if dry_run:
                continue

            for code, leave_type in leave_types.items():
                if code == "EL":
                    opening = Decimal("0.0")
                    accrued = converted
                    current = converted
                elif code in next_year_defaults:
                    opening = next_year_defaults[code]
                    accrued = Decimal("0.0")
                    current = opening
                else:
                    opening = Decimal("0.0")
                    accrued = Decimal("0.0")
                    current = Decimal("0.0")

                EmployeeLeaveBalance.objects.update_or_create(
                    employee=employee,
                    leave_type=leave_type,
                    year=target_year,
                    defaults={
                        "opening_balance": opening,
                        "accrued": accrued,
                        "availed": Decimal("0.0"),
                        "current_balance": current,
                    },
                )

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"Dry run: would convert VL to EL for {converted_count} faculty (total EL added: {total_converted})"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Converted VL to EL for {converted_count} faculty (total EL added: {total_converted})"
            ))
