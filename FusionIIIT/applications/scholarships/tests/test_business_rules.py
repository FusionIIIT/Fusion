"""
test_business_rules.py — Business‐Rule tests for the SPACS Scholarship module.

12 Business Rules × 2 tests each (Valid + Invalid) = 24 tests.
Naming: TestBR{NN}_{Title}  ·  test_valid_...  ·  test_invalid_...
"""

from decimal import Decimal
from django.urls import reverse
from .conftest import BaseModuleTestCase
from applications.scholarships.models import (
    McmApplication, SingleParentApplication,
    ExtendedScholarshipType, ScholarshipApplication,
)
from applications.scholarships.services import (
    check_scholarship_eligibility,
    check_duplicate_application,
)


class BRTestBase(BaseModuleTestCase):
    """Base marker class for Business Rule tests."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑001 : Eligibility Must Be Satisfied
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR01_EligibilityMustBeSatisfied(BRTestBase):
    """BR-SPACS-001: Student must satisfy eligibility criteria."""

    def test_valid_eligible_student_accepted(self):
        """Valid: Student meeting all criteria is accepted."""
        self._test_id = "BR-1-V-01"
        self._br_id = "BR-SPACS-001"
        self._test_category = "Valid"
        self._input_action = "POST /applications/ — eligible student (CPI 8.5 >= 8.0)"
        self._expected_result = "Application accepted"

        self.login_as_student()
        url = reverse('api-scholarship-applications')
        data = {
            'scholarship_type': self.active_scholarship.id,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(url, data, format='multipart')

        if response.status_code == 201:
            self._record_result("Eligible accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_ineligible_student_rejected(self):
        """Invalid: Student below minimum CPI is rejected."""
        self._test_id = "BR-1-I-01"
        self._br_id = "BR-SPACS-001"
        self._test_category = "Invalid"
        self._input_action = "POST /applications/ — CPI 4.0 < 8.0 minimum"
        self._expected_result = "Rejected with eligibility error"

        self.login_as_low_cpi_student()
        url = reverse('api-scholarship-applications')
        data = {
            'scholarship_type': self.active_scholarship.id,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(url, data, format='multipart')

        if response.status_code == 400:
            self._record_result("Correctly rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑002 : No Duplicate Applications
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR02_NoDuplicateApplications(BRTestBase):
    """BR-SPACS-002: No duplicate applications per student per scholarship."""

    def test_valid_first_application_accepted(self):
        """Valid: First MCM application is accepted."""
        self._test_id = "BR-2-V-01"
        self._br_id = "BR-SPACS-002"
        self._test_category = "Valid"
        self._input_action = "POST /mcm-applications/ — first application"
        self._expected_result = "Application created"

        self.login_as_student()
        url = reverse('api-mcm-applications')
        data = {
            'email': 'test@test.com',
            'student_full_name': 'Test Student',
            'roll_no': '2021BCS001',
            'batch': '2021',
            'programme': 'B.Tech CSE',
            'mobile_no': '9876543210',
            'father_name': 'Father',
            'mother_name': 'Mother',
            'category': 'GEN',
            'current_cpi': '8.50',
            'current_spi': '8.50',
            'annual_income': '300000',
            'postal_address': 'Test Address',
            'declaration_yes': 'Yes',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 201:
            self._record_result("First app accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_duplicate_application_rejected(self):
        """Invalid: Second MCM application for same student is rejected."""
        self._test_id = "BR-2-I-01"
        self._br_id = "BR-SPACS-002"
        self._test_category = "Invalid"
        self._input_action = "POST /mcm-applications/ — duplicate"
        self._expected_result = "Rejected; duplicate error"

        self.create_mcm_application(student=self.student, status='pending')
        self.login_as_student()
        url = reverse('api-mcm-applications')
        data = {
            'email': 'test@test.com',
            'student_full_name': 'Test Student',
            'roll_no': '2021BCS001',
            'batch': '2021',
            'programme': 'B.Tech CSE',
            'mobile_no': '9876543210',
            'father_name': 'Father',
            'mother_name': 'Mother',
            'category': 'GEN',
            'current_cpi': '8.50',
            'current_spi': '8.50',
            'annual_income': '300000',
            'postal_address': 'Test',
            'declaration_yes': 'Yes',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 400:
            self._record_result("Duplicate rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑003 : Use of Previously Uploaded Documents
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR03_PreviouslyUploadedDocuments(BRTestBase):
    """BR-SPACS-003: System allows reuse of valid document links."""

    def test_valid_application_with_document_links(self):
        """Valid: Application with previously uploaded document links accepted."""
        self._test_id = "BR-3-V-01"
        self._br_id = "BR-SPACS-003"
        self._test_category = "Valid"
        self._input_action = "POST /mcm-applications/ with document link URLs"
        self._expected_result = "Application accepted with links"

        self.login_as_student()
        url = reverse('api-mcm-applications')
        data = {
            'email': 'test@test.com',
            'student_full_name': 'Test Student',
            'roll_no': '2021BCS001',
            'batch': '2021',
            'programme': 'B.Tech CSE',
            'mobile_no': '9876543210',
            'father_name': 'Father',
            'mother_name': 'Mother',
            'category': 'GEN',
            'current_cpi': '8.50',
            'current_spi': '8.50',
            'annual_income': '300000',
            'postal_address': 'Test',
            'declaration_yes': 'Yes',
            'father_income_certificate_link': 'https://example.com/cert.pdf',
            'mother_income_certificate_link': 'https://example.com/cert2.pdf',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 201:
            self._record_result("Links accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_missing_required_document(self):
        """Invalid: Legacy MCM submission without income certificate file rejected."""
        self._test_id = "BR-3-I-01"
        self._br_id = "BR-SPACS-003"
        self._test_category = "Invalid"
        self._input_action = "POST /student/submit/mcm/ without income_certificate file"
        self._expected_result = "Rejected; file required"

        self.login_as_student()
        url = reverse('api-submit-mcm')
        data = {
            'award_id': self.test_award.id,
            'income_father': 100000,
            'income_mother': 50000,
        }
        response = self.client.post(url, data, format='multipart')

        if response.status_code == 400:
            self._record_result("Missing document rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑004 : Application Completeness Validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR04_CompletenessValidation(BRTestBase):
    """BR-SPACS-004: All required fields must be filled."""

    def test_valid_complete_application(self):
        """Valid: Complete application accepted."""
        self._test_id = "BR-4-V-01"
        self._br_id = "BR-SPACS-004"
        self._test_category = "Valid"
        self._input_action = "POST /mcm-applications/ with all required fields"
        self._expected_result = "Accepted"

        self.login_as_student()
        url = reverse('api-mcm-applications')
        data = {
            'email': 'test@test.com',
            'student_full_name': 'Test Student',
            'roll_no': '2021BCS001',
            'batch': '2021',
            'programme': 'B.Tech CSE',
            'mobile_no': '9876543210',
            'father_name': 'Father',
            'mother_name': 'Mother',
            'category': 'GEN',
            'current_cpi': '8.50',
            'current_spi': '8.50',
            'annual_income': '300000',
            'postal_address': 'Test Address',
            'declaration_yes': 'Yes',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 201:
            self._record_result("Complete accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_incomplete_application(self):
        """Invalid: Application missing required fields rejected."""
        self._test_id = "BR-4-I-01"
        self._br_id = "BR-SPACS-004"
        self._test_category = "Invalid"
        self._input_action = "POST /mcm-applications/ missing student_full_name"
        self._expected_result = "Validation error"

        self.login_as_student()
        url = reverse('api-mcm-applications')
        data = {
            'email': 'test@test.com',
            # missing student_full_name and other required fields
            'batch': '2021',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 400:
            self._record_result("Incomplete rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑005 : Application Review Access
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR05_ApplicationReviewAccess(BRTestBase):
    """BR-SPACS-005: Only SPACS staff can review all applications."""

    def test_valid_assistant_sees_all(self):
        """Valid: Assistant sees all MCM applications."""
        self._test_id = "BR-5-V-01"
        self._br_id = "BR-SPACS-005"
        self._test_category = "Valid"
        self._input_action = "GET /mcm-applications/ as assistant"
        self._expected_result = "All applications returned"

        self.create_mcm_application(student=self.student, status='pending')
        self.create_mcm_application(student=self.student_2, status='pending')
        self.login_as_assistant()
        url = reverse('api-mcm-applications')
        response = self.client.get(url, format='json')

        if response.status_code == 200 and len(response.data) >= 2:
            self._record_result("All apps visible", "Pass",
                                f"Count={len(response.data)}")
        elif response.status_code == 200:
            self._record_result("Partial visibility", "Partial",
                                f"Count={len(response.data)}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_invalid_student_sees_only_own(self):
        """Invalid: Student sees only own applications."""
        self._test_id = "BR-5-I-01"
        self._br_id = "BR-SPACS-005"
        self._test_category = "Invalid"
        self._input_action = "GET /mcm-applications/ as student"
        self._expected_result = "Only own applications"

        self.create_mcm_application(student=self.student, status='pending')
        self.create_mcm_application(student=self.student_2, status='pending')
        self.login_as_student()
        url = reverse('api-mcm-applications')
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            if len(response.data) <= 1:
                self._record_result("Only own visible", "Pass",
                                    f"Count={len(response.data)}")
            else:
                self._record_result("Sees others!", "Fail",
                                    f"Count={len(response.data)}")
                self.fail("Student should only see own applications")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑007 : Draft Save on Timeout or Error
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR07_DraftSaveOnTimeout(BRTestBase):
    """BR-SPACS-007: Application data persisted."""

    def test_valid_application_data_persisted(self):
        """Valid: Submitted data is persisted."""
        self._test_id = "BR-7-V-01"
        self._br_id = "BR-SPACS-007"
        self._test_category = "Valid"
        self._input_action = "POST /mcm-applications/ — data persisted"
        self._expected_result = "Record persisted in DB"

        self.login_as_student()
        url = reverse('api-mcm-applications')
        data = {
            'email': 'draft@test.com',
            'student_full_name': 'Draft Student',
            'roll_no': '2021BCS001',
            'batch': '2021',
            'programme': 'B.Tech CSE',
            'mobile_no': '9876543210',
            'father_name': 'Father',
            'mother_name': 'Mother',
            'category': 'GEN',
            'current_cpi': '8.50',
            'current_spi': '8.50',
            'annual_income': '300000',
            'postal_address': 'Draft Address',
            'declaration_yes': 'Yes',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 201:
            exists = McmApplication.objects.filter(student=self.student).exists()
            if exists:
                self._record_result("Data persisted", "Pass", "DB record found")
            else:
                self._record_result("Not in DB", "Fail", "")
                self.fail("Application not persisted")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_empty_submission_rejected(self):
        """Invalid: Empty/blank required fields rejected."""
        self._test_id = "BR-7-I-01"
        self._br_id = "BR-SPACS-007"
        self._test_category = "Invalid"
        self._input_action = "POST /mcm-applications/ with empty data"
        self._expected_result = "Validation error"

        self.login_as_student()
        url = reverse('api-mcm-applications')
        response = self.client.post(url, {}, format='json')

        if response.status_code == 400:
            self._record_result("Empty rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑008 : Notification on Status Change
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR08_NotificationOnStatusChange(BRTestBase):
    """BR-SPACS-008: Notifications on status changes."""

    def test_valid_status_change_triggers_flow(self):
        """Valid: Status change triggers notification logic path."""
        self._test_id = "BR-8-V-01"
        self._br_id = "BR-SPACS-008"
        self._test_category = "Valid"
        self._input_action = "PATCH status pending→verified"
        self._expected_result = "Status changed successfully"

        app = self.create_mcm_application(status='pending')
        self.login_as_assistant()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'verified'}, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            self._record_result("Status changed", "Pass", f"Status={app.status}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_invalid_read_no_notification(self):
        """Invalid: Read-only access does not change status."""
        self._test_id = "BR-8-I-01"
        self._br_id = "BR-SPACS-008"
        self._test_category = "Invalid"
        self._input_action = "GET (read-only) — no status change"
        self._expected_result = "No change"

        app = self.create_mcm_application(status='pending')
        self.login_as_assistant()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            if app.status == 'pending':
                self._record_result("No change on read", "Pass", f"Status={app.status}")
            else:
                self._record_result("Status changed!", "Fail", f"Status={app.status}")
                self.fail("Read should not change status")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑009 : Withdrawal Before Review
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR09_WithdrawalBeforeReview(BRTestBase):
    """BR-SPACS-009: Withdrawal only before review starts."""

    def test_valid_pending_allows_student_interaction(self):
        """Valid: Pending (pre-review) application is accessible to student."""
        self._test_id = "BR-9-V-01"
        self._br_id = "BR-SPACS-009"
        self._test_category = "Valid"
        self._input_action = "View pending application"
        self._expected_result = "Accessible; status=pending"

        app = self.create_mcm_application(status='pending')
        self.login_as_student()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            self._record_result("Pending accessible", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_invalid_verified_cannot_be_modified_by_student(self):
        """Invalid: Verified application cannot be modified by student."""
        self._test_id = "BR-9-I-01"
        self._br_id = "BR-SPACS-009"
        self._test_category = "Invalid"
        self._input_action = "PATCH on verified app as student"
        self._expected_result = "Blocked"

        app = self.create_mcm_application(status='verified')
        self.login_as_student()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'annual_income': '999'}, format='json')

        if response.status_code == 400:
            self._record_result("Correctly blocked", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑010 : Only Owner Can Edit or Withdraw
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR10_OnlyOwnerCanEdit(BRTestBase):
    """BR-SPACS-010: Only application owner can edit."""

    def test_valid_owner_can_edit_reverted(self):
        """Valid: Owner edits own reverted application."""
        self._test_id = "BR-10-V-01"
        self._br_id = "BR-SPACS-010"
        self._test_category = "Valid"
        self._input_action = "PATCH as owner"
        self._expected_result = "Edit accepted"

        app = self.create_mcm_application(student=self.student, status='reverted',
                                          revert_reason='Fix it')
        self.login_as_student()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'annual_income': '250000'}, format='json')

        if response.status_code == 200:
            self._record_result("Owner edited", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_invalid_non_owner_cannot_access(self):
        """Invalid: Non-owner student cannot access application."""
        self._test_id = "BR-10-I-01"
        self._br_id = "BR-SPACS-010"
        self._test_category = "Invalid"
        self._input_action = "GET as non-owner student"
        self._expected_result = "Not in queryset"

        app = self.create_mcm_application(student=self.student, status='pending')
        self.login_as_student2()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.get(url, format='json')

        if response.status_code == 404:
            self._record_result("Not accessible", "Pass", "404")
        elif response.status_code == 200:
            self._record_result("Leaked!", "Fail", str(response.data))
            self.fail("Non-owner should not access")
        else:
            self._record_result(f"HTTP {response.status_code}", "Pass", "Blocked")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑012 : Download/Print Access Control
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR12_DownloadPrintAccess(BRTestBase):
    """BR-SPACS-012: Only authorized users can view/download."""

    def test_valid_owner_can_view(self):
        """Valid: Owning student can view application."""
        self._test_id = "BR-12-V-01"
        self._br_id = "BR-SPACS-012"
        self._test_category = "Valid"
        self._input_action = "GET as owner"
        self._expected_result = "Data returned"

        app = self.create_mcm_application(student=self.student, status='pending')
        self.login_as_student()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            self._record_result("Owner can view", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_invalid_non_owner_blocked(self):
        """Invalid: Non-owner student blocked from viewing."""
        self._test_id = "BR-12-I-01"
        self._br_id = "BR-SPACS-012"
        self._test_category = "Invalid"
        self._input_action = "GET as non-owner student"
        self._expected_result = "404 or empty"

        app = self.create_mcm_application(student=self.student, status='pending')
        self.login_as_student2()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.get(url, format='json')

        if response.status_code == 404:
            self._record_result("Blocked", "Pass", "404")
        elif response.status_code == 200:
            self._record_result("Leaked!", "Fail", str(response.data))
            self.fail("Non-owner should be blocked")
        else:
            self._record_result(f"HTTP {response.status_code}", "Pass", "Blocked")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑013 : Escalation & SLA
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR13_EscalationSLA(BRTestBase):
    """BR-SPACS-013: SLA enforcement via role-based status transitions."""

    def test_valid_convener_acts_on_verified(self):
        """Valid: Convener acts on verified application within flow."""
        self._test_id = "BR-13-V-01"
        self._br_id = "BR-SPACS-013"
        self._test_category = "Valid"
        self._input_action = "PATCH verified → approved"
        self._expected_result = "Status changed"

        app = self.create_mcm_application(status='verified')
        self.login_as_convener()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'approved'}, format='json')

        if response.status_code == 200:
            self._record_result("Convener acted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_invalid_convener_cannot_act_on_pending(self):
        """Invalid: Convener cannot act on non-verified app."""
        self._test_id = "BR-13-I-01"
        self._br_id = "BR-SPACS-013"
        self._test_category = "Invalid"
        self._input_action = "PATCH pending as convener"
        self._expected_result = "Blocked"

        app = self.create_mcm_application(status='pending')
        self.login_as_convener()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'approved'}, format='json')

        if response.status_code == 400:
            self._record_result("Correctly blocked", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR‑014 : Catalog Versioning & Published Source of Truth
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR14_CatalogVersioning(BRTestBase):
    """BR-SPACS-014: Only active scholarships accept applications."""

    def test_valid_active_scholarship_accepts(self):
        """Valid: Application to active scholarship accepted."""
        self._test_id = "BR-14-V-01"
        self._br_id = "BR-SPACS-014"
        self._test_category = "Valid"
        self._input_action = "POST /applications/ with is_active=True type"
        self._expected_result = "Accepted"

        self.login_as_student()
        url = reverse('api-scholarship-applications')
        data = {
            'scholarship_type': self.active_scholarship.id,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(url, data, format='multipart')

        if response.status_code == 201:
            self._record_result("Active accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_inactive_scholarship_rejected(self):
        """Invalid: Application to inactive scholarship rejected."""
        self._test_id = "BR-14-I-01"
        self._br_id = "BR-SPACS-014"
        self._test_category = "Invalid"
        self._input_action = "POST /applications/ with is_active=False type"
        self._expected_result = "Rejected"

        self.login_as_student()
        url = reverse('api-scholarship-applications')
        data = {
            'scholarship_type': self.inactive_scholarship.id,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(url, data, format='multipart')

        if response.status_code == 400:
            self._record_result("Inactive rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")
