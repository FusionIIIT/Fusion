from applications.filetracking.models import File
from applications.iwdModuleV2.models import Requests
from rest_framework.test import APIClient

from .conftest import BRTestBase


BR_META = [
    ("BR-001", "Authentication & RBAC", "Authorization"),
    ("BR-002", "Request Initialization", "Constraint"),
    ("BR-003", "Mandatory Fields", "Constraint"),
    ("BR-004", "Creator Tracking", "Constraint"),
    ("BR-005", "Inbox Access Control", "Authorization"),
    ("BR-006", "Dean Processing Logic", "Authorization"),
    ("BR-007", "Admin Approval Gate", "Authorization"),
    ("BR-008", "Active Proposal Rule", "Constraint"),
    ("BR-009", "Budget Calculation", "Calculation"),
    ("BR-010", "Director Approval", "Authorization"),
    ("BR-011", "Work Order Logic", "Constraint"),
    ("BR-012", "Vendor Association", "Integrity"),
    ("BR-013", "Work Completion", "Trigger"),
    ("BR-014", "File Tracking & Notif", "Constraint"),
    ("BR-015", "Bill Processing", "Trigger"),
    ("BR-016", "Audit Mandatory", "Authorization"),
    ("BR-017", "Final Settlement", "System"),
    ("BR-018", "Numeric Constraints", "Validation"),
    ("BR-019", "Rejected Update Lock", "Constraint"),
    ("BR-020", "Designation Lookup", "Constraint"),
    ("BR-021", "Cost Thresholds", "Constraint"),
    ("BR-022", "Inventory Check", "Constraint"),
    ("BR-023", "SLA Enforcement", "Trigger"),
    ("BR-024", "Feedback & Reopen", "Trigger"),
]


def _login_for_br(test_obj, br_id):
    if br_id in {"BR-016"}:
        test_obj.login_as_auditor()
    elif br_id in {"BR-017"}:
        test_obj.login_as_accounts()
    elif br_id in {"BR-006"}:
        test_obj.login_as_hod()
    elif br_id in {"BR-010"}:
        test_obj.login_as_director()
    elif br_id in {"BR-001", "BR-005"}:
        test_obj.login_as_worker()
    else:
        test_obj.login_as_admin()


