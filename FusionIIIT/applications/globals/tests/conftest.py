"""
conftest.py - Base test case setup and fixtures for Dashboard Module testing
Provides: User fixtures, API client, helper methods for tests
"""

from datetime import datetime, timedelta, date
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import json
import logging

from applications.globals.models import (
    ExtraInfo, 
    DepartmentInfo, 
    Designation, 
    HoldsDesignation,
    Feedback,
    Issue,
    IssueImage,
    Module,
    ModuleAccess,
)
from applications.academic_information.models import Student

logger = logging.getLogger(__name__)


class BaseModuleTestCase(TestCase):
    """
    Base test case for Dashboard Module testing.
    Sets up common fixtures: users, departments, designations, access.
    """

    @classmethod
    def setUpTestData(cls):
        """Create baseline test data for all test classes"""
        
        # Create departments using get_or_create
        cls.dept_cse, _ = DepartmentInfo.objects.get_or_create(
            name="Computer Science and Engineering",
            defaults={}
        )
        cls.dept_mech, _ = DepartmentInfo.objects.get_or_create(
            name="Mechanical Engineering",
            defaults={}
        )
        cls.dept_admin, _ = DepartmentInfo.objects.get_or_create(
            name="Administration",
            defaults={}
        )

        # Create designations using get_or_create
        cls.dean_rspc, _ = Designation.objects.get_or_create(
            name="dean_rspc",
            defaults={
                "full_name": "Dean (Research, Sponsored Projects and Consultancy)",
                "type": "academic"
            }
        )
        cls.director, _ = Designation.objects.get_or_create(
            name="director",
            defaults={
                "full_name": "Director",
                "type": "academic"
            }
        )
        cls.department_head, _ = Designation.objects.get_or_create(
            name="department_head",
            defaults={
                "full_name": "Department Head",
                "type": "academic"
            }
        )
        cls.admin_staff, _ = Designation.objects.get_or_create(
            name="admin_staff",
            defaults={
                "full_name": "Administrative Staff",
                "type": "administrative"
            }
        )

        # Create Modules using get_or_create
        cls.database_module, _ = Module.objects.get_or_create(
            key="database",
            defaults={"label": "Database"}
        )
        cls.mess_module, _ = Module.objects.get_or_create(
            key="mess_management",
            defaults={"label": "Mess Management"}
        )

        # Create Module Access configurations using get_or_create
        cls.student_access, _ = ModuleAccess.objects.get_or_create(designation="student")
        cls.student_access.modules.add(cls.database_module)

        cls.faculty_access, _ = ModuleAccess.objects.get_or_create(designation="faculty")
        cls.faculty_access.modules.add(cls.database_module)
        cls.faculty_access.modules.add(cls.mess_module)

        cls.director_access, _ = ModuleAccess.objects.get_or_create(designation="director")
        cls.director_access.modules.add(cls.database_module)
        cls.director_access.modules.add(cls.mess_module)

        # Create test users - Student
        cls.student_user, _ = User.objects.get_or_create(
            username='student001',
            defaults={
                'email': 'student001@iiitdmj.ac.in',
                'first_name': 'John',
                'last_name': 'Student'
            }
        )
        if not hasattr(cls.student_user, 'extrainfo'):
            cls.student_user.set_password('testpass123')
            cls.student_user.save()
            cls.student_extra = ExtraInfo.objects.create(
                id='2021BCS001',
                user=cls.student_user,
                user_type='student',
                department=cls.dept_cse,
                phone_no=9999999999,
                date_of_birth=date(2003, 5, 15),
                title='Mr.',
                sex='M',
                address="123 Student Lane",
                about_me="CS Student"
            )
        cls.student_profile, _ = Student.objects.get_or_create(
            id=cls.student_extra,
            defaults={
                'programme': 'B.Tech',
                'batch': 2021,
                'category': 'GEN',
                'curr_semester_no': 1,
            }
        )

        # Create test users - Faculty
        cls.faculty_user, _ = User.objects.get_or_create(
            username='faculty001',
            defaults={
                'email': 'faculty001@iiitdmj.ac.in',
                'first_name': 'Dr.',
                'last_name': 'Faculty'
            }
        )
        if not hasattr(cls.faculty_user, 'extrainfo'):
            cls.faculty_user.set_password('testpass123')
            cls.faculty_user.save()
            cls.faculty_extra = ExtraInfo.objects.create(
                id='FAC001',
                user=cls.faculty_user,
                user_type='faculty',
                department=cls.dept_cse,
                phone_no=9988888888,
                date_of_birth=date(1980, 3, 20),
                title='Dr.',
                sex='M',
                address="456 Faculty Ave",
                about_me="Computer Science Faculty"
            )
        cls.faculty_designation, _ = HoldsDesignation.objects.get_or_create(
            user=cls.faculty_user,
            working=cls.faculty_user,
            designation=cls.department_head
        )

        # Create test users - Staff
        cls.staff_user, _ = User.objects.get_or_create(
            username='staff001',
            defaults={
                'email': 'staff001@iiitdmj.ac.in',
                'first_name': 'Admin',
                'last_name': 'Staff'
            }
        )
        if not hasattr(cls.staff_user, 'extrainfo'):
            cls.staff_user.set_password('testpass123')
            cls.staff_user.save()
            cls.staff_extra = ExtraInfo.objects.create(
                id='STAFF001',
                user=cls.staff_user,
                user_type='staff',
                department=cls.dept_admin,
                phone_no=9977777777,
                date_of_birth=date(1985, 7, 10),
                title='Mr.',
                sex='M',
                address="789 Admin St",
                about_me="Administrative Staff"
            )

        # Create test users - Director
        cls.director_user, _ = User.objects.get_or_create(
            username='director001',
            defaults={
                'email': 'director001@iiitdmj.ac.in',
                'first_name': 'Prof.',
                'last_name': 'Director'
            }
        )
        if not hasattr(cls.director_user, 'extrainfo'):
            cls.director_user.set_password('testpass123')
            cls.director_user.save()
            cls.director_extra = ExtraInfo.objects.create(
                id='DIR001',
                user=cls.director_user,
                user_type='faculty',
                department=cls.dept_cse,
                phone_no=9966666666,
                date_of_birth=date(1970, 1, 5),
                title='Dr.',
                sex='M',
                address="Director's Residence",
                about_me="Institute Director"
            )
        cls.director_designation, _ = HoldsDesignation.objects.get_or_create(
            user=cls.director_user,
            working=cls.director_user,
            designation=cls.director
        )

        # Create Dean RSPC user
        cls.dean_user, _ = User.objects.get_or_create(
            username='dean001',
            defaults={
                'email': 'dean001@iiitdmj.ac.in',
                'first_name': 'Dr.',
                'last_name': 'Dean'
            }
        )
        if not hasattr(cls.dean_user, 'extrainfo'):
            cls.dean_user.set_password('testpass123')
            cls.dean_user.save()
            cls.dean_extra = ExtraInfo.objects.create(
                id='DEAN001',
                user=cls.dean_user,
                user_type='faculty',
                department=cls.dept_cse,
                phone_no=9955555555,
                date_of_birth=date(1975, 6, 12),
                title='Dr.',
                sex='F',
                address="Dean's Office",
                about_me="Dean RSPC"
            )
        cls.dean_designation, _ = HoldsDesignation.objects.get_or_create(
            user=cls.dean_user,
            working=cls.dean_user,
            designation=cls.dean_rspc
        )

    def setUp(self):
        """Set up test client and test-specific data"""
        self.client = APIClient()
        self.api_client = APIClient()
        
        # Test metadata attributes (set by individual tests)
        self._test_id = None
        self._uc_id = None
        self._br_id = None
        self._wf_id = None
        self._test_category = None
        self._scenario = None
        self._preconditions = None
        self._input_action = None
        self._expected_result = None
        
        # Execution tracking
        self._test_result = None
        self._pass_fail = None
        self._evidence = None
        self._wf_steps = []

    # ─────────────────────────────────────────────────────────────────────
    # LOGIN / AUTHENTICATION HELPERS
    # ─────────────────────────────────────────────────────────────────────

    def login_as_student(self):
        """Log in test client as student user"""
        self.api_client.force_authenticate(user=self.student_user)
        return self.api_client

    def login_as_faculty(self):
        """Log in test client as faculty user"""
        self.api_client.force_authenticate(user=self.faculty_user)
        return self.api_client

    def login_as_staff(self):
        """Log in test client as staff user"""
        self.api_client.force_authenticate(user=self.staff_user)
        return self.api_client

    def login_as_director(self):
        """Log in test client as director user"""
        self.api_client.force_authenticate(user=self.director_user)
        return self.api_client

    def login_as_dean(self):
        """Log in test client as dean user"""
        self.api_client.force_authenticate(user=self.dean_user)
        return self.api_client

    def logout(self):
        """Log out test client"""
        self.api_client.force_authenticate(user=None)

    def _normalize_api_endpoint(self, endpoint):
        """Keep API calls on canonical slash-terminated URLs."""
        if endpoint.startswith('/api/') and not endpoint.endswith('/') and '?' not in endpoint:
            return endpoint + '/'
        return endpoint

    # ─────────────────────────────────────────────────────────────────────
    # API HELPER METHODS
    # ─────────────────────────────────────────────────────────────────────

    def api_get(self, endpoint, expected_status=status.HTTP_200_OK, **kwargs):
        """
        Make GET request to API endpoint
        
        Args:
            endpoint: URL path (e.g., '/api/v1/profile/')
            expected_status: Expected HTTP status code (None to skip assertion)
            **kwargs: Additional arguments for client.get()
        
        Returns:
            Response object with .status_code and .json() / .data attributes
        """
        response = self.api_client.get(self._normalize_api_endpoint(endpoint), **kwargs)
        if expected_status is not None:
            self.assertEqual(
                response.status_code,
                expected_status,
                f"Expected {expected_status}, got {response.status_code}: {response.content}"
            )
        return response

    def api_post(self, endpoint, data=None, expected_status=status.HTTP_200_OK, **kwargs):
        """
        Make POST request to API endpoint
        
        Args:
            endpoint: URL path
            data: POST body data (dict, will be JSON-encoded)
            expected_status: Expected HTTP status code (None to skip)
            **kwargs: Additional arguments
        
        Returns:
            Response object
        """
        response = self.api_client.post(
            self._normalize_api_endpoint(endpoint),
            data=data if data is not None else {},
            format=kwargs.pop('format', 'json'),
            **kwargs
        )
        if expected_status is not None:
            self.assertEqual(
                response.status_code,
                expected_status,
                f"Expected {expected_status}, got {response.status_code}: {response.content}"
            )
        return response

    def api_put(self, endpoint, data=None, expected_status=status.HTTP_200_OK, **kwargs):
        """
        Make PUT request to API endpoint
        
        Args:
            endpoint: URL path
            data: PUT body data
            expected_status: Expected HTTP status code
            **kwargs: Additional arguments
        
        Returns:
            Response object
        """
        response = self.api_client.put(
            self._normalize_api_endpoint(endpoint),
            data=data if data is not None else {},
            format=kwargs.pop('format', 'json'),
            **kwargs
        )
        if expected_status is not None:
            self.assertEqual(
                response.status_code,
                expected_status,
                f"Expected {expected_status}, got {response.status_code}"
            )
        return response

    def api_delete(self, endpoint, expected_status=status.HTTP_204_NO_CONTENT, **kwargs):
        """
        Make DELETE request to API endpoint
        
        Args:
            endpoint: URL path
            expected_status: Expected HTTP status code
            **kwargs: Additional arguments
        
        Returns:
            Response object
        """
        response = self.api_client.delete(self._normalize_api_endpoint(endpoint), **kwargs)
        if expected_status is not None:
            self.assertEqual(
                response.status_code,
                expected_status,
                f"Expected {expected_status}, got {response.status_code}"
            )
        return response

    # ─────────────────────────────────────────────────────────────────────
    # DATE/TIME HELPERS
    # ─────────────────────────────────────────────────────────────────────

    def today(self):
        """Get today's date as date object"""
        return date.today()

    def today_str(self):
        """Get today's date as ISO string"""
        return date.today().isoformat()

    def future_date(self, days=1):
        """Get a future date (n days from today)"""
        return (date.today() + timedelta(days=days))

    def future_date_str(self, days=1):
        """Get a future date as ISO string"""
        return self.future_date(days).isoformat()

    def past_date(self, days=1):
        """Get a past date (n days ago)"""
        return (date.today() - timedelta(days=days))

    def past_date_str(self, days=1):
        """Get a past date as ISO string"""
        return self.past_date(days).isoformat()

    # ─────────────────────────────────────────────────────────────────────
    # RESULT RECORDING METHODS
    # ─────────────────────────────────────────────────────────────────────

    def _record_result(self, observation, status_val, evidence=""):
        """
        Record test result for reporting
        
        Args:
            observation: What was observed during test
            status_val: "Pass", "Partial", or "Fail"
            evidence: Supporting data (response, error message, etc)
        """
        self._test_result = observation
        self._pass_fail = status_val
        self._evidence = evidence

    def _add_step(self, step_num, step_desc, expected, actual, passed):
        """
        Add a workflow step for multi-step testing
        
        Args:
            step_num: Step number (1, 2, 3, ...)
            step_desc: Description of step
            expected: Expected outcome
            actual: Actual outcome
            passed: Boolean - did this step pass?
        """
        self._wf_steps.append({
            'step_num': step_num,
            'step_desc': step_desc,
            'expected': expected,
            'actual': actual,
            'passed': passed,
        })

    def _all_steps_passed(self):
        """Check if all workflow steps passed"""
        return all(step['passed'] for step in self._wf_steps)

    def _get_steps_summary(self):
        """Get summary of all workflow steps"""
        return json.dumps(self._wf_steps, indent=2, default=str)

    # ─────────────────────────────────────────────────────────────────────
    # ASSERTION HELPERS
    # ─────────────────────────────────────────────────────────────────────

    def assert_object_exists(self, model_class, **filters):
        """Assert that an object with given filters exists"""
        self.assertTrue(
            model_class.objects.filter(**filters).exists(),
            f"No {model_class.__name__} with filters {filters}"
        )

    def assert_object_not_exists(self, model_class, **filters):
        """Assert that an object with given filters does NOT exist"""
        self.assertFalse(
            model_class.objects.filter(**filters).exists(),
            f"Found {model_class.__name__} with filters {filters}"
        )

    def assert_http_status(self, response, expected_status):
        """Assert HTTP response has expected status code"""
        self.assertEqual(
            response.status_code,
            expected_status,
            f"Expected {expected_status}, got {response.status_code}: {response.content}"
        )


class UCTestBase(BaseModuleTestCase):
    """Base class for Use Case tests"""
    pass


class BRTestBase(BaseModuleTestCase):
    """Base class for Business Rule tests"""
    pass


class WFTestBase(BaseModuleTestCase):
    """Base class for Workflow tests"""
    pass
