"""
conftest.py — Base test setup for SPACS (Scholarships & Awards) module.

Creates all test actors (Student, Assistant, Convener, Admin) and provides
shared helper methods used by all test files.
"""

import json
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from applications.globals.models import (
    ExtraInfo, DepartmentInfo, Designation, HoldsDesignation,
)
from applications.academic_information.models import Student
from applications.scholarships.models import (
    Award_and_scholarship, Release, Application,
    McmApplication, SingleParentApplication,
    ExtendedScholarshipType, ScholarshipApplication,
)


class BaseModuleTestCase(TestCase):
    """
    Base class for every SPACS test.  Call super().setUpTestData() in
    subclasses that override it.
    """

    # ── Class-level fixtures (created ONCE for the entire TestCase) ──────────

    @classmethod
    def setUpTestData(cls):
        # ── Department ──────────────────────────────────────────────────────
        cls.dept = DepartmentInfo.objects.create(name='CSE')

        # ── Student 1 (primary test student — high CPI, GEN) ───────────────
        cls.student_user = User.objects.create_user(
            username='2021BCS001', password='test123',
            first_name='Test', last_name='Student',
        )
        cls.student_extra = ExtraInfo.objects.create(
            user=cls.student_user, id='2021BCS001',
            user_type='student', department=cls.dept,
            phone_no=9999999999,
        )
        cls.student = Student.objects.create(
            id=cls.student_extra,
            programme='B.Tech', batch=2021,
            cpi=8.5, category='GEN',
        )

        # ── Student 2 (second student — for ownership / access tests) ──────
        cls.student_user_2 = User.objects.create_user(
            username='2021BCS002', password='test123',
            first_name='Other', last_name='Student',
        )
        cls.student_extra_2 = ExtraInfo.objects.create(
            user=cls.student_user_2, id='2021BCS002',
            user_type='student', department=cls.dept,
        )
        cls.student_2 = Student.objects.create(
            id=cls.student_extra_2,
            programme='B.Tech', batch=2021,
            cpi=7.5, category='GEN',
        )

        # ── Student 3 (low CPI, for eligibility‐failure tests) ─────────────
        cls.low_cpi_user = User.objects.create_user(
            username='2021BCS003', password='test123',
        )
        cls.low_cpi_extra = ExtraInfo.objects.create(
            user=cls.low_cpi_user, id='2021BCS003',
            user_type='student', department=cls.dept,
        )
        cls.low_cpi_student = Student.objects.create(
            id=cls.low_cpi_extra,
            programme='B.Tech', batch=2021,
            cpi=4.0, category='GEN',
        )

        # ── SPACS Assistant ─────────────────────────────────────────────────
        cls.assistant_user = User.objects.create_user(
            username='spacsassistant1', password='test123',
        )
        cls.assistant_extra = ExtraInfo.objects.create(
            user=cls.assistant_user, id='spacsassistant1',
            user_type='staff', department=cls.dept,
        )

        # ── SPACS Convener ──────────────────────────────────────────────────
        cls.convener_user = User.objects.create_user(
            username='spacsconvenor1', password='test123',
        )
        cls.convener_extra = ExtraInfo.objects.create(
            user=cls.convener_user, id='spacsconvenor1',
            user_type='staff', department=cls.dept,
        )

        # ── Admin / Superuser ───────────────────────────────────────────────
        cls.admin_user = User.objects.create_superuser(
            username='admin1', password='test123', email='admin@test.com',
        )
        cls.admin_extra = ExtraInfo.objects.create(
            user=cls.admin_user, id='admin1',
            user_type='staff', department=cls.dept,
        )

        # ── Designations & HoldsDesignation ─────────────────────────────────
        cls.assistant_desig = Designation.objects.create(
            name='spacsassistant', full_name='SPACS Assistant',
        )
        cls.convener_desig = Designation.objects.create(
            name='spacsconvenor', full_name='SPACS Convenor',
        )
        HoldsDesignation.objects.create(
            user=cls.assistant_user,
            working=cls.assistant_user,
            designation=cls.assistant_desig,
        )
        HoldsDesignation.objects.create(
            user=cls.convener_user,
            working=cls.convener_user,
            designation=cls.convener_desig,
        )

        # ── Legacy award + open release window ──────────────────────────────
        cls.test_award = Award_and_scholarship.objects.create(
            award_name='Test MCM Award', award_type='MCM',
            catalog='Test scholarship for MCM',
        )
        cls.test_release = Release.objects.create(
            award=cls.test_award,
            startdate=timezone.now().date() - timedelta(days=1),
            enddate=timezone.now().date() + timedelta(days=30),
            batch='2021', programme='B.Tech',
        )

        # ── Extended Scholarship Type (active) ──────────────────────────────
        cls.active_scholarship = ExtendedScholarshipType.objects.create(
            name='Test Merit Scholarship',
            category='MERIT',
            description='Test merit-based scholarship',
            eligibility_criteria='CPI >= 8.0',
            minimum_cgpa=8.0,
            is_active=True,
            amount=Decimal('50000.00'),
        )

        # ── Extended Scholarship Type (inactive) ────────────────────────────
        cls.inactive_scholarship = ExtendedScholarshipType.objects.create(
            name='Inactive Scholarship',
            category='MERIT',
            description='Deactivated scholarship',
            eligibility_criteria='CPI >= 6.0',
            minimum_cgpa=6.0,
            is_active=False,
        )

    # ── Per-test setup ──────────────────────────────────────────────────────

    def setUp(self):
        self.client = APIClient()

        # Result tracking for reporter
        self._test_id = ''
        self._uc_id = ''
        self._br_id = ''
        self._wf_id = ''
        self._test_category = ''
        self._scenario = ''
        self._preconditions = ''
        self._input_action = ''
        self._expected_result = ''
        self._results = []
        self._steps = []

    # ── Login helpers ───────────────────────────────────────────────────────

    def login_as_student(self, user=None):
        self.client.force_authenticate(user=user or self.student_user)

    def login_as_student2(self):
        self.client.force_authenticate(user=self.student_user_2)

    def login_as_low_cpi_student(self):
        self.client.force_authenticate(user=self.low_cpi_user)

    def login_as_assistant(self):
        self.client.force_authenticate(user=self.assistant_user)

    def login_as_convener(self):
        self.client.force_authenticate(user=self.convener_user)

    def login_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)

    def logout(self):
        self.client.force_authenticate(user=None)

    # ── API helpers ─────────────────────────────────────────────────────────

    def api_get(self, path, expected_status=200):
        response = self.client.get(path, format='json')
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"GET {path} → {response.status_code}: {getattr(response, 'data', '')}")
        return response

    def api_post(self, path, data=None, expected_status=201, fmt='json'):
        response = self.client.post(path, data or {}, format=fmt)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"POST {path} → {response.status_code}: {getattr(response, 'data', '')}")
        return response

    def api_patch(self, path, data=None, expected_status=200, fmt='json'):
        response = self.client.patch(path, data or {}, format=fmt)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"PATCH {path} → {response.status_code}: {getattr(response, 'data', '')}")
        return response

    def api_put(self, path, data=None, expected_status=200, fmt='json'):
        response = self.client.put(path, data or {}, format=fmt)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"PUT {path} → {response.status_code}: {getattr(response, 'data', '')}")
        return response

    # ── Date helpers ────────────────────────────────────────────────────────

    @staticmethod
    def future_date(days=5):
        return (date.today() + timedelta(days=days)).isoformat()

    @staticmethod
    def past_date(days=3):
        return (date.today() - timedelta(days=days)).isoformat()

    @staticmethod
    def today():
        return date.today().isoformat()

    # ── DB assertion helpers ────────────────────────────────────────────────

    def assert_object_exists(self, model, **kwargs):
        self.assertTrue(
            model.objects.filter(**kwargs).exists(),
            f"{model.__name__} with {kwargs} does not exist",
        )

    def assert_object_not_exists(self, model, **kwargs):
        self.assertFalse(
            model.objects.filter(**kwargs).exists(),
            f"{model.__name__} with {kwargs} should not exist",
        )

    # ── MCM Application factory ─────────────────────────────────────────────

    def create_mcm_application(self, student=None, status='pending', **overrides):
        """Create an McmApplication for testing."""
        s = student or self.student
        user = s.id.user
        defaults = {
            'student': s,
            'email': f'{user.username}@test.com',
            'student_full_name': f'{user.first_name} {user.last_name}'.strip() or user.username,
            'roll_no': str(s.id),
            'batch': str(s.batch),
            'programme': s.programme,
            'mobile_no': '9876543210',
            'father_name': 'Father Name',
            'mother_name': 'Mother Name',
            'category': s.category,
            'current_cpi': Decimal(str(s.cpi)),
            'current_spi': Decimal(str(s.cpi)),
            'annual_income': '300000',
            'postal_address': '123 Test Street',
            'status': status,
        }
        defaults.update(overrides)
        return McmApplication.objects.create(**defaults)

    # ── Single Parent Application factory ────────────────────────────────────

    def create_single_parent_application(self, student=None, status='pending', **overrides):
        """Create a SingleParentApplication for testing."""
        s = student or self.student
        user = s.id.user
        defaults = {
            'student': s,
            'email': f'{user.username}@test.com',
            'student_full_name': f'{user.first_name} {user.last_name}'.strip() or user.username,
            'roll_no': str(s.id),
            'batch': str(s.batch),
            'programme': s.programme,
            'mobile_no': '9876543210',
            'postal_address': '123 Test Street',
            'father_name': 'Father Name',
            'mother_name': 'Mother Name',
            'category': s.category,
            'current_cpi': Decimal(str(s.cpi)),
            'status': status,
        }
        defaults.update(overrides)
        return SingleParentApplication.objects.create(**defaults)

    # ── Extended Scholarship Application factory ─────────────────────────────

    def create_ext_scholarship_app(self, student=None, scholarship=None,
                                   status='PENDING', **overrides):
        """Create a ScholarshipApplication for testing."""
        s = student or self.student
        sch = scholarship or self.active_scholarship
        defaults = {
            'student': s,
            'scholarship_type': sch,
            'academic_year': '2024-25',
            'semester': 1,
            'status': status,
        }
        defaults.update(overrides)
        return ScholarshipApplication.objects.create(**defaults)

    # ── Result recording (used by runner.py) ────────────────────────────────

    def _record_result(self, actual, status, evidence=''):
        self._results.append({
            'test_id': self._test_id,
            'actual': actual,
            'status': status,
            'evidence': evidence,
        })

    def _add_step(self, step_num, action, expected, actual, passed):
        self._steps.append({
            'step': step_num,
            'action': action,
            'expected': expected,
            'actual': actual,
            'passed': passed,
        })

    def _all_steps_passed(self):
        return all(s['passed'] for s in self._steps)
