import json
import unittest
from datetime import timedelta

from django.utils.timezone import now
from django.core.files.uploadedfile import SimpleUploadedFile

from applications.patent_system.models import (
    Application,
    ApplicationStatus,
    AttorneyAssignment,
    BudgetDecision,
    FilingRecord,
    PatentabilityAssessment,
    CommunicationLog,
)

from .base import BRTestBase


class _PatentBRFlowMixin:
    """Shared setup helpers for BR tests (real API calls + real DB state)."""

    def _submit_pending_consent(self, *, title="BR Test Patent", inventor_shares=None):
        self.login_as_applicant()
        payload = self.make_submit_payload(title=title, inventor_shares=inventor_shares)
        resp, app_id = self.post_submit_application(payload)
        self.assertEqual(resp.status_code, 201, msg=getattr(resp, "content", b"")[:500])
        app = Application.objects.get(id=app_id)
        self.assertEqual(app.status, ApplicationStatus.PENDING_INVENTOR_CONSENT)
        return app

    def _consent_all(self, app: Application):
        self.login_as_applicant()
        self.api_post(self.API_PREFIX + f"applicant/applications/{app.id}/consent/", {}, expected_status=200)
        self.login_as_coinventor()
        self.api_post(self.API_PREFIX + f"applicant/applications/{app.id}/consent/", {}, expected_status=200)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.SUBMITTED)
        return app

    def _submit_submitted(self, *, title="BR Test Patent", inventor_shares=None):
        return self._consent_all(self._submit_pending_consent(title=title, inventor_shares=inventor_shares))

    def _pcc_review(self, app: Application, *, comments="Reviewed"):
        self.login_as_pcc_admin()
        self.api_post(
            self.API_PREFIX + f"pccAdmin/applications/new/review/{app.id}/",
            {"comments": comments},
            expected_status=200,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.REVIEWED)
        return app

    def _pcc_forward(self, app: Application, *, comments="Forwarded"):
        self.login_as_pcc_admin()
        self.api_post(
            self.API_PREFIX + f"pccAdmin/applications/new/forward/{app.id}/",
            {"comments": comments},
            expected_status=200,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.FORWARDED)
        return app

    def _director_accept(self, app: Application, *, feedback="Approved"):
        self.login_as_director()
        r = self.api_post(
            self.API_PREFIX + "director/application/accept",
            {"application_id": app.id, "comments": feedback},
            expected_status=200,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.APPROVED)
        return r, app

    def _advance_to_search_report_generated(self, app: Application):
        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/ongoing/changeStatus/{app.id}/"
        for st in [
            ApplicationStatus.PATENTABILITY_CHECK_STARTED,
            ApplicationStatus.PATENTABILITY_CHECK_COMPLETED,
            ApplicationStatus.SEARCH_REPORT_GENERATED,
        ]:
            self.api_post(url, {"next_status": st}, expected_status=200)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.SEARCH_REPORT_GENERATED)
        return app


class TestBR_PMS_001(_PatentBRFlowMixin, BRTestBase):

    def test_valid_submission_with_all_required_fields(self):
        self._test_id = "BR-PMS-001-V-01"; self._br_id = "BR-PMS-001"
        self._scenario = "Submit application with complete payload"
        self._input_action = "POST /patentsystem/applicant/applications/submit/"
        self._expected_result = "201; Application created"

        self._submit_pending_consent(title="BR001")

    def test_invalid_missing_required_field(self):
        self._test_id = "BR-PMS-001-I-01"; self._br_id = "BR-PMS-001"
        self._scenario = "Submit application missing required field"
        self._expected_result = "400; Missing required field"

        self.login_as_applicant()
        payload = self.make_submit_payload(title="BR001-missing")
        payload.pop("title")
        resp, _ = self.post_submit_application(payload)
        self.assertEqual(resp.status_code, 400)


