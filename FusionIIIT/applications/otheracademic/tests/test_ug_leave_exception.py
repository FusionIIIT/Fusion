"""
Test suite for UG Leave exception workflows (T18).
Tests emergency leaves, medical/compassionate conditions, fast-track approvals,
and special exception handling.
"""
import json
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from datetime import datetime, timedelta

from applications.otheracademic.models import (
    LeaveFormTable,
    LeaveStatusChoices,
    LeaveExceptionType,  # Assuming this model exists or will be created
)
from applications.globals.models import ExtraInfo, HoldsDesignation


class UGLeaveExceptionTestCase(APITestCase):
    """Test suite for UG leave exception workflows."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.student_user = User.objects.create_user(
            username='ug_student',
            password='testpass123',
            email='student@test.com',
            first_name='UG',
            last_name='Student'
        )
        
        self.dean_user = User.objects.create_user(
            username='dean_user',
            password='testpass123',
            email='dean@test.com'
        )
        
        self.medical_office_user = User.objects.create_user(
            username='medical_office',
            password='testpass123',
            email='medical@test.com'
        )
        
        # Create ExtraInfo
        self.student_extra = ExtraInfo.objects.create(
            user=self.student_user,
            roll_no='2024501',
            curr_semester='3'
        )
        
        self.dean_extra = ExtraInfo.objects.create(
            user=self.dean_user,
            roll_no='DEAN001',
            curr_semester='1'
        )
        
        # Create designation for dean
        HoldsDesignation.objects.create(
            user=self.dean_user,
            designation='dean'
        )
        
        self.client = APIClient()

    def test_emergency_leave_request_immediate_approval(self):
        """Test emergency leave bypasses normal approval process."""
        self.client.force_authenticate(user=self.student_user)
        
        # Emergency leave (e.g., accident, sudden illness)
        emergency_payload = {
            'start_date': datetime.now().date().isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=2)).isoformat(),
            'reason': 'Medical emergency - hospitalization required',
            'is_emergency': True,
            'exception_type': 'medical_emergency',
            'supporting_documents': 'hospital_admission_letter.pdf'
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-form/',
            data=emergency_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify emergency flag
        leave = LeaveFormTable.objects.get(student_id=self.student_extra)
        self.assertTrue(leave.is_emergency)
        self.assertEqual(leave.leave_exception_type, 'medical_emergency')

    def test_medical_leave_with_health_center_verification(self):
        """Test medical leave with health center documentation."""
        self.client.force_authenticate(user=self.student_user)
        
        medical_payload = {
            'start_date': (datetime.now().date() + timedelta(days=1)).isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=3)).isoformat(),
            'reason': 'Severe viral infection - fever, cough',
            'leave_type': 'medical',
            'medical_certificate_present': True,
            'health_center_recommendation': 'Rest for 3 days advised',
            'supporting_documents': 'health_center_certificate.pdf'
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-form/',
            data=medical_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        leave = LeaveFormTable.objects.get(student_id=self.student_extra)
        self.assertTrue(leave.medical_certificate_present)
        self.assertEqual(leave.leave_type, 'medical')

    def test_medical_leave_fast_track_approval(self):
        """Test medical leave with health center approval gets fast-tracked."""
        # Create medical leave
        leave = LeaveFormTable.objects.create(
            student_id=self.student_extra,
            start_date=datetime.now().date() + timedelta(days=1),
            end_date=datetime.now().date() + timedelta(days=3),
            reason='High fever and cough',
            leave_type='medical',
            medical_certificate_present=True,
            status=LeaveStatusChoices.PENDING,
            date_of_application=datetime.now()
        )
        
        # Medical office verifies
        self.client.force_authenticate(user=self.medical_office_user)
        
        verification_payload = {
            'leave_id': leave.id,
            'action': 'verify_medical',
            'medical_findings': 'Flu diagnosed, rest recommended'
        }
        
        response = self.client.post(
            '/api/otheracademic/verify-medical-leave/',
            data=verification_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        leave.refresh_from_db()
        self.assertTrue(leave.medical_verified)

    def test_compassionate_leave_exception_approval(self):
        """Test compassionate leave handling (death, family emergency)."""
        self.client.force_authenticate(user=self.student_user)
        
        compassionate_payload = {
            'start_date': datetime.now().date().isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=5)).isoformat(),
            'reason': 'Death of immediate family member (grandfather)',
            'leave_type': 'compassionate',
            'exception_type': 'family_death',
            'supporting_documents': 'death_certificate.pdf'
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-form/',
            data=compassionate_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        leave = LeaveFormTable.objects.get(student_id=self.student_extra)
        self.assertEqual(leave.leave_type, 'compassionate')
        self.assertEqual(leave.exception_type, 'family_death')

    def test_compassionate_leave_fast_track_verification(self):
        """Test compassionate leave gets fast-track approval to dean."""
        # Create compassionate leave
        leave = LeaveFormTable.objects.create(
            student_id=self.student_extra,
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=5),
            reason='Death of grandmother',
            leave_type='compassionate',
            status=LeaveStatusChoices.PENDING,
            date_of_application=datetime.now(),
            supporting_documents='death_certificate.pdf'
        )
        
        # Dean approves immediately
        self.client.force_authenticate(user=self.dean_user)
        
        dean_payload = {
            'leave_id': leave.id,
            'action': 'approve',
            'remarks': 'Compassionate leave approved for 5 days'
        }
        
        response = self.client.post(
            '/api/otheracademic/update-leave-status/',
            data=dean_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        leave.refresh_from_db()
        self.assertEqual(leave.status, LeaveStatusChoices.APPROVED)

    def test_exception_leave_exceeding_limit_requires_dean_approval(self):
        """Test leave exceeding policy limit requires dean exception approval."""
        self.client.force_authenticate(user=self.student_user)
        
        # Request 15 days (exceeds typical 10-day limit)
        exception_payload = {
            'start_date': (datetime.now().date() + timedelta(days=7)).isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=22)).isoformat(),  # 15 days
            'reason': 'Extended family business handling after grandfather death',
            'leave_type': 'general',
            'requires_dean_exception': True,
            'justification': 'Family business settlement requires extended time. All coursework completed in advance.'
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-form/',
            data=exception_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        leave = LeaveFormTable.objects.get(student_id=self.student_extra)
        self.assertTrue(leave.requires_dean_exception)
        self.assertGreater((leave.end_date - leave.start_date).days, 10)

    def test_exception_leave_dean_rejection_with_alternative_dates(self):
        """Test dean can reject exception leave and suggest alternative dates."""
        # Create exception leave request
        leave = LeaveFormTable.objects.create(
            student_id=self.student_extra,
            start_date=datetime.now().date() + timedelta(days=7),
            end_date=datetime.now().date() + timedelta(days=22),
            reason='Extended research trip',
            leave_type='general',
            requires_dean_exception=True,
            status=LeaveStatusChoices.PENDING,
            date_of_application=datetime.now()
        )
        
        # Dean rejects but suggests alternative
        self.client.force_authenticate(user=self.dean_user)
        
        dean_payload = {
            'leave_id': leave.id,
            'action': 'reject',
            'remarks': 'Cannot approve 15-day leave. Suggest reducing to 8 days during mid-semester break (dates provided by registrar).',
            'suggested_start_date': (datetime.now().date() + timedelta(days=14)).isoformat(),
            'suggested_end_date': (datetime.now().date() + timedelta(days=22)).isoformat()
        }
        
        response = self.client.post(
            '/api/otheracademic/update-leave-status/',
            data=dean_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        leave.refresh_from_db()
        self.assertEqual(leave.status, LeaveStatusChoices.REJECTED)
        # Verify suggestion in remarks
        self.assertIn('suggest', leave.rejection_remarks.lower())

    def test_disability_accommodation_leave_priority_processing(self):
        """Test leave for students with disabilities gets priority."""
        self.client.force_authenticate(user=self.student_user)
        
        disability_payload = {
            'start_date': (datetime.now().date() + timedelta(days=3)).isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=8)).isoformat(),
            'reason': 'Medical treatment for registered disability accommodation',
            'has_disability_registration': True,
            'disability_accommodation_id': 'DA-2024-001',
            'high_priority': True
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-form/',
            data=disability_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        leave = LeaveFormTable.objects.get(student_id=self.student_extra)
        self.assertTrue(leave.has_disability_registration)
        self.assertTrue(leave.high_priority)

    def test_exceptional_academic_circumstances_leave(self):
        """Test leave for exceptional academic circumstances (exam makeup, etc.)."""
        self.client.force_authenticate(user=self.student_user)
        
        academic_exception_payload = {
            'start_date': (datetime.now().date() + timedelta(days=14)).isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=16)).isoformat(),
            'reason': 'Makeup examination required due to medical absence',
            'exception_type': 'academic_circumstance',
            'exam_details': {
                'course_code': 'CS301',
                'course_name': 'Algorithms',
                'exam_date': (datetime.now().date() + timedelta(days=15)).isoformat()
            }
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-form/',
            data=academic_exception_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        leave = LeaveFormTable.objects.get(student_id=self.student_extra)
        self.assertEqual(leave.exception_type, 'academic_circumstance')

    def test_concurrent_leave_exception_rule(self):
        """Test concurrent leave overlaps are detected and rejected."""
        # Create first leave
        leave1 = LeaveFormTable.objects.create(
            student_id=self.student_extra,
            start_date=datetime.now().date() + timedelta(days=10),
            end_date=datetime.now().date() + timedelta(days=15),
            reason='Planned leave 1',
            leave_type='general',
            status=LeaveStatusChoices.APPROVED,
            date_of_application=datetime.now()
        )
        
        # Try to create overlapping leave
        self.client.force_authenticate(user=self.student_user)
        
        overlapping_payload = {
            'start_date': (datetime.now().date() + timedelta(days=12)).isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=17)).isoformat(),
            'reason': 'Overlapping leave attempt'
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-form/',
            data=overlapping_payload,
            format='json'
        )
        
        # Should be rejected due to overlap
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('overlap', response.json().get('error', '').lower())

    def test_exception_leave_documentation_requirement(self):
        """Test exception leaves require proper supporting documentation."""
        self.client.force_authenticate(user=self.student_user)
        
        # Medical exception without documentation
        incomplete_payload = {
            'start_date': (datetime.now().date() + timedelta(days=1)).isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=5)).isoformat(),
            'reason': 'Medical emergency',
            'exception_type': 'medical_emergency',
            # Missing supporting_documents
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-form/',
            data=incomplete_payload,
            format='json'
        )
        
        # Should require documentation for medical exception
        if response.status_code == status.HTTP_201_CREATED:
            leave = LeaveFormTable.objects.get(student_id=self.student_extra)
            self.assertFalse(leave.is_complete)  # Marked as incomplete without docs
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_emergency_leave_minimal_documentation(self):
        """Test emergency leave can be approved with minimal documentation initially."""
        self.client.force_authenticate(user=self.student_user)
        
        emergency_payload = {
            'start_date': datetime.now().date().isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=1)).isoformat(),
            'reason': 'Sudden family emergency',
            'is_emergency': True,
            'exception_type': 'family_emergency',
            'documentation_to_follow': True
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-form/',
            data=emergency_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        leave = LeaveFormTable.objects.get(student_id=self.student_extra)
        self.assertTrue(leave.documentation_to_follow)
        # Should auto-approve or fast-track
        self.assertIn(leave.status, [
            LeaveStatusChoices.APPROVED,
            LeaveStatusChoices.PENDING,  # Fast-tracked to dean
        ])

    def test_exception_leave_deadline_extension(self):
        """Test student can request deadline extension for documentation."""
        # Create exception leave awaiting documentation
        leave = LeaveFormTable.objects.create(
            student_id=self.student_extra,
            start_date=datetime.now().date() + timedelta(days=1),
            end_date=datetime.now().date() + timedelta(days=3),
            reason='Medical emergency',
            is_emergency=True,
            documentation_to_follow=True,
            documentation_deadline=datetime.now().date() + timedelta(days=3),
            status=LeaveStatusChoices.PENDING,
            date_of_application=datetime.now()
        )
        
        self.client.force_authenticate(user=self.student_user)
        
        extension_payload = {
            'leave_id': leave.id,
            'action': 'request_extension',
            'extension_days': 5,
            'reason': 'Hospital still evaluating test results'
        }
        
        response = self.client.post(
            '/api/otheracademic/extend-documentation-deadline/',
            data=extension_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        leave.refresh_from_db()
        self.assertEqual(
            leave.documentation_deadline,
            datetime.now().date() + timedelta(days=8)
        )

    def test_exception_leave_submission_after_approval(self):
        """Test submitting documentation after emergency leave approval."""
        # Emergency leave created and approved
        leave = LeaveFormTable.objects.create(
            student_id=self.student_extra,
            start_date=datetime.now().date() + timedelta(days=1),
            end_date=datetime.now().date() + timedelta(days=2),
            reason='Medical emergency',
            is_emergency=True,
            documentation_to_follow=True,
            status=LeaveStatusChoices.APPROVED,
            date_of_application=datetime.now()
        )
        
        self.client.force_authenticate(user=self.student_user)
        
        # Student submits documentation
        doc_payload = {
            'leave_id': leave.id,
            'supporting_documents': 'emergency_room_receipt.pdf',
            'doctor_notes': 'Patient admitted with acute severe infection'
        }
        
        response = self.client.post(
            '/api/otheracademic/submit-leave-documentation/',
            data=doc_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        leave.refresh_from_db()
        self.assertFalse(leave.documentation_to_follow)
        self.assertTrue(leave.documentation_submitted)
