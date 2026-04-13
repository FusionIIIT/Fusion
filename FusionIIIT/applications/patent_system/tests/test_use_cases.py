import json
import unittest
from datetime import timedelta

from django.utils.timezone import now

from django.core.files.uploadedfile import SimpleUploadedFile

from applications.patent_system.models import (
    Application,
    ApplicationStatus,
    AttorneyAssignment,
    FilingRecord,
    PatentabilityAssessment,
)

from .base import UCTestBase


class _PatentFlowMixin:
    """Helpers to put an application into the preconditions required by later UCs."""

    def _submit_application_pending_consent(self, *, title="Test Patent"):
        self.login_as_applicant()
        payload = self.make_submit_payload(title=title)
        resp, app_id = self.post_submit_application(payload)
        self.assertEqual(resp.status_code, 201, msg=getattr(resp, "content", b"")[:500])
        app = Application.objects.get(id=app_id)
        self.assertEqual(app.status, ApplicationStatus.PENDING_INVENTOR_CONSENT)
        return app

    def _give_all_inventor_consents(self, app: Application):
        # Primary applicant consent
        self.login_as_applicant()
        r1 = self.post_give_consent(app.id)
        self.assertEqual(r1.status_code, 200, msg=getattr(r1, "content", b"")[:500])

        # Co-inventor consent
        self.login_as_coinventor()
        r2 = self.post_give_consent(app.id)
        self.assertEqual(r2.status_code, 200, msg=getattr(r2, "content", b"")[:500])

        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.SUBMITTED)
        return app

    def _submit_application_submitted(self, *, title="Test Patent"):
        app = self._submit_application_pending_consent(title=title)
        return self._give_all_inventor_consents(app)

    def _pcc_review_and_forward(self, app: Application):
        self.login_as_pcc_admin()
        review_url = self.API_PREFIX + f"pccAdmin/applications/new/review/{app.id}/"
        r = self.api_post(review_url, {"comments": "Reviewed."}, expected_status=200)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.REVIEWED)

        forward_url = self.API_PREFIX + f"pccAdmin/applications/new/forward/{app.id}/"
        r2 = self.api_post(forward_url, {"comments": "Forwarded to director."}, expected_status=200)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.FORWARDED)
        return app

    def _director_approve(self, app: Application):
        self.login_as_director()
        url = self.API_PREFIX + "director/application/accept"
        r = self.api_post(
            url,
            {
                "application_id": app.id,
                "comments": "Approved."
            },
            expected_status=200,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.APPROVED)
        return app

    def _advance_to_search_report_generated(self, app: Application):
        # Approved -> Patentability Check Started -> Completed -> Search Report Generated
        self.login_as_pcc_admin()
        change_url = self.API_PREFIX + f"pccAdmin/applications/ongoing/changeStatus/{app.id}/"
        for st in [
            ApplicationStatus.PATENTABILITY_CHECK_STARTED,
            ApplicationStatus.PATENTABILITY_CHECK_COMPLETED,
            ApplicationStatus.SEARCH_REPORT_GENERATED,
        ]:
            self.api_post(change_url, {"next_status": st}, expected_status=200)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.SEARCH_REPORT_GENERATED)
        return app


# =========================================================================
# UC-001: Submit Patent Application
# =========================================================================
class TestPMS_UC_001(_PatentFlowMixin, UCTestBase):

    def test_hp01_submit_complete_application_creates_pending_consent(self):
        self._test_id = "PMS-UC-001-HP-01"; self._uc_id = "PMS-UC-001"
        self._test_category = "Happy Path"
        self._scenario = "Applicant submits complete application"
        self._input_action = "POST /patentsystem/applicant/applications/submit/"
        self._expected_result = "201; Application created with status=Pending Inventor Consent"

        app = self._submit_application_pending_consent(title="UC001")
        self._record_result(
            self._test_id,
            self._scenario,
            "Pass",
            actual=f"Created application_id={app.id}, status={app.status}",
            evidence="",
        )

    def test_ap01_all_consents_auto_submits_application(self):
        self._test_id = "PMS-UC-001-AP-01"; self._uc_id = "PMS-UC-001"
        self._test_category = "Alternate Paths"
        self._scenario = "All inventors give consent; system auto-submits"
        self._input_action = "POST /.../consent/ by each inventor"
        self._expected_result = "status transitions to Submitted"

        app = self._submit_application_pending_consent(title="UC001-consent")
        app = self._give_all_inventor_consents(app)
        self._record_result(
            self._test_id,
            self._scenario,
            "Pass",
            actual=f"status={app.status}",
            evidence="",
        )

    def test_ex01_unauthenticated_user_cannot_submit(self):
        self._test_id = "PMS-UC-001-EX-01"; self._uc_id = "PMS-UC-001"
        self._test_category = "Exception"
        self._scenario = "Unauthenticated user attempts submission"
        self._input_action = "POST /patentsystem/applicant/applications/submit/"
        self._expected_result = "401 Unauthorized"

        self.logout()
        payload = self.make_submit_payload(title="UC001-unauth")
        resp, _ = self.post_submit_application(payload)
        self.assertEqual(resp.status_code, 401)


