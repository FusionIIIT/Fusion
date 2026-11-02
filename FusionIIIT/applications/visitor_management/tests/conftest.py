"""Shared fixtures for the VMS test suite (Django TestCase, no pytest needed)."""

import datetime
from pathlib import Path

import yaml
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation
from applications.visitor_management.constants import RoleScope, VisitStatus, VmsRole, ZoneAccessLevel
from applications.visitor_management.models import Gate, VisitPass, VisitRequest, VmsRoleAssignment, Zone

SPECS_DIR = Path(__file__).resolve().parent / "specs"


def load_catalog(filename, key):
    with (SPECS_DIR / filename).open("r", encoding="utf-8") as handle:
        return (yaml.safe_load(handle) or {}).get(key, [])


class VmsTestBase(TestCase):
    """Campus with zones/gates, one user per VMS role, and API/visit helpers."""

    def setUp(self):
        cache.clear()  # reset DRF throttle counters between tests
        self.now = timezone.now()
        self.dept = DepartmentInfo.objects.create(name="CSE")
        self.common = Zone.objects.create(code="COMMON", name="Common areas", access_level=ZoneAccessLevel.PUBLIC)
        self.acad = Zone.objects.create(code="ACAD", name="Academic block")
        self.labs = Zone.objects.create(code="LABS", name="Research labs")
        self.hostel = Zone.objects.create(code="HOSTEL", name="Hostel area", is_hostel_area=True)
        self.main_gate = Gate.objects.create(code="MAIN", name="Main gate")
        self.hostel_gate = Gate.objects.create(code="HOSTEL_GATE", name="Hostel gate", zone=self.hostel)

        self.superadmin = self.make_user("superadmin", "staff")
        designation = Designation.objects.create(name="vms_super_admin", full_name="VMS Super Admin")
        HoldsDesignation.objects.create(user=self.superadmin, working=self.superadmin, designation=designation)
        self.admin = self.make_user("campusadmin", "staff")
        self.assign(self.admin, VmsRole.ADMIN, RoleScope.CAMPUS)
        self.zone_admin = self.make_user("labsadmin", "staff")
        self.assign(self.zone_admin, VmsRole.ADMIN, RoleScope.ZONE, zone=self.labs)
        self.security = self.make_user("guard", "staff")
        self.assign(self.security, VmsRole.SECURITY, RoleScope.GATE, gate=self.main_gate)
        self.hostel_guard = self.make_user("hostelguard", "staff")
        self.assign(self.hostel_guard, VmsRole.SECURITY, RoleScope.GATE, gate=self.hostel_gate)
        self.zone_guard = self.make_user("labsguard", "staff")
        self.assign(self.zone_guard, VmsRole.SECURITY, RoleScope.ZONE, zone=self.labs)
        self.host_user = self.make_user("prof", "faculty", first_name="Asha", last_name="Rao")
        self.host = self.host_user.extrainfo
        self.other_host_user = self.make_user("staffhost", "staff", first_name="Ravi", last_name="Kumar")
        self.student = self.make_user("student1", "student")

    # ------------------------------------------------------------------ users

    def make_user(self, username, user_type, **names):
        user = User.objects.create_user(username=username, password="pw", email=username + "@iiitdmj.ac.in", **names)
        ExtraInfo.objects.create(id=username.upper(), user=user, user_type=user_type, department=self.dept)
        return user

    def assign(self, user, role, scope, zone=None, gate=None, days=30):
        return VmsRoleAssignment.objects.create(
            user=user, role=role, scope_type=scope, zone=zone, gate=gate,
            valid_from=timezone.now() - datetime.timedelta(minutes=5),
            valid_until=timezone.now() + datetime.timedelta(days=days))

    # -------------------------------------------------------------------- api

    def client_for(self, user=None, visitor_token=None, integration_key=None):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)
        if visitor_token:
            client.credentials(HTTP_X_VISITOR_TOKEN=visitor_token)
        if integration_key:
            client.credentials(HTTP_X_VMS_INTEGRATION_KEY=integration_key)
        return client

    def post(self, path, data=None, user=None, fmt="json", **kwargs):
        return self.client_for(user, **kwargs).post(path, data or {}, format=fmt)

    def get(self, path, data=None, user=None, **kwargs):
        return self.client_for(user, **kwargs).get(path, data or {})

    def patch(self, path, data=None, user=None):
        return self.client_for(user).patch(path, data or {}, format="json")

    def put(self, path, data=None, user=None):
        return self.client_for(user).put(path, data or {}, format="json")

    # ----------------------------------------------------------------- visits

    @staticmethod
    def fmt(moment):
        return moment.strftime("%Y-%m-%dT%H:%M:%S")

    def visitor_payload(self, **overrides):
        start = overrides.pop("start", timezone.now() + datetime.timedelta(hours=3))
        end = overrides.pop("end", start + datetime.timedelta(hours=2))
        payload = {
            "full_name": "Meera Iyer",
            "phone": "+91 98765 43210",
            "email": "meera@example.com",
            "organization": "Example Labs",
            "id_doc_type": "NATIONAL_ID",
            "id_doc_number": "ABCD-1234-5678",
            "purpose": "OFFICIAL",
            "purpose_details": "Project review",
            "host_id": self.host.pk,
            "scheduled_start": self.fmt(start),
            "scheduled_end": self.fmt(end),
            "requested_zones": ["ACAD"],
        }
        payload.update(overrides)
        return payload

    def pre_register(self, token=None, **overrides):
        return self.post("/vms/api/public/visits/", self.visitor_payload(**overrides), visitor_token=token)

    def pending_visit(self, **overrides):
        response = self.pre_register(**overrides)
        self.assertEqual(response.status_code, 201, response.data)
        return VisitRequest.objects.get(reference=response.data["visit"]["reference"]), response.data["visitor_token"]

    def approve(self, visit, user=None, **data):
        payload = {"decision": "APPROVE"}
        payload.update(data)
        response = self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), payload,
                             user=user or self.host_user)
        self.assertEqual(response.status_code, 200, response.data)
        visit.refresh_from_db()
        return visit

    def make_valid_now(self, visit):
        """Simulate the scheduled time arriving (validity window contains now)."""
        moment = timezone.now()
        VisitPass.objects.filter(visit=visit).update(valid_from=moment - datetime.timedelta(minutes=1),
                                                     valid_until=moment + datetime.timedelta(hours=2))
        visit.refresh_from_db()
        return visit

    def active_visit(self, **overrides):
        visit, token = self.pending_visit(**overrides)
        self.approve(visit)
        return self.make_valid_now(visit), token

    def scan(self, visit, gate="MAIN", user=None, **extra):
        payload = {"credential_type": "QR", "credential": visit.visit_pass.qr_token, "gate": gate,
                   "device_id": "GATE-SCANNER-1"}
        payload.update(extra)
        return self.post("/vms/api/security/gate/validate/", payload, user=user or self.security)

    def on_site_visit(self, **overrides):
        visit, token = self.active_visit(**overrides)
        response = self.scan(visit)
        self.assertTrue(response.data["allowed"], response.data)
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitStatus.ON_SITE)
        return visit, token

    def walk_in_payload(self, **overrides):
        payload = self.visitor_payload()
        for key in ("scheduled_start", "scheduled_end"):
            payload.pop(key)
        payload.update({"gate": "MAIN", "full_name": "Walk In Visitor", "id_doc_number": "WALK-0001",
                        "phone": "9000000001"})
        payload.update(overrides)
        return payload

    def publish_blacklist(self, list_type="BLACKLIST", **identity):
        values = {"list_type": list_type, "full_name": "Banned Person", "id_doc_number": "BAN-9999",
                  "reason": "Prior incident", "severity": "HIGH"}
        values.update(identity)
        created = self.post("/vms/api/admin/registry/", values, user=self.admin)
        self.assertEqual(created.status_code, 201, created.data)
        published = self.post("/vms/api/admin/registry/publish/", {}, user=self.admin)
        self.assertEqual(published.status_code, 200, published.data)
        return created.data
