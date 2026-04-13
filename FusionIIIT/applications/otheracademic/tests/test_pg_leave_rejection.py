"""
Test suite for PG Leave rejection workflow (T8).
Tests the complete rejection process including remarks capture,
resubmission, and student notifications.
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import datetime, timedelta

from applications.otheracademic.models import (
    LeavePG,
    LeaveStatusChoices,
)
from applications.globals.models import ExtraInfo


class PGLeaveRejectionTestCase(APITestCase):
    """Test suite for PG leave rejection workflow."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.student_user = User.objects.create_user(
            username='pg_student',
            password='testpass123',
            email='student@test.com',
            first_name='PG',
            last_name='Student'
        )
        
        self.admin_user = User.objects.create_user(
            username='pg_admin',
            password='testpass123',
            email='admin@test.com',
            first_name='Admin',
            last_name='User'
        )
        
        # Create ExtraInfo for both users
        self.student_extra = ExtraInfo.objects.create(
            user=self.student_user,
            roll_no='PG2024001',
            curr_semester='2'
        )
        
        self.admin_extra = ExtraInfo.objects.create(
            user=self.admin_user,
            roll_no='ADMIN001',
            curr_semester='1'
        )
        
        # Create API client
        self.client = APIClient()
        
        # Create leave request
        self.leave_request = LeavePG.objects.create(
            student_id=self.student_extra,
            start_date=datetime.now().date() + timedelta(days=7),
            end_date=datetime.now().date() + timedelta(days=14),
            reason='Research conference attendance',
            status=LeaveStatusChoices.PENDING,
            date_of_application=datetime.now()
        )

    def test_pg_leave_rejection_without_remarks(self):
        """Test rejecting PG leave without remarks."""
        self.client.force_authenticate(user=self.admin_user)
        
        payload = {
            'leave_request_id': self.leave_request.id,
            'action': 'reject',
            'remarks': ''
        }
        
        response = self.client.post(
            '/api/otheracademic/update-leave-pg-status/',
            data=payload,
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify database update
        self.leave_request.refresh_from_db()
        self.assertEqual(self.leave_request.status, LeaveStatusChoices.REJECTED)
        self.assertEqual(self.leave_request.rejection_remarks, '')

    def test_pg_leave_rejection_with_remarks(self):
        """Test rejecting PG leave with specific remarks."""
        self.client.force_authenticate(user=self.admin_user)
        
        remarks = "Insufficient justification provided. Please submit detailed research proposal."
        
        payload = {
            'leave_request_id': self.leave_request.id,
            'action': 'reject',
            'remarks': remarks
        }
        
        response = self.client.post(
            '/api/otheracademic/update-leave-pg-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify remarks stored correctly
        self.leave_request.refresh_from_db()
        self.assertEqual(self.leave_request.status, LeaveStatusChoices.REJECTED)
        self.assertEqual(self.leave_request.rejection_remarks, remarks)

    def test_pg_leave_rejection_remarks_length_validation(self):
        """Test remarks field validates maximum length."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create remarks exceeding max length (1000 chars)
        long_remarks = 'x' * 1001
        
        payload = {
            'leave_request_id': self.leave_request.id,
            'action': 'reject',
            'remarks': long_remarks
        }
        
        response = self.client.post(
            '/api/otheracademic/update-leave-pg-status/',
            data=payload,
            format='json'
        )
        
        # Should return validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pg_leave_resubmission_after_rejection(self):
        """Test student can resubmit after rejection."""
        # First rejection
        self.leave_request.status = LeaveStatusChoices.REJECTED
        self.leave_request.rejection_remarks = "Need more documentation"
        self.leave_request.save()
        
        # Student resubmits with additional documents
        self.client.force_authenticate(user=self.student_user)
        
        new_leave_request = {
            'start_date': (datetime.now().date() + timedelta(days=7)).isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=14)).isoformat(),
            'reason': 'Research conference attendance - with approved letter attached',
            'supporting_documents': 'conference_approval.pdf'
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-pg/',
            data=new_leave_request,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify new request created with PENDING status
        new_request = LeavePG.objects.filter(
            student_id=self.student_extra,
            status=LeaveStatusChoices.PENDING
        ).latest('date_of_application')
        
        self.assertEqual(new_request.status, LeaveStatusChoices.PENDING)
        self.assertNotEqual(new_request.id, self.leave_request.id)

    def test_pg_leave_rejection_access_control(self):
        """Test only authorized users can reject PG leave."""
        # Try with student (should fail)
        self.client.force_authenticate(user=self.student_user)
        
        payload = {
            'leave_request_id': self.leave_request.id,
            'action': 'reject',
            'remarks': 'Unauthorized'
        }
        
        response = self.client.post(
            '/api/otheracademic/update-leave-pg-status/',
            data=payload,
            format='json'
        )
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Leave status should remain PENDING
        self.leave_request.refresh_from_db()
        self.assertEqual(self.leave_request.status, LeaveStatusChoices.PENDING)

    def test_pg_leave_rejection_then_approval(self):
        """Test leave can be approved after being rejected and resubmitted."""
        # Initial rejection
        self.leave_request.status = LeaveStatusChoices.REJECTED
        self.leave_request.rejection_remarks = "Resubmit with better documentation"
        self.leave_request.save()
        
        # Create resubmitted request
        resubmitted = LeavePG.objects.create(
            student_id=self.student_extra,
            start_date=self.leave_request.start_date,
            end_date=self.leave_request.end_date,
            reason=self.leave_request.reason + " - addressing previous comments",
            status=LeaveStatusChoices.PENDING,
            date_of_application=datetime.now()
        )
        
        # Admin approves the resubmitted request
        self.client.force_authenticate(user=self.admin_user)
        
        payload = {
            'leave_request_id': resubmitted.id,
            'action': 'approve'
        }
        
        response = self.client.post(
            '/api/otheracademic/update-leave-pg-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify approval
        resubmitted.refresh_from_db()
        self.assertEqual(resubmitted.status, LeaveStatusChoices.APPROVED)

    def test_pg_leave_rejection_idempotency(self):
        """Test rejecting same request multiple times (idempotency)."""
        self.client.force_authenticate(user=self.admin_user)
        
        remarks1 = "First rejection reason"
        
        # First rejection
        payload1 = {
            'leave_request_id': self.leave_request.id,
            'action': 'reject',
            'remarks': remarks1
        }
        
        response1 = self.client.post(
            '/api/otheracademic/update-leave-pg-status/',
            data=payload1,
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second rejection attempt (should be idempotent)
        remarks2 = "Updated rejection reason"
        payload2 = {
            'leave_request_id': self.leave_request.id,
            'action': 'reject',
            'remarks': remarks2
        }
        
        response2 = self.client.post(
            '/api/otheracademic/update-leave-pg-status/',
            data=payload2,
            format='json'
        )
        
        # Second update should succeed or be idempotent (depends on business logic)
        self.assertIn(response2.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_pg_leave_rejection_notification_trigger(self):
        """Test that rejection triggers student notification."""
        self.client.force_authenticate(user=self.admin_user)
        
        remarks = "Please provide additional documentation"
        
        payload = {
            'leave_request_id': self.leave_request.id,
            'action': 'reject',
            'remarks': remarks
        }
        
        response = self.client.post(
            '/api/otheracademic/update-leave-pg-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response indicates notification sent
        response_data = response.json()
        self.assertIn('notification_sent', response_data)
        self.assertTrue(response_data.get('notification_sent', False))

    def test_pg_leave_cancelled_before_rejection(self):
        """Test rejecting cancelled leave request."""
        # Student cancels the request
        self.leave_request.status = LeaveStatusChoices.CANCELLED
        self.leave_request.save()
        
        self.client.force_authenticate(user=self.admin_user)
        
        payload = {
            'leave_request_id': self.leave_request.id,
            'action': 'reject',
            'remarks': 'Cannot process - request was cancelled'
        }
        
        response = self.client.post(
            '/api/otheracademic/update-leave-pg-status/',
            data=payload,
            format='json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pg_leave_rejection_remarks_contain_actionable_info(self):
        """Test rejection remarks include actionable information for student."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Well-structured remarks with action items
        remarks = """Your request was rejected for the following reasons:
1. Insufficient justification for 7-day absence
2. Missing recommendation letter from supervisor
3. No alternative work arrangement plan

Please resubmit with:
- Detailed research plan
- Supervisor's approval letter
- Contingency plan for research continuity"""
        
        payload = {
            'leave_request_id': self.leave_request.id,
            'action': 'reject',
            'remarks': remarks
        }
        
        response = self.client.post(
            '/api/otheracademic/update-leave-pg-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify full remarks stored
        self.leave_request.refresh_from_db()
        self.assertEqual(self.leave_request.rejection_remarks, remarks)
        self.assertIn('resubmit', self.leave_request.rejection_remarks.lower())