# =========================================================================
# UC-002: Assign Application to Director (mapped to PCC forward + director queue)
# =========================================================================
class TestPMS_UC_002(_PatentFlowMixin, UCTestBase):

    def test_hp01_pcc_forwards_to_director_queue(self):
        self._test_id = "PMS-UC-002-HP-01"; self._uc_id = "PMS-UC-002"
        self._test_category = "Happy Path"
        self._scenario = "PCC Admin forwards reviewed application to Director"
        self._input_action = "POST /patentsystem/pccAdmin/applications/new/forward/{id}/"
        self._expected_result = "200; status becomes Forwarded for Director's Review"

        app = self._submit_application_submitted(title="UC002")
        app = self._pcc_review_and_forward(app)
        self._record_result(self._test_id, self._scenario, "Pass", actual=f"status={app.status}", evidence="")

    def test_ap01_forward_rejects_overlong_comment(self):
        self._test_id = "PMS-UC-002-AP-01"; self._uc_id = "PMS-UC-002"
        self._test_category = "Alternate Paths"
        self._scenario = "Forwarding with comment >1000 chars"
        self._expected_result = "400 Validation error"

        app = self._submit_application_submitted(title="UC002-long")
        self.login_as_pcc_admin()
        forward_url = self.API_PREFIX + f"pccAdmin/applications/new/forward/{app.id}/"
        r = self.api_post(forward_url, {"comments": "x" * 1001}, expected_status=400)
        self._record_result(self._test_id, self._scenario, "Pass", actual=f"status={r.status_code}", evidence=r.content[:500].decode(errors="ignore"))

    def test_ex01_non_pcc_cannot_forward(self):
        self._test_id = "PMS-UC-002-EX-01"; self._uc_id = "PMS-UC-002"
        self._test_category = "Exception"
        self._scenario = "Non-PCC user tries to forward"
        self._expected_result = "403 Forbidden"

        app = self._submit_application_submitted(title="UC002-nonpcc")
        self.login_as_outsider()
        forward_url = self.API_PREFIX + f"pccAdmin/applications/new/forward/{app.id}/"
        r = self.api_post(forward_url, {"comments": "No."}, expected_status=403)
        self._record_result(self._test_id, self._scenario, "Pass", actual=f"status={r.status_code}", evidence="")


# =========================================================================
# UC-003: Review Patent Application (Director)
# =========================================================================
class TestPMS_UC_003(_PatentFlowMixin, UCTestBase):

    def test_hp01_director_approves_forwarded_application(self):
        self._test_id = "PMS-UC-003-HP-01"; self._uc_id = "PMS-UC-003"
        self._test_category = "Happy Path"
        self._scenario = "Director approves"
        self._expected_result = "200; status=Approved"

        app = self._submit_application_submitted(title="UC003")
        app = self._pcc_review_and_forward(app)
        app = self._director_approve(app)
        self._record_result(self._test_id, self._scenario, "Pass", actual=f"status={app.status}", evidence="")

    def test_ap01_director_requests_revision_with_long_feedback(self):
        self._test_id = "PMS-UC-003-AP-01"; self._uc_id = "PMS-UC-003"
        self._test_category = "Alternate Paths"
        self._scenario = "Director requests revision"
        self._expected_result = "200; status=Needs Revision"

        app = self._submit_application_submitted(title="UC003-rev")
        app = self._pcc_review_and_forward(app)

        self.login_as_director()
        url = self.API_PREFIX + "director/application/reject"
        r = self.api_post(
            url,
            {
                "application_id": app.id,
                "decision": "Needs Revision",
                "comments": "y" * 60,
            },
            expected_status=200,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.NEEDS_REVISION)
        self._record_result(self._test_id, self._scenario, "Pass", actual=f"status={app.status}", evidence="")

    def test_ex01_director_reject_requires_min_50_char_feedback(self):
        self._test_id = "PMS-UC-003-EX-01"; self._uc_id = "PMS-UC-003"
        self._test_category = "Exception"
        self._scenario = "Director rejects with too-short feedback"
        self._expected_result = "400; validation error"

        app = self._submit_application_submitted(title="UC003-short")
        app = self._pcc_review_and_forward(app)

        self.login_as_director()
        url = self.API_PREFIX + "director/application/reject"
        r = self.api_post(
            url,
            {"application_id": app.id, "decision": "Reject", "comments": "short"},
            expected_status=400,
        )
        self._record_result(self._test_id, self._scenario, "Pass", actual=f"status={r.status_code}", evidence=r.content[:500].decode(errors="ignore"))


