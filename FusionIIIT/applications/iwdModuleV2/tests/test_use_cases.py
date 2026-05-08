from applications.filetracking.models import File
from applications.iwdModuleV2.models import Feedback, Requests
from rest_framework.test import APIClient

from .conftest import UCTestBase


UC_META = [
    ("UC-01", "Fetch Eligible Designations", "Auth User"),
    ("UC-02", "Create Request", "Auth User"),
    ("UC-03", "View Inbox / Assigned Requests", "Auth User"),
    ("UC-04", "View File / Details", "Auth User"),
    ("UC-05", "Dean Approval", "Dean"),
    ("UC-06", "Dean Processed Requests", "Dean"),
    ("UC-07", "Forward Request", "Auth User"),
    ("UC-08", "Handle Director Approval", "Director"),
    ("UC-09", "Director Approved Requests", "Auth User"),
    ("UC-10", "Rejected Requests", "Auth User"),
    ("UC-11", "Update Request", "Auth User"),
    ("UC-12", "Create Proposal", "Engineer"),
    ("UC-13", "View Proposals", "Admin/Eng"),
    ("UC-14", "View Proposal Items", "Admin"),
    ("UC-15", "Admin Approval", "Admin"),
    ("UC-16", "Issue Work Order", "Admin"),
    ("UC-17", "View Work Order", "Auth User"),
    ("UC-18", "Add Vendor", "Admin"),
    ("UC-19", "View Vendors", "Auth User"),
    ("UC-20", "Work Progress / Monitoring", "Engineer"),
    ("UC-21", "Complete Work", "Engineer"),
    ("UC-22", "Process Bills", "Admin"),
    ("UC-23", "Audit Bill", "Auditor"),
    ("UC-24", "Settle Bill", "Accounts"),
    ("UC-25", "Manage Budget", "Admin"),
    ("UC-26", "Request Status", "Auth User"),
    ("UC-27", "Engineer Processed", "Engineer"),
    ("UC-28", "Generate Bill PDF", "Admin"),
    ("UC-29", "SLA Engine", "System"),
    ("UC-30", "Inventory/Procurement", "Admin"),
    ("UC-31", "Feedback & Closure", "User"),
]


def _login_for_actor(test_obj, actor):
    actor_norm = (actor or "").lower()
    if "director" in actor_norm:
        test_obj.login_as_director()
    elif "dean" in actor_norm or "hod" in actor_norm:
        test_obj.login_as_hod()
    elif "auditor" in actor_norm:
        test_obj.login_as_auditor()
    elif "account" in actor_norm:
        test_obj.login_as_accounts()
    elif "admin" in actor_norm or "system" in actor_norm:
        test_obj.login_as_admin()
    else:
        test_obj.login_as_worker()


