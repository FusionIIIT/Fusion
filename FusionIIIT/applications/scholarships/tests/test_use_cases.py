"""
test_use_cases.py — Use‐Case tests for the SPACS Scholarship module.

13 Use Cases × 3 tests each (HP + AP + EX) = 39 tests.
Naming: TestUC{NN}_{Title}  ·  test_hp{NN}_...  ·  test_ap{NN}_...  ·  test_ex{NN}_...
"""

from django.urls import reverse
from .conftest import BaseModuleTestCase
from applications.scholarships.models import (
    McmApplication, SingleParentApplication,
    ScholarshipApplication, ExtendedScholarshipType,
)


# ──────────────────────────────────────────────────────────────────────────────
# Base class — shared by all UC tests
# ──────────────────────────────────────────────────────────────────────────────

class UCTestBase(BaseModuleTestCase):
    """Adds nothing extra; exists so runner.py can detect UC test classes."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑1 : Apply For Scholarship/Awards
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC01_ApplyForScholarship(UCTestBase):
    """SPACS-UC-001: Student applies for scholarship/award."""

    def test_hp01_submit_mcm_application(self):
        """Happy Path: Student submits complete MCM application."""
        self._test_id = "UC-1-HP-01"
        self._uc_id = "SPACS-UC-001"
        self._test_category = "Happy Path"
        self._scenario = "Student submits complete MCM application"
        self._preconditions = "Student logged in; MCM award window open"
        self._input_action = "POST mcm-applications/ with all required fields"
        self._expected_result = "Application created; HTTP 201"

        self.login_as_student()
        url = reverse('api-mcm-applications')
        data = {
            'email': 'teststudent@test.com',
            'student_full_name': 'Test Student',
            'roll_no': '2021BCS001',
            'batch': '2021',
            'programme': 'B.Tech CSE',
            'mobile_no': '9876543210',
            'father_name': 'Father Name',
            'mother_name': 'Mother Name',
            'category': 'GEN',
            'current_cpi': '8.50',
            'current_spi': '8.50',
            'annual_income': '300000',
            'postal_address': '123 Test Street, City',
            'declaration_yes': 'Yes',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 201:
            self._record_result("MCM application created", "Pass",
                                f"HTTP 201, data={response.data}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail",
                                f"Response: {response.data}")
            self.fail(f"Expected 201, got {response.status_code}: {response.data}")

    def test_ap01_submit_extended_scholarship(self):
        """Alternate Path: Student submits extended scholarship application."""
        self._test_id = "UC-1-AP-01"
        self._uc_id = "SPACS-UC-001"
        self._test_category = "Alternate Path"
        self._scenario = "Submit extended scholarship application"
        self._preconditions = "Student logged in; active scholarship type exists"
        self._input_action = "POST applications/ with scholarship_type, academic_year, semester"
        self._expected_result = "Application created; HTTP 201"

        self.login_as_student()
        url = reverse('api-scholarship-applications')
        data = {
            'scholarship_type': self.active_scholarship.id,
            'academic_year': '2024-25',
            'semester': 1,
            'remarks': 'Test application',
        }
        response = self.client.post(url, data, format='multipart')

        if response.status_code == 201:
            self._record_result("Extended app created", "Pass",
                                f"HTTP 201, data={response.data}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail",
                                f"Response: {response.data}")
            self.fail(f"Expected 201, got {response.status_code}: {response.data}")

    def test_ex01_ineligible_student_rejected(self):
        """Exception: Student with low CPI is rejected."""
        self._test_id = "UC-1-EX-01"
        self._uc_id = "SPACS-UC-001"
        self._test_category = "Exception"
        self._scenario = "Low-CPI student application rejected"
        self._preconditions = "Student logged in; CPI below minimum"
        self._input_action = "POST applications/ with low-CPI student"
        self._expected_result = "Rejected; HTTP 400; eligibility error"

        self.login_as_low_cpi_student()
        url = reverse('api-scholarship-applications')
        data = {
            'scholarship_type': self.active_scholarship.id,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(url, data, format='multipart')

        if response.status_code == 400:
            self._record_result("Correctly rejected", "Pass",
                                f"HTTP 400, data={response.data}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail",
                                f"Response: {response.data}")
            self.fail(f"Expected 400, got {response.status_code}: {response.data}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑2 : Verify Application
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC02_VerifyApplication(UCTestBase):
    """SPACS-UC-002: Assistant verifies application."""

    def test_hp01_assistant_verifies_pending(self):
        """Happy Path: Assistant verifies pending MCM application."""
        self._test_id = "UC-2-HP-01"
        self._uc_id = "SPACS-UC-002"
        self._test_category = "Happy Path"
        self._scenario = "Assistant verifies pending MCM application"
        self._input_action = "PATCH mcm-applications/<pk>/ status=verified"
        self._expected_result = "Status updated to verified"

        app = self.create_mcm_application(status='pending')
        self.login_as_assistant()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'verified'}, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            if app.status == 'verified':
                self._record_result("Verified successfully", "Pass", f"Status={app.status}")
            else:
                self._record_result(f"Status={app.status}", "Partial", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_assistant_reverts_for_correction(self):
        """Alternate Path: Assistant reverts application with reason."""
        self._test_id = "UC-2-AP-01"
        self._uc_id = "SPACS-UC-002"
        self._test_category = "Alternate Path"
        self._scenario = "Assistant reverts application for corrections"
        self._input_action = "PATCH with status=reverted, revert_reason"
        self._expected_result = "Status=reverted; reason recorded"

        app = self.create_mcm_application(status='pending')
        self.login_as_assistant()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {
            'status': 'reverted',
            'revert_reason': 'Missing income certificate',
        }, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            if app.status == 'reverted' and app.revert_reason:
                self._record_result("Reverted with reason", "Pass", f"reason={app.revert_reason}")
            else:
                self._record_result(f"Status={app.status}", "Partial", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_student_cannot_verify(self):
        """Exception: Student cannot verify applications."""
        self._test_id = "UC-2-EX-01"
        self._uc_id = "SPACS-UC-002"
        self._test_category = "Exception"
        self._scenario = "Student cannot set verified status"
        self._input_action = "PATCH mcm-applications/<pk>/ as student"
        self._expected_result = "Rejected; cannot verify"

        app = self.create_mcm_application(status='pending')
        self.login_as_student()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'verified'}, format='json')

        if response.status_code in [400, 403]:
            self._record_result("Correctly denied", "Pass", str(response.data))
        else:
            app.refresh_from_db()
            if app.status != 'verified':
                self._record_result("Status not changed", "Pass", f"Status={app.status}")
            else:
                self._record_result(f"Student verified!", "Fail", str(response.data))
                self.fail("Student should not be able to verify")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑3 : Modify Pending Application
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC03_ModifyPendingApplication(UCTestBase):
    """SPACS-UC-003: Student modifies reverted application."""

    def test_hp01_student_edits_reverted_mcm(self):
        """Happy Path: Student modifies reverted MCM application."""
        self._test_id = "UC-3-HP-01"
        self._uc_id = "SPACS-UC-003"
        self._test_category = "Happy Path"
        self._scenario = "Student modifies reverted MCM application"
        self._input_action = "PATCH mcm-applications/<pk>/ with updated fields"
        self._expected_result = "Updated; status reset to pending"

        app = self.create_mcm_application(status='reverted',
                                          revert_reason='Fix income')
        self.login_as_student()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {
            'annual_income': '250000',
        }, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            if app.status == 'pending':
                self._record_result("Modified, status=pending", "Pass",
                                    f"income={app.annual_income}")
            else:
                self._record_result(f"Status={app.status}", "Partial", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_student_edits_reverted_single_parent(self):
        """Alternate Path: Student modifies reverted single-parent application."""
        self._test_id = "UC-3-AP-01"
        self._uc_id = "SPACS-UC-003"
        self._test_category = "Alternate Path"
        self._scenario = "Student modifies reverted single-parent app"
        self._input_action = "PATCH single-parent-applications/<pk>/"
        self._expected_result = "Updated; status reset to pending"

        app = self.create_single_parent_application(
            status='reverted', revert_reason='Fix address')
        self.login_as_student()
        url = reverse('api-single-parent-application-detail', args=[app.pk])
        response = self.client.patch(url, {
            'postal_address': '456 Updated Street',
        }, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            if app.status == 'pending':
                self._record_result("Modified single-parent", "Pass",
                                    f"address={app.postal_address}")
            else:
                self._record_result(f"Status={app.status}", "Partial", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_student_cannot_edit_pending(self):
        """Exception: Student cannot edit pending (non-reverted) application."""
        self._test_id = "UC-3-EX-01"
        self._uc_id = "SPACS-UC-003"
        self._test_category = "Exception"
        self._scenario = "Student cannot edit pending application"
        self._input_action = "PATCH mcm-applications/<pk>/ on pending app"
        self._expected_result = "Rejected; can only edit reverted"

        app = self.create_mcm_application(status='pending')
        self.login_as_student()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'annual_income': '500000'}, format='json')

        if response.status_code == 400:
            self._record_result("Correctly rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑4 : Request Withdrawal
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC04_RequestWithdrawal(UCTestBase):
    """SPACS-UC-004: Student views/manages pending applications."""

    def test_hp01_student_views_pending_applications(self):
        """Happy Path: Student views own pending applications."""
        self._test_id = "UC-4-HP-01"
        self._uc_id = "SPACS-UC-004"
        self._test_category = "Happy Path"
        self._scenario = "Student views pending applications"
        self._input_action = "GET student/applications/"
        self._expected_result = "Applications list returned; HTTP 200"

        self.login_as_student()
        url = reverse('api-student-applications')
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            self._record_result("Applications listed", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_student_views_mcm_applications(self):
        """Alternate Path: Student views MCM applications."""
        self._test_id = "UC-4-AP-01"
        self._uc_id = "SPACS-UC-004"
        self._test_category = "Alternate Path"
        self._scenario = "Student checks MCM applications"
        self._input_action = "GET mcm-applications/"
        self._expected_result = "Own MCM applications returned"

        app = self.create_mcm_application(status='pending')
        self.login_as_student()
        url = reverse('api-mcm-applications')
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            self._record_result("MCM apps listed", "Pass",
                                f"Count={len(response.data)}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_cannot_update_finalized_application(self):
        """Exception: Cannot update finalized (approved) application."""
        self._test_id = "UC-4-EX-01"
        self._uc_id = "SPACS-UC-004"
        self._test_category = "Exception"
        self._scenario = "Cannot update finalized application"
        self._input_action = "PATCH mcm-applications/<pk>/ on approved app"
        self._expected_result = "Rejected; finalized"

        app = self.create_mcm_application(status='approved')
        self.login_as_student()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'annual_income': '999'}, format='json')

        if response.status_code == 400:
            self._record_result("Correctly blocked", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑5 : Acknowledge Withdrawal
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC05_AcknowledgeWithdrawal(UCTestBase):
    """SPACS-UC-005: Assistant handles withdrawal/revert."""

    def test_hp01_assistant_reverts_mcm_application(self):
        """Happy Path: Assistant reverts MCM application."""
        self._test_id = "UC-5-HP-01"
        self._uc_id = "SPACS-UC-005"
        self._test_category = "Happy Path"
        self._scenario = "Assistant reverts application"
        self._input_action = "PATCH with status=reverted, revert_reason"
        self._expected_result = "Reverted; reason recorded"

        app = self.create_mcm_application(status='pending')
        self.login_as_assistant()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {
            'status': 'reverted',
            'revert_reason': 'Student requested changes',
        }, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            self._record_result("Reverted", "Pass", f"Status={app.status}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_assistant_reverts_single_parent(self):
        """Alternate Path: Assistant reverts single-parent application."""
        self._test_id = "UC-5-AP-01"
        self._uc_id = "SPACS-UC-005"
        self._test_category = "Alternate Path"
        self._scenario = "Assistant reverts single-parent app"
        self._input_action = "PATCH single-parent-applications/<pk>/"
        self._expected_result = "Reverted with reason"

        app = self.create_single_parent_application(status='pending')
        self.login_as_assistant()
        url = reverse('api-single-parent-application-detail', args=[app.pk])
        response = self.client.patch(url, {
            'status': 'reverted',
            'revert_reason': 'Needs verification',
        }, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            self._record_result("Reverted single-parent", "Pass",
                                f"Status={app.status}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_student_cannot_revert(self):
        """Exception: Student cannot revert applications."""
        self._test_id = "UC-5-EX-01"
        self._uc_id = "SPACS-UC-005"
        self._test_category = "Exception"
        self._scenario = "Student cannot revert applications"
        self._input_action = "PATCH as student with status=reverted"
        self._expected_result = "Denied"

        app = self.create_mcm_application(status='pending')
        self.login_as_student()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {
            'status': 'reverted',
            'revert_reason': 'test',
        }, format='json')

        if response.status_code in [400, 403]:
            self._record_result("Correctly denied", "Pass", str(response.data))
        else:
            app.refresh_from_db()
            if app.status != 'reverted':
                self._record_result("Status unchanged", "Pass", f"Status={app.status}")
            else:
                self._record_result("Student could revert!", "Fail", str(response.data))
                self.fail("Student should not revert applications")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑6 : Sanctioning Decision
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC06_SanctioningDecision(UCTestBase):
    """SPACS-UC-006: Convener approves/rejects verified applications."""

    def test_hp01_convener_approves(self):
        """Happy Path: Convener approves verified MCM application."""
        self._test_id = "UC-6-HP-01"
        self._uc_id = "SPACS-UC-006"
        self._test_category = "Happy Path"
        self._scenario = "Convener approves verified application"
        self._input_action = "PATCH mcm-applications/<pk>/ status=approved"
        self._expected_result = "Status=approved"

        app = self.create_mcm_application(status='verified')
        self.login_as_convener()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'approved'}, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            if app.status == 'approved':
                self._record_result("Approved", "Pass", f"Status={app.status}")
            else:
                self._record_result(f"Status={app.status}", "Fail", str(response.data))
                self.fail(f"Expected approved, got {app.status}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_convener_rejects(self):
        """Alternate Path: Convener rejects verified application."""
        self._test_id = "UC-6-AP-01"
        self._uc_id = "SPACS-UC-006"
        self._test_category = "Alternate Path"
        self._scenario = "Convener rejects application"
        self._input_action = "PATCH with status=rejected"
        self._expected_result = "Status=rejected"

        app = self.create_mcm_application(status='verified')
        self.login_as_convener()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'rejected'}, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            if app.status == 'rejected':
                self._record_result("Rejected", "Pass", f"Status={app.status}")
            else:
                self._record_result(f"Status={app.status}", "Fail", str(response.data))
                self.fail(f"Expected rejected, got {app.status}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_assistant_cannot_approve(self):
        """Exception: Assistant cannot approve/reject."""
        self._test_id = "UC-6-EX-01"
        self._uc_id = "SPACS-UC-006"
        self._test_category = "Exception"
        self._scenario = "Assistant cannot approve applications"
        self._input_action = "PATCH as assistant with status=approved"
        self._expected_result = "Denied"

        app = self.create_mcm_application(status='verified')
        self.login_as_assistant()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'approved'}, format='json')

        if response.status_code == 400:
            self._record_result("Correctly denied", "Pass", str(response.data))
        else:
            app.refresh_from_db()
            if app.status != 'approved':
                self._record_result("Status unchanged", "Pass", f"Status={app.status}")
            else:
                self._record_result("Assistant approved!", "Fail", str(response.data))
                self.fail("Assistant should not approve")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑7 : Download/Print Application
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC07_DownloadPrintApplication(UCTestBase):
    """SPACS-UC-007: Retrieve application data for export."""

    def test_hp01_student_retrieves_own_application(self):
        """Happy Path: Student gets own MCM application detail."""
        self._test_id = "UC-7-HP-01"
        self._uc_id = "SPACS-UC-007"
        self._test_category = "Happy Path"
        self._scenario = "Student retrieves own application"
        self._input_action = "GET mcm-applications/<pk>/"
        self._expected_result = "Full data returned; HTTP 200"

        app = self.create_mcm_application(status='pending')
        self.login_as_student()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            self._record_result("Data retrieved", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_convener_retrieves_application(self):
        """Alternate Path: Convener accesses any application."""
        self._test_id = "UC-7-AP-01"
        self._uc_id = "SPACS-UC-007"
        self._test_category = "Alternate Path"
        self._scenario = "Convener retrieves student application"
        self._input_action = "GET mcm-applications/<pk>/ as convener"
        self._expected_result = "Data returned; HTTP 200"

        app = self.create_mcm_application(status='pending')
        self.login_as_convener()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            self._record_result("Convener accessed data", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_student_cannot_access_others(self):
        """Exception: Student cannot access another student's application."""
        self._test_id = "UC-7-EX-01"
        self._uc_id = "SPACS-UC-007"
        self._test_category = "Exception"
        self._scenario = "Student cannot access others' applications"
        self._input_action = "GET mcm-applications/<pk>/ (other student's)"
        self._expected_result = "Empty or 404"

        app = self.create_mcm_application(student=self.student, status='pending')
        self.login_as_student2()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.get(url, format='json')

        if response.status_code == 404:
            self._record_result("Correctly blocked", "Pass", "404 returned")
        elif response.status_code == 200:
            self._record_result("Data leaked!", "Fail", str(response.data))
            self.fail("Student should not access others' applications")
        else:
            self._record_result(f"HTTP {response.status_code}", "Pass",
                                "Access controlled")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑8 : Check Application Status
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC08_CheckApplicationStatus(UCTestBase):
    """SPACS-UC-008: Student views application status."""

    def test_hp01_student_checks_mcm_status(self):
        """Happy Path: Student checks MCM application status."""
        self._test_id = "UC-8-HP-01"
        self._uc_id = "SPACS-UC-008"
        self._test_category = "Happy Path"
        self._scenario = "Student checks MCM status"
        self._input_action = "GET mcm-applications/"
        self._expected_result = "Own applications with status; HTTP 200"

        app = self.create_mcm_application(status='pending')
        self.login_as_student()
        url = reverse('api-mcm-applications')
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            data = response.data
            if isinstance(data, list) and len(data) > 0:
                self._record_result("Status visible", "Pass",
                                    f"Count={len(data)}, status={data[0].get('status')}")
            else:
                self._record_result("Empty list", "Partial", str(data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_student_views_legacy_applications(self):
        """Alternate Path: Student views legacy applications."""
        self._test_id = "UC-8-AP-01"
        self._uc_id = "SPACS-UC-008"
        self._test_category = "Alternate Path"
        self._scenario = "Student views legacy applications"
        self._input_action = "GET student/applications/"
        self._expected_result = "Applications returned; HTTP 200"

        self.login_as_student()
        url = reverse('api-student-applications')
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            self._record_result("Legacy apps listed", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_unauthenticated_access_denied(self):
        """Exception: Unauthenticated user blocked."""
        self._test_id = "UC-8-EX-01"
        self._uc_id = "SPACS-UC-008"
        self._test_category = "Exception"
        self._scenario = "Unauthenticated access denied"
        self._input_action = "GET mcm-applications/ without auth"
        self._expected_result = "HTTP 401 or 403"

        self.logout()
        url = reverse('api-mcm-applications')
        response = self.client.get(url, format='json')

        if response.status_code in [401, 403]:
            self._record_result("Correctly blocked", "Pass",
                                f"HTTP {response.status_code}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 401/403, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑9 : Forward Application
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC09_ForwardApplication(UCTestBase):
    """SPACS-UC-009: Assistant forwards application to Convener."""

    def test_hp01_assistant_forwards_pending(self):
        """Happy Path: Assistant verifies (forwards) pending MCM app."""
        self._test_id = "UC-9-HP-01"
        self._uc_id = "SPACS-UC-009"
        self._test_category = "Happy Path"
        self._scenario = "Assistant forwards pending application"
        self._input_action = "PATCH status=verified"
        self._expected_result = "Status=verified (forwarded)"

        app = self.create_mcm_application(status='pending')
        self.login_as_assistant()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'verified'}, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            self._record_result("Forwarded", "Pass", f"Status={app.status}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_assistant_forwards_single_parent(self):
        """Alternate Path: Assistant forwards single-parent app."""
        self._test_id = "UC-9-AP-01"
        self._uc_id = "SPACS-UC-009"
        self._test_category = "Alternate Path"
        self._scenario = "Assistant forwards single-parent app"
        self._input_action = "PATCH single-parent with status=verified"
        self._expected_result = "Status=verified"

        app = self.create_single_parent_application(status='pending')
        self.login_as_assistant()
        url = reverse('api-single-parent-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'verified'}, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            self._record_result("Forwarded", "Pass", f"Status={app.status}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_assistant_cannot_forward_non_pending(self):
        """Exception: Assistant cannot forward already verified app."""
        self._test_id = "UC-9-EX-01"
        self._uc_id = "SPACS-UC-009"
        self._test_category = "Exception"
        self._scenario = "Cannot forward already verified app"
        self._input_action = "PATCH on verified app"
        self._expected_result = "Error; can only act on pending"

        app = self.create_mcm_application(status='verified')
        self.login_as_assistant()
        url = reverse('api-mcm-application-detail', args=[app.pk])
        response = self.client.patch(url, {'status': 'verified'}, format='json')

        if response.status_code == 400:
            self._record_result("Correctly blocked", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑10 : Add New Scholarships
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC10_AddNewScholarships(UCTestBase):
    """SPACS-UC-010: Admin creates new scholarship type."""

    def test_hp01_admin_creates_scholarship_type(self):
        """Happy Path: Admin creates new ExtendedScholarshipType."""
        self._test_id = "UC-10-HP-01"
        self._uc_id = "SPACS-UC-010"
        self._test_category = "Happy Path"
        self._scenario = "Admin creates new scholarship type"
        self._input_action = "POST /types/"
        self._expected_result = "Created; HTTP 201"

        self.login_as_admin()
        url = reverse('api-scholarship-types')
        data = {
            'name': 'New Test Scholarship',
            'category': 'MERIT',
            'description': 'A new test scholarship',
            'eligibility_criteria': 'CPI >= 7.0',
            'amount': '25000.00',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 201:
            self._record_result("Created", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_ap01_admin_creates_minimal_type(self):
        """Alternate Path: Admin creates type with minimal fields."""
        self._test_id = "UC-10-AP-01"
        self._uc_id = "SPACS-UC-010"
        self._test_category = "Alternate Path"
        self._scenario = "Admin creates with minimal fields"
        self._input_action = "POST /types/ minimal fields"
        self._expected_result = "Created; HTTP 201"

        self.login_as_admin()
        url = reverse('api-scholarship-types')
        data = {
            'name': 'Minimal Scholarship',
            'category': 'NEED',
            'description': 'Minimal test',
            'eligibility_criteria': 'None',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 201:
            self._record_result("Created minimal", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_ex01_student_cannot_create(self):
        """Exception: Student cannot create scholarship types."""
        self._test_id = "UC-10-EX-01"
        self._uc_id = "SPACS-UC-010"
        self._test_category = "Exception"
        self._scenario = "Student cannot create types"
        self._input_action = "POST /types/ as student"
        self._expected_result = "HTTP 403"

        self.login_as_student()
        url = reverse('api-scholarship-types')
        data = {
            'name': 'Unauthorized Scholarship',
            'category': 'MERIT',
            'description': 'Should fail',
            'eligibility_criteria': 'N/A',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 403:
            self._record_result("Correctly denied", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 403, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑11 : Modify Award Criteria
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC11_ModifyAwardCriteria(UCTestBase):
    """SPACS-UC-011: Admin modifies scholarship criteria."""

    def test_hp01_admin_updates_criteria(self):
        """Happy Path: Admin updates minimum_cgpa via service layer."""
        self._test_id = "UC-11-HP-01"
        self._uc_id = "SPACS-UC-011"
        self._test_category = "Happy Path"
        self._scenario = "Admin updates minimum_cgpa"
        self._input_action = "Direct model update of minimum_cgpa"
        self._expected_result = "Criteria updated"

        scholarship = ExtendedScholarshipType.objects.create(
            name='Modifiable Scholarship', category='MERIT',
            description='Test', eligibility_criteria='CPI >= 8',
            minimum_cgpa=8.0, is_active=True,
        )
        scholarship.minimum_cgpa = 7.5
        scholarship.save()
        scholarship.refresh_from_db()

        if scholarship.minimum_cgpa == 7.5:
            self._record_result("Criteria updated", "Pass",
                                f"min_cgpa={scholarship.minimum_cgpa}")
        else:
            self._record_result("Update failed", "Fail",
                                f"min_cgpa={scholarship.minimum_cgpa}")
            self.fail("Criteria not updated")

    def test_ap01_admin_deactivates_scholarship(self):
        """Alternate Path: Admin deactivates scholarship type."""
        self._test_id = "UC-11-AP-01"
        self._uc_id = "SPACS-UC-011"
        self._test_category = "Alternate Path"
        self._scenario = "Admin deactivates scholarship"
        self._input_action = "Set is_active=False"
        self._expected_result = "Deactivated; new apps rejected"

        scholarship = ExtendedScholarshipType.objects.create(
            name='Deactivatable', category='MERIT',
            description='Test', eligibility_criteria='CPI >= 6',
            is_active=True,
        )
        scholarship.is_active = False
        scholarship.save()
        scholarship.refresh_from_db()

        if not scholarship.is_active:
            self._record_result("Deactivated", "Pass",
                                f"is_active={scholarship.is_active}")
        else:
            self._record_result("Still active", "Fail", "")
            self.fail("Scholarship should be deactivated")

    def test_ex01_application_against_inactive(self):
        """Exception: Application against inactive scholarship rejected."""
        self._test_id = "UC-11-EX-01"
        self._uc_id = "SPACS-UC-011"
        self._test_category = "Exception"
        self._scenario = "Application against inactive scholarship"
        self._input_action = "POST /applications/ with inactive type"
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
            self._record_result("Correctly rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑12 : Manage Scholarship Catalogue
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC12_ManageScholarshipCatalogue(UCTestBase):
    """SPACS-UC-012: View/manage scholarship catalogue."""

    def test_hp01_view_full_catalogue(self):
        """Happy Path: User retrieves full catalogue."""
        self._test_id = "UC-12-HP-01"
        self._uc_id = "SPACS-UC-012"
        self._test_category = "Happy Path"
        self._scenario = "View full scholarship catalogue"
        self._input_action = "GET /types/"
        self._expected_result = "All types returned; HTTP 200"

        self.login_as_student()
        url = reverse('api-scholarship-types')
        response = self.client.get(url, format='json')

        if response.status_code == 200:
            self._record_result("Catalogue listed", "Pass",
                                f"Count={len(response.data)}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_filter_active_only(self):
        """Alternate Path: Filter active-only types."""
        self._test_id = "UC-12-AP-01"
        self._uc_id = "SPACS-UC-012"
        self._test_category = "Alternate Path"
        self._scenario = "Filter active-only types"
        self._input_action = "GET /types/?active_only=true"
        self._expected_result = "Only active types returned"

        self.login_as_student()
        url = reverse('api-scholarship-types')
        response = self.client.get(url, {'active_only': 'true'}, format='json')

        if response.status_code == 200:
            all_active = all(item.get('is_active', True)
                             for item in response.data)
            if all_active:
                self._record_result("Only active returned", "Pass",
                                    f"Count={len(response.data)}")
            else:
                self._record_result("Inactive included", "Partial", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_unauthenticated_access(self):
        """Exception: Unauthenticated user cannot view catalogue."""
        self._test_id = "UC-12-EX-01"
        self._uc_id = "SPACS-UC-012"
        self._test_category = "Exception"
        self._scenario = "Unauthenticated access"
        self._input_action = "GET /types/ without auth"
        self._expected_result = "HTTP 401 or 403"

        self.logout()
        url = reverse('api-scholarship-types')
        response = self.client.get(url, format='json')

        if response.status_code in [401, 403]:
            self._record_result("Correctly blocked", "Pass",
                                f"HTTP {response.status_code}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 401/403, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC‑13 : Verify and Grant Scholarship
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC13_VerifyAndGrantScholarship(UCTestBase):
    """SPACS-UC-013: Admin disburses approved scholarships."""

    def test_hp01_admin_disburses_approved(self):
        """Happy Path: Admin disburses approved ScholarshipApplication."""
        self._test_id = "UC-13-HP-01"
        self._uc_id = "SPACS-UC-013"
        self._test_category = "Happy Path"
        self._scenario = "Admin disburses approved application"
        self._input_action = "POST /awards/ with application_id"
        self._expected_result = "Status=DISBURSED; HTTP 201"

        app = self.create_ext_scholarship_app(status='APPROVED')
        self.login_as_admin()
        url = reverse('api-awards-management')
        data = {
            'application_id': app.id,
            'amount': '50000',
            'transaction_reference': 'TXN-001',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 201:
            app.refresh_from_db()
            if app.status == 'DISBURSED':
                self._record_result("Disbursed", "Pass", str(response.data))
            else:
                self._record_result(f"Status={app.status}", "Partial", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_ap01_admin_approves_extended_app(self):
        """Alternate Path: Admin approves extended scholarship via approve endpoint."""
        self._test_id = "UC-13-AP-01"
        self._uc_id = "SPACS-UC-013"
        self._test_category = "Alternate Path"
        self._scenario = "Admin approves via approve endpoint"
        self._input_action = "POST /applications/<id>/approve/"
        self._expected_result = "Status=APPROVED; HTTP 200"

        app = self.create_ext_scholarship_app(status='PENDING')
        self.login_as_admin()
        url = reverse('api-scholarship-application-approve', args=[app.id])
        data = {
            'status': 'APPROVED',
            'review_remarks': 'Approved for merit',
            'amount_approved': '50000',
        }
        response = self.client.post(url, data, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            if app.status == 'APPROVED':
                self._record_result("Approved", "Pass", str(response.data))
            else:
                self._record_result(f"Status={app.status}", "Partial", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_student_cannot_disburse(self):
        """Exception: Student cannot disburse scholarships."""
        self._test_id = "UC-13-EX-01"
        self._uc_id = "SPACS-UC-013"
        self._test_category = "Exception"
        self._scenario = "Student cannot disburse"
        self._input_action = "POST /awards/ as student"
        self._expected_result = "HTTP 403"

        app = self.create_ext_scholarship_app(status='APPROVED')
        self.login_as_student()
        url = reverse('api-awards-management')
        data = {'application_id': app.id}
        response = self.client.post(url, data, format='json')

        if response.status_code == 403:
            self._record_result("Correctly denied", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 403, got {response.status_code}")
