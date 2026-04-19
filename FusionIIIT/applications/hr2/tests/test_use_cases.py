import os
import re
from typing import Any, Dict, Optional, Tuple

import yaml

from .conftest import UCTestBase


class HR2UCTestBase(UCTestBase):
    """Dynamic UC tests generated from specs/use_cases.yaml."""

    _created_ids: Dict[str, int] = {}

    def _login_for_context(self, text: str) -> None:
        normalized = text.lower()
        if "not authenticated" in normalized or "unauthorized" in normalized:
            self.logout()
            return

        if "director" in normalized:
            self.login_as_director()
        elif "registrar" in normalized:
            self.login_as_registrar()
        elif "hod" in normalized:
            self.login_as_hod()
        elif "accountant" in normalized:
            self.login_as_accountant()
        elif "nominee" in normalized:
            self.login_as_nominee()
        elif "hr" in normalized or "staff" in normalized:
            self.login_as_staff()
        else:
            self.login_as_employee()

    def _parse_action(self, input_action: str) -> Tuple[str, str]:
        match = re.search(r"\b(GET|POST|PUT|DELETE)\b\s+([^\s]+)", input_action)
        if not match:
            return "GET", "/"
        method = match.group(1).upper()
        path = match.group(2)
        if not path.startswith("/"):
            path = f"/{path}"
        return method, path

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
        if "/leave-balance/" in path:
            return re.sub(
                r"/leave-balance/\d+",
                f"/leave-balance/{self.employee_extra.id}",
                path,
            )
        if "/employees/" in path:
            return re.sub(r"/employees/\d+", f"/employees/{self.employee_extra.id}", path)
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
        payload: Dict[str, Any] = {}
        scenario_lower = scenario.lower()

        if "/leave-applications/" in path and path.endswith("/leave-applications/"):
            leave_type = "Casual"
            if "vacation" in scenario_lower:
                leave_type = "Vacation"
            payload = {
                "leave_type": leave_type,
                "start_date": self.future_date(2),
                "end_date": self.future_date(4),
                "total_days": 3,
                "reason": "Personal work",
                "contact_during_leave": "9876543210",
                "address_during_leave": "Jabalpur, MP",
            }
            if "nominee" in scenario_lower:
                payload["nominee_employee_id"] = self.nominee_extra.id
        elif "/leave-applications/" in path and path.endswith("/cancel-request/"):
            payload = {"reason": "Change of plan"}
        elif "/leave-applications/" in path and path.endswith("/extension-request/"):
            payload = {"new_end_date": self.future_date(6), "reason": "Medical"}
        elif "/leave-applications/" in path and path.endswith("/request-document/"):
            payload = {"message": "Submit proof"}
        elif "/leave-applications/" in path and path.endswith("/submit-document/"):
            payload = {"submission": "doc-ref"}
        elif "/leave-applications/" in path and path.endswith("/cancel-decision/approve/"):
            payload = {"remarks": "Approved"}
        elif "/leave-applications/" in path and path.endswith("/extension-decision/approve/"):
            payload = {"remarks": "Approved"}
        elif "/leave-nominee/" in path:
            if "decline" in scenario_lower:
                payload = {"action": "decline"}
            else:
                payload = {"action": "accept"}
        elif "/attendance/" in path and path.endswith("/attendance/"):
            status = "PRESENT" if "half" not in scenario_lower else "HALF_DAY"
            payload = {"date": self.today(), "status": status}
        elif "/ltc/" in path and path.endswith("/ltc/"):
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
        elif "/cpda-advances/" in path and path.endswith("/cpda-advances/"):
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
        elif "/cpda-reimbursements/" in path and path.endswith("/cpda-reimbursements/"):
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
        elif "/appraisal-forms/" in path and path.endswith("/appraisal-forms/"):
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
        elif "/appraisals/" in path and path.endswith("/appraisals/"):
            payload = {
                "period": self.appraisal_period.id,
                "teaching_score": 4,
                "research_score": 4,
                "admin_score": 3,
            }
        elif "/training-nominations/" in path:
            payload = {"program": self.training_program.id}
        elif "/promotions/" in path:
            payload = {
                "current_designation": self.promotion_current_designation.id,
                "applied_designation": self.promotion_applied_designation.id,
                "application_date": self.today(),
                "eligibility_date": self.today(),
                "api_score": 8,
            }
        elif "/employees/" in path:
            payload = {"phone_number": "9876543210", "full_address": "Updated"}

        return payload

    def _dispatch(self, method: str, path: str, payload: Dict[str, Any]):
        if method == "POST":
            return self.api_post(path, payload, expected_status=None)
        if method == "PUT":
            return self.api_put(path, payload, expected_status=None)
        if method == "DELETE":
            return self.api_delete(path, expected_status=None)
        return self.api_get(path, expected_status=None)

    def _prepare_state_for(self, path: str, method: str) -> str:
        if "/leave-applications/" in path and path.endswith("/cancel-request/"):
            leave_id = self._ensure_approved_leave_id()
            self.login_as_employee()
            return f"/hr2/api/leave-applications/{leave_id}/cancel-request/"

        if "/leave-applications/" in path and path.endswith("/extension-request/"):
            leave_id = self._ensure_approved_leave_id()
            self.login_as_employee()
            return f"/hr2/api/leave-applications/{leave_id}/extension-request/"

        if "/leave-applications/" in path and "/cancel-decision/" in path:
            leave_id = self._ensure_approved_leave_id()
            self.login_as_employee()
            self.api_post(
                f"/hr2/api/leave-applications/{leave_id}/cancel-request/",
                {"reason": "Change of plan"},
                expected_status=None,
            )
            self.login_as_director()
            return re.sub(
                r"/leave-applications/\d+/cancel-decision/",
                f"/leave-applications/{leave_id}/cancel-decision/",
                path,
            )

        if "/leave-applications/" in path and "/extension-decision/" in path:
            leave_id = self._ensure_approved_leave_id()
            self.login_as_employee()
            self.api_post(
                f"/hr2/api/leave-applications/{leave_id}/extension-request/",
                {"new_end_date": self.future_date(6)},
                expected_status=None,
            )
            self.login_as_director()
            return re.sub(
                r"/leave-applications/\d+/extension-decision/",
                f"/leave-applications/{leave_id}/extension-decision/",
                path,
            )

        if "/leave-applications/" in path and "/request-document/" in path:
            leave_id = self._ensure_leave_id()
            self.login_as_hod()
            return f"/hr2/api/leave-applications/{leave_id}/request-document/"

        if "/leave-applications/" in path and "/submit-document/" in path:
            leave_id = self._ensure_leave_id()
            self.login_as_hod()
            self.api_post(
                f"/hr2/api/leave-applications/{leave_id}/request-document/",
                {"message": "Submit proof"},
                expected_status=None,
            )
            self.login_as_employee()
            return f"/hr2/api/leave-applications/{leave_id}/submit-document/"

        if "/leave-applications/" in path and "/approve/" in path:
            leave_id = self._ensure_leave_id()
            self.login_as_director()
            return f"/hr2/api/leave-applications/{leave_id}/approve/"

        if "/leave-applications/" in path and "/forward/" in path:
            leave_id = self._ensure_leave_id()
            self.login_as_hod()
            return f"/hr2/api/leave-applications/{leave_id}/forward/"

        if "/leave-applications/" in path and "/reject/" in path:
            leave_id = self._ensure_leave_id()
            self.login_as_director()
            return f"/hr2/api/leave-applications/{leave_id}/reject/"

        if "/leave-applications/" in path and "/withdraw/" in path:
            leave_id = self._ensure_leave_id()
            self.login_as_employee()
            return f"/hr2/api/leave-applications/{leave_id}/withdraw/"

        if "/leave-nominee/" in path and "/leave-nominee/" in path:
            leave_id = self._ensure_leave_with_nominee_id()
            self.login_as_nominee()
            return f"/hr2/api/leave-nominee/{leave_id}/"

        if "/ltc/" in path and "/download/" in path:
            ltc_id = self._ensure_ltc_id()
            return f"/hr2/api/ltc/{ltc_id}/download/"

        if "/ltc/" in path and "/withdraw/" in path:
            ltc_id = self._ensure_ltc_id()
            self.login_as_employee()
            return f"/hr2/api/ltc/{ltc_id}/withdraw/"

        if "/ltc/" in path and "/forward/" in path:
            ltc_id = self._ensure_ltc_id()
            self.login_as_staff()
            return f"/hr2/api/ltc/{ltc_id}/forward/"

        if "/ltc/" in path and "/approve/" in path:
            ltc_id = self._ensure_ltc_id()
            self.login_as_accountant()
            return f"/hr2/api/ltc/{ltc_id}/approve/"

        if "/ltc/" in path and "/reject/" in path:
            ltc_id = self._ensure_ltc_id()
            self.login_as_accountant()
            return f"/hr2/api/ltc/{ltc_id}/reject/"

        if "/cpda-advances/" in path and "/download/" in path:
            cpda_id = self._ensure_cpda_advance_id()
            return f"/hr2/api/cpda-advances/{cpda_id}/download/"

        if "/cpda-advances/" in path and "/withdraw/" in path:
            cpda_id = self._ensure_cpda_advance_id()
            self.login_as_employee()
            return f"/hr2/api/cpda-advances/{cpda_id}/withdraw/"

        if "/cpda-advances/" in path and "/forward-accountant/" in path:
            cpda_id = self._ensure_cpda_advance_id()
            self.login_as_staff()
            return f"/hr2/api/cpda-advances/{cpda_id}/forward-accountant/"

        if "/cpda-advances/" in path and "/forward-director/" in path:
            cpda_id = self._ensure_cpda_advance_id()
            self.login_as_staff()
            return f"/hr2/api/cpda-advances/{cpda_id}/forward-director/"

        if "/cpda-advances/" in path and "/approve/" in path:
            cpda_id = self._ensure_cpda_advance_id()
            self.login_as_accountant()
            return f"/hr2/api/cpda-advances/{cpda_id}/approve/"

        if "/cpda-advances/" in path and "/reject/" in path:
            cpda_id = self._ensure_cpda_advance_id()
            self.login_as_accountant()
            return f"/hr2/api/cpda-advances/{cpda_id}/reject/"

        if "/cpda-reimbursements/" in path and "/approve/" in path:
            cpda_id = self._ensure_cpda_reimbursement_id()
            self.login_as_accountant()
            return f"/hr2/api/cpda-reimbursements/{cpda_id}/approve/"

        if "/cpda-reimbursements/" in path and "/reject/" in path:
            cpda_id = self._ensure_cpda_reimbursement_id()
            self.login_as_accountant()
            return f"/hr2/api/cpda-reimbursements/{cpda_id}/reject/"

        if "/appraisal-forms/" in path and "/download/" in path:
            appraisal_id = self._ensure_appraisal_form_id()
            return f"/hr2/api/appraisal-forms/{appraisal_id}/download/"

        if "/appraisal-forms/" in path and "/review/" in path:
            appraisal_id = self._ensure_appraisal_form_id()
            self.login_as_hod()
            return f"/hr2/api/appraisal-forms/{appraisal_id}/review/"

        return path


