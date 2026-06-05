"""
conftest.py — Test setup for AUDIT ACCOUNT module.
Creates test users, roles, budgets, and base data.
"""

from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from applications.audit_account.models import (
    DepartmentBudget,
    RequestStatus,
    TARequestStatus,
    AuditObservationStatus,
    WorkflowType,
)


class BaseModuleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create users
        cls.student_user = User.objects.create_user(
            username='2021BCS001', password='test123'
        )
        cls.staff_user = User.objects.create_user(
            username='staffuser', password='test123'
        )
        cls.finance_user = User.objects.create_user(
            username='financeuser', password='test123'
        )
        cls.hod_user = User.objects.create_user(
            username='hoduser', password='test123'
        )
        cls.dean_user = User.objects.create_user(
            username='deanuser', password='test123'
        )
        cls.director_user = User.objects.create_user(
            username='directoruser', password='test123'
        )
        cls.auditor_user = User.objects.create_user(
            username='auditoruser', password='test123'
        )

        # Create ExtraInfo
        cls.student_extra = ExtraInfo.objects.create(
            user=cls.student_user,
            id='2021BCS001',
            user_type='student'
        )
        cls.staff_extra = ExtraInfo.objects.create(
            user=cls.staff_user,
            id='staffuser',
            user_type='staff'
        )
        cls.finance_extra = ExtraInfo.objects.create(
            user=cls.finance_user,
            id='financeuser',
            user_type='staff'
        )
        cls.hod_extra = ExtraInfo.objects.create(
            user=cls.hod_user,
            id='hoduser',
            user_type='staff'
        )
        cls.dean_extra = ExtraInfo.objects.create(
            user=cls.dean_user,
            id='deanuser',
            user_type='staff'
        )
        cls.director_extra = ExtraInfo.objects.create(
            user=cls.director_user,
            id='directoruser',
            user_type='staff'
        )
        cls.auditor_extra = ExtraInfo.objects.create(
            user=cls.auditor_user,
            id='auditoruser',
            user_type='staff'
        )

        # Create designations
        cls.finance_designation = Designation.objects.create(name='finance')
        cls.hod_designation = Designation.objects.create(name='hod')
        cls.dean_designation = Designation.objects.create(name='dean_s')
        cls.director_designation = Designation.objects.create(name='director')
        cls.auditor_designation = Designation.objects.create(name='auditor')

        # Assign designations
        HoldsDesignation.objects.create(
            user=cls.finance_user,
            working=cls.finance_user,
            designation=cls.finance_designation
        )
        HoldsDesignation.objects.create(
            user=cls.hod_user,
            working=cls.hod_user,
            designation=cls.hod_designation
        )
        HoldsDesignation.objects.create(
            user=cls.dean_user,
            working=cls.dean_user,
            designation=cls.dean_designation
        )
        HoldsDesignation.objects.create(
            user=cls.director_user,
            working=cls.director_user,
            designation=cls.director_designation
        )
        HoldsDesignation.objects.create(
            user=cls.auditor_user,
            working=cls.auditor_user,
            designation=cls.auditor_designation
        )

        # Create department budgets
        cls.budget_cse_travel = DepartmentBudget.objects.create(
            department='CSE',
            budget_head='travel',
            allocated_amount=Decimal('50000.00'),
            remaining_amount=Decimal('50000.00'),
            is_active=True
        )
        cls.budget_cse_equipment = DepartmentBudget.objects.create(
            department='CSE',
            budget_head='equipment',
            allocated_amount=Decimal('200000.00'),
            remaining_amount=Decimal('200000.00'),
            is_active=True
        )
        cls.budget_hr_head = DepartmentBudget.objects.create(
            department='HR',
            budget_head='head',
            allocated_amount=Decimal('10000.00'),
            remaining_amount=Decimal('10000.00'),
            is_active=True
        )

    def login_as_student(self):
        """Helper to login as student user"""
        from django.test import Client
        self.client = Client()
        self.client.login(username='2021BCS001', password='test123')
        return self.client

    def login_as_staff(self):
        """Helper to login as staff user"""
        from django.test import Client
        self.client = Client()
        self.client.login(username='staffuser', password='test123')
        return self.client

    def login_as_finance(self):
        """Helper to login as finance user"""
        from django.test import Client
        self.client = Client()
        self.client.login(username='financeuser', password='test123')
        return self.client

    def login_as_hod(self):
        """Helper to login as HOD user"""
        from django.test import Client
        self.client = Client()
        self.client.login(username='hoduser', password='test123')
        return self.client

    def login_as_dean(self):
        """Helper to login as dean user"""
        from django.test import Client
        self.client = Client()
        self.client.login(username='deanuser', password='test123')
        return self.client

    def login_as_director(self):
        """Helper to login as director user"""
        from django.test import Client
        self.client = Client()
        self.client.login(username='directoruser', password='test123')
        return self.client

    def login_as_auditor(self):
        """Helper to login as auditor user"""
        from django.test import Client
        self.client = Client()
        self.client.login(username='auditoruser', password='test123')
        return self.client

    def api_post(self, url, data, expected_status=200):
        """Helper for API POST requests"""
        response = self.client.post(f'/api{url}', data, format='json')
        if expected_status is not None and response.status_code != expected_status:
            print(f"Expected status {expected_status}, got {response.status_code}")
        return response

    def api_get(self, url, expected_status=200):
        """Helper for API GET requests"""
        response = self.client.get(f'/api{url}')
        if expected_status is not None and response.status_code != expected_status:
            print(f"Expected status {expected_status}, got {response.status_code}")
        return response

    def future_date(self, days=1):
        """Helper to get future date"""
        from datetime import datetime, timedelta
        return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

    def past_date(self, days=1):
        """Helper to get past date"""
        from datetime import datetime, timedelta
        return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    def _record_result(self, actual, status, evidence=""):
        """Record test result for reporting"""
        if not hasattr(self, '_results'):
            self._results = []
        self._results.append({
            'actual': actual,
            'status': status,
            'evidence': evidence
        })

    def _add_step(self, step_num, description, expected, actual, success):
        """Add workflow step for reporting"""
        if not hasattr(self, '_steps'):
            self._steps = []
        self._steps.append({
            'step': step_num,
            'description': description,
            'expected': expected,
            'actual': actual,
            'success': success
        })

    def _all_steps_passed(self):
        """Check if all workflow steps passed"""
        return all(step['success'] for step in getattr(self, '_steps', []))
