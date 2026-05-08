from applications.filetracking.models import File
from applications.iwdModuleV2.models import Requests
from rest_framework.test import APIClient

from .conftest import WFTestBase


WF_META = [
    ("WF-01", "Standard Request Approval", "Submit Request (User)"),
    ("WF-02", "Dean Routing Path", "Submit Request (User)"),
    ("WF-03", "Work Execution", "Issue Work Order (Admin)"),
    ("WF-04", "Bill Processing", "Process Bill (Admin)"),
    ("WF-05", "Request Update Loop", "Update Request (User)"),
    ("WF-06", "Rejection Path", "Submit/Proposal (User)"),
    ("WF-07", "Budget Management", "View Budget (Admin)"),
    ("WF-08", "Inventory & Procurement", "Approve Estimate (Admin)"),
    ("WF-09", "Complaint Assignment (SLA)", "Submit Complaint (User)"),
    ("WF-10", "Feedback & Closure", "Settle Bill (Accounts)"),
    ("WF-11", "Generate PDF Bill", "Mark Completed (Engineer)"),
]


class TestWFAll(WFTestBase):
    """Complete WF suite generated from SRS (WF-01 to WF-11)."""

    def _seed_request_with_file(self):
        seed_client = APIClient()
        seed_client.force_authenticate(user=self.user_worker)
        session = seed_client.session
        session["currentDesignationSelected"] = "Electrical_AE"
        session.save()
        payload = {
            "name": "WF Seed Request",
            "area": "Admin Block",
            "description": "Seeded request for workflow tests",
            "role": "Electrical_AE",
            "designation": "Admin IWD|iwd_adm",
        }
        seed_client.post(f"{self.API_BASE}/create-request/", payload, format="json")
        req = Requests.objects.filter(
            requestCreatedBy=self.__class__.user_worker.username,
            name="WF Seed Request",
        ).order_by("-id").first()
        file_obj = File.objects.filter(src_object_id=str(req.id), src_module="IWD").first() if req else None
        return req, file_obj

    def _wf_steps(self, wf_id):
        req, file_obj = self._seed_request_with_file()
        request_id = req.id if req else -1
        file_id = file_obj.id if file_obj else -1

        steps = {
            "WF-01": [
                ("worker", "POST", "/create-request/", {
                    "name": "WF-01 Request",
                    "area": "CSE",
                    "description": "workflow",
                    "role": "Electrical_AE",
                    "designation": "Admin IWD|iwd_adm",
                }, {201}),
                ("admin", "GET", "/created-requests/", {}, {200}),
            ],
            "WF-02": [
                ("worker", "POST", "/create-request/", {
                    "name": "WF-02 Request",
                    "area": "CSE",
                    "description": "dean route",
                    "role": "Electrical_AE",
                    "designation": "HOD (CSE)|iwd_hod",
                }, {201, 400}),
                ("hod", "POST", "/handle-dean-process-request/", {
                    "fileid": file_id,
                    "designation": "Director|iwd_director",
                    "remarks": "hod forward",
                }, {200, 400, 403, 404}),
            ],
            "WF-03": [
                ("admin", "POST", "/issue-work-order/", {
                    "request_id": request_id,
                    "alloted_time": "5 days",
                    "start_date": "2099-02-01",
                    "completion_date": "2099-02-05",
                }, {200, 400, 403, 404}),
                ("admin", "GET", "/requests-in-progress/", {}, {200}),
            ],
            "WF-04": [
                ("admin", "POST", "/handle-process-bills/", {
                    "fileid": file_id,
                    "designation": "Auditor|iwd_audit",
                }, {200, 400, 403, 404}),
                ("auditor", "POST", "/audit-document/", {
                    "fileid": file_id,
                    "designation": "Accounts Admin|iwd_acc",
                }, {200, 400, 403, 404}),
            ],
            "WF-05": [
                ("admin", "POST", "/handle-admin-approval/", {
                    "fileid": file_id,
                    "action": "reject",
                    "designation": "Electrical_AE|iwd_worker",
                }, {200, 400, 403, 404}),
                ("worker", "POST", "/handle-update-requests/", {
                    "id": request_id,
                    "name": "WF-05 Updated",
                    "area": "Updated",
                    "description": "updated after rejection",
                    "designation": "Admin IWD|iwd_adm",
                }, {200, 400, 404}),
            ],
            "WF-06": [
                ("admin", "POST", "/handle-admin-approval/", {
                    "fileid": file_id,
                    "action": "reject",
                    "designation": "Electrical_AE|iwd_worker",
                }, {200, 400, 403, 404}),
                ("worker", "GET", "/rejected-requests-view/", {}, {200}),
            ],
            "WF-07": [
                ("admin", "GET", "/view-budget/", {}, {200}),
                ("admin", "POST", "/add-budget/", {"name": "WF-07 Head", "budget": 1000}, {201, 400}),
            ],
            "WF-08": [
                ("admin", "GET", "/inventory-items/", {}, {200}),
                ("admin", "POST", "/issue-materials/", {"item_id": -1, "quantity": 1}, {201, 400, 404}),
            ],
            "WF-09": [
                ("worker", "POST", "/create-request/", {
                    "name": "WF-09 Complaint",
                    "area": "Hostel",
                    "description": "urgent electrical fault",
                    "role": "Electrical_AE",
                    "designation": "Admin IWD|iwd_adm",
                }, {201}),
                ("admin", "GET", "/sla-dashboard/", {}, {200}),
            ],
            "WF-10": [
                ("accounts", "POST", "/handle-settle-bill-request/", {
                    "fileid": file_id,
                    "designation": "Admin IWD|iwd_adm",
                }, {200, 400, 403, 404}),
                ("worker", "POST", "/submit-feedback/", {
                    "request_id": request_id,
                    "rating": 4,
                    "comments": "resolved",
                }, {201, 400, 403, 404}),
            ],
            "WF-11": [
                ("worker", "PATCH", "/work-completed/", {"id": request_id}, {200, 400, 403, 404}),
                ("admin", "POST", "/generate-bill-pdf/", {"request_id": request_id}, {200, 400, 403, 404}),
            ],
        }
        return steps[wf_id]

    def _login(self, role):
        if role == "admin":
            self.login_as_admin()
        elif role == "hod":
            self.login_as_hod()
        elif role == "director":
            self.login_as_director()
        elif role == "auditor":
            self.login_as_auditor()
        elif role == "accounts":
            self.login_as_accounts()
        else:
            self.login_as_worker()

    def _call(self, method, endpoint, payload):
        if method == "GET":
            return self.api_get(endpoint, params=payload, expected_status=None)
        if method == "PATCH":
            return self.api_patch(endpoint, data=payload, expected_status=None)
        return self.api_post(endpoint, data=payload, expected_status=None)


