import os
import re
from typing import Any, Dict, Optional, Tuple

import yaml

from .conftest import BRTestBase


class HR2BRTestBase(BRTestBase):
    """Dynamic BR tests generated from specs/business_rules.yaml."""

    _created_ids: Dict[str, int] = {}

    def _login_for_action(self, text: str) -> None:
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
        elif "hr" in normalized or "staff" in normalized:
            self.login_as_staff()
        else:
            self.login_as_employee()

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
        if "/appraisal-forms/" in path:
            appraisal_id = self._ensure_appraisal_form_id()
            return re.sub(r"/appraisal-forms/\d+", f"/appraisal-forms/{appraisal_id}", path)
        return path

    def _payload_for(self, path: str, action_text: str, valid_case: bool) -> Dict[str, Any]:
        action_lower = action_text.lower()
        payload: Dict[str, Any] = {}

        day_match = re.search(r"(\d+)\s*day", action_lower)
        requested_days = int(day_match.group(1)) if day_match else None

        start_date = self.future_date(1) if valid_case else self.past_date(1)
        total_days = requested_days or (3 if valid_case else 2)
        end_date = self.future_date((total_days or 1) - 1) if valid_case else self.future_date(1)

        if "/leave-applications/" in path and path.endswith("/leave-applications/"):
            if "total_days" in action_lower and "mismatch" in action_lower:
                total_days = 2 if valid_case else 1
            payload = {
                "leave_type": "Casual",
                "start_date": start_date,
                "end_date": end_date,
                "total_days": total_days,
                "reason": "Personal work",
                "contact_during_leave": "9876543210",
                "address_during_leave": "Jabalpur, MP",
            }
            if "nominee" in action_lower:
                payload["nominee_employee_id"] = self.nominee_extra.id if valid_case else 999999
        elif path.endswith("/withdraw/"):
            payload = {}
        elif path.endswith("/cancel-request/"):
            payload = {"reason": "Change of plan"}
        elif path.endswith("/extension-request/"):
            payload = {"new_end_date": self.future_date(6)}
        elif path.endswith("/request-document/"):
            payload = {"message": "Submit proof"} if valid_case else {}
        elif path.endswith("/submit-document/"):
            payload = {"submission": "doc-ref"}
        elif path.endswith("/leave-nominee/") or "/leave-nominee/" in path:
            payload = {"action": "accept" if valid_case else "invalid"}
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
        elif path.endswith("/appraisal-forms/"):
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
        elif path.endswith("/review/"):
            payload = {"action": "approve" if valid_case else "invalid"}

        return payload

    def _endpoint_for_action(self, action_text: str) -> str:
        action_lower = action_text.lower()
        if "ltc" in action_lower:
            if "withdraw" in action_lower:
                return "/hr2/api/ltc/1/withdraw/"
            if "decision" in action_lower or "approve" in action_lower or "forward" in action_lower:
                return "/hr2/api/ltc/1/forward/"
            return "/hr2/api/ltc/"
        if "cpda" in action_lower:
            if "advance" in action_lower:
                if "withdraw" in action_lower:
                    return "/hr2/api/cpda-advances/1/withdraw/"
                if "decision" in action_lower or "approve" in action_lower or "forward" in action_lower:
                    return "/hr2/api/cpda-advances/1/forward-accountant/"
                return "/hr2/api/cpda-advances/"
        if "appraisal" in action_lower and "review" in action_lower:
            return "/hr2/api/appraisal-forms/1/review/"
        if "document" in action_lower and "request" in action_lower:
            return "/hr2/api/leave-applications/1/request-document/"
        if "document" in action_lower and "submit" in action_lower:
            return "/hr2/api/leave-applications/1/submit-document/"
        if "nominee" in action_lower:
            return "/hr2/api/leave-nominee/1/"
        if "extension" in action_lower:
            return "/hr2/api/leave-applications/1/extension-request/"
        if "cancellation" in action_lower or "cancel" in action_lower:
            return "/hr2/api/leave-applications/1/cancel-request/"
        if "withdraw" in action_lower:
            return "/hr2/api/leave-applications/1/withdraw/"
        if "download" in action_lower:
            return "/hr2/api/leave-applications/1/download/"
        if "leave" in action_lower:
            return "/hr2/api/leave-applications/"
        return "/hr2/api/leave-applications/"

    def _method_for_action(self, action_text: str) -> str:
        action_lower = action_text.lower()
        if "download" in action_lower:
            return "GET"
        if "apply" in action_lower or "request" in action_lower or "submit" in action_lower:
            return "POST"
        if "withdraw" in action_lower or "approve" in action_lower or "reject" in action_lower or "forward" in action_lower:
            return "POST"
        return "POST"

    def _dispatch(self, method: str, path: str, payload: Dict[str, Any]):
        if method == "POST":
            return self.api_post(path, payload, expected_status=None)
        if method == "PUT":
            return self.api_put(path, payload, expected_status=None)
        if method == "DELETE":
            return self.api_delete(path, expected_status=None)
        return self.api_get(path, expected_status=None)


def _load_business_rules() -> Dict[str, Any]:
    specs_path = os.path.join(os.path.dirname(__file__), "specs", "business_rules.yaml")
    with open(specs_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")
    return slug.lower() or "rule"


def _expected_statuses(valid_case: bool) -> Tuple[int, ...]:
    return (200, 201) if valid_case else (400, 401, 403, 404, 302)


def _build_test(rule: Dict[str, Any], case: Dict[str, Any], valid_case: bool, index: int):
    def _test(self: HR2BRTestBase):
        suffix = "V" if valid_case else "I"
        self._test_id = f"{rule.get('id')}-{suffix}-{index:02d}"
        self._br_id = rule.get("id")
        self._test_category = "Valid" if valid_case else "Invalid"
        self._input_action = case.get("input_action", "")
        self._expected_result = case.get("expected_result", "")

        self._login_for_action(self._input_action)
        method = self._method_for_action(self._input_action)
        path = self._endpoint_for_action(self._input_action)
        path = self._resolve_path(path)
        payload = self._payload_for(path, self._input_action, valid_case)
        response = self._dispatch(method, path, payload)
        expected = _expected_statuses(valid_case)

        if response.status_code in expected:
            self._record_result("Expected response", "Pass", str(getattr(response, "data", "")))
        else:
            self._record_result(
                f"Unexpected status {response.status_code}",
                "Fail",
                str(getattr(response, "data", "")),
            )
            self.fail(f"Expected status in {expected}, got {response.status_code}")

    return _test


def _generate_br_tests():
    specs = _load_business_rules()
    rules = specs.get("business_rules", [])
    for rule in rules:
        class_name = f"Test_{rule.get('id', 'BR')}_{_slugify(rule.get('title', 'rule'))}"
        attrs: Dict[str, Any] = {"__doc__": f"{rule.get('id')}: {rule.get('title')}"}

        for valid_case, key in ((True, "valid_tests"), (False, "invalid_tests")):
            cases = rule.get(key, []) or []
            for index, case in enumerate(cases, start=1):
                prefix = "valid" if valid_case else "invalid"
                name = f"test_{prefix}_{index:02d}_{_slugify(case.get('input_action', 'case'))}"
                attrs[name] = _build_test(rule, case, valid_case, index)

        globals()[class_name] = type(class_name, (HR2BRTestBase,), attrs)


_generate_br_tests()
