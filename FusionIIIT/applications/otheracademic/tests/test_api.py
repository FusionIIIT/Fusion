"""
Tests for otheracademic API endpoints.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock


class LeaveAPITestCase(TestCase):
    """Tests for leave API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            first_name='Test',
            last_name='User'
        )

    def test_leave_form_submit_requires_auth(self):
        """Test that leave form submission requires authentication."""
        response = self.client.post('/otheracademic/api/leave-form-submit/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fetch_pending_leaves_requires_auth(self):
        """Test that fetching pending leaves requires authentication."""
        response = self.client.get('/otheracademic/api/fetch-pending-leaves/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_leave_requests_requires_auth(self):
        """Test that getting leave requests requires authentication."""
        response = self.client.get('/otheracademic/api/get-leave-requests/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BonafideAPITestCase(TestCase):
    """Tests for bonafide API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            first_name='Test',
            last_name='User'
        )

    def test_bonafide_form_submit_requires_auth(self):
        """Test that bonafide form submission requires authentication."""
        response = self.client.post('/otheracademic/api/bonafide-form-submit/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fetch_pending_bonafides_requires_auth(self):
        """Test that fetching pending bonafides requires authentication."""
        response = self.client.get('/otheracademic/api/admin-bonafide-requests/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AssistantshipAPITestCase(TestCase):
    """Tests for assistantship API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            first_name='Test',
            last_name='User'
        )

    def test_assistantship_form_submit_requires_auth(self):
        """Test that assistantship form submission requires authentication."""
        response = self.client.post('/otheracademic/api/assistantship-form-submit/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ta_supervisor_pending_requires_auth(self):
        """Test that TA supervisor pending requests requires authentication."""
        response = self.client.get('/otheracademic/api/TA-supervisor-pending-requests/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_hod_pending_requires_auth(self):
        """Test that HOD pending requests requires authentication."""
        response = self.client.get('/otheracademic/api/deptadmin-pending-requests/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_acad_admin_pending_requires_auth(self):
        """Test that Academic Admin pending requests requires authentication."""
        response = self.client.get('/otheracademic/api/acadadmin-pending-requests/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ta_assignment_options_requires_auth(self):
        """Test that TA assignment options requires authentication."""
        response = self.client.get('/otheracademic/api/ta-assignment-options/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_faculty_supervisor_assignment_options_requires_auth(self):
        """Test that faculty supervisor assignment options requires authentication."""
        response = self.client.get('/otheracademic/api/faculty-supervisor-assignment-options/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ta_assignment_options_forbidden_without_dept_admin_role(self):
        """Authenticated non-dept-admin user should be forbidden."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/otheracademic/api/ta-assignment-options/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_faculty_supervisor_assignment_update_forbidden_without_dept_admin_role(self):
        """Authenticated non-dept-admin user should be forbidden."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/otheracademic/api/faculty-supervisor-assignment-update/',
            {'assignments': [{'roll_no': '23MCS111', 'faculty_user_id': 1}]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