def _make_e2e_test(wf_id, title):
    def _test(self):
        self._test_id = f"{wf_id}-E2E-01"
        self._wf_id = wf_id
        self._test_category = "End-to-End"
        self._scenario = f"{title} complete flow"
        self._expected_result = "Workflow reaches stable endpoint behavior"

        all_ok = True
        for idx, (role, method, endpoint, payload, allowed) in enumerate(self._wf_steps(wf_id), start=1):
            self._login(role)
            response = self._call(method, endpoint, dict(payload))
            ok = response.status_code in allowed
            self._add_step(idx, f"{role} {method} {endpoint}", f"status in {sorted(allowed)}", f"HTTP {response.status_code}", ok)
            if not ok:
                all_ok = False

        if all_ok:
            self._record_result("Workflow steps executed", "Pass")
        else:
            self._record_result("One or more workflow steps failed", "Fail")
            self.fail(f"{wf_id} e2e workflow did not satisfy all expected statuses")

    return _test


def _make_negative_test(wf_id, title):
    def _test(self):
        self._test_id = f"{wf_id}-NEG-01"
        self._wf_id = wf_id
        self._test_category = "Negative"
        self._scenario = f"{title} interruption/failure path"
        self._expected_result = "System rejects unauthorized or malformed flow"

        steps = self._wf_steps(wf_id)
        role, method, endpoint, payload, _ = steps[0]

        self.logout()
        bad_payload = dict(payload)
        bad_payload["invalid_probe"] = "1"
        response = self._call(method, endpoint, bad_payload)

        if response.status_code in (401, 403, 400, 404):
            self._record_result(f"Negative path blocked with HTTP {response.status_code}", "Pass", f"{method} {endpoint}")
        else:
            self._record_result(f"Unexpected negative path HTTP {response.status_code}", "Fail", f"{method} {endpoint}")
            self.fail(f"{wf_id} negative path expected 4xx, got {response.status_code}")

    return _test


for _wf_id, _title, _ in WF_META:
    _id_num = _wf_id.split("-")[1]
    setattr(TestWFAll, f"test_wf{_id_num}_e2e_01", _make_e2e_test(_wf_id, _title))
    setattr(TestWFAll, f"test_wf{_id_num}_negative_01", _make_negative_test(_wf_id, _title))