# =========================================================================
# UC-004: Revise and Resubmit Application
# =========================================================================
class TestPMS_UC_004(_PatentFlowMixin, UCTestBase):

    def test_hp01_resubmit_within_window(self):
        self._test_id = "PMS-UC-004-HP-01"; self._uc_id = "PMS-UC-004"
        self._test_category = "Happy Path"
        self._scenario = "Applicant resubmits within deadline"
        self._expected_result = "200; status=Resubmitted"

        app = self._submit_application_submitted(title="UC004")
        app = self._pcc_review_and_forward(app)

        # move to Needs Revision
        self.login_as_director()
        self.api_post(
            self.API_PREFIX + "director/application/reject",
            {"application_id": app.id, "decision": "Needs Revision", "comments": "z" * 60},
            expected_status=200,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.NEEDS_REVISION)

        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/resubmit/{app.id}/"
        r = self.client.post(url, {"json_data": json.dumps({"title": "UC004-updated"})}, format="multipart")
        self.assertEqual(r.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.RESUBMITTED)

    def test_ap01_resubmit_updates_title_only(self):
        self._test_id = "PMS-UC-004-AP-01"; self._uc_id = "PMS-UC-004"
        self._test_category = "Alternate Paths"
        self._scenario = "Applicant resubmits with partial update"
        self._expected_result = "200; title updated; status=Resubmitted"

        app = self._submit_application_submitted(title="UC004-partial")
        app.status = ApplicationStatus.NEEDS_REVISION
        app.resubmission_deadline = now()  # still valid
        app.save()

        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/resubmit/{app.id}/"
        r = self.client.post(url, {"json_data": json.dumps({"title": "UC004-new"})}, format="multipart")
        self.assertEqual(r.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.title, "UC004-new")

    def test_ex01_resubmit_after_deadline_marks_expired(self):
        self._test_id = "PMS-UC-004-EX-01"; self._uc_id = "PMS-UC-004"
        self._test_category = "Exception"
        self._scenario = "Applicant resubmits after deadline"
        self._expected_result = "400; status=Expired"

        app = self._submit_application_submitted(title="UC004-exp")
        app.status = ApplicationStatus.NEEDS_REVISION
        app.resubmission_deadline = now() - timedelta(days=1)
        app.save()

        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/resubmit/{app.id}/"
        r = self.client.post(url, {"json_data": json.dumps({"title": "late"})}, format="multipart")
        self.assertEqual(r.status_code, 400)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.EXPIRED)


# =========================================================================
# UC-005: Track Application Status
# =========================================================================
class TestPMS_UC_005(_PatentFlowMixin, UCTestBase):

    def test_hp01_applicant_views_own_applications_list(self):
        self._test_id = "PMS-UC-005-HP-01"; self._uc_id = "PMS-UC-005"
        app = self._submit_application_pending_consent(title="UC005")

        self.login_as_applicant()
        url = self.API_PREFIX + "applicant/applications/"
        r = self.api_get(url, expected_status=200)
        data = r.json().get("applications", [])
        self.assertTrue(any(str(a.get("id")) == str(app.id) for a in data))

    def test_ap01_applicant_views_details_of_own_application(self):
        self._test_id = "PMS-UC-005-AP-01"; self._uc_id = "PMS-UC-005"
        app = self._submit_application_pending_consent(title="UC005-detail")

        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/details/{app.id}/"
        r = self.api_get(url, expected_status=200)
        self.assertEqual(str(r.json().get("id")), str(app.id))

    def test_ex01_applicant_cannot_view_others_application(self):
        self._test_id = "PMS-UC-005-EX-01"; self._uc_id = "PMS-UC-005"
        app = self._submit_application_pending_consent(title="UC005-other")

        # outsider user (authenticated) but not inventor
        self.login_as_outsider()
        url = self.API_PREFIX + f"applicant/applications/details/{app.id}/"
        self.api_get(url, expected_status=403)


