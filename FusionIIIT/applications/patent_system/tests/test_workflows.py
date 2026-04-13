import json
from datetime import timedelta

from django.utils.timezone import now

from applications.patent_system.models import Application, ApplicationStatus, BudgetDecision

from .base import WFTestBase


class _PatentWFBaseMixin:
    def _submit(self, *, title="WF Patent", inventor_shares=None):
        self.login_as_applicant()
        payload = self.make_submit_payload(title=title, inventor_shares=inventor_shares)
        resp, app_id = self.post_submit_application(payload)
        self.assertEqual(resp.status_code, 201, msg=getattr(resp, "content", b"")[:500])
        return Application.objects.get(id=app_id)

    def _consent_all(self, app: Application):
        self.login_as_applicant()
        self.api_post(self.API_PREFIX + f"applicant/applications/{app.id}/consent/", {}, expected_status=200)
        self.login_as_coinventor()
        self.api_post(self.API_PREFIX + f"applicant/applications/{app.id}/consent/", {}, expected_status=200)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.SUBMITTED)
        return app

    def _review_and_forward(self, app: Application):
        self.login_as_pcc_admin()
        self.api_post(
            self.API_PREFIX + f"pccAdmin/applications/new/review/{app.id}/",
            {"comments": "Reviewed"},
            expected_status=200,
        )
        self.api_post(
            self.API_PREFIX + f"pccAdmin/applications/new/forward/{app.id}/",
            {"comments": "Forwarded"},
            expected_status=200,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.FORWARDED)
        return app

    def _director_accept(self, app: Application):
        self.login_as_director()
        self.api_post(
            self.API_PREFIX + "director/application/accept",
            {"application_id": app.id, "comments": "Approved"},
            expected_status=200,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.APPROVED)
        return app

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


# =========================
# WF-101: Submit Patent Application
# =========================
class TestPMS_WF_101(_PatentWFBaseMixin, WFTestBase):

    def test_e2e_submit_application(self):
        self._test_id = "PMS-WF-101-E2E-01"; self._wf_id = "PMS-WF-101"
        app = self._submit(title="WF101")
        self.assertEqual(app.status, ApplicationStatus.PENDING_INVENTOR_CONSENT)

    def test_negative_unauthorized(self):
        self._test_id = "PMS-WF-101-NEG-01"; self._wf_id = "PMS-WF-101"
        self.logout()
        payload = self.make_submit_payload(title="WF101-unauth")
        resp, _ = self.post_submit_application(payload)
        self.assertEqual(resp.status_code, 401)


# =========================
# WF-201: Revision Workflow
# =========================
class TestPMS_WF_201(_PatentWFBaseMixin, WFTestBase):

    def test_e2e_resubmit(self):
        self._test_id = "PMS-WF-201-E2E-01"; self._wf_id = "PMS-WF-201"
        app = self._consent_all(self._submit(title="WF201"))

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
        r = self.client.post(url, {"json_data": json.dumps({"title": "WF201-new"})}, format="multipart")
        self.assertEqual(r.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.RESUBMITTED)

    def test_negative_expired(self):
        self._test_id = "PMS-WF-201-NEG-01"; self._wf_id = "PMS-WF-201"
        app = self._consent_all(self._submit(title="WF201-exp"))
        app.status = ApplicationStatus.NEEDS_REVISION
        app.resubmission_deadline = now() - timedelta(days=1)
        app.save()

        self.login_as_applicant()
        url = self.API_PREFIX + f"applicant/applications/resubmit/{app.id}/"
        r = self.client.post(url, {"json_data": json.dumps({"title": "late"})}, format="multipart")
        self.assertEqual(r.status_code, 400)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.EXPIRED)


