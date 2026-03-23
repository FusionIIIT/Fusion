"""
Tests for otheracademic services.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from datetime import date

from applications.otheracademic import services
from applications.otheracademic.models import (
    LeaveFormTable,
    LeavePG,
    BonafideFormTableUpdated,
    AssistantshipClaimFormStatusUpd,
    LeaveStatusChoices,
)


class LeaveServicesTestCase(TestCase):
    """Tests for leave-related services."""

    @patch('applications.otheracademic.services.selectors.get_user_by_username')
    def test_submit_ug_leave_invalid_hod(self, mock_get_user):
        """Test that submitting leave with invalid HOD raises error."""
        mock_get_user.return_value = None
        user = MagicMock()
        user.first_name = 'Test'
        user.last_name = 'User'

        with self.assertRaises(services.LeaveServiceError) as context:
            services.submit_ug_leave(
                user=user,
                date_from=date.today(),
                date_to=date.today(),
                leave_type='Casual',
                address='Test Address',
                purpose='Test Purpose',
                hod_credential='invalid_hod',
                semester='1',
            )
        self.assertIn('not found', str(context.exception))


class BonafideServicesTestCase(TestCase):
    """Tests for bonafide-related services."""

    @patch('applications.otheracademic.services.selectors.get_first_user_for_designation')
    @patch('applications.otheracademic.services.otheracademic_notif')
    def test_submit_bonafide_creates_record(self, mock_notif, mock_get_admin):
        """Test that submitting bonafide creates a record."""
        mock_get_admin.return_value = None  # No admin to notify

        user = MagicMock()
        user.first_name = 'Test'
        user.last_name = 'User'
        user.extrainfo = MagicMock()

        result = services.submit_bonafide(
            user=user,
            branch='CSE',
            semester='3',
            purpose='Test Purpose',
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.branch_types, 'CSE')
        self.assertEqual(result.semester_types, '3')


class AssistantshipServicesTestCase(TestCase):
    """Tests for assistantship-related services."""

    def test_get_assistantship_status_text_rejected(self):
        """Test status text when rejected at any stage."""
        form = MagicMock()
        form.Director_rejected = True
        form.Dean_rejected = False
        form.AcadAdmin_rejected = False
        form.HOD_rejected = False
        form.TA_rejected = False
        form.Ths_rejected = False
        form.Director_approved = False

        result = services.get_assistantship_status_text(form)
        self.assertEqual(result, "Rejected")

    def test_get_assistantship_status_text_approved(self):
        """Test status text when fully approved."""
        form = MagicMock()
        form.Director_rejected = False
        form.Dean_rejected = False
        form.AcadAdmin_rejected = False
        form.HOD_rejected = False
        form.TA_rejected = False
        form.Ths_rejected = False
        form.Director_approved = True

        result = services.get_assistantship_status_text(form)
        self.assertEqual(result, "Approved")

    def test_get_assistantship_status_text_pending(self):
        """Test status text when pending."""
        form = MagicMock()
        form.Director_rejected = False
        form.Dean_rejected = False
        form.AcadAdmin_rejected = False
        form.HOD_rejected = False
        form.TA_rejected = False
        form.Ths_rejected = False
        form.Director_approved = False

        result = services.get_assistantship_status_text(form)
        self.assertEqual(result, "Pending")

    def test_get_assistantship_approval_stages(self):
        """Test getting approval stages."""
        form = MagicMock()
        form.TA_approved = True
        form.TA_rejected = False
        form.Ths_approved = False
        form.Ths_rejected = True
        form.HOD_approved = False
        form.HOD_rejected = False
        form.AcadAdmin_approved = False
        form.AcadAdmin_rejected = False
        form.Dean_approved = False
        form.Dean_rejected = False
        form.Director_approved = False
        form.Director_rejected = False

        result = services.get_assistantship_approval_stages(form)

        self.assertEqual(result['TA_Supervisor'], 'Approved')
        self.assertEqual(result['Thesis_Supervisor'], 'Rejected')
        self.assertEqual(result['HOD'], 'Pending')