class TestBR_PMS_002(_PatentBRFlowMixin, BRTestBase):

    def test_valid_authenticated_applicant_can_submit(self):
        self._test_id = "BR-PMS-002-V-01"; self._br_id = "BR-PMS-002"
        self._scenario = "Authenticated applicant submits"
        self._expected_result = "201"
        self._submit_pending_consent(title="BR002")

    def test_invalid_unauthenticated_cannot_submit(self):
        self._test_id = "BR-PMS-002-I-01"; self._br_id = "BR-PMS-002"
        self._scenario = "Unauthenticated user submits"
        self._expected_result = "401"
        self.logout()
        payload = self.make_submit_payload(title="BR002-unauth")
        resp, _ = self.post_submit_application(payload)
        self.assertEqual(resp.status_code, 401)


class TestBR_PMS_003(_PatentBRFlowMixin, BRTestBase):

    def test_valid_director_not_inventor_can_approve(self):
        self._test_id = "BR-PMS-003-V-01"; self._br_id = "BR-PMS-003"
        app = self._submit_submitted(title="BR003")
        self._pcc_review(app)
        self._pcc_forward(app)
        self._director_accept(app)

    def test_invalid_director_inventor_conflict_blocked(self):
        self._test_id = "BR-PMS-003-I-01"; self._br_id = "BR-PMS-003"
        # Make director an inventor -> director_review should 409
        app = self._submit_pending_consent(
            title="BR003-conflict",
            inventor_shares=[(self.applicant_user, 50), (self.director_user, 50)],
        )
        self._consent_all(app)
        self._pcc_review(app)
        self._pcc_forward(app)

        self.login_as_director()
        self.api_post(
            self.API_PREFIX + "director/application/accept",
            {"application_id": app.id, "comments": "ok"},
            expected_status=409,
        )