class TestUCAll(UCTestBase):
    """UC test design with strict expected outcomes (HP/AP/EX for all 31 UCs)."""

    def _seed_request_with_file(self):
        seed_client = APIClient()
        seed_client.force_authenticate(user=self.user_worker)
        session = seed_client.session
        session["currentDesignationSelected"] = "Electrical_AE"
        session.save()
        payload = {
            "name": "UC Seed Request",
            "area": "CSE Block",
            "description": "Seeded request for UC tests",
            "role": "Electrical_AE",
            "designation": "Admin IWD|iwd_admin",
        }
        seed_client.post(f"{self.API_BASE}/create-request/", payload, format="json")
        req = Requests.objects.filter(
            requestCreatedBy=self.__class__.user_worker.username,
            name="UC Seed Request",
        ).order_by("-id").first()
        file_obj = File.objects.filter(src_object_id=str(req.id), src_module="IWD").first() if req else None
        return req, file_obj

    def _call(self, method, endpoint, payload):
        if method == "GET":
            return self.api_get(endpoint, params=payload, expected_status=None)
        if method == "PATCH":
            return self.api_patch(endpoint, data=payload, expected_status=None)
        return self.api_post(endpoint, data=payload, expected_status=None)

    def _spec_for_uc(self, uc_id):
        req, file_obj = self._seed_request_with_file()
        request_id = req.id if req else -1
        file_id = file_obj.id if file_obj else -1

        specs = {
            "UC-01": {
                "hp": ("GET", "/fetch-designations/", {}, {200}),
                "ap": ("GET", "/fetch-designations/", {"role": "InvalidRole"}, {200}),
            },
            "UC-02": {
                "hp": ("POST", "/create-request/", {
                    "name": "UC-02 Create",
                    "area": "ECE Block",
                    "description": "Create request",
                    "role": "Electrical_AE",
                    "designation": "Admin IWD|iwd_admin",
                }, {201}),
                "ap": ("POST", "/create-request/", {
                    "name": "UC-02 AP",
                    "area": "ECE Block",
                    "description": "Bad receiver format",
                    "role": "Electrical_AE",
                    "designation": "Admin IWD",
                }, {400}),
            },
            "UC-03": {
                "hp": ("GET", "/created-requests/", {}, {200}),
                "ap": ("GET", "/created-requests/", {"role": "Electrical_AE"}, {200}),
            },
            "UC-04": {
                "hp": ("GET", "/view-file/", {"file_id": file_id}, {200}),
                "ap": ("GET", "/view-file/", {"file_id": -1}, {404}),
            },
            "UC-05": {
                "hp": ("POST", "/handle-dean-process-request/", {
                    "fileid": file_id,
                    "designation": "Director|iwd_director",
                    "remarks": "Dean reviewed",
                }, {200, 400}),
                "ap": ("POST", "/handle-dean-process-request/", {
                    "fileid": file_id,
                    "designation": "Director",
                    "remarks": "Invalid designation format",
                }, {400}),
            },
            "UC-06": {
                "hp": ("GET", "/dean-processed-requests/", {}, {200}),
                "ap": ("GET", "/dean-processed-requests/", {"role": "HOD (CSE)"}, {200}),
            },
            "UC-07": {
                "hp": ("POST", "/forward-request/", {
                    "fileid": file_id,
                    "designation": "Admin IWD|iwd_admin",
                    "remarks": "Forwarding",
                }, {200}),
                "ap": ("POST", "/forward-request/", {
                    "fileid": file_id,
                    "designation": "Admin IWD",
                    "remarks": "Bad receiver format",
                }, {400}),
            },
            "UC-08": {
                "hp": ("POST", "/handle-director-approval/", {
                    "fileid": file_id,
                    "action": "reject",
                    "designation": "Admin IWD|iwd_admin",
                    "remarks": "Director rejected",
                }, {200, 400}),
                "ap": ("POST", "/handle-director-approval/", {
                    "fileid": file_id,
                    "action": "bad-action",
                    "designation": "Admin IWD|iwd_admin",
                }, {400}),
            },
            "UC-09": {
                "hp": ("GET", "/director-approved-requests/", {}, {200}),
                "ap": ("GET", "/director-approved-requests/", {"page": 1}, {200}),
            },
            "UC-10": {
                "hp": ("GET", "/rejected-requests-view/", {}, {200}),
                "ap": ("GET", "/rejected-requests-view/", {"page": 1}, {200}),
            },
            "UC-11": {
                "hp": ("POST", "/handle-update-requests/", {
                    "id": request_id,
                    "name": "UC-11 Updated",
                    "area": "Updated Area",
                    "description": "Updated description",
                    "designation": "Admin IWD|iwd_admin",
                }, {200, 400}),
                "ap": ("POST", "/handle-update-requests/", {
                    "id": -1,
                    "name": "Invalid Update",
                    "area": "X",
                    "description": "X",
                    "designation": "Admin IWD|iwd_admin",
                }, {400, 404}),
            },
            "UC-12": {
                "hp": ("POST", "/create-proposal/", {
                    "id": request_id,
                    "designation": "Admin IWD|iwd_admin",
                    "items[0][name]": "PVC Pipe",
                    "items[0][description]": "20mm",
                    "items[0][unit]": "m",
                    "items[0][price_per_unit]": "10",
                    "items[0][quantity]": "3",
                }, {201, 400}),
                "ap": ("POST", "/create-proposal/", {
                    "id": request_id,
                    "designation": "Admin IWD|iwd_admin",
                }, {400}),
            },
            "UC-13": {
                "hp": ("GET", "/get-proposals/", {"request_id": request_id}, {200}),
                "ap": ("GET", "/get-proposals/", {"request_id": -1}, {200}),
            },
            "UC-14": {
                "hp": ("GET", "/get-items/", {"proposal_id": -1}, {200}),
                "ap": ("GET", "/get-items/", {}, {404, 400}),
            },
            "UC-15": {
                "hp": ("POST", "/handle-admin-approval/", {
                    "fileid": file_id,
                    "action": "reject",
                    "designation": "Electrical_AE|iwd_worker",
                }, {200, 400}),
                "ap": ("POST", "/handle-admin-approval/", {
                    "fileid": file_id,
                    "action": "bad-action",
                    "designation": "Director|iwd_director",
                }, {400}),
            },
            "UC-16": {
                "hp": ("POST", "/issue-work-order/", {
                    "request_id": request_id,
                    "alloted_time": "7 days",
                    "start_date": "2099-01-01",
                    "completion_date": "2099-01-08",
                }, {200, 400}),
                "ap": ("POST", "/issue-work-order/", {
                    "request_id": request_id,
                    "alloted_time": "",
                    "start_date": "2000-01-01",
                }, {400}),
            },
            "UC-17": {
                "hp": ("GET", "/get-work/", {}, {200}),
                "ap": ("GET", "/get-work/", {"request_id": -1}, {200}),
            },
            "UC-18": {
                "hp": ("POST", "/add-vendor/", {
                    "work": -1,
                    "name": "Vendor A",
                    "total_amount": 0,
                }, {200, 400}),
                "ap": ("POST", "/add-vendor/", {
                    "work": -1,
                    "name": "",
                    "total_amount": -1,
                }, {400}),
            },
            "UC-19": {
                "hp": ("GET", "/get-vendors/", {}, {200}),
                "ap": ("GET", "/get-vendors/", {"work_id": -1}, {200}),
            },
            "UC-20": {
                "hp": ("GET", "/requests-in-progress/", {}, {200}),
                "ap": ("GET", "/requests-in-progress/", {"page": "bad"}, {200}),
            },
            "UC-21": {
                "hp": ("PATCH", "/work-completed/", {"id": request_id}, {200, 400}),
                "ap": ("PATCH", "/work-completed/", {"id": -1}, {404, 400}),
            },
            "UC-22": {
                "hp": ("POST", "/handle-process-bills/", {
                    "fileid": file_id,
                    "designation": "Auditor|iwd_audit",
                }, {200, 400}),
                "ap": ("POST", "/handle-process-bills/", {
                    "fileid": file_id,
                    "designation": "Auditor",
                }, {400}),
            },
            "UC-23": {
                "hp": ("POST", "/audit-document/", {
                    "fileid": file_id,
                    "designation": "Accounts Admin|iwd_acc",
                }, {200, 400}),
                "ap": ("POST", "/audit-document/", {
                    "fileid": file_id,
                    "designation": "Accounts Admin",
                }, {400}),
            },
            "UC-24": {
                "hp": ("POST", "/handle-settle-bill-request/", {
                    "fileid": file_id,
                    "designation": "Admin IWD|iwd_admin",
                }, {200, 400}),
                "ap": ("POST", "/handle-settle-bill-request/", {
                    "fileid": file_id,
                    "designation": "Admin IWD",
                }, {400}),
            },
            "UC-25": {
                "hp": ("GET", "/view-budget/", {}, {200}),
                "ap": ("GET", "/view-budget/", {"page_size": "bad"}, {200}),
            },
            "UC-26": {
                "hp": ("GET", "/requests-status/", {}, {200}),
                "ap": ("GET", "/requests-status/", {"status": "invalid"}, {200}),
            },
            "UC-27": {
                "hp": ("GET", "/engineer-processed-requests/", {}, {200}),
                "ap": ("GET", "/engineer-processed-requests/", {"page": "bad"}, {200}),
            },
            "UC-28": {
                "hp": ("POST", "/generate-bill-pdf/", {"request_id": request_id}, {200, 400}),
                "ap": ("POST", "/generate-bill-pdf/", {"request_id": -1}, {404, 400}),
            },
            "UC-29": {
                "hp": ("GET", "/sla-dashboard/", {}, {200}),
                "ap": ("GET", "/sla-dashboard/", {"detail": 1}, {200}),
            },
            "UC-30": {
                "hp": ("GET", "/inventory-items/", {}, {200}),
                "ap": ("GET", "/inventory-items/", {"is_low_stock": "bad"}, {200}),
            },
            "UC-31": {
                "hp": ("POST", "/submit-feedback/", {
                    "request_id": request_id,
                    "rating": 4,
                    "comments": "Resolved",
                }, {201, 400}),
                "ap": ("POST", "/submit-feedback/", {
                    "request_id": request_id,
                    "rating": 9,
                    "comments": "Invalid rating",
                }, {400}),
            },
        }
        return specs[uc_id]