# =========================
# WF-301: Budget Workflow
# =========================
class TestPMS_WF_301(_PatentWFBaseMixin, WFTestBase):

    def test_e2e_budget_approval(self):
        self._test_id = "PMS-WF-301-E2E-01"; self._wf_id = "PMS-WF-301"
        app = self._consent_all(self._submit(title="WF301"))

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/budget/"
        r = self.api_post(url, {"filing_cost": 1000, "attorney_fees": 0, "administrative_cost": 0}, expected_status=200)
        self.assertEqual(r.json().get("decision"), BudgetDecision.APPROVED_PCC)

    def test_negative_budget_denied(self):
        self._test_id = "PMS-WF-301-NEG-01"; self._wf_id = "PMS-WF-301"
        app = self._consent_all(self._submit(title="WF301-escalate"))

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/budget/"
        r = self.api_post(url, {"filing_cost": 999999, "attorney_fees": 0, "administrative_cost": 0}, expected_status=200)
        self.assertEqual(r.json().get("decision"), BudgetDecision.ESCALATED)

        self.login_as_director()
        durl = self.API_PREFIX + f"director/budget/{app.id}/decision/"
        self.api_post(durl, {"decision": "Reject", "remarks": "no"}, expected_status=200)


# =========================
# WF-401: Director Assignment (forwarding)
# =========================
class TestPMS_WF_401(_PatentWFBaseMixin, WFTestBase):

    def test_e2e_assignment(self):
        self._test_id = "PMS-WF-401-E2E-01"; self._wf_id = "PMS-WF-401"
        app = self._consent_all(self._submit(title="WF401"))
        self._review_and_forward(app)
        self._director_accept(app)

    def test_negative_no_director(self):
        self._test_id = "PMS-WF-401-NEG-01"; self._wf_id = "PMS-WF-401"
        app = self._consent_all(self._submit(title="WF401-non"))
        self._review_and_forward(app)

        self.login_as_applicant()
        self.api_post(
            self.API_PREFIX + "director/application/accept",
            {"application_id": app.id, "comments": "Approved"},
            expected_status=403,
        )


# =========================
# WF-501: Post Grant Workflow (ongoing status transitions)
# =========================
class TestPMS_WF_501(_PatentWFBaseMixin, WFTestBase):

    def test_e2e_fee_payment(self):
        self._test_id = "PMS-WF-501-E2E-01"; self._wf_id = "PMS-WF-501"
        app = self._consent_all(self._submit(title="WF501"))
        self._review_and_forward(app)
        self._director_accept(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/ongoing/changeStatus/{app.id}/"
        self.api_post(url, {"next_status": ApplicationStatus.PATENTABILITY_CHECK_STARTED}, expected_status=200)

    def test_negative_fee_missed(self):
        self._test_id = "PMS-WF-501-NEG-01"; self._wf_id = "PMS-WF-501"
        app = self._consent_all(self._submit(title="WF501-bad"))
        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/ongoing/changeStatus/{app.id}/"
        self.api_post(url, {"next_status": ApplicationStatus.PATENT_FILED}, expected_status=400)


# =========================
# WF-601: External Filing Workflow
# =========================
class TestPMS_WF_601(_PatentWFBaseMixin, WFTestBase):

    def test_e2e_filing(self):
        self._test_id = "PMS-WF-601-E2E-01"; self._wf_id = "PMS-WF-601"
        app = self._consent_all(self._submit(title="WF601"))
        self._review_and_forward(app)
        self._director_accept(app)
        self._advance_to_search_report_generated(app)

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/filing/"
        r = self.client.post(
            url,
            {"filing_office": "Indian Patent Office", "jurisdiction": "India", "external_filing_id": "IN-001"},
            format="multipart",
        )
        self.assertEqual(r.status_code, 201)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.PATENT_FILED)

    def test_negative_filing_error(self):
        self._test_id = "PMS-WF-601-NEG-01"; self._wf_id = "PMS-WF-601"
        app = self._consent_all(self._submit(title="WF601-early"))

        self.login_as_pcc_admin()
        url = self.API_PREFIX + f"pccAdmin/applications/{app.id}/filing/"
        r = self.client.post(
            url,
            {"filing_office": "Indian Patent Office", "jurisdiction": "India", "external_filing_id": "IN-002"},
            format="multipart",
        )
        self.assertEqual(r.status_code, 400)