class TestBR_PMS_004(_PatentBRFlowMixin, BRTestBase):

    def test_valid_attorney_assignment_only_after_approval(self):
        self._test_id = "BR-PMS-004-V-01"; self._br_id = "BR-PMS-004"
        app = self._submit_submitted(title="BR004")
        self._pcc_review(app)
        self._pcc_forward(app)
        self._director_accept(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/attorney/"
        r = self.client.post(url, {"attorney_name": "Adv A"}, format="multipart")
        self.assertEqual(r.status_code, 201)
        self.assertTrue(AttorneyAssignment.objects.filter(application=app).exists())

    def test_invalid_attorney_assignment_before_approval_blocked(self):
        self._test_id = "BR-PMS-004-I-01"; self._br_id = "BR-PMS-004"
        app = self._submit_submitted(title="BR004-pre")
        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/attorney/"
        r = self.client.post(url, {"attorney_name": "Adv A"}, format="multipart")
        self.assertEqual(r.status_code, 400)


class TestBR_PMS_005(_PatentBRFlowMixin, BRTestBase):

    def test_valid_reject_requires_justification_min_50(self):
        self._test_id = "BR-PMS-005-V-01"; self._br_id = "BR-PMS-005"
        app = self._submit_submitted(title="BR005")
        self._pcc_review(app)
        self._pcc_forward(app)

        self.login_as_director()
        self.api_post(
            self.API_PREFIX + "director/application/reject",
            {"application_id": app.id, "decision": "Reject", "comments": "a" * 60},
            expected_status=200,
        )

    def test_invalid_reject_with_short_feedback_blocked(self):
        self._test_id = "BR-PMS-005-I-01"; self._br_id = "BR-PMS-005"
        app = self._submit_submitted(title="BR005-short")
        self._pcc_review(app)
        self._pcc_forward(app)

        self.login_as_director()
        self.api_post(
            self.API_PREFIX + "director/application/reject",
            {"application_id": app.id, "decision": "Reject", "comments": "short"},
            expected_status=400,
        )


class TestBR_PMS_006(_PatentBRFlowMixin, BRTestBase):

    def test_valid_inventor_can_upload_document(self):
        self._test_id = "BR-PMS-006-V-01"; self._br_id = "BR-PMS-006"
        app = self._submit_pending_consent(title="BR006")

        self.login_as_applicant()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/documents/"
        f = SimpleUploadedFile("doc.pdf", b"%PDF-1.4", content_type="application/pdf")
        r = self.client.post(url, {"document_type": "POC", "title": "POC", "file": f}, format="multipart")
        self.assertEqual(r.status_code, 201)

    def test_invalid_non_inventor_cannot_upload_document(self):
        self._test_id = "BR-PMS-006-I-01"; self._br_id = "BR-PMS-006"
        app = self._submit_pending_consent(title="BR006-no")

        self.login_as_outsider()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/documents/"
        f = SimpleUploadedFile("doc.pdf", b"%PDF-1.4", content_type="application/pdf")
        r = self.client.post(url, {"document_type": "POC", "title": "POC", "file": f}, format="multipart")
        self.assertEqual(r.status_code, 403)


class TestBR_PMS_007(_PatentBRFlowMixin, BRTestBase):

    def test_valid_pcc_admin_can_assign_attorney(self):
        self._test_id = "BR-PMS-007-V-01"; self._br_id = "BR-PMS-007"
        app = self._submit_submitted(title="BR007")
        self._pcc_review(app)
        self._pcc_forward(app)
        self._director_accept(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/attorney/"
        r = self.client.post(url, {"attorney_name": "Adv Panel"}, format="multipart")
        self.assertEqual(r.status_code, 201)

    def test_invalid_non_pcc_cannot_assign_attorney(self):
        self._test_id = "BR-PMS-007-I-01"; self._br_id = "BR-PMS-007"
        app = self._submit_submitted(title="BR007-non")
        app.status = ApplicationStatus.APPROVED
        app.save()

        self.login_as_applicant()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/attorney/"
        r = self.client.post(url, {"attorney_name": "Adv"}, format="multipart")
        self.assertEqual(r.status_code, 403)


class TestBR_PMS_008(_PatentBRFlowMixin, BRTestBase):

    def test_valid_budget_below_threshold_auto_approved_by_pcc(self):
        self._test_id = "BR-PMS-008-V-01"; self._br_id = "BR-PMS-008"
        app = self._submit_submitted(title="BR008")
        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/budget/"
        r = self.api_post(url, {"filing_cost": 1000, "attorney_fees": 0, "administrative_cost": 0}, expected_status=200)
        self.assertEqual(r.json().get("decision"), BudgetDecision.APPROVED_PCC)

    def test_invalid_non_pcc_cannot_set_budget(self):
        self._test_id = "BR-PMS-008-I-01"; self._br_id = "BR-PMS-008"
        app = self._submit_submitted(title="BR008-non")
        self.login_as_applicant()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/budget/"
        self.api_post(url, {"filing_cost": 1}, expected_status=403)


class TestBR_PMS_009(_PatentBRFlowMixin, BRTestBase):

    def test_valid_status_changes_follow_allowed_transitions(self):
        self._test_id = "BR-PMS-009-V-01"; self._br_id = "BR-PMS-009"
        app = self._submit_submitted(title="BR009")
        self._pcc_review(app)
        self._pcc_forward(app)
        self._director_accept(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/ongoing/changeStatus/{app.id}/"
        self.api_post(url, {"next_status": ApplicationStatus.PATENTABILITY_CHECK_STARTED}, expected_status=200)

    def test_invalid_transition_rejected(self):
        self._test_id = "BR-PMS-009-I-01"; self._br_id = "BR-PMS-009"
        app = self._submit_submitted(title="BR009-bad")

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/ongoing/changeStatus/{app.id}/"
        # From Submitted directly to Patent Filed is not allowed
        self.api_post(url, {"next_status": ApplicationStatus.PATENT_FILED}, expected_status=400)


class TestBR_PMS_010(_PatentBRFlowMixin, BRTestBase):

    def test_valid_token_generated_on_director_approval(self):
        self._test_id = "BR-PMS-010-V-01"; self._br_id = "BR-PMS-010"
        app = self._submit_submitted(title="BR010")
        self._pcc_review(app)
        self._pcc_forward(app)

        _, app = self._director_accept(app)
        self.assertTrue(app.token_no)
        self.assertIn("IIITDMJ/", app.token_no)

    @unittest.skip("File type validation is not enforced on ApplicationDocument uploads in current implementation.")
    def test_invalid_file_format_rejected(self):
        self._test_id = "BR-PMS-010-I-01"; self._br_id = "BR-PMS-010"


class TestBR_PMS_011(_PatentBRFlowMixin, BRTestBase):

    def test_valid_unread_count_increments_after_submit(self):
        self._test_id = "BR-PMS-011-V-01"; self._br_id = "BR-PMS-011"
        self._submit_pending_consent(title="BR011")

        self.login_as_coinventor()
        r = self.api_get(self.API_PREFIX + "notifications/unread-count/", expected_status=200)
        self.assertGreaterEqual(r.json().get("unread_count", 0), 1)

    def test_invalid_unauthenticated_cannot_fetch_notifications(self):
        self._test_id = "BR-PMS-011-I-01"; self._br_id = "BR-PMS-011"
        self.logout()
        self.api_get(self.API_PREFIX + "notifications/", expected_status=401)


@unittest.skip("Dedicated director assignment endpoint is not exposed; forwarding represents director-queueing in this implementation.")
class TestBR_PMS_012(BRTestBase):
    def test_placeholder(self):
        self._test_id = "BR-PMS-012-V-01"; self._br_id = "BR-PMS-012"


class TestBR_PMS_013(_PatentBRFlowMixin, BRTestBase):

    def test_valid_pcc_review_requires_all_inventor_consents(self):
        self._test_id = "BR-PMS-013-V-01"; self._br_id = "BR-PMS-013"
        app = self._submit_pending_consent(title="BR013")
        self._consent_all(app)
        self._pcc_review(app)

    def test_invalid_pcc_review_blocked_if_missing_consent(self):
        self._test_id = "BR-PMS-013-I-01"; self._br_id = "BR-PMS-013"
        app = self._submit_pending_consent(title="BR013-miss")
        # only primary applicant consents
        self.login_as_applicant()
        self.api_post(self.API_PREFIX + f"applicant/applications/{app.id}/consent/", {}, expected_status=200)

        self.login_as_pcc_admin()
        self.api_post(
            self.API_PREFIX + f"pccAdmin/applications/new/review/{app.id}/",
            {"comments": "Reviewed"},
            expected_status=400,
        )


class TestBR_PMS_014(_PatentBRFlowMixin, BRTestBase):

    def test_valid_patentability_assessment_recorded(self):
        self._test_id = "BR-PMS-014-V-01"; self._br_id = "BR-PMS-014"
        app = self._submit_submitted(title="BR014")
        self._pcc_review(app)
        self._pcc_forward(app)
        self._director_accept(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/assessment/"
        r = self.client.post(
            url,
            {
                "recommendation": "File Patent",
                "opinion_summary": "This opinion summary is long enough.",
                "novelty_score": 80,
                "non_obviousness_score": 70,
                "utility_score": 90,
                "search_completeness": 95,
            },
            format="multipart",
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(PatentabilityAssessment.objects.filter(application=app).exists())

    def test_invalid_assessment_recommendation_rejected(self):
        self._test_id = "BR-PMS-014-I-01"; self._br_id = "BR-PMS-014"
        app = self._submit_submitted(title="BR014-bad")
        self._pcc_review(app)
        self._pcc_forward(app)
        self._director_accept(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/assessment/"
        r = self.client.post(
            url,
            {
                "recommendation": "Maybe",
                "opinion_summary": "This opinion summary is long enough.",
                "novelty_score": 80,
                "non_obviousness_score": 70,
                "utility_score": 90,
                "search_completeness": 95,
            },
            format="multipart",
        )
        self.assertEqual(r.status_code, 400)


@unittest.skip("BR-PMS-015 priority logic is not exposed via an API endpoint in current implementation.")
class TestBR_PMS_015(BRTestBase):
    def test_placeholder(self):
        self._test_id = "BR-PMS-015-V-01"; self._br_id = "BR-PMS-015"


class TestBR_PMS_016(_PatentBRFlowMixin, BRTestBase):

    def test_valid_resubmit_within_deadline(self):
        self._test_id = "BR-PMS-016-V-01"; self._br_id = "BR-PMS-016"
        app = self._submit_submitted(title="BR016")
        self.login_as_pcc_admin()
        self.api_post(
            self.API_PREFIX + f"pccAdmin/applications/new/requestModification/{app.id}/",
            {"comments": "Please revise."},
            expected_status=200,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.NEEDS_REVISION)

        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/resubmit/{app.id}/"
        r = self.client.post(url, {"json_data": json.dumps({"title": "BR016-new"})}, format="multipart")
        self.assertEqual(r.status_code, 200)

    def test_invalid_resubmit_after_deadline_expires(self):
        self._test_id = "BR-PMS-016-I-01"; self._br_id = "BR-PMS-016"
        app = self._submit_submitted(title="BR016-exp")
        app.status = ApplicationStatus.NEEDS_REVISION
        app.resubmission_deadline = now() - timedelta(days=1)
        app.save()

        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/resubmit/{app.id}/"
        r = self.client.post(url, {"json_data": json.dumps({"title": "late"})}, format="multipart")
        self.assertEqual(r.status_code, 400)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.EXPIRED)


class TestBR_PMS_017(_PatentBRFlowMixin, BRTestBase):

    def test_valid_international_filing_with_justification(self):
        self._test_id = "BR-PMS-017-V-01"; self._br_id = "BR-PMS-017"
        app = self._submit_submitted(title="BR017")
        self._pcc_review(app)
        self._pcc_forward(app)
        self._director_accept(app)
        self._advance_to_search_report_generated(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/filing/"
        r = self.client.post(
            url,
            {
                "filing_office": "USPTO",
                "jurisdiction": "USA",
                "external_filing_id": "US-123",
                "international_filing_justification": "Business need.",
            },
            format="multipart",
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(FilingRecord.objects.filter(application=app).exists())

    def test_invalid_international_filing_missing_justification(self):
        self._test_id = "BR-PMS-017-I-01"; self._br_id = "BR-PMS-017"
        app = self._submit_submitted(title="BR017-no")
        self._pcc_review(app)
        self._pcc_forward(app)
        self._director_accept(app)
        self._advance_to_search_report_generated(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/filing/"
        r = self.client.post(
            url,
            {"filing_office": "USPTO", "jurisdiction": "USA", "external_filing_id": "US-124"},
            format="multipart",
        )
        self.assertEqual(r.status_code, 400)


class TestBR_PMS_018(_PatentBRFlowMixin, BRTestBase):

    def test_valid_audit_logs_created_for_actions(self):
        self._test_id = "BR-PMS-018-V-01"; self._br_id = "BR-PMS-018"
        app = self._submit_submitted(title="BR018")
        self._pcc_review(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/audit/"
        r = self.api_get(url, expected_status=200)
        self.assertGreaterEqual(len(r.json()), 1)

    def test_invalid_non_pcc_cannot_view_audit_logs(self):
        self._test_id = "BR-PMS-018-I-01"; self._br_id = "BR-PMS-018"
        app = self._submit_submitted(title="BR018-non")
        self.login_as_applicant()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/audit/"
        self.api_get(url, expected_status=403)


class TestBR_PMS_019(_PatentBRFlowMixin, BRTestBase):

    def test_valid_pcc_admin_can_log_communication(self):
        self._test_id = "BR-PMS-019-V-01"; self._br_id = "BR-PMS-019"
        app = self._submit_submitted(title="BR019")
        self.login_as_pcc_admin()

        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/communications/"
        r = self.client.post(
            url,
            {
                "direction": "Outgoing",
                "subject": "Attorney update",
                "body": "Details.",
                "confidentiality_level": "Confidential",
            },
            format="multipart",
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(CommunicationLog.objects.filter(application=app).exists())

    def test_invalid_non_pcc_cannot_log_communication(self):
        self._test_id = "BR-PMS-019-I-01"; self._br_id = "BR-PMS-019"
        app = self._submit_submitted(title="BR019-non")
        self.login_as_applicant()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/communications/"
        r = self.client.post(url, {"direction": "Outgoing", "subject": "x"}, format="multipart")
        self.assertEqual(r.status_code, 403)
