from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation
from applications.iwdModuleV2.models import Requests


class BaseModuleTestCase(TestCase):
    API_BASE = "/iwdModuleV2/api"

    @classmethod
    def setUpTestData(cls):
        cls.department, _ = DepartmentInfo.objects.get_or_create(name="CSE")

        # Required users provided by you
        cls.user_acc = cls._get_existing_user("iwd_acc")
        cls.user_adm = cls._get_existing_user("iwd_adm")
        cls.user_audit = cls._get_existing_user("iwd_audit")
        cls.user_director = cls._get_existing_user("iwd_director")
        cls.user_hod = cls._get_existing_user("iwd_hod")
        cls.user_worker = cls._get_existing_user("iwd_worker")

        # ExtraInfo records
        cls.extra_acc = cls._get_existing_extrainfo(cls.user_acc)
        cls.extra_adm = cls._get_existing_extrainfo(cls.user_adm)
        cls.extra_audit = cls._get_existing_extrainfo(cls.user_audit)
        cls.extra_director = cls._get_existing_extrainfo(cls.user_director)
        cls.extra_hod = cls._get_existing_extrainfo(cls.user_hod)
        cls.extra_worker = cls._get_existing_extrainfo(cls.user_worker)

        for extra in [
            cls.extra_acc,
            cls.extra_adm,
            cls.extra_audit,
            cls.extra_director,
            cls.extra_hod,
            cls.extra_worker,
        ]:
            if extra.department_id is None:
                extra.department = cls.department
                extra.save(update_fields=["department"])

        # IWD role mappings used by module auth checks
        cls._require_designation(cls.user_worker, "Electrical_AE")
        cls._require_designation(cls.user_adm, "Admin IWD")
        cls._require_designation(cls.user_hod, "HOD (CSE)")
        cls._require_designation(cls.user_director, "Director")
        cls._require_designation(cls.user_audit, "Auditor")
        cls._require_designation(cls.user_acc, "Accounts Admin")

    @classmethod
    def _get_existing_user(cls, username):
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password("institute123")
            user.save(update_fields=["password"])
        return user

    @classmethod
    def _get_existing_extrainfo(cls, user):
        extra_info, _ = ExtraInfo.objects.get_or_create(
            user=user,
            defaults={
                "id": user.username,
                "user_type": "staff",
                "department": cls.department,
            },
        )
        if extra_info.department_id is None:
            extra_info.department = cls.department
            extra_info.save(update_fields=["department"])
        return extra_info

    @classmethod
    def _require_designation(cls, user, designation_name):
        designation, _ = Designation.objects.get_or_create(
            name=designation_name,
            defaults={
                "full_name": designation_name,
                "type": "administrative",
            },
        )

        HoldsDesignation.objects.get_or_create(
            user=user,
            working=user,
            designation=designation,
        )

    def setUp(self):
        self.client = APIClient()

        self._results = []
        self._steps = []

        self._test_id = ""
        self._uc_id = ""
        self._br_id = ""
        self._wf_id = ""
        self._test_category = ""
        self._scenario = ""
        self._preconditions = ""
        self._input_action = ""
        self._expected_result = ""

    def _set_selected_role(self, role_name):
        session = self.client.session
        session["currentDesignationSelected"] = role_name
        session.save()

    def _set_last_role(self, extra_obj, role_name):
        extra_obj.last_selected_role = role_name
        extra_obj.save(update_fields=["last_selected_role"])

    # Primary role-based logins
    def login_as_worker(self):
        self.client.force_authenticate(user=self.user_worker)
        self._set_selected_role("Electrical_AE")
        self._set_last_role(self.extra_worker, "Electrical_AE")

    def login_as_admin(self):
        self.client.force_authenticate(user=self.user_adm)
        self._set_selected_role("Admin IWD")
        self._set_last_role(self.extra_adm, "Admin IWD")

    def login_as_hod(self):
        self.client.force_authenticate(user=self.user_hod)
        self._set_selected_role("HOD (CSE)")
        self._set_last_role(self.extra_hod, "HOD (CSE)")

    def login_as_dean(self):
        # Alias kept for compatibility with older tests; HOD role is used in this setup.
        self.login_as_hod()

    def login_as_director(self):
        self.client.force_authenticate(user=self.user_director)
        self._set_selected_role("Director")
        self._set_last_role(self.extra_director, "Director")

    def login_as_auditor(self):
        self.client.force_authenticate(user=self.user_audit)
        self._set_selected_role("Auditor")
        self._set_last_role(self.extra_audit, "Auditor")

    def login_as_accounts(self):
        self.client.force_authenticate(user=self.user_acc)
        self._set_selected_role("Accounts Admin")
        self._set_last_role(self.extra_acc, "Accounts Admin")

    # Backward-compatible aliases
    def login_as_requester(self):
        self.login_as_worker()

    def logout(self):
        self.client.force_authenticate(user=None)

    def _full_url(self, endpoint):
        endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        return f"{self.API_BASE}{endpoint}"

    def api_get(self, endpoint, params=None, expected_status=200):
        response = self.client.get(self._full_url(endpoint), params or {}, format="json")
        if expected_status is not None:
            self.assertEqual(
                response.status_code,
                expected_status,
                msg=f"GET {endpoint} expected {expected_status}, got {response.status_code}. Body: {getattr(response, 'data', response.content)}",
            )
        return response

    def api_post(self, endpoint, data=None, expected_status=200, format_type="json"):
        response = self.client.post(self._full_url(endpoint), data or {}, format=format_type)
        if expected_status is not None:
            self.assertEqual(
                response.status_code,
                expected_status,
                msg=f"POST {endpoint} expected {expected_status}, got {response.status_code}. Body: {getattr(response, 'data', response.content)}",
            )
        return response

    def api_put(self, endpoint, data=None, expected_status=200):
        response = self.client.put(self._full_url(endpoint), data or {}, format="json")
        if expected_status is not None:
            self.assertEqual(
                response.status_code,
                expected_status,
                msg=f"PUT {endpoint} expected {expected_status}, got {response.status_code}. Body: {getattr(response, 'data', response.content)}",
            )
        return response

    def api_patch(self, endpoint, data=None, expected_status=200):
        response = self.client.patch(self._full_url(endpoint), data or {}, format="json")
        if expected_status is not None:
            self.assertEqual(
                response.status_code,
                expected_status,
                msg=f"PATCH {endpoint} expected {expected_status}, got {response.status_code}. Body: {getattr(response, 'data', response.content)}",
            )
        return response

    def today(self):
        return date.today().isoformat()

    def future_date(self, days):
        return (date.today() + timedelta(days=days)).isoformat()

    def past_date(self, days):
        return (date.today() - timedelta(days=days)).isoformat()

    def _record_result(self, actual, status_label, evidence=""):
        self._results.append(
            {
                "actual": str(actual),
                "status": str(status_label),
                "evidence": str(evidence),
            }
        )

    def _add_step(self, step_no, action, expected, actual, passed):
        self._steps.append(
            {
                "step": step_no,
                "action": str(action),
                "expected": str(expected),
                "actual": str(actual),
                "passed": bool(passed),
            }
        )

    def _all_steps_passed(self):
        return bool(self._steps) and all(step["passed"] for step in self._steps)

    def get_request(self, request_id):
        return Requests.objects.get(id=request_id)


class UCTestBase(BaseModuleTestCase):
    pass


class BRTestBase(BaseModuleTestCase):
    pass


class WFTestBase(BaseModuleTestCase):
    pass