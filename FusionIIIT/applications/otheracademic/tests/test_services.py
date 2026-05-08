"""
Tests for otheracademic services.
"""
from django.test import TestCase
from unittest.mock import patch, MagicMock
from datetime import date

from applications.otheracademic import services


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
        form.TA_rejected = False
        form.HOD_rejected = False
        form.Acad_rejected = True
        form.remark = ""

        result = services.get_assistantship_status_text(form)
        self.assertEqual(result, "Rejected")

    def test_get_assistantship_status_text_approved(self):
        """Test status text when fully approved."""
        form = MagicMock()
        form.TA_rejected = False
        form.HOD_rejected = False
        form.Acad_rejected = False
        form.remark = "Stipend disbursed (audit completed)"

        result = services.get_assistantship_status_text(form)
        self.assertEqual(result, "Approved")

    def test_get_assistantship_status_text_pending(self):
        """Test status text when pending."""
        form = MagicMock()
        form.TA_rejected = False
        form.HOD_rejected = False
        form.Acad_rejected = False
        form.remark = ""

        result = services.get_assistantship_status_text(form)
        self.assertEqual(result, "Pending")

    def test_get_assistantship_approval_stages(self):
        """Test getting approval stages."""
        form = MagicMock()
        form.TA_approved = True
        form.TA_rejected = False
        form.HOD_approved = True
        form.HOD_rejected = False
        form.Acad_approved = True
        form.Acad_rejected = False
        form.remark = "Stipend disbursed (audit completed)"

        result = services.get_assistantship_approval_stages(form)

        self.assertEqual(result['Faculty_Supervisor'], 'Approved')
        self.assertEqual(result['Department_Admin'], 'Approved')
        self.assertEqual(result['HOD'], 'Approved')
        self.assertEqual(result['Acad_Admin_Audit'], 'Disbursed')

    @patch('applications.otheracademic.services.otheracademic_notif')
    @patch('applications.otheracademic.services.AssistantshipClaimFormStatusUpd.objects.create')
    @patch('applications.otheracademic.services.selectors.get_first_user_for_designation')
    @patch('applications.otheracademic.services.selectors.assistantship_exists_for_period')
    @patch('applications.otheracademic.services.selectors.get_pg_faculty_supervisor_assignment_for_student')
    def test_submit_assistantship_uses_assigned_supervisor(
        self,
        mock_get_assignment,
        mock_exists,
        mock_get_dept_admin,
        mock_create,
        mock_notif,
    ):
        """Submission should use configured faculty supervisor assignment."""
        student_user = MagicMock()
        student_user.extrainfo.id = "23MCS111"
        student_user.first_name = "PG"
        student_user.last_name = "Student"

        assigned_supervisor = MagicMock()
        assigned_supervisor.username = "fac1"
        mock_get_assignment.return_value = MagicMock(faculty_supervisor=assigned_supervisor)
        mock_exists.return_value = False
        mock_get_dept_admin.return_value = MagicMock(username="dept1")
        mock_create.return_value = MagicMock(id=101)

        services.submit_assistantship(
            user=student_user,
            discipline="CSE",
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
            date_applied=date(2026, 4, 1),
            bank_account="123",
            signature_file="sig.jpg",
            ta_supervisor="fac1",
            thesis_supervisor="",
            hod="",
            applicability="monthly",
        )

        self.assertTrue(mock_create.called)
        kwargs = mock_create.call_args.kwargs
        self.assertEqual(kwargs["ta_supervisor"], "fac1")

    @patch('applications.otheracademic.services.selectors.get_pg_faculty_supervisor_assignment_for_student')
    @patch('applications.otheracademic.services.selectors.assistantship_exists_for_period')
    def test_submit_assistantship_fails_without_supervisor_assignment(
        self,
        mock_exists,
        mock_get_assignment,
    ):
        """Submission should fail when no supervisor is assigned and no valid fallback is provided."""
        student_user = MagicMock()
        student_user.extrainfo.id = "23MCS111"
        mock_exists.return_value = False
        mock_get_assignment.return_value = None

        with self.assertRaises(services.AssistantshipServiceError):
            services.submit_assistantship(
                user=student_user,
                discipline="CSE",
                date_from=date(2026, 4, 1),
                date_to=date(2026, 4, 30),
                date_applied=date(2026, 4, 1),
                bank_account="123",
                signature_file="sig.jpg",
                ta_supervisor="",
                thesis_supervisor="",
                hod="",
                applicability="monthly",
            )
