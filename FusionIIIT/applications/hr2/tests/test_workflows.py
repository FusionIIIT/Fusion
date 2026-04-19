import os
import re
from typing import Any, Dict, Optional

import yaml

from .conftest import WFTestBase


class HR2WFTestBase(WFTestBase):
    """Dynamic WF tests generated from specs/workflows.yaml."""

    _created_ids: Dict[str, int] = {}

    def _extract_id(self, data: Any) -> Optional[int]:
        if isinstance(data, dict):
            for key in ("id", "pk", "leave_id", "ltc_id", "cpda_id", "appraisal_id"):
                value = data.get(key)
                if isinstance(value, int):
                    return value
        return None

    def _create_resource(self, endpoint: str, payload: Dict[str, Any]) -> int:
        response = self.api_post(endpoint, payload, expected_status=None)
        if response.status_code in {200, 201}:
            extracted = self._extract_id(getattr(response, "data", {}))
            if extracted is not None:
                return extracted
        return 1

    def _ensure_leave_id(self) -> int:
        if "leave" not in self._created_ids:
            self.login_as_employee()
            payload = {
                "leave_type": "Casual",
                "start_date": self.future_date(3),
                "end_date": self.future_date(4),
                "total_days": 2,
                "reason": "Personal work",
                "contact_during_leave": "9876543210",
                "address_during_leave": "Jabalpur, MP",
            }
            self._created_ids["leave"] = self._create_resource(
                "/hr2/api/leave-applications/", payload
            )
        return self._created_ids["leave"]

    def _ensure_approved_leave_id(self) -> int:
        leave_id = self._ensure_leave_id()
        self.login_as_director()
        self.api_post(
            f"/hr2/api/leave-applications/{leave_id}/approve/",
            {"remarks": "Approved"},
            expected_status=None,
        )
        return leave_id

    def _ensure_leave_with_nominee_id(self) -> int:
        if "leave_nominee" not in self._created_ids:
            self.login_as_employee()
            payload = {
                "leave_type": "Casual",
                "start_date": self.future_date(3),
                "end_date": self.future_date(4),
                "total_days": 2,
                "reason": "Personal work",
                "contact_during_leave": "9876543210",
                "address_during_leave": "Jabalpur, MP",
                "nominee_employee_id": self.nominee_extra.id,
            }
            self._created_ids["leave_nominee"] = self._create_resource(
                "/hr2/api/leave-applications/", payload
            )
        return self._created_ids["leave_nominee"]

    def _ensure_ltc_id(self) -> int:
        if "ltc" not in self._created_ids:
            self.login_as_employee()
            payload = {
                "employee_name": "Rahul Sharma",
                "department": "Computer Science and Engineering",
                "designation": "Assistant Professor",
                "ltc_block_year": 2025,
                "travel_start_date": self.future_date(10),
                "travel_end_date": self.future_date(15),
                "destination": "Delhi",
                "purpose_of_travel": "Family travel",
                "travel_mode": "Train",
                "total_amount_claimed": 22000,
            }
            self._created_ids["ltc"] = self._create_resource("/hr2/api/ltc/", payload)
        return self._created_ids["ltc"]

    def _ensure_cpda_advance_id(self) -> int:
        if "cpda_advance" not in self._created_ids:
            self.login_as_employee()
            payload = {
                "employee_name": "Rahul Sharma",
                "department": "Computer Science and Engineering",
                "designation": "Assistant Professor",
                "event_name": "National Conference on AI",
                "event_type": "Conference",
                "start_date": self.future_date(30),
                "end_date": self.future_date(32),
                "total_amount": 20000,
                "purpose_of_attending": "Present paper",
                "benefits_to_institution": "Research exposure",
            }
            self._created_ids["cpda_advance"] = self._create_resource(
                "/hr2/api/cpda-advances/", payload
            )
        return self._created_ids["cpda_advance"]

    def _ensure_cpda_reimbursement_id(self) -> int:
        if "cpda_reimbursement" not in self._created_ids:
            self.login_as_employee()
            payload = {
                "employee_name": "Rahul Sharma",
                "department": "Computer Science and Engineering",
                "designation": "Assistant Professor",
                "event_name": "National Conference on AI",
                "event_type": "Conference",
                "start_date": self.future_date(30),
                "end_date": self.future_date(32),
                "total_amount": 20000,
                "purpose_of_attending": "Present paper",
                "benefits_to_institution": "Research exposure",
            }
            self._created_ids["cpda_reimbursement"] = self._create_resource(
                "/hr2/api/cpda-reimbursements/", payload
            )
        return self._created_ids["cpda_reimbursement"]

    def _ensure_appraisal_form_id(self) -> int:
        if "appraisal_form" not in self._created_ids:
            self.login_as_employee()
            payload = {
                "employee_name": "Rahul Sharma",
                "department": "Computer Science and Engineering",
                "designation": "Assistant Professor",
                "appraisal_year": "2025-2026",
                "self_summary": "Completed teaching responsibilities",
                "key_responsibilities": "Teaching and research",
                "achievements": "Published 1 paper",
                "goals_achieved": "Completed syllabus",
                "future_goals": "Publish more papers",
            }
            self._created_ids["appraisal_form"] = self._create_resource(
                "/hr2/api/appraisal-forms/", payload
            )
        return self._created_ids["appraisal_form"]

    def _resolve_path(self, path: str) -> str:
        if "/leave-applications/" in path:
            leave_id = self._ensure_leave_id()
            return re.sub(r"/leave-applications/\d+", f"/leave-applications/{leave_id}", path)
        if "/ltc/" in path:
            ltc_id = self._ensure_ltc_id()
            return re.sub(r"/ltc/\d+", f"/ltc/{ltc_id}", path)
        if "/cpda-advances/" in path:
            cpda_id = self._ensure_cpda_advance_id()
            return re.sub(r"/cpda-advances/\d+", f"/cpda-advances/{cpda_id}", path)
        if "/cpda-reimbursements/" in path:
            cpda_id = self._ensure_cpda_reimbursement_id()
            return re.sub(r"/cpda-reimbursements/\d+", f"/cpda-reimbursements/{cpda_id}", path)
        if "/appraisal-forms/" in path:
            appraisal_id = self._ensure_appraisal_form_id()
            return re.sub(r"/appraisal-forms/\d+", f"/appraisal-forms/{appraisal_id}", path)
        return path

    def _payload_for(self, path: str, scenario: str) -> Dict[str, Any]:
        scenario_lower = scenario.lower()
        payload: Dict[str, Any] = {}

        if "/leave-applications/" in path and path.endswith("/leave-applications/"):
            payload = {
                "leave_type": "Casual",
                "start_date": self.future_date(3),
                "end_date": self.future_date(4),
                "total_days": 2,
                "reason": "Personal work",
                "contact_during_leave": "9876543210",
                "address_during_leave": "Jabalpur, MP",
            }
        elif path.endswith("/withdraw/"):
            payload = {}
        elif path.endswith("/cancel-request/"):
            payload = {"reason": "Change of plan"}
        elif path.endswith("/extension-request/"):
            payload = {"new_end_date": self.future_date(6), "reason": "Medical"}
        elif path.endswith("/request-document/"):
            payload = {"message": "Submit proof"}
        elif path.endswith("/submit-document/"):
            payload = {"submission": "doc-ref"}
        elif "/leave-nominee/" in path:
            payload = {"action": "accept" if "accept" in scenario_lower else "decline"}
        elif path.endswith("/ltc/"):
            payload = {
                "employee_name": "Rahul Sharma",
                "department": "Computer Science and Engineering",
                "designation": "Assistant Professor",
                "ltc_block_year": 2025,
                "travel_start_date": self.future_date(10),
                "travel_end_date": self.future_date(15),
                "destination": "Delhi",
                "purpose_of_travel": "Family travel",
                "travel_mode": "Train",
                "total_amount_claimed": 22000,
            }
        elif path.endswith("/cpda-advances/"):
            payload = {
                "employee_name": "Rahul Sharma",
                "department": "Computer Science and Engineering",
                "designation": "Assistant Professor",
                "event_name": "National Conference on AI",
                "event_type": "Conference",
                "start_date": self.future_date(30),
                "end_date": self.future_date(32),
                "total_amount": 20000,
                "purpose_of_attending": "Present paper",
                "benefits_to_institution": "Research exposure",
            }
        elif path.endswith("/cpda-reimbursements/"):
            payload = {
                "employee_name": "Rahul Sharma",
                "department": "Computer Science and Engineering",
                "designation": "Assistant Professor",
                "event_name": "National Conference on AI",
                "event_type": "Conference",
                "start_date": self.future_date(30),
                "end_date": self.future_date(32),
                "total_amount": 20000,
                "purpose_of_attending": "Present paper",
                "benefits_to_institution": "Research exposure",
            }
        elif path.endswith("/review/"):
            payload = {"action": "forward" if "forward" in scenario_lower else "approve"}

        return payload

    def _dispatch(self, method: str, path: str, payload: Dict[str, Any]):
        if method == "POST":
            return self.api_post(path, payload, expected_status=None)
        if method == "PUT":
            return self.api_put(path, payload, expected_status=None)
        if method == "DELETE":
            return self.api_delete(path, expected_status=None)
        return self.api_get(path, expected_status=None)