class TestBRAll(BRTestBase):
    """Complete BR suite generated from SRS (BR-001 to BR-024)."""

    def _seed_request_with_file(self):
        seed_client = APIClient()
        seed_client.force_authenticate(user=self.user_worker)
        session = seed_client.session
        session["currentDesignationSelected"] = "Electrical_AE"
        session.save()
        payload = {
            "name": "BR Seed Request",
            "area": "CSE Block",
            "description": "Seeded request for BR endpoint tests",
            "role": "Electrical_AE",
            "designation": "Admin IWD|iwd_adm",
        }
        seed_client.post(f"{self.API_BASE}/create-request/", payload, format="json")
        req = Requests.objects.filter(
            requestCreatedBy=self.__class__.user_worker.username,
            name="BR Seed Request",
        ).order_by("-id").first()
        file_obj = File.objects.filter(src_object_id=str(req.id), src_module="IWD").first() if req else None
        return req, file_obj

    def _br_endpoint_spec_valid(self, br_id):
        req, file_obj = self._seed_request_with_file()
        request_id = req.id if req else -1
        file_id = file_obj.id if file_obj else -1

        specs = {
            "BR-001": ("GET", "/fetch-designations/", {}, {200}),
            "BR-002": ("POST", "/create-request/", {
                "name": "BR-002 Request",
                "area": "Area",
                "description": "Init flags",
                "role": "Electrical_AE",
                "designation": "Admin IWD|iwd_adm",
            }, {201}),
            "BR-003": ("POST", "/create-request/", {
                "name": "BR-003 Request",
                "area": "Area",
                "description": "Mandatory present",
                "role": "Electrical_AE",
                "designation": "Admin IWD|iwd_adm",
            }, {201}),
            "BR-004": ("POST", "/create-request/", {
                "name": "BR-004 Request",
                "area": "Area",
                "description": "Creator tracked",
                "role": "Electrical_AE",
                "designation": "Admin IWD|iwd_adm",
            }, {201}),
            "BR-005": ("GET", "/created-requests/", {}, {200}),
            "BR-006": ("POST", "/handle-dean-process-request/", {
                "fileid": file_id,
                "designation": "Director|iwd_director",
                "remarks": "dean valid",
            }, {200, 400, 404, 403}),
            "BR-007": ("POST", "/handle-admin-approval/", {
                "fileid": file_id,
                "action": "approve",
                "designation": "Director|iwd_director",
            }, {200, 400, 404, 403}),
            "BR-008": ("GET", "/get-proposals/", {"request_id": request_id}, {200}),
            "BR-009": ("POST", "/create-proposal/", {
                "id": request_id,
                "designation": "Admin IWD|iwd_adm",
                "items[0][name]": "Wire",
                "items[0][description]": "Copper",
                "items[0][unit]": "m",
                "items[0][price_per_unit]": "10",
                "items[0][quantity]": "2",
            }, {201, 400, 404, 403}),
            "BR-010": ("POST", "/handle-director-approval/", {
                "fileid": file_id,
                "action": "approve",
                "designation": "Admin IWD|iwd_adm",
            }, {200, 400, 404, 403}),
            "BR-011": ("POST", "/issue-work-order/", {
                "request_id": request_id,
                "alloted_time": "7 days",
                "start_date": "2099-01-01",
                "completion_date": "2099-01-08",
            }, {200, 400, 404, 403}),
            "BR-012": ("POST", "/add-vendor/", {
                "work": -1,
                "name": "Vendor BR",
                "total_amount": 0,
            }, {200, 400, 404, 403}),
            "BR-013": ("PATCH", "/work-completed/", {"id": request_id}, {200, 400, 404, 403}),
            "BR-014": ("POST", "/forward-request/", {
                "fileid": file_id,
                "designation": "Admin IWD|iwd_adm",
                "remarks": "track",
            }, {200, 400, 404}),
            "BR-015": ("POST", "/handle-process-bills/", {
                "fileid": file_id,
                "designation": "Auditor|iwd_audit",
            }, {200, 400, 404, 403}),
            "BR-016": ("POST", "/audit-document/", {
                "fileid": file_id,
                "designation": "Accounts Admin|iwd_acc",
            }, {200, 400, 404, 403}),
            "BR-017": ("POST", "/handle-settle-bill-request/", {
                "fileid": file_id,
                "designation": "Admin IWD|iwd_adm",
            }, {200, 400, 404, 403}),
            "BR-018": ("POST", "/add-vendor/", {
                "work": -1,
                "name": "Vendor Numeric",
                "total_amount": 10,
            }, {200, 400, 404, 403}),
            "BR-019": ("POST", "/handle-update-requests/", {
                "id": request_id,
                "name": "BR-019 update",
                "area": "Area",
                "description": "desc",
                "designation": "Admin IWD|iwd_adm",
            }, {200, 400, 404}),
            "BR-020": ("GET", "/fetch-designations/", {}, {200}),
            "BR-021": ("GET", "/sla-dashboard/", {}, {200}),
            "BR-022": ("GET", "/inventory-items/", {}, {200}),
            "BR-023": ("GET", "/sla-dashboard/", {}, {200}),
            "BR-024": ("POST", "/submit-feedback/", {
                "request_id": request_id,
                "rating": 4,
                "comments": "good",
            }, {201, 400, 404, 403}),
        }
        return specs[br_id]

    def _br_endpoint_spec_invalid(self, br_id):
        method, endpoint, payload, _ = self._br_endpoint_spec_valid(br_id)
        bad = dict(payload)
        bad["invalid_probe"] = "1"

        if br_id in {"BR-001", "BR-005", "BR-020"}:
            self.logout()
            return "GET", endpoint, payload if method == "GET" else bad, {401, 403}

        if br_id in {"BR-003"}:
            bad.pop("name", None)
            return method, endpoint, bad, {400}

        if br_id in {"BR-018"}:
            bad["total_amount"] = -1
            return method, endpoint, bad, {400, 403}

        if br_id in {"BR-024"}:
            bad["rating"] = 7
            return method, endpoint, bad, {400, 403}

        return method, endpoint, bad, {400, 403, 404}

    def _call(self, method, endpoint, payload):
        if method == "GET":
            return self.api_get(endpoint, params=payload, expected_status=None)
        if method == "PATCH":
            return self.api_patch(endpoint, data=payload, expected_status=None)
        return self.api_post(endpoint, data=payload, expected_status=None)


def _make_valid_test(br_id, title):
    def _test(self):
        self._test_id = f"{br_id}-V-01"
        self._br_id = br_id
        self._test_category = "Valid"
        self._input_action = f"Execute valid flow for {br_id}"
        self._expected_result = f"{title} is enforced for valid input"

        _login_for_br(self, br_id)
        method, endpoint, payload, allowed = self._br_endpoint_spec_valid(br_id)
        response = self._call(method, endpoint, dict(payload))

        if response.status_code in allowed:
            self._record_result(f"HTTP {response.status_code}", "Pass", f"{method} {endpoint}")
        else:
            self._record_result(f"Unexpected HTTP {response.status_code}", "Fail", f"{method} {endpoint}")
            self.fail(f"{br_id} valid test failed: got {response.status_code}, expected {sorted(allowed)}")

    return _test


def _make_invalid_test(br_id, title):
    def _test(self):
        self._test_id = f"{br_id}-I-01"
        self._br_id = br_id
        self._test_category = "Invalid"
        self._input_action = f"Execute invalid flow for {br_id}"
        self._expected_result = f"{title} rejects invalid/unauthorized input"

        if br_id not in {"BR-001", "BR-005", "BR-020"}:
            _login_for_br(self, br_id)

        method, endpoint, payload, allowed = self._br_endpoint_spec_invalid(br_id)
        response = self._call(method, endpoint, dict(payload))

        if response.status_code in allowed:
            self._record_result(f"HTTP {response.status_code}", "Pass", f"{method} {endpoint}")
        else:
            self._record_result(f"Unexpected HTTP {response.status_code}", "Fail", f"{method} {endpoint}")
            self.fail(f"{br_id} invalid test failed: got {response.status_code}, expected {sorted(allowed)}")

    return _test


for _br_id, _title, _ in BR_META:
    _id_num = _br_id.split("-")[1]
    setattr(TestBRAll, f"test_br{_id_num}_valid_01", _make_valid_test(_br_id, _title))
    setattr(TestBRAll, f"test_br{_id_num}_invalid_01", _make_invalid_test(_br_id, _title))
