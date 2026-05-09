"""
conftest.py - Shared base test class for the Notification Module (NAM).

Each test class inherits from BaseNAMTestCase which sets up:
  - A student (is_staff=False) and a staff/admin user (is_staff=True)
  - A DRF APIClient pre-wired for force_authenticate
  - Helper methods to login as either role
  - _record_result() to populate the report-metadata attributes the custom
    test runner (runner.py) reads.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


User = get_user_model()


class BaseNAMTestCase(TestCase):
    """Base class shared by UC, BR, and WF test classes."""

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username="nam_student", password="testpass123",
            first_name="Test", last_name="Student",
            email="nam_student@fusion.edu", is_staff=False,
        )
        cls.staff = User.objects.create_user(
            username="nam_staff", password="testpass123",
            first_name="Test", last_name="Staff",
            email="nam_staff@fusion.edu", is_staff=True,
        )
        cls.admin = User.objects.create_user(
            username="nam_admin", password="testpass123",
            first_name="Test", last_name="Admin",
            email="nam_admin@fusion.edu", is_staff=True, is_superuser=True,
        )

    def setUp(self):
        self.client = APIClient()

    # ── Auth helpers ────────────────────────────────────────────
    def login_as_student(self):
        self.client.force_authenticate(user=self.student)

    def login_as_staff(self):
        self.client.force_authenticate(user=self.staff)

    def login_as_admin(self):
        self.client.force_authenticate(user=self.admin)

    def logout(self):
        self.client.force_authenticate(user=None)

    # ── Report-metadata recorder ────────────────────────────────
    def _record_result(self, *, test_id, source_id, category, scenario,
                        preconditions, input_action, expected_result,
                        actual_result, status="Pass", evidence=""):
        """Attach report metadata to the test instance so runner.py picks it up."""
        self._test_id = test_id
        self._test_category = category
        self._scenario = scenario
        self._preconditions = preconditions
        self._input_action = input_action
        self._expected_result = expected_result
        self._actual_result = actual_result
        self._status = status
        self._evidence = evidence

        # source_id is either a UC ID, BR ID or WF ID.
        if source_id.startswith("UC"):
            self._uc_id = source_id
        elif source_id.startswith("BR"):
            self._br_id = source_id
        elif source_id.startswith("WF"):
            self._wf_id = source_id
