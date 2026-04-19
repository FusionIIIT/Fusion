import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation
from applications.hr2.models import (
    AppraisalPeriod,
    Employee,
    EmployeeLeaveBalance,
    LeaveBalance,
    LeavePerYear,
    LeaveType,
    TrainingProgram,
)

from .runner import REPORT_STORE


User = get_user_model()


class BaseModuleTestCase(TestCase):
    """Shared helpers and base data for HR2 tests."""

    @classmethod
    def setUpTestData(cls):
        cls.department_cse = DepartmentInfo.objects.create(
            name="Computer Science and Engineering"
        )
        cls.department_admin = DepartmentInfo.objects.create(name="Administration")
        cls.department_finance = DepartmentInfo.objects.create(name="Finance")
        cls.department_director = DepartmentInfo.objects.create(name="Director Office")

        cls.employee_user = User.objects.create_user(
            username="rahul1001",
            password="rahul123",
            first_name="Rahul",
            last_name="Sharma",
            email="rahul.sharma@iiitdmj.ac.in",
        )
        cls.hod_user = User.objects.create_user(
            username="hod1002",
            password="hod123",
            first_name="Anil",
            last_name="Kumar",
            email="anil.kumar@iiitdmj.ac.in",
        )
        cls.director_user = User.objects.create_user(
            username="director1003",
            password="director123",
            first_name="Meena",
            last_name="Verma",
            email="director@iiitdmj.ac.in",
        )
        cls.registrar_user = User.objects.create_user(
            username="registrar1004",
            password="registrar123",
            first_name="Suresh",
            last_name="Verma",
            email="registrar@iiitdmj.ac.in",
        )
        cls.staff_user = User.objects.create_user(
            username="hradmin1005",
            password="hradmin123",
            first_name="Priya",
            last_name="Nair",
            email="hr.admin@iiitdmj.ac.in",
        )
        cls.accountant_user = User.objects.create_user(
            username="accountant1006",
            password="accountant123",
            first_name="Arun",
            last_name="Joshi",
            email="accountant@iiitdmj.ac.in",
        )
        cls.nominee_user = User.objects.create_user(
            username="nominee",
            password="test123",
            first_name="Nominee",
            last_name="User",
            email="nominee@example.com",
        )

        cls.employee_extra = ExtraInfo.objects.create(
            user=cls.employee_user,
            id="1001",
            user_type="faculty",
            department=cls.department_cse,
        )
        cls.hod_extra = ExtraInfo.objects.create(
            user=cls.hod_user,
            id="1002",
            user_type="staff",
            department=cls.department_cse,
        )
        cls.director_extra = ExtraInfo.objects.create(
            user=cls.director_user,
            id="1003",
            user_type="staff",
            department=cls.department_director,
        )
        cls.registrar_extra = ExtraInfo.objects.create(
            user=cls.registrar_user,
            id="1004",
            user_type="staff",
            department=cls.department_admin,
        )
        cls.staff_extra = ExtraInfo.objects.create(
            user=cls.staff_user,
            id="1005",
            user_type="staff",
            department=cls.department_admin,
        )
        cls.accountant_extra = ExtraInfo.objects.create(
            user=cls.accountant_user,
            id="1006",
            user_type="staff",
            department=cls.department_finance,
        )
        cls.nominee_extra = ExtraInfo.objects.create(
            user=cls.nominee_user,
            id="2001",
            user_type="staff",
            department=cls.department_cse,
        )

        cls.employee = cls._create_employee(
            cls.employee_user,
            department_name="Computer Science and Engineering",
            employee_type="Faculty",
            phone="9876543210",
            personal_email="rahul.sharma@iiitdmj.ac.in",
            date_of_joining=datetime.date(2021, 8, 1),
            date_of_birth=datetime.date(1990, 5, 12),
        )
        cls.hod_employee = cls._create_employee(
            cls.hod_user,
            department_name="Computer Science and Engineering",
            employee_type="Faculty",
            phone="9876543211",
            personal_email="anil.kumar@iiitdmj.ac.in",
            date_of_joining=datetime.date(2015, 6, 15),
            date_of_birth=datetime.date(1980, 7, 20),
        )
        cls.director_employee = cls._create_employee(
            cls.director_user,
            department_name="Director Office",
            employee_type="Faculty",
            phone="9876543212",
            personal_email="director@iiitdmj.ac.in",
            date_of_joining=datetime.date(2019, 1, 10),
            date_of_birth=datetime.date(1975, 2, 11),
        )
        cls.registrar_employee = cls._create_employee(
            cls.registrar_user,
            department_name="Administration",
            employee_type="Staff",
            phone="9876543213",
            personal_email="registrar@iiitdmj.ac.in",
            date_of_joining=datetime.date(2018, 1, 15),
            date_of_birth=datetime.date(1982, 3, 10),
        )
        cls.staff_employee = cls._create_employee(
            cls.staff_user,
            department_name="Administration",
            employee_type="Staff",
            phone="9876543214",
            personal_email="hr.admin@iiitdmj.ac.in",
            date_of_joining=datetime.date(2020, 11, 5),
            date_of_birth=datetime.date(1987, 9, 25),
        )
        cls.accountant_employee = cls._create_employee(
            cls.accountant_user,
            department_name="Finance",
            employee_type="Staff",
            phone="9876543215",
            personal_email="accountant@iiitdmj.ac.in",
            date_of_joining=datetime.date(2019, 8, 12),
            date_of_birth=datetime.date(1985, 12, 18),
        )
        cls.nominee_employee = cls._create_employee(cls.nominee_user)

        cls._ensure_leave_balances(cls.employee, casual_leave=10)
        cls._ensure_leave_balances(cls.hod_employee)
        cls._ensure_leave_balances(cls.director_employee)
        cls._ensure_leave_balances(cls.registrar_employee)
        cls._ensure_leave_balances(cls.staff_employee)
        cls._ensure_leave_balances(cls.accountant_employee)
        cls._ensure_leave_balances(cls.nominee_employee)

        cls._create_designation("hod", cls.hod_user)
        cls._create_designation("registrar", cls.registrar_user)
        cls._create_designation("director", cls.director_user)
        cls._create_designation("accountant", cls.accountant_user)
        cls._create_designation("hr_admin", cls.staff_user)

        cls.leave_types = cls._create_leave_types()
        cls._create_leave_balances_for_employee(cls.employee_extra)

        cls.appraisal_period = AppraisalPeriod.objects.create(
            name="2025-2026",
            start_date=datetime.date(2025, 7, 1),
            end_date=datetime.date(2026, 6, 30),
            submission_deadline=datetime.date(2026, 5, 31),
            is_active=True,
        )
        cls.training_program = TrainingProgram.objects.create(
            title="AI Workshop",
            description="AI fundamentals",
            organizer="IIITDMJ",
            venue="Jabalpur",
            start_date=datetime.date.today() + datetime.timedelta(days=10),
            end_date=datetime.date.today() + datetime.timedelta(days=12),
            max_participants=30,
            is_mandatory=False,
        )
        cls.promotion_current_designation, _ = Designation.objects.get_or_create(
            name="assistant_professor",
            defaults={"full_name": "Assistant Professor", "type": "academic"},
        )
        cls.promotion_applied_designation, _ = Designation.objects.get_or_create(
            name="associate_professor",
            defaults={"full_name": "Associate Professor", "type": "academic"},
        )

    @classmethod
    def _create_employee(
        cls,
        user: User,
        department_name: str = "Computer Science and Engineering",
        employee_type: str = "Faculty",
        phone: str = "9999999999",
        personal_email: Optional[str] = None,
        date_of_joining: Optional[datetime.date] = None,
        date_of_birth: Optional[datetime.date] = None,
    ) -> Employee:
        return Employee.objects.create(
            id=user,
            father_name="Father",
            mother_name="Mother",
            category="General",
            caste="NA",
            home_state="Madhya Pradesh",
            home_district="Jabalpur",
            full_address=f"{department_name} quarters",
            date_of_joining=date_of_joining or datetime.date(2024, 1, 1),
            date_of_birth=date_of_birth or datetime.date(1990, 1, 1),
            blood_group="A+",
            phone_number=phone,
            personal_email=personal_email or f"{user.username}@example.com",
            emergency_contact_number="8888888888",
            emergency_contact_name="Emergency",
            employee_type=employee_type,
        )

    @classmethod
    def _ensure_leave_balances(cls, employee: Employee, casual_leave: int = 8) -> None:
        LeaveBalance.objects.create(
            empid=employee,
            casual_leave_taken=0,
        )
        LeavePerYear.objects.create(empid=employee)

    @classmethod
    def _create_leave_types(cls) -> Dict[str, LeaveType]:
        leave_types = {}
        for name, code in (
            ("Casual", "CL"),
            ("Vacation", "VL"),
            ("Earned", "EL"),
            ("Medical", "ML"),
            ("Restricted", "RL"),
            ("Sabbatical", "SL"),
        ):
            leave_type, _ = LeaveType.objects.get_or_create(
                name=name,
                code=code,
                defaults={"max_days_per_year": 30, "carry_forward": False},
            )
            leave_types[name] = leave_type
        return leave_types

    @classmethod
    def _create_leave_balances_for_employee(cls, employee_extra: ExtraInfo) -> None:
        current_year = datetime.date.today().year
        for leave_type in cls.leave_types.values():
            EmployeeLeaveBalance.objects.get_or_create(
                employee=employee_extra,
                leave_type=leave_type,
                year=current_year,
                defaults={
                    "opening_balance": Decimal("10"),
                    "accrued": Decimal("0"),
                    "availed": Decimal("0"),
                    "current_balance": Decimal("10"),
                },
            )

    @classmethod
    def _create_designation(cls, name: str, user: User) -> None:
        designation, _ = Designation.objects.get_or_create(name=name)
        HoldsDesignation.objects.get_or_create(
            user=user,
            working=user,
            designation=designation,
        )

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self._result_recorded = False
        self._steps: List[Dict[str, Any]] = []

    def tearDown(self):
        if not self._result_recorded:
            error_message = self._get_test_error_message()
            if error_message:
                self._record_result("Unhandled error", "Fail", error_message)
        super().tearDown()

    def _get_test_error_message(self) -> Optional[str]:
        outcome = getattr(self, "_outcome", None)
        if not outcome:
            return None
        for _, error in outcome.errors:
            if error:
                return str(error)
        return None

    def login_as_user(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def logout(self) -> None:
        self.client.force_authenticate(user=None)

    def login_as_employee(self) -> None:
        self.login_as_user(self.employee_user)

    def login_as_staff(self) -> None:
        self.login_as_user(self.staff_user)

    def login_as_hod(self) -> None:
        self.login_as_user(self.hod_user)

    def login_as_registrar(self) -> None:
        self.login_as_user(self.registrar_user)

    def login_as_director(self) -> None:
        self.login_as_user(self.director_user)

    def login_as_accountant(self) -> None:
        self.login_as_user(self.accountant_user)

    def login_as_nominee(self) -> None:
        self.login_as_user(self.nominee_user)

    def api_get(self, path: str, expected_status: Optional[int] = 200, **kwargs):
        response = self.client.get(path, **kwargs)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status)
        return response

    def api_post(self, path: str, data: Optional[Dict[str, Any]] = None, expected_status: Optional[int] = 200, **kwargs):
        response = self.client.post(path, data=data or {}, format="json", **kwargs)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status)
        return response

    def api_put(self, path: str, data: Optional[Dict[str, Any]] = None, expected_status: Optional[int] = 200, **kwargs):
        response = self.client.put(path, data=data or {}, format="json", **kwargs)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status)
        return response

    def api_delete(self, path: str, expected_status: Optional[int] = 200, **kwargs):
        response = self.client.delete(path, **kwargs)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status)
        return response

    def today(self) -> str:
        return datetime.date.today().isoformat()

    def future_date(self, days: int) -> str:
        return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()

    def past_date(self, days: int) -> str:
        return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()

    def _record_result(self, message: str, status: str, evidence: str = "") -> None:
        REPORT_STORE.add_execution(
            test_id=getattr(self, "_test_id", self._testMethodName),
            artifact_id=(
                getattr(self, "_uc_id", None)
                or getattr(self, "_br_id", None)
                or getattr(self, "_wf_id", None)
            ),
            artifact_type=self._artifact_type,
            category=getattr(self, "_test_category", ""),
            scenario=getattr(self, "_scenario", ""),
            preconditions=getattr(self, "_preconditions", ""),
            input_action=getattr(self, "_input_action", ""),
            expected_result=getattr(self, "_expected_result", "")
            or getattr(self, "_expected_final_state", ""),
            status=status,
            message=message,
            evidence=evidence,
            steps=self._steps,
        )
        self._result_recorded = True

    def _add_step(self, step_number: int, action: str, expected: str, actual: str, passed: bool) -> None:
        self._steps.append(
            {
                "step": step_number,
                "action": action,
                "expected": expected,
                "actual": actual,
                "passed": passed,
            }
        )

    def _all_steps_passed(self) -> bool:
        return all(step["passed"] for step in self._steps)


class UCTestBase(BaseModuleTestCase):
    _artifact_type = "UC"


class BRTestBase(BaseModuleTestCase):
    _artifact_type = "BR"


class WFTestBase(BaseModuleTestCase):
    _artifact_type = "WF"
