import json
import traceback
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient

from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation

User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        # Use DRF client because the patent_system API is protected by TokenAuthentication.
        self.client = APIClient()
        self.API_PREFIX = "/patentsystem/"

        # Minimal shared fixtures
        self.department, _ = DepartmentInfo.objects.get_or_create(name="CSE")

        # Core users used across tests
        self.applicant_user = self._create_user(
            username="applicant1",
            email="applicant1@example.com",
            user_type="faculty",
        )
        self.coinventor_user = self._create_user(
            username="inventor2",
            email="inventor2@example.com",
            user_type="faculty",
        )
        self.outsider_user = self._create_user(
            username="outsider",
            email="outsider@example.com",
            user_type="student",
        )

        # Role users (designation-backed)
        self.pcc_admin_user = self._create_user(
            username="pccadmin",
            email="pccadmin@example.com",
            user_type="staff",
            designation_name="pcc_admin",
        )
        self.director_user = self._create_user(
            username="director",
            email="director@example.com",
            user_type="faculty",
            designation_name="director",
        )

        # Default to no authentication (tests should opt-in)
        self.logout()

    # -----------------------------
    # 👤 FIXTURE HELPERS
    # -----------------------------
    def _create_user(self, username, email, user_type, designation_name=None):
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        if not created and user.email != email:
            user.email = email
        user.set_password("pass")
        user.save()

        # ExtraInfo is required by token generation and department-based logic.
        # NOTE: ExtraInfo.id is (in this codebase) a primary key.
        # Do not overwrite it for an existing record; doing so can force an
        # INSERT and trip the unique constraint on user_id (especially with --keepdb).
        extra_defaults = {
            "user_type": user_type,
            "department": self.department,
        }
        extra_info, extra_created = ExtraInfo.objects.get_or_create(
            user=user,
            defaults={
                "id": (username[:3].upper() + uuid.uuid4().hex[:6]).upper(),
                **extra_defaults,
            },
        )
        if not extra_created:
            changed = False
            for key, value in extra_defaults.items():
                if getattr(extra_info, key) != value:
                    setattr(extra_info, key, value)
                    changed = True
            if changed:
                extra_info.save()

        if designation_name:
            designation, _ = Designation.objects.get_or_create(
                name=designation_name,
                defaults={"full_name": designation_name, "type": "administrative"},
            )
            HoldsDesignation.objects.get_or_create(
                user=user,
                working=user,
                designation=designation,
            )

        return user

    # -----------------------------
    # 🔐 AUTH METHODS (FIXED)
    # -----------------------------
    def login_as_applicant(self):
        self.client.force_authenticate(user=self.applicant_user)
        return self.applicant_user

    def login_as_coinventor(self):
        self.client.force_authenticate(user=self.coinventor_user)
        return self.coinventor_user

    def login_as_outsider(self):
        self.client.force_authenticate(user=self.outsider_user)
        return self.outsider_user

    def login_as_pcc_admin(self):
        self.client.force_authenticate(user=self.pcc_admin_user)
        return self.pcc_admin_user

    def login_as_director(self):
        self.client.force_authenticate(user=self.director_user)
        return self.director_user

    def logout(self):
        # DRF client auth
        self.client.force_authenticate(user=None)

    # -----------------------------
    # 🧰 COMMON PAYLOADS
    # -----------------------------
    def make_submit_payload(self, *, title="Test Patent", inventor_shares=None):
        """Build a minimal valid payload for UC-001 submit_application service."""
        if inventor_shares is None:
            inventor_shares = [
                (self.applicant_user, 50),
                (self.coinventor_user, 50),
            ]

        inventors = []
        for user, pct in inventor_shares:
            inventors.append(
                {
                    "name": user.get_full_name() or user.username,
                    "institute_mail": user.email,
                    "personal_mail": user.email,
                    "mobile": "9999999999",
                    "address": "Campus",
                    "percentage": pct,
                }
            )

        return {
            "title": title,
            "inventors": inventors,
            "area_of_invention": "AI",
            "problem_statement": "Problem",
            "objective": "Objective",
            "ip_type": "Patent",
            "novelty": "Novelty",
            "advantages": "Advantages",
            "tested_experimentally": False,
            "applications": "Use cases",
            "funding_details": "Self",
            "funding_source": "Institute",
            "publication_details": "None",
            "mou_details": "None",
            "research_details": "Details",
            "company_details": [
                {
                    "company_name": "Acme",
                    "contact_person": "Alice",
                    "contact_no": "9999999999",
                }
            ],
            "development_stage": "Embryonic",
        }

    def post_submit_application(self, payload):
        """POST UC-001 endpoint; returns (response, application_id|None)."""
        url = self.API_PREFIX + "applicant/applications/submit/"
        resp = self.client.post(url, {"json_data": json.dumps(payload)}, format="multipart")
        app_id = None
        try:
            app_id = resp.json().get("application_id")
        except Exception:
            app_id = None
        return resp, app_id

    def post_give_consent(self, application_id):
        url = self.API_PREFIX + f"applicant/applications/{application_id}/consent/"
        return self.client.post(url, {}, format="json")

    # -----------------------------
    # 🧠 TEST WRAPPER (SAFE)
    # -----------------------------
    def _callTestMethod(self, method):
        try:
            method()

        except AssertionError:
            if not getattr(self, "_results", None):
                self._record_result(
                    getattr(self, "_test_id", "") or self.id(),
                    getattr(self, "_scenario", "") or "Assertion failed",
                    "Fail",
                    actual="Assertion failed",
                    evidence=traceback.format_exc(),
                )
            raise

        except Exception as exc:
            if not getattr(self, "_results", None):
                self._record_result(
                    getattr(self, "_test_id", "") or self.id(),
                    getattr(self, "_scenario", "") or "Unhandled exception",
                    "Error",
                    actual=str(exc),
                    evidence=traceback.format_exc(),
                )
            raise AssertionError(str(exc))

        else:
            if not getattr(self, "_results", None):
                self._record_result(
                    getattr(self, "_test_id", "") or self.id(),
                    getattr(self, "_scenario", "") or "Completed",
                    "Pass",
                    actual="OK",
                    evidence="",
                )

    # -----------------------------
    # 📊 RESULT RECORDING
    # -----------------------------
    def _record_result(self, test_id="", scenario="", status="Pass", actual="", evidence=""):

        # Backward compatibility handling
        if (
            scenario in {"Pass", "Fail", "Error", "Partial"}
            and test_id
            and not str(test_id).startswith(("PMS-UC-", "PMS-WF-", "BR-"))
        ):
            test_id, scenario, status = getattr(self, "_test_id", ""), str(test_id), str(scenario)

        if test_id:
            self._test_id = str(test_id)

        self._scenario = str(scenario)

        entry = {
            "status": status,
            "actual": actual,
            "evidence": evidence
        }

        if not hasattr(self, "_results") or self._results is None:
            self._results = [entry]
        elif len(self._results) == 0:
            self._results = [entry]
        else:
            self._results[0] = entry

        # ID mapping for summary
        normalized_test_id = str(test_id or getattr(self, "_test_id", "") or "")
        parts = normalized_test_id.split("-")

        if normalized_test_id.startswith("PMS-UC-") and len(parts) >= 3 and not getattr(self, "_uc_id", ""):
            self._uc_id = "-".join(parts[:3])
        elif normalized_test_id.startswith("BR-") and len(parts) >= 3 and not getattr(self, "_br_id", ""):
            self._br_id = "-".join(parts[:3])
        elif normalized_test_id.startswith("PMS-WF-") and len(parts) >= 3 and not getattr(self, "_wf_id", ""):
            self._wf_id = "-".join(parts[:3])

    # -----------------------------
    # 🔄 WORKFLOW HELPERS
    # -----------------------------
    def _add_step(self, step_no, action, expected, actual, passed):
        if not hasattr(self, "_steps"):
            self._steps = []

        self._steps.append({
            "step_no": step_no,
            "action": action,
            "expected": expected,
            "actual": actual,
            "status": "Pass" if passed else "Fail",
        })

    def _all_steps_passed(self):
        steps = getattr(self, "_steps", []) or []
        return all(step.get("status") == "Pass" for step in steps)

    # -----------------------------
    # 🌐 SAFE API METHODS
    # -----------------------------
    def api_get(self, url, *, expected_status=None, query=None):
        resp = self.client.get(url, data=query or {}, format="json")
        if expected_status is not None:
            self.assertEqual(resp.status_code, expected_status, msg=getattr(resp, "content", b"")[:500])
        return resp

    def api_post(self, url, data=None, *, expected_status=None, as_json=True):
        fmt = "json" if as_json else "multipart"
        resp = self.client.post(url, data or {}, format=fmt)
        if expected_status is not None:
            self.assertEqual(resp.status_code, expected_status, msg=getattr(resp, "content", b"")[:500])
        return resp

    def api_patch(self, url, data=None, *, expected_status=None):
        resp = self.client.patch(url, data or {}, format="json")
        if expected_status is not None:
            self.assertEqual(resp.status_code, expected_status, msg=getattr(resp, "content", b"")[:500])
        return resp

    def api_put(self, url, data=None, *, expected_status=None):
        resp = self.client.put(url, data or {}, format="json")
        if expected_status is not None:
            self.assertEqual(resp.status_code, expected_status, msg=getattr(resp, "content", b"")[:500])
        return resp

    def api_delete(self, url, data=None, *, expected_status=None):
        resp = self.client.delete(url, data or {}, format="json")
        if expected_status is not None:
            self.assertEqual(resp.status_code, expected_status, msg=getattr(resp, "content", b"")[:500])
        return resp


class UCTestBase(BaseTestCase):
    pass


class BRTestBase(BaseTestCase):
    pass


class WFTestBase(BaseTestCase):
    pass