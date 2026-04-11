"""
Test suite for Assistantship rejection workflows (T9).
Tests all approval stages: HoD, Academic Admin, Thesis Supervisor, TA Supervisor.
Each stage can reject with remarks; tests parallel and sequential approval flows.
"""
import json
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from datetime import datetime, timedelta

from applications.otheracademic.models import (
    AssistantshipClaimFormStatusUpd,
    AssistantshipStatusChoices,
)
from applications.globals.models import ExtraInfo, HoldsDesignation


class AssistantshipRejectionTestCase(APITestCase):
    """Test suite for assistantship rejection workflows through all approval stages."""

    def setUp(self):
        """Set up test data with all approval levels."""
        # Create test users for each approval level
        self.student_user = User.objects.create_user(
            username='assist_student',
            password='testpass123',
            email='student@test.com'
        )
        
        self.hod_user = User.objects.create_user(
            username='hod_user',
            password='testpass123',
            email='hod@test.com'
        )
        
        self.acad_admin_user = User.objects.create_user(
            username='acad_admin',
            password='testpass123',
            email='acadadmin@test.com'
        )
        
        self.thesis_supervisor = User.objects.create_user(
            username='thesis_supervisor',
            password='testpass123',
            email='thesis@test.com'
        )
        
        self.ta_supervisor = User.objects.create_user(
            username='ta_supervisor',
            password='testpass123',
            email='ta@test.com'
        )
        
        # Create ExtraInfo
        self.student_extra = ExtraInfo.objects.create(
            user=self.student_user,
            roll_no='2024001',
            curr_semester='4'
        )
        
        self.hod_extra = ExtraInfo.objects.create(
            user=self.hod_user,
            roll_no='HOD001',
            curr_semester='1'
        )
        
        # Create designation records
        HoldsDesignation.objects.create(
            user=self.hod_user,
            designation='hod'
        )
        
        HoldsDesignation.objects.create(
            user=self.acad_admin_user,
            designation='acadadmin'
        )
        
        # Create assistantship claim
        self.assistantship_claim = AssistantshipClaimFormStatusUpd.objects.create(
            student_id=self.student_extra,
            ta_approval_status=AssistantshipStatusChoices.PENDING,
            hod_approval_status=AssistantshipStatusChoices.PENDING,
            acad_admin_approval_status=AssistantshipStatusChoices.PENDING,
            thesis_supervisor_approval_status=AssistantshipStatusChoices.PENDING,
            date_of_application=datetime.now()
        )
        
        self.client = APIClient()

    def test_hod_rejects_assistantship_claim(self):
        """Test HoD rejection of assistantship claim."""
        self.client.force_authenticate(user=self.hod_user)
        
        remarks = "Insufficient academic performance. GPA below 3.0 requirement."
        
        payload = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'hod',
            'action': 'reject',
            'remarks': remarks
        }
        
        response = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify status update
        self.assistantship_claim.refresh_from_db()
        self.assertEqual(
            self.assistantship_claim.hod_approval_status,
            AssistantshipStatusChoices.REJECTED
        )
        self.assertEqual(self.assistantship_claim.remark, remarks)

    def test_acad_admin_rejects_after_hod_approval(self):
        """Test Academic Admin can reject even after HoD approval."""
        # HoD approves first
        self.assistantship_claim.hod_approval_status = AssistantshipStatusChoices.APPROVED
        self.assistantship_claim.save()
        
        self.client.force_authenticate(user=self.acad_admin_user)
        
        remarks = "Budget allocation exceeded for this semester."
        
        payload = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'acad_admin',
            'action': 'reject',
            'remarks': remarks
        }
        
        response = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assistantship_claim.refresh_from_db()
        self.assertEqual(
            self.assistantship_claim.acad_admin_approval_status,
            AssistantshipStatusChoices.REJECTED
        )
        self.assertEqual(self.assistantship_claim.remark, remarks)

    def test_sequential_approval_flow_with_rejection(self):
        """Test sequential approval: HoD->Acad Admin->Thesis->TA, with rejection at stage 2."""
        # Stage 1: HoD approves
        self.assistantship_claim.hod_approval_status = AssistantshipStatusChoices.APPROVED
        self.assistantship_claim.save()
        
        # Stage 2: Acad Admin rejects
        self.client.force_authenticate(user=self.acad_admin_user)
        
        remarks = "Requires official letter from department"
        
        payload = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'acad_admin',
            'action': 'reject',
            'remarks': remarks
        }
        
        response = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify workflow stops at rejection
        self.assistantship_claim.refresh_from_db()
        self.assertEqual(
            self.assistantship_claim.acad_admin_approval_status,
            AssistantshipStatusChoices.REJECTED
        )
        # Subsequent stages should not progress
        self.assertEqual(
            self.assistantship_claim.thesis_supervisor_approval_status,
            AssistantshipStatusChoices.PENDING
        )

    def test_thesis_supervisor_rejection_with_detailed_feedback(self):
        """Test thesis supervisor rejection with constructive feedback."""
        # Assume all prior approvals passed
        self.assistantship_claim.hod_approval_status = AssistantshipStatusChoices.APPROVED
        self.assistantship_claim.acad_admin_approval_status = AssistantshipStatusChoices.APPROVED
        self.assistantship_claim.save()
        
        self.client.force_authenticate(user=self.thesis_supervisor)
        
        detailed_remarks = """The assistantship is rejected because:
1. Research work not sufficiently advanced
2. Need to focus on thesis completion first
3. Time commitment conflicts with current timeline

Recommended action: Reapply after completing literature review (by June 30)"""
        
        payload = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'thesis_supervisor',
            'action': 'reject',
            'remarks': detailed_remarks
        }
        
        response = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assistantship_claim.refresh_from_db()
        self.assertEqual(
            self.assistantship_claim.thesis_supervisor_approval_status,
            AssistantshipStatusChoices.REJECTED
        )
        self.assertIn('June 30', self.assistantship_claim.remark)

    def test_ta_supervisor_rejects_final_stage(self):
        """Test TA Supervisor rejection at final approval stage."""
        # All prior stages approved
        self.assistantship_claim.hod_approval_status = AssistantshipStatusChoices.APPROVED
        self.assistantship_claim.acad_admin_approval_status = AssistantshipStatusChoices.APPROVED
        self.assistantship_claim.thesis_supervisor_approval_status = AssistantshipStatusChoices.APPROVED
        self.assistantship_claim.save()
        
        self.client.force_authenticate(user=self.ta_supervisor)
        
        remarks = "Position already filled for this semester. Consider next semester."
        
        payload = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'ta_supervisor',
            'action': 'reject',
            'remarks': remarks
        }
        
        response = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assistantship_claim.refresh_from_db()
        self.assertEqual(
            self.assistantship_claim.ta_approval_status,
            AssistantshipStatusChoices.REJECTED
        )

    def test_parallel_approval_rejection_scenario(self):
        """Test parallel approval flow where multiple approvers act simultaneously."""
        # In parallel mode: HoD and TA can approve/reject independently
        
        self.client.force_authenticate(user=self.hod_user)
        
        # HoD rejects
        payload_hod = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'hod',
            'action': 'reject',
            'remarks': 'Academic standing concerns'
        }
        
        response_hod = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload_hod,
            format='json'
        )
        
        self.assertEqual(response_hod.status_code, status.HTTP_200_OK)
        
        # In parallel mode, TA supervisor can still act
        self.client.force_authenticate(user=self.ta_supervisor)
        
        # TA approves (regardless of HoD rejection)
        payload_ta = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'ta_supervisor',
            'action': 'approve'
        }
        
        response_ta = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload_ta,
            format='json'
        )
        
        self.assertEqual(response_ta.status_code, status.HTTP_200_OK)
        
        # Both statuses should be recorded
        self.assistantship_claim.refresh_from_db()
        self.assertEqual(
            self.assistantship_claim.hod_approval_status,
            AssistantshipStatusChoices.REJECTED
        )
        self.assertEqual(
            self.assistantship_claim.ta_approval_status,
            AssistantshipStatusChoices.APPROVED
        )

    def test_multiple_rejection_attempts_same_level(self):
        """Test updating rejection remarks at same approval level."""
        self.client.force_authenticate(user=self.hod_user)
        
        # First rejection
        payload1 = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'hod',
            'action': 'reject',
            'remarks': 'Initial reason: Low GPA'
        }
        
        response1 = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload1,
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Update rejection with more details
        payload2 = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'hod',
            'action': 'reject',
            'remarks': 'Updated reason: Low GPA (2.8/4.0) and attendance issues'
        }
        
        response2 = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload2,
            format='json'
        )
        
        # Second update should succeed
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        self.assistantship_claim.refresh_from_db()
        self.assertIn('attendance', self.assistantship_claim.remark.lower())

    def test_rejection_access_control_by_level(self):
        """Test only authorized users can reject at their approval level."""
        # Student tries to reject (should fail)
        self.client.force_authenticate(user=self.student_user)
        
        payload = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'hod',
            'action': 'reject',
            'remarks': 'Unauthorized'
        }
        
        response = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Status should remain unchanged
        self.assistantship_claim.refresh_from_db()
        self.assertEqual(
            self.assistantship_claim.hod_approval_status,
            AssistantshipStatusChoices.PENDING
        )

    def test_escalation_after_rejection(self):
        """Test escalation workflow triggers after rejection."""
        self.client.force_authenticate(user=self.hod_user)
        
        remarks = "Rejected - requires director approval for exception"
        
        payload = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'hod',
            'action': 'reject',
            'remarks': remarks,
            'requires_escalation': True
        }
        
        response = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify escalation flag is set
        response_data = response.json()
        self.assertTrue(response_data.get('escalation_required', False))

    def test_rejection_reversal_workflow(self):
        """Test workflow for reversing a rejection (admin override)."""
        # Initial state: rejected
        self.assistantship_claim.hod_approval_status = AssistantshipStatusChoices.REJECTED
        self.assistantship_claim.remark = "Initial rejection"
        self.assistantship_claim.save()
        
        self.client.force_authenticate(user=self.hod_user)
        
        # HoD changes mind and approves
        payload = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'hod',
            'action': 'approve',
            'remarks': 'After further review, condition waived'
        }
        
        response = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assistantship_claim.refresh_from_db()
        self.assertEqual(
            self.assistantship_claim.hod_approval_status,
            AssistantshipStatusChoices.APPROVED
        )
        self.assertIn('waived', self.assistantship_claim.remark.lower())

    def test_all_rejections_lead_to_overall_rejected_status(self):
        """Test that if any approval level rejects, overall status is rejected."""
        # Multiple rejections
        self.assistantship_claim.hod_approval_status = AssistantshipStatusChoices.REJECTED
        self.assistantship_claim.acad_admin_approval_status = AssistantshipStatusChoices.PENDING
        self.assistantship_claim.save()
        
        self.client.force_authenticate(user=self.hod_user)
        
        payload = {
            'claim_id': self.assistantship_claim.id,
            'approval_level': 'hod',
            'action': 'reject',
            'remarks': 'Overall status should be rejected'
        }
        
        response = self.client.post(
            '/api/otheracademic/update-assistantship-status/',
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify overall workflow status is rejected
        response_data = response.json()
        overall_status = response_data.get('overall_status')
        self.assertEqual(overall_status, 'REJECTED')