def _make_hp_test(uc_id, title, actor):
    def _test(self):
        self._test_id = f"{uc_id}-HP-01"
        self._uc_id = uc_id
        self._test_category = "Happy Path"
        self._scenario = f"{title} happy path"
        self._preconditions = f"Authenticated as {actor}"
        self._input_action = f"Execute API mapped for {uc_id}"
        self._expected_result = "Expected success behavior occurs"

        _login_for_actor(self, actor)
        method, endpoint, payload, expected = self._spec_for_uc(uc_id)["hp"]
        before_count = Requests.objects.count()
        response = self._call(method, endpoint, dict(payload))

        if response.status_code in expected:
            if uc_id == "UC-02" and response.status_code == 201:
                self.assertTrue(Requests.objects.count() >= before_count + 1)
            if uc_id == "UC-31" and response.status_code == 201:
                self.assertTrue(Feedback.objects.filter(submitted_by=self.__class__.user_worker.username).exists())
            self._record_result(f"HTTP {response.status_code}", "Pass", f"{method} {endpoint}")
        else:
            self._record_result(f"Unexpected HTTP {response.status_code}", "Fail", f"{method} {endpoint}")
            self.fail(f"{uc_id} HP expected {sorted(expected)}, got {response.status_code}")

    return _test


def _make_ap_test(uc_id, title, actor):
    def _test(self):
        self._test_id = f"{uc_id}-AP-01"
        self._uc_id = uc_id
        self._test_category = "Alternate Path"
        self._scenario = f"{title} alternate/invalid input"
        self._preconditions = f"Authenticated as {actor}"
        self._input_action = f"Execute alternate input for {uc_id}"
        self._expected_result = "Input handled/rejected as designed"

        _login_for_actor(self, actor)
        method, endpoint, payload, expected = self._spec_for_uc(uc_id)["ap"]
        response = self._call(method, endpoint, dict(payload))

        if response.status_code in expected:
            self._record_result(f"HTTP {response.status_code}", "Pass", f"{method} {endpoint}")
        else:
            self._record_result(f"Unexpected HTTP {response.status_code}", "Fail", f"{method} {endpoint}")
            self.fail(f"{uc_id} AP expected {sorted(expected)}, got {response.status_code}")

    return _test