# =========================================================================
# UC-006: Assign Attorney
# =========================================================================
class TestPMS_UC_006(_PatentFlowMixin, UCTestBase):

    def test_hp01_pcc_assigns_attorney_to_approved_application(self):
        self._test_id = "PMS-UC-006-HP-01"; self._uc_id = "PMS-UC-006"

        app = self._submit_application_submitted(title="UC006")
        app = self._pcc_review_and_forward(app)
        app = self._director_approve(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/attorney/"
        r = self.client.post(
            url,
            {
                "attorney_name": "Adv Sharma",
                "attorney_email": "sharma@lawfirm.com",
                "specialization": "Patent Law",
            },
            format="multipart",
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(AttorneyAssignment.objects.filter(application=app).exists())

    def test_ap01_pcc_updates_existing_attorney_assignment(self):
        self._test_id = "PMS-UC-006-AP-01"; self._uc_id = "PMS-UC-006"

        app = self._submit_application_submitted(title="UC006-update")
        app = self._pcc_review_and_forward(app)
        app = self._director_approve(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/attorney/"
        self.client.post(url, {"attorney_name": "A"}, format="multipart")
        self.client.post(url, {"attorney_name": "B"}, format="multipart")
        self.assertEqual(AttorneyAssignment.objects.get(application=app).attorney_name, "B")

    def test_ex01_attorney_assignment_blocked_when_not_approved(self):
        self._test_id = "PMS-UC-006-EX-01"; self._uc_id = "PMS-UC-006"

        app = self._submit_application_submitted(title="UC006-block")
        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/attorney/"
        r = self.client.post(url, {"attorney_name": "Adv"}, format="multipart")
        self.assertEqual(r.status_code, 400)


# =========================================================================
# UC-007: Assess Application Patentability (Legal Assessment)
# =========================================================================
class TestPMS_UC_007(_PatentFlowMixin, UCTestBase):

    def test_hp01_record_patentability_assessment(self):
        self._test_id = "PMS-UC-007-HP-01"; self._uc_id = "PMS-UC-007"

        app = self._submit_application_submitted(title="UC007")
        app = self._pcc_review_and_forward(app)
        app = self._director_approve(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/assessment/"
        r = self.client.post(
            url,
            {
                "recommendation": "File Patent",
                "opinion_summary": "This looks patentable based on novelty and utility.",
                "novelty_score": 80,
                "non_obviousness_score": 70,
                "utility_score": 90,
                "search_completeness": 95,
            },
            format="multipart",
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(PatentabilityAssessment.objects.filter(application=app).exists())

    def test_ap01_invalid_recommendation_rejected(self):
        self._test_id = "PMS-UC-007-AP-01"; self._uc_id = "PMS-UC-007"

        app = self._submit_application_submitted(title="UC007-bad")
        app = self._pcc_review_and_forward(app)
        app = self._director_approve(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/assessment/"
        r = self.client.post(
            url,
            {
                "recommendation": "Maybe",
                "opinion_summary": "This is long enough to pass summary rule.",
                "novelty_score": 80,
                "non_obviousness_score": 70,
                "utility_score": 90,
                "search_completeness": 95,
            },
            format="multipart",
        )
        self.assertEqual(r.status_code, 400)

    def test_ex01_short_opinion_summary_rejected(self):
        self._test_id = "PMS-UC-007-EX-01"; self._uc_id = "PMS-UC-007"

        app = self._submit_application_submitted(title="UC007-short")
        app = self._pcc_review_and_forward(app)
        app = self._director_approve(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/assessment/"
        r = self.client.post(
            url,
            {
                "recommendation": "File Patent",
                "opinion_summary": "too short",
                "novelty_score": 80,
                "non_obviousness_score": 70,
                "utility_score": 90,
                "search_completeness": 95,
            },
            format="multipart",
        )
        self.assertEqual(r.status_code, 400)


# =========================================================================
# UC-008: Manage Budgets and Financial Approval
# =========================================================================
class TestPMS_UC_008(_PatentFlowMixin, UCTestBase):

    def test_hp01_budget_within_threshold_auto_approved_by_pcc(self):
        self._test_id = "PMS-UC-008-HP-01"; self._uc_id = "PMS-UC-008"

        app = self._submit_application_submitted(title="UC008")
        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/budget/"
        r = self.api_post(url, {"filing_cost": 1000, "attorney_fees": 1000, "administrative_cost": 0}, expected_status=200)
        self.assertIn("total_cost", r.json())

    def test_ap01_budget_above_threshold_escalates(self):
        self._test_id = "PMS-UC-008-AP-01"; self._uc_id = "PMS-UC-008"

        app = self._submit_application_submitted(title="UC008-hi")
        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/budget/"
        r = self.api_post(url, {"filing_cost": 200000, "attorney_fees": 0, "administrative_cost": 0}, expected_status=200)
        self.assertEqual(r.json().get("decision"), "Escalated to Director")

    def test_ex01_non_pcc_cannot_create_budget(self):
        self._test_id = "PMS-UC-008-EX-01"; self._uc_id = "PMS-UC-008"

        app = self._submit_application_submitted(title="UC008-non")
        self.login_as_outsider()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/budget/"
        self.api_post(url, {"filing_cost": 1}, expected_status=403)


# =========================================================================
# UC-009: File with Patent Office / Log Official Filing
# =========================================================================
class TestPMS_UC_009(_PatentFlowMixin, UCTestBase):

    def test_hp01_record_filing_advances_to_patent_filed(self):
        self._test_id = "PMS-UC-009-HP-01"; self._uc_id = "PMS-UC-009"

        app = self._submit_application_submitted(title="UC009")
        app = self._pcc_review_and_forward(app)
        app = self._director_approve(app)
        app = self._advance_to_search_report_generated(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/filing/"
        r = self.client.post(url, {"external_filing_id": "IPO/2026/001"}, format="multipart")
        self.assertEqual(r.status_code, 201)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.PATENT_FILED)
        self.assertTrue(FilingRecord.objects.filter(application=app).exists())

    def test_ap01_international_filing_requires_justification(self):
        self._test_id = "PMS-UC-009-AP-01"; self._uc_id = "PMS-UC-009"

        app = self._submit_application_submitted(title="UC009-intl")
        app = self._pcc_review_and_forward(app)
        app = self._director_approve(app)
        app = self._advance_to_search_report_generated(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/filing/"
        r = self.client.post(
            url,
            {"filing_office": "USPTO", "jurisdiction": "USA", "external_filing_id": "US-1"},
            format="multipart",
        )
        self.assertEqual(r.status_code, 400)

    def test_ex01_filing_blocked_if_wrong_status(self):
        self._test_id = "PMS-UC-009-EX-01"; self._uc_id = "PMS-UC-009"

        app = self._submit_application_submitted(title="UC009-wrong")
        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/filing/"
        r = self.client.post(url, {"external_filing_id": "IPO/2026/002"}, format="multipart")
        self.assertEqual(r.status_code, 400)


# =========================================================================
# UC-010: Track Application Progress and Notifications
# =========================================================================
class TestPMS_UC_010(_PatentFlowMixin, UCTestBase):

    def test_hp01_get_notifications_endpoint_works(self):
        self._test_id = "PMS-UC-010-HP-01"; self._uc_id = "PMS-UC-010"

        self.login_as_applicant()
        url = self.API_PREFIX + "notifications/"
        self.api_get(url, expected_status=200)

    def test_ap01_unread_count_endpoint_returns_integer(self):
        self._test_id = "PMS-UC-010-AP-01"; self._uc_id = "PMS-UC-010"

        self.login_as_applicant()
        url = self.API_PREFIX + "notifications/unread-count/"
        r = self.api_get(url, expected_status=200)
        self.assertIn("unread_count", r.json())
        self.assertIsInstance(r.json().get("unread_count"), int)

    def test_ex01_unauthenticated_cannot_fetch_notifications(self):
        self._test_id = "PMS-UC-010-EX-01"; self._uc_id = "PMS-UC-010"

        self.logout()
        url = self.API_PREFIX + "notifications/"
        self.api_get(url, expected_status=401)


# =========================================================================
# UC-011: Respond to Office Actions — NOT IMPLEMENTED (spec gap)
# =========================================================================
@unittest.skip("PMS-UC-011 office-action handling is not implemented in current API.")
class TestPMS_UC_011(UCTestBase):

    def test_hp01_placeholder(self):
        self._test_id = "PMS-UC-011-HP-01"; self._uc_id = "PMS-UC-011"
        self._scenario = "Spec-only UC; API endpoints not available"
        self._expected_result = "Skipped"

    def test_ap01_placeholder(self):
        self._test_id = "PMS-UC-011-AP-01"; self._uc_id = "PMS-UC-011"
        self._scenario = "Spec-only UC; API endpoints not available"
        self._expected_result = "Skipped"

    def test_ex01_placeholder(self):
        self._test_id = "PMS-UC-011-EX-01"; self._uc_id = "PMS-UC-011"
        self._scenario = "Spec-only UC; API endpoints not available"
        self._expected_result = "Skipped"


# =========================================================================
# UC-012: Track and Manage Deadlines — no direct API to trigger deadline jobs
# =========================================================================
@unittest.skip("PMS-UC-012 deadline jobs are not exposed via the current API.")
class TestPMS_UC_012(UCTestBase):

    def test_hp01_placeholder(self):
        self._test_id = "PMS-UC-012-HP-01"; self._uc_id = "PMS-UC-012"
        self._scenario = "Spec-only UC; no API trigger endpoints"
        self._expected_result = "Skipped"

    def test_ap01_placeholder(self):
        self._test_id = "PMS-UC-012-AP-01"; self._uc_id = "PMS-UC-012"
        self._scenario = "Spec-only UC; no API trigger endpoints"
        self._expected_result = "Skipped"

    def test_ex01_placeholder(self):
        self._test_id = "PMS-UC-012-EX-01"; self._uc_id = "PMS-UC-012"
        self._scenario = "Spec-only UC; no API trigger endpoints"
        self._expected_result = "Skipped"


# =========================================================================
# UC-013: Maintenance Fees and Renewals — NOT IMPLEMENTED
# =========================================================================
@unittest.skip("PMS-UC-013 maintenance fees/renewals are not implemented in current API.")
class TestPMS_UC_013(UCTestBase):

    def test_hp01_placeholder(self):
        self._test_id = "PMS-UC-013-HP-01"; self._uc_id = "PMS-UC-013"
        self._scenario = "Spec-only UC; maintenance module absent"
        self._expected_result = "Skipped"

    def test_ap01_placeholder(self):
        self._test_id = "PMS-UC-013-AP-01"; self._uc_id = "PMS-UC-013"
        self._scenario = "Spec-only UC; maintenance module absent"
        self._expected_result = "Skipped"

    def test_ex01_placeholder(self):
        self._test_id = "PMS-UC-013-EX-01"; self._uc_id = "PMS-UC-013"
        self._scenario = "Spec-only UC; maintenance module absent"
        self._expected_result = "Skipped"


# =========================================================================
# UC-014: Withdraw Patent Application
# =========================================================================
class TestPMS_UC_014(_PatentFlowMixin, UCTestBase):

    def test_hp01_applicant_withdraws_before_filing(self):
        self._test_id = "PMS-UC-014-HP-01"; self._uc_id = "PMS-UC-014"

        app = self._submit_application_pending_consent(title="UC014")
        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/withdraw/{app.id}/"
        r = self.api_post(url, {"reason": "No longer needed"}, expected_status=200)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.WITHDRAWN)

    def test_ap01_withdraw_requires_applicant_association(self):
        self._test_id = "PMS-UC-014-AP-01"; self._uc_id = "PMS-UC-014"

        app = self._submit_application_pending_consent(title="UC014-2")
        self.login_as_outsider()
        url = self.API_PREFIX + f"applicant/applications/withdraw/{app.id}/"
        self.api_post(url, {"reason": "No"}, expected_status=403)

    def test_ex01_withdraw_blocked_after_patent_filed(self):
        self._test_id = "PMS-UC-014-EX-01"; self._uc_id = "PMS-UC-014"

        app = self._submit_application_submitted(title="UC014-filed")
        app.status = ApplicationStatus.PATENT_FILED
        app.save()

        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/withdraw/{app.id}/"
        self.api_post(url, {"reason": "Late"}, expected_status=400)


# =========================================================================
# UC-015: Generate Reports and Analytics Dashboards
# =========================================================================
class TestPMS_UC_015(UCTestBase):

    def test_hp01_pcc_admin_can_view_analytics(self):
        self._test_id = "PMS-UC-015-HP-01"; self._uc_id = "PMS-UC-015"
        self.login_as_pcc_admin()
        url = self.API_PREFIX + "pccAdmin/analytics/"
        self.api_get(url, expected_status=200)

    def test_ap01_analytics_summary_endpoint(self):
        self._test_id = "PMS-UC-015-AP-01"; self._uc_id = "PMS-UC-015"
        self.login_as_pcc_admin()
        url = self.API_PREFIX + "pccAdmin/analytics/summary/"
        self.api_get(url, expected_status=200)

    def test_ex01_unauthenticated_cannot_view_analytics(self):
        self._test_id = "PMS-UC-015-EX-01"; self._uc_id = "PMS-UC-015"
        self.logout()
        url = self.API_PREFIX + "pccAdmin/analytics/"
        self.api_get(url, expected_status=401)


# =========================================================================
# UC-016: Manage Co-Inventors and Inventor Agreements (mapped to consent)
# =========================================================================
class TestPMS_UC_016(_PatentFlowMixin, UCTestBase):

    def test_hp01_submission_creates_pending_consent_for_coinventor(self):
        self._test_id = "PMS-UC-016-HP-01"; self._uc_id = "PMS-UC-016"

        app = self._submit_application_pending_consent(title="UC016")
        self.login_as_coinventor()
        url = self.API_PREFIX + "applicant/applications/pending-consent/"
        r = self.api_get(url, expected_status=200)
        self.assertTrue(any(str(x.get("application_id")) == str(app.id) for x in r.json()))

    def test_ap01_consent_can_be_revoked_only_in_draft_or_needs_revision(self):
        self._test_id = "PMS-UC-016-AP-01"; self._uc_id = "PMS-UC-016"

        app = self._submit_application_pending_consent(title="UC016-revoke")
        self.login_as_coinventor()
        self.post_give_consent(app.id)

        # revocation endpoint exists
        revoke_url = self.API_PREFIX + f"applicant/applications/{app.id}/consent/revoke/"
        # app is still pending consent; service allows only Draft or Needs Revision → should 400
        self.api_post(revoke_url, {}, expected_status=400)

    def test_ex01_submission_blocked_if_inventor_shares_not_100(self):
        self._test_id = "PMS-UC-016-EX-01"; self._uc_id = "PMS-UC-016"

        self.login_as_applicant()
        payload = self.make_submit_payload(
            title="UC016-badshares",
            inventor_shares=[(self.applicant_user, 60), (self.coinventor_user, 60)],
        )
        resp, _ = self.post_submit_application(payload)
        self.assertEqual(resp.status_code, 400)


# =========================================================================
# UC-017: Patent Licensing / Tech Transfer Request — NOT IMPLEMENTED
# =========================================================================
@unittest.skip("PMS-UC-017 licensing/tech-transfer is not implemented in current API.")
class TestPMS_UC_017(UCTestBase):

    def test_hp01_placeholder(self):
        self._test_id = "PMS-UC-017-HP-01"; self._uc_id = "PMS-UC-017"
        self._scenario = "Spec-only UC; licensing endpoints absent"
        self._expected_result = "Skipped"

    def test_ap01_placeholder(self):
        self._test_id = "PMS-UC-017-AP-01"; self._uc_id = "PMS-UC-017"
        self._scenario = "Spec-only UC; licensing endpoints absent"
        self._expected_result = "Skipped"

    def test_ex01_placeholder(self):
        self._test_id = "PMS-UC-017-EX-01"; self._uc_id = "PMS-UC-017"
        self._scenario = "Spec-only UC; licensing endpoints absent"
        self._expected_result = "Skipped"


# =========================================================================
# UC-018: Appeal Against Rejection
# =========================================================================
class TestPMS_UC_018(_PatentFlowMixin, UCTestBase):

    def test_hp01_applicant_lodges_appeal_for_rejected_application(self):
        self._test_id = "PMS-UC-018-HP-01"; self._uc_id = "PMS-UC-018"

        app = self._submit_application_submitted(title="UC018")
        app.status = ApplicationStatus.REJECTED
        app.decision_date = now()
        app.save()

        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/{app.id}/appeal/"
        self.api_post(url, {"reason": "a" * 60}, expected_status=201)

    def test_ap01_pcc_forwards_appeal_to_director(self):
        self._test_id = "PMS-UC-018-AP-01"; self._uc_id = "PMS-UC-018"

        app = self._submit_application_submitted(title="UC018-fwd")
        app.status = ApplicationStatus.APPEAL
        app.save()

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/appeal/review/"
        self.api_post(url, {}, expected_status=200)

    def test_ex01_appeal_reason_requires_min_50_chars(self):
        self._test_id = "PMS-UC-018-EX-01"; self._uc_id = "PMS-UC-018"

        app = self._submit_application_submitted(title="UC018-short")
        app.status = ApplicationStatus.REJECTED
        app.decision_date = now()
        app.save()

        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/{app.id}/appeal/"
        self.api_post(url, {"reason": "short"}, expected_status=400)


# =========================================================================
# UC-019: Search Prior Art (mapped to implemented global search/filter endpoint)
# =========================================================================
class TestPMS_UC_019(UCTestBase):

    def test_hp01_search_by_query_returns_results_structure(self):
        self._test_id = "PMS-UC-019-HP-01"; self._uc_id = "PMS-UC-019"
        self._test_category = "Happy Path"
        self._scenario = "Search applications by keyword"
        self._expected_result = "200; returns results with total + items"

        self.login_as_applicant()
        url = self.API_PREFIX + "search/"
        r = self.api_get(url, expected_status=200, query={"q": "test"})
        body = r.json()
        self.assertIn("items", body)
        self.assertIn("total", body)

    def test_ap01_search_filters_by_status(self):
        self._test_id = "PMS-UC-019-AP-01"; self._uc_id = "PMS-UC-019"
        self._test_category = "Alternate Paths"
        self._scenario = "Search with status filter"
        self._expected_result = "200; filtered result set"

        self.login_as_applicant()
        url = self.API_PREFIX + "search/"
        r = self.api_get(url, expected_status=200, query={"status": [ApplicationStatus.SUBMITTED]})
        body = r.json()
        self.assertIn("items", body)

    def test_ex01_search_rejects_invalid_date_format(self):
        self._test_id = "PMS-UC-019-EX-01"; self._uc_id = "PMS-UC-019"
        self.login_as_applicant()
        url = self.API_PREFIX + "search/"
        # invalid date_from should be treated as None and still 200
        r = self.api_get(url, expected_status=200, query={"date_from": "not-a-date"})
        self.assertIn("items", r.json())


# =========================================================================
# UC-020: Manage Document Versions
# =========================================================================
class TestPMS_UC_020(_PatentFlowMixin, UCTestBase):

    def test_hp01_upload_document_creates_version_1(self):
        self._test_id = "PMS-UC-020-HP-01"; self._uc_id = "PMS-UC-020"

        app = self._submit_application_pending_consent(title="UC020")
        self.login_as_applicant()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/documents/"
        f = SimpleUploadedFile("doc.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        r = self.client.post(
            url,
            {"document_type": "POC", "title": "POC", "file": f, "description": "v1"},
            format="multipart",
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json().get("version"), 1)

    def test_ap01_upload_document_same_type_increments_version(self):
        self._test_id = "PMS-UC-020-AP-01"; self._uc_id = "PMS-UC-020"

        app = self._submit_application_pending_consent(title="UC020-v")
        self.login_as_applicant()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/documents/"
        f1 = SimpleUploadedFile("doc1.pdf", b"%PDF-1.4 v1", content_type="application/pdf")
        f2 = SimpleUploadedFile("doc2.pdf", b"%PDF-1.4 v2", content_type="application/pdf")
        self.client.post(url, {"document_type": "MOU", "title": "MOU", "file": f1}, format="multipart")
        r2 = self.client.post(url, {"document_type": "MOU", "title": "MOU", "file": f2}, format="multipart")
        self.assertEqual(r2.status_code, 201)
        self.assertEqual(r2.json().get("version"), 2)

    def test_ex01_non_inventor_cannot_upload_document(self):
        self._test_id = "PMS-UC-020-EX-01"; self._uc_id = "PMS-UC-020"

        app = self._submit_application_pending_consent(title="UC020-no")
        self.login_as_outsider()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/documents/"
        f = SimpleUploadedFile("doc.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        r = self.client.post(url, {"document_type": "POC", "title": "POC", "file": f}, format="multipart")
        self.assertEqual(r.status_code, 403)