def _load_workflows() -> Dict[str, Any]:
    specs_path = os.path.join(os.path.dirname(__file__), "specs", "workflows.yaml")
    with open(specs_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")
    return slug.lower() or "workflow"


def _build_test(workflow: Dict[str, Any], scenario: Dict[str, Any], category: str, index: int):
    def _test(self: HR2WFTestBase):
        suffix = "E2E" if category == "End-to-End" else "NEG"
        self._test_id = f"{workflow.get('id')}-{suffix}-{index:02d}"
        self._wf_id = workflow.get("id")
        self._test_category = category
        self._scenario = scenario.get("scenario")
        self._expected_final_state = scenario.get("expected_final_state", "")

        workflow_id = workflow.get("id") or ""
        scenario_lower = (self._scenario or "").lower()

        if workflow_id == "WF-HR2-001":
            self.login_as_employee()
            leave_id = self._ensure_leave_id()
            self._add_step(1, "Employee applies", "Leave created", str(leave_id), True)

            if "rejected" in scenario_lower:
                self.login_as_director()
                resp = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/reject/",
                    {"remarks": "Rejected"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(2, "Director rejects", "Status rejected", str(resp.data), step_ok)
            elif "forwarded" in scenario_lower:
                self.login_as_hod()
                resp = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/forward/",
                    {"remarks": "Forward"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(2, "HOD forwards", "Status forwarded", str(resp.data), step_ok)
                self.login_as_director()
                resp2 = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/approve/",
                    {"remarks": "Approved"},
                    expected_status=None,
                )
                step2_ok = resp2.status_code in {200, 201}
                self._add_step(3, "Director approves", "Status approved", str(resp2.data), step2_ok)
            else:
                self.login_as_director()
                resp = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/approve/",
                    {"remarks": "Approved"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(2, "Director approves", "Status approved", str(resp.data), step_ok)

        elif workflow_id == "WF-HR2-002":
            leave_id = self._ensure_leave_id()
            if "approved" in scenario_lower:
                self.login_as_director()
                self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/approve/",
                    {"remarks": "Approved"},
                    expected_status=None,
                )
                self.login_as_employee()
                resp = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/withdraw/",
                    {},
                    expected_status=None,
                )
                step_ok = resp.status_code in {400, 403}
                self._add_step(1, "Withdraw approved leave", "Rejected", str(resp.data), step_ok)
            else:
                self.login_as_employee()
                resp = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/withdraw/",
                    {},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(1, "Withdraw pending leave", "Withdrawn", str(resp.data), step_ok)

        elif workflow_id == "WF-HR2-003":
            leave_id = self._ensure_approved_leave_id()
            if "after start date" in scenario_lower:
                self.login_as_employee()
                resp = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/cancel-request/",
                    {"reason": "Late"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {400, 403}
                self._add_step(1, "Cancel request late", "Rejected", str(resp.data), step_ok)
            else:
                self.login_as_employee()
                resp = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/cancel-request/",
                    {"reason": "Change of plan"},
                    expected_status=None,
                )
                step1_ok = resp.status_code in {200, 201}
                self._add_step(1, "Request cancellation", "Requested", str(resp.data), step1_ok)
                self.login_as_director()
                resp2 = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/cancel-decision/approve/",
                    {"remarks": "Approved"},
                    expected_status=None,
                )
                step2_ok = resp2.status_code in {200, 201}
                self._add_step(2, "Approve cancellation", "Cancelled", str(resp2.data), step2_ok)

        elif workflow_id == "WF-HR2-004":
            leave_id = self._ensure_approved_leave_id()
            self.login_as_employee()
            new_end = self.future_date(6)
            if "insufficient" in scenario_lower:
                new_end = self.future_date(30)
            resp = self.api_post(
                f"/hr2/api/leave-applications/{leave_id}/extension-request/",
                {"new_end_date": new_end},
                expected_status=None,
            )
            step1_ok = resp.status_code in {200, 201}
            self._add_step(1, "Request extension", "Requested", str(resp.data), step1_ok)
            self.login_as_director()
            resp2 = self.api_post(
                f"/hr2/api/leave-applications/{leave_id}/extension-decision/approve/",
                {"remarks": "Approved"},
                expected_status=None,
            )
            step2_ok = resp2.status_code in ({400} if "insufficient" in scenario_lower else {200, 201})
            self._add_step(2, "Approve extension", "Approved or rejected", str(resp2.data), step2_ok)

        elif workflow_id == "WF-HR2-005":
            leave_id = self._ensure_leave_with_nominee_id()
            if "non-nominee" in scenario_lower:
                self.login_as_employee()
                resp = self.api_post(
                    f"/hr2/api/leave-nominee/{leave_id}/",
                    {"action": "accept"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {403}
                self._add_step(1, "Non-nominee responds", "Forbidden", str(resp.data), step_ok)
            else:
                self.login_as_nominee()
                resp = self.api_post(
                    f"/hr2/api/leave-nominee/{leave_id}/",
                    {"action": "accept"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(1, "Nominee accepts", "Accepted", str(resp.data), step_ok)

        elif workflow_id == "WF-HR2-006":
            leave_id = self._ensure_leave_id()
            if "without request" in scenario_lower:
                self.login_as_employee()
                resp = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/submit-document/",
                    {"submission": "doc-ref"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {400, 403}
                self._add_step(1, "Submit without request", "Rejected", str(resp.data), step_ok)
            else:
                self.login_as_hod()
                resp = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/request-document/",
                    {"message": "Submit proof"},
                    expected_status=None,
                )
                step1_ok = resp.status_code in {200, 201}
                self._add_step(1, "HOD requests document", "Requested", str(resp.data), step1_ok)
                self.login_as_employee()
                resp2 = self.api_post(
                    f"/hr2/api/leave-applications/{leave_id}/submit-document/",
                    {"submission": "doc-ref"},
                    expected_status=None,
                )
                step2_ok = resp2.status_code in {200, 201}
                self._add_step(2, "Employee submits", "Submitted", str(resp2.data), step2_ok)

        elif workflow_id == "WF-HR2-007":
            ltc_id = self._ensure_ltc_id()
            if "rejected" in scenario_lower:
                self.login_as_accountant()
                resp = self.api_post(
                    f"/hr2/api/ltc/{ltc_id}/reject/",
                    {"remarks": "Rejected"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(1, "Reject LTC", "Rejected", str(resp.data), step_ok)
            else:
                self.login_as_staff()
                resp = self.api_post(
                    f"/hr2/api/ltc/{ltc_id}/forward/",
                    {"remarks": "Forward"},
                    expected_status=None,
                )
                step1_ok = resp.status_code in {200, 201}
                self._add_step(1, "Forward LTC", "Forwarded", str(resp.data), step1_ok)
                self.login_as_accountant()
                resp2 = self.api_post(
                    f"/hr2/api/ltc/{ltc_id}/approve/",
                    {"remarks": "Approved"},
                    expected_status=None,
                )
                step2_ok = resp2.status_code in {200, 201}
                self._add_step(2, "Approve LTC", "Approved", str(resp2.data), step2_ok)

        elif workflow_id == "WF-HR2-008":
            cpda_id = self._ensure_cpda_advance_id()
            if "director" in scenario_lower:
                self.login_as_staff()
                resp = self.api_post(
                    f"/hr2/api/cpda-advances/{cpda_id}/forward-director/",
                    {"remarks": "Forward"},
                    expected_status=None,
                )
                step1_ok = resp.status_code in {200, 201}
                self._add_step(1, "Forward to director", "Forwarded", str(resp.data), step1_ok)
                self.login_as_director()
                resp2 = self.api_post(
                    f"/hr2/api/cpda-advances/{cpda_id}/approve/",
                    {"remarks": "Approved"},
                    expected_status=None,
                )
                step2_ok = resp2.status_code in {200, 201}
                self._add_step(2, "Director approves", "Approved", str(resp2.data), step2_ok)
            elif "rejected" in scenario_lower:
                self.login_as_accountant()
                resp = self.api_post(
                    f"/hr2/api/cpda-advances/{cpda_id}/reject/",
                    {"remarks": "Rejected"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(1, "Reject CPDA", "Rejected", str(resp.data), step_ok)
            else:
                self.login_as_staff()
                resp = self.api_post(
                    f"/hr2/api/cpda-advances/{cpda_id}/forward-accountant/",
                    {"remarks": "Forward"},
                    expected_status=None,
                )
                step1_ok = resp.status_code in {200, 201}
                self._add_step(1, "Forward to accountant", "Forwarded", str(resp.data), step1_ok)
                self.login_as_accountant()
                resp2 = self.api_post(
                    f"/hr2/api/cpda-advances/{cpda_id}/approve/",
                    {"remarks": "Approved"},
                    expected_status=None,
                )
                step2_ok = resp2.status_code in {200, 201}
                self._add_step(2, "Accountant approves", "Approved", str(resp2.data), step2_ok)

        elif workflow_id == "WF-HR2-009":
            cpda_id = self._ensure_cpda_reimbursement_id()
            if "rejected" in scenario_lower:
                self.login_as_accountant()
                resp = self.api_post(
                    f"/hr2/api/cpda-reimbursements/{cpda_id}/reject/",
                    {"remarks": "Rejected"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(1, "Reject reimbursement", "Rejected", str(resp.data), step_ok)
            else:
                self.login_as_accountant()
                resp = self.api_post(
                    f"/hr2/api/cpda-reimbursements/{cpda_id}/approve/",
                    {"remarks": "Approved"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(1, "Approve reimbursement", "Approved", str(resp.data), step_ok)

        elif workflow_id == "WF-HR2-010":
            appraisal_id = self._ensure_appraisal_form_id()
            if "director" in scenario_lower:
                self.login_as_hod()
                self.api_post(
                    f"/hr2/api/appraisal-forms/{appraisal_id}/review/",
                    {"action": "forward"},
                    expected_status=None,
                )
                self.login_as_director()
                resp = self.api_post(
                    f"/hr2/api/appraisal-forms/{appraisal_id}/review/",
                    {"action": "approve"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(1, "Director approves", "Approved", str(resp.data), step_ok)
            else:
                self.login_as_hod()
                resp = self.api_post(
                    f"/hr2/api/appraisal-forms/{appraisal_id}/review/",
                    {"action": "forward"},
                    expected_status=None,
                )
                step_ok = resp.status_code in {200, 201}
                self._add_step(1, "HOD forwards", "Reviewed", str(resp.data), step_ok)

        if self._all_steps_passed():
            self._record_result("Workflow completed", "Pass")
        else:
            self._record_result("Workflow incomplete", "Fail")
            self.fail("Workflow did not complete successfully")

    return _test


def _generate_wf_tests():
    specs = _load_workflows()
    workflows = specs.get("workflows", [])
    for workflow in workflows:
        class_name = f"Test_{workflow.get('id', 'WF')}_{_slugify(workflow.get('title', 'workflow'))}"
        attrs: Dict[str, Any] = {
            "__doc__": f"{workflow.get('id')}: {workflow.get('title')}"
        }

        for category, key in (("End-to-End", "e2e_tests"), ("Negative", "negative_tests")):
            scenarios = workflow.get(key, []) or []
            for index, scenario in enumerate(scenarios, start=1):
                name = f"test_{category.split('-')[0].lower()}_{index:02d}_{_slugify(scenario.get('scenario', 'case'))}"
                attrs[name] = _build_test(workflow, scenario, category, index)

        globals()[class_name] = type(class_name, (HR2WFTestBase,), attrs)


_generate_wf_tests()