def _load_use_cases() -> Dict[str, Any]:
    specs_path = os.path.join(os.path.dirname(__file__), "specs", "use_cases.yaml")
    with open(specs_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")
    return slug.lower() or "scenario"


def _expected_statuses(category: str, method: str) -> Tuple[int, ...]:
    if method == "DELETE":
        return (204,)
    if category == "Exception":
        return (400, 401, 403, 404, 302)
    return (200, 201)


def _build_test(
    uc: Dict[str, Any], category: str, scenario: Dict[str, Any], index: int
):
    def _test(self: HR2UCTestBase):
        self._test_id = f"{uc.get('id')}-{category[:2].upper()}-{index:02d}"
        self._uc_id = uc.get("id")
        self._test_category = category
        self._scenario = scenario.get("scenario")
        self._preconditions = scenario.get("preconditions", uc.get("preconditions", ""))
        self._input_action = scenario.get("input_action", "")
        self._expected_result = scenario.get("expected_result", "")

        login_text = f"{uc.get('actors', '')} {self._preconditions}"
        self._login_for_context(login_text)

        method, path = self._parse_action(self._input_action)
        path = self._resolve_path(path)
        path = self._prepare_state_for(path, method)
        payload = self._payload_for(path, self._scenario or "") if method in {"POST", "PUT"} else {}

        response = self._dispatch(method, path, payload)
        expected_statuses = _expected_statuses(category, method)

        if response.status_code in expected_statuses:
            self._record_result("Expected response", "Pass", str(getattr(response, "data", "")))
        else:
            self._record_result(
                f"Unexpected status {response.status_code}",
                "Fail",
                str(getattr(response, "data", "")),
            )
            self.fail(f"Expected status in {expected_statuses}, got {response.status_code}")

    return _test


def _generate_uc_tests():
    specs = _load_use_cases()
    use_cases = specs.get("use_cases", [])
    for uc in use_cases:
        class_name = f"Test_{uc.get('id', 'UC')}_{_slugify(uc.get('title', 'uc'))}"
        attrs: Dict[str, Any] = {"__doc__": f"{uc.get('id')}: {uc.get('title')}"}

        for category, key in (
            ("Happy Path", "happy_paths"),
            ("Alternate Path", "alternate_paths"),
            ("Exception", "exception_paths"),
        ):
            scenarios = uc.get(key, []) or []
            for index, scenario in enumerate(scenarios, start=1):
                test_name = f"test_{category.split()[0].lower()}_{index:02d}_{_slugify(scenario.get('scenario', 'case'))}"
                attrs[test_name] = _build_test(uc, category, scenario, index)

        globals()[class_name] = type(class_name, (HR2UCTestBase,), attrs)


_generate_uc_tests()
