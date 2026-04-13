"""
Patent Management System — Tests
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from applications.patent_system.models import (
    Applicant, Application, ApplicationStatus, DecisionStatus,
    Inventor, CommunicationLog, Budget, AuditLog,
    AttorneyAssignment, PatentabilityAssessment, FilingRecord,
    PatentabilityRecommendation,
)
from applications.patent_system import services


class PatentModelTests(TestCase):
    """Basic model creation tests."""

    def setUp(self):
        self.user = User.objects.create_user("testuser", "test@iiitdmj.ac.in", "pass")
        self.applicant = Applicant.objects.create(
            user=self.user, name="Test User", email="test@iiitdmj.ac.in"
        )
        self.application = Application.objects.create(
            title="Test Patent",
            primary_applicant=self.applicant,
            status=ApplicationStatus.DRAFT,
        )

    def test_application_created(self):
        self.assertEqual(self.application.status, ApplicationStatus.DRAFT)

    def test_inventor_association(self):
        inv = Inventor.objects.create(
            applicant=self.applicant, application=self.application, percentage_share=100
        )
        self.assertEqual(inv.percentage_share, 100)

    def test_budget_total_calculation(self):
        b = Budget.objects.create(
            application=self.application,
            filing_cost=1000,
            attorney_fees=2000,
            administrative_cost=500,
        )
        self.assertEqual(b.total_cost, 3500)

    def test_audit_log_creation(self):
        AuditLog.objects.create(
            application=self.application,
            user=self.user,
            action="Test action",
        )
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_attorney_assignment_creation(self):
        """UC-006: Test that AttorneyAssignment model can be created."""
        assignment = AttorneyAssignment.objects.create(
            application=self.application,
            attorney_name="Adv. Sharma",
            attorney_email="sharma@lawfirm.com",
            attorney_firm="Sharma & Associates",
            specialization="Patent Law",
            assigned_by=self.user,
        )
        self.assertEqual(assignment.attorney_name, "Adv. Sharma")
        self.assertTrue(assignment.is_active)

    def test_patentability_assessment_creation(self):
        """UC-007 / BR-PMS-014: Test PatentabilityAssessment model."""
        assessment = PatentabilityAssessment.objects.create(
            application=self.application,
            assessed_by_attorney="Adv. Sharma",
            novelty_score=85,
            non_obviousness_score=70,
            utility_score=90,
            search_completeness=95,
            recommendation=PatentabilityRecommendation.FILE_PATENT,
            opinion_summary="The invention shows significant novelty and utility.",
            recorded_by=self.user,
        )
        self.assertEqual(assessment.recommendation, PatentabilityRecommendation.FILE_PATENT)

    def test_filing_record_creation(self):
        """UC-009 / WF-601: Test FilingRecord model."""
        filing = FilingRecord.objects.create(
            application=self.application,
            filing_office="Indian Patent Office",
            jurisdiction="India",
            external_filing_id="IPO/2026/001234",
            filed_by=self.user,
        )
        self.assertEqual(filing.external_filing_id, "IPO/2026/001234")

    def test_communication_log_confidentiality(self):
        """BR-PMS-019: Test that CommunicationLog supports confidentiality_level."""
        log = CommunicationLog.objects.create(
            application=self.application,
            logged_by=self.user,
            direction="Outgoing",
            subject="Initial contact with attorney",
            confidentiality_level="Attorney-Client Privileged",
        )
        self.assertEqual(log.confidentiality_level, "Attorney-Client Privileged")


class StatusTransitionTests(TestCase):
    """Test valid/invalid status transitions."""

    def test_valid_transition(self):
        # Should not raise
        services._validate_transition(ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED)

    def test_invalid_transition(self):
        with self.assertRaises(services.ValidationError):
            services._validate_transition(ApplicationStatus.DRAFT, ApplicationStatus.APPROVED)