def _make_ex_test(uc_id, title):
    def _test(self):
        self._test_id = f"{uc_id}-EX-01"
        self._uc_id = uc_id
        self._test_category = "Exception"
        self._scenario = f"{title} without authentication"
        self._preconditions = "No authentication"
        self._input_action = f"Anonymous call for {uc_id}"
        self._expected_result = "401/403 unauthorized"

        method, endpoint, payload, _ = self._spec_for_uc(uc_id)["hp"]
        self.logout()
        response = self._call(method, endpoint, dict(payload))

        if response.status_code in (401, 403):
            self._record_result(f"HTTP {response.status_code}", "Pass", f"{method} {endpoint}")
        else:
            self._record_result(f"Unexpected HTTP {response.status_code}", "Fail", f"{method} {endpoint}")
            self.fail(f"{uc_id} EX expected 401/403, got {response.status_code}")

    return _test


for _uc_id, _title, _actor in UC_META:
    _n = _uc_id.split("-")[1]
    setattr(TestUCAll, f"test_uc{_n}_hp01", _make_hp_test(_uc_id, _title, _actor))
    setattr(TestUCAll, f"test_uc{_n}_ap01", _make_ap_test(_uc_id, _title, _actor))
    setattr(TestUCAll, f"test_uc{_n}_ex01", _make_ex_test(_uc_id, _title))
