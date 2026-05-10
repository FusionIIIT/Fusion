import tempfile
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from applications.audit_account.models import (
    AuditObservation,
    DepartmentBudget,
    Request,
    RequestStatus,
    TARequestStatus,
    TravelAllowance,
)
from applications.audit_account.tasks import run_audit_account_escalations
from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class AuditAccountApiTests(APITestCase):
    def setUp(self):
        self.department = DepartmentInfo.objects.create(name="CSE")
        self.designations = {
            "finance": Designation.objects.create(name="finance", full_name="Finance"),
            "hod": Designation.objects.create(name="hod", full_name="Head"),
            "dean": Designation.objects.create(name="dean", full_name="Dean"),
            "director": Designation.objects.create(name="director", full_name="Director"),
            "auditor": Designation.objects.create(name="auditor", full_name="Auditor"),
        }
        self.employee = self._make_user("employee", "faculty")
        self.finance = self._make_user("finance", "staff", "finance")
        self.hod = self._make_user("hod", "faculty", "hod")
        self.dean = self._make_user("dean", "faculty", "dean")
        self.director = self._make_user("director", "staff", "director")
        self.auditor = self._make_user("auditor", "staff", "auditor")
        DepartmentBudget.objects.create(
            department="CSE",
            budget_head="Operations",
            allocated_amount="100000",
            remaining_amount="80000",
        )
        self.client = APIClient()

    def _make_user(self, username, user_type, designation=None):
        user = User.objects.create_user(username=username, password="pass123")
        ExtraInfo.objects.create(
            id=f"{username}-id",
            user=user,
            user_type=user_type,
            department=self.department,
        )
        if designation:
            HoldsDesignation.objects.create(
                user=user,
                working=user,
                designation=self.designations[designation],
            )
        return user

    def _file(self, name="proof.pdf"):
        return SimpleUploadedFile(name, b"file-content", content_type="application/pdf")

    def test_request_workflow_routes_and_closes(self):
        self.client.force_authenticate(self.employee)
        draft = self.client.post(
            "/api/audit-account/requests/draft/",
            {
                "type": "EXPENSE",
                "amount": "20000",
                "department": "CSE",
                "budget_head": "Operations",
                "budget_remaining": "90000",
                "description": "Lab purchase",
                "attachments": [self._file()],
            },
            format="multipart",
        )
        self.assertEqual(draft.status_code, 201)
        request_id = draft.data["id"]

        submit = self.client.post("/api/audit-account/requests/submit/", {"id": request_id})
        self.assertEqual(submit.status_code, 200)
        self.assertEqual(submit.data["status"], RequestStatus.SUBMITTED)

        self.client.force_authenticate(self.finance)
        validated = self.client.post(
            "/api/audit-account/requests/status/",
            {"id": request_id, "action": "VALIDATE", "remarks": "Checked"},
        )
        self.assertEqual(validated.status_code, 200)
        self.assertEqual(validated.data["status"], RequestStatus.FINANCE_VALIDATED)
        self.assertEqual(validated.data["current_approver_role"], "hod")

        self.client.force_authenticate(self.hod)
        approved = self.client.post(
            "/api/audit-account/requests/status/",
            {"id": request_id, "action": "APPROVE", "remarks": "Approved"},
        )
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.data["status"], RequestStatus.ESCALATED)
        self.assertEqual(approved.data["current_approver_role"], "director")

        self.client.force_authenticate(self.director)
        director_approved = self.client.post(
            "/api/audit-account/requests/status/",
            {"id": request_id, "action": "APPROVE", "remarks": "Approved by Director"},
        )
        self.assertEqual(director_approved.status_code, 200)
        self.assertEqual(director_approved.data["status"], RequestStatus.APPROVED)

        self.client.force_authenticate(self.finance)
        closed = self.client.post(
            "/api/audit-account/requests/status/",
            {"id": request_id, "action": "CLOSE"},
        )
        self.assertEqual(closed.status_code, 200)
        self.assertEqual(closed.data["status"], RequestStatus.CLOSED)

    def test_budget_anomaly_creates_observation(self):
        req = Request.objects.create(
            type="EXPENSE",
            amount="90000",
            department="CSE",
            budget_head="Operations",
            budget_remaining="1000",
            created_by=self.employee.id,
            created_by_user=self.employee,
            document_names=["proof.pdf"],
            status=RequestStatus.SUBMITTED,
        )
        self.client.force_authenticate(self.finance)
        response = self.client.post(
            "/api/audit-account/requests/status/",
            {"id": req.id, "action": "VALIDATE", "remarks": "Over budget"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], RequestStatus.ESCALATED)
        self.assertTrue(
            AuditObservation.objects.filter(request=req, title__icontains="Budget").exists()
        )

    def test_ta_workflow_handles_normal_and_high_value(self):
        self.client.force_authenticate(self.employee)
        low = self.client.post(
            "/api/audit-account/ta/create/",
            {
                "department": "CSE",
                "travel_from": "Jabalpur",
                "travel_to": "Delhi",
                "purpose": "Workshop",
                "amount_claimed": "10000",
                "attachments": [self._file("ticket.pdf")],
            },
            format="multipart",
        )
        self.assertEqual(low.status_code, 201)

        self.client.force_authenticate(self.finance)
        low_verify = self.client.post(
            "/api/audit-account/ta/status/",
            {"id": low.data["id"], "action": "VERIFY", "remarks": "Verified"},
        )
        self.assertEqual(low_verify.status_code, 200)
        self.assertEqual(low_verify.data["status"], TARequestStatus.CLOSED)

        self.client.force_authenticate(self.employee)
        high = self.client.post(
            "/api/audit-account/ta/create/",
            {
                "department": "CSE",
                "travel_from": "Jabalpur",
                "travel_to": "Mumbai",
                "purpose": "Conference",
                "amount_claimed": "60000",
                "attachments": [self._file("bill.pdf")],
            },
            format="multipart",
        )
        self.assertEqual(high.status_code, 201)

        self.client.force_authenticate(self.finance)
        high_verify = self.client.post(
            "/api/audit-account/ta/status/",
            {"id": high.data["id"], "action": "VERIFY", "remarks": "Checked"},
        )
        self.assertEqual(high_verify.status_code, 200)
        self.assertEqual(high_verify.data["status"], TARequestStatus.VERIFIED)

        self.client.force_authenticate(self.dean)
        approved = self.client.post(
            "/api/audit-account/ta/status/",
            {"id": high.data["id"], "action": "APPROVE", "remarks": "Approved"},
        )
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.data["status"], TARequestStatus.APPROVED)

    def test_observation_lifecycle(self):
        req = Request.objects.create(
            type="EXPENSE",
            amount="1000",
            department="CSE",
            budget_head="Operations",
            budget_remaining="1000",
            created_by=self.employee.id,
            created_by_user=self.employee,
            document_names=["proof.pdf"],
        )
        self.client.force_authenticate(self.auditor)
        created = self.client.post(
            "/api/audit-account/observations/create/",
            {
                "target_workflow": "EXPENSE",
                "request": req.id,
                "title": "Need details",
                "details": "Share invoices",
                "attachments": [self._file("obs.pdf")],
            },
            format="multipart",
        )
        self.assertEqual(created.status_code, 201)
        obs_id = created.data["id"]

        self.client.force_authenticate(self.employee)
        responded = self.client.post(
            "/api/audit-account/observations/status/",
            {
                "id": obs_id,
                "action": "RESPOND",
                "response_text": "Attached.",
                "response_attachments": [self._file("reply.pdf")],
            },
            format="multipart",
        )
        self.assertEqual(responded.status_code, 200)
        self.assertEqual(responded.data["status"], "RESPONDED")

        self.client.force_authenticate(self.auditor)
        closed = self.client.post(
            "/api/audit-account/observations/status/",
            {"id": obs_id, "action": "CLOSE", "remarks": "Done"},
        )
        self.assertEqual(closed.status_code, 200)
        reopened = self.client.post(
            "/api/audit-account/observations/status/",
            {"id": obs_id, "action": "REOPEN", "remarks": "Need one more file"},
        )
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.data["status"], "OPEN")

    def test_unauthorized_views_and_actions_are_restricted(self):
        req = Request.objects.create(
            type="EXPENSE",
            amount="2000",
            department="CSE",
            budget_head="Operations",
            budget_remaining="3000",
            created_by=self.employee.id,
            created_by_user=self.employee,
            document_names=["proof.pdf"],
            status=RequestStatus.FINANCE_VALIDATED,
            current_approver_role="hod",
        )
        observation = AuditObservation.objects.create(
            target_workflow="EXPENSE",
            request=req,
            title="Need invoice",
            details="Upload the final invoice copy.",
            raised_by=self.auditor,
        )

        self.client.force_authenticate(self.employee)
        view_response = self.client.get("/api/audit-account/requests/", {"view": "director"})
        self.assertEqual(view_response.status_code, 403)

        reject_response = self.client.post(
            "/api/audit-account/requests/status/",
            {"id": req.id, "action": "REJECT", "remarks": "Not allowed"},
        )
        self.assertEqual(reject_response.status_code, 403)

        self.client.force_authenticate(self.finance)
        respond_response = self.client.post(
            "/api/audit-account/observations/status/",
            {
                "id": observation.id,
                "action": "RESPOND",
                "response_text": "Trying to respond without assignment.",
                "response_attachments": [self._file("reply.pdf")],
            },
            format="multipart",
        )
        self.assertEqual(respond_response.status_code, 403)

    def test_timeout_task_escalates_request_and_ta(self):
        req = Request.objects.create(
            type="EXPENSE",
            amount="5000",
            department="CSE",
            budget_head="Operations",
            budget_remaining="7000",
            created_by=self.employee.id,
            created_by_user=self.employee,
            document_names=["proof.pdf"],
            status=RequestStatus.FINANCE_VALIDATED,
            current_approver_role="hod",
            assigned_at=timezone.now() - timedelta(hours=30),
        )
        ta = TravelAllowance.objects.create(
            employee=self.employee,
            employee_name=self.employee.username,
            department="CSE",
            travel_from="A",
            travel_to="B",
            purpose="Trip",
            amount_claimed="60000",
            document_names=["bill.pdf"],
            status=TARequestStatus.VERIFIED,
            high_value=True,
            current_approver_role="dean",
            assigned_at=timezone.now() - timedelta(hours=30),
        )
        run_audit_account_escalations()
        req.refresh_from_db()
        ta.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.ESCALATED)
        self.assertEqual(req.current_approver_role, "dean")
        self.assertEqual(ta.current_approver_role, "director")
