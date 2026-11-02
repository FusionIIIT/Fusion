"""API wiring, authentication boundaries and integration endpoints."""

from django.urls import reverse

from applications.visitor_management.tests.conftest import VmsTestBase


class TestApiWiring(VmsTestBase):
    def test_module_mounted_under_vms(self):
        self.assertEqual(reverse("vms:me"), "/vms/api/me/")
        self.assertEqual(reverse("vms:vms"), "/vms/")  # notification URL name

    def test_staff_endpoints_require_authentication(self):
        for path in ("/vms/api/me/", "/vms/api/dashboard/", "/vms/api/host/requests/", "/vms/api/admin/policies/",
                     "/vms/api/superadmin/roles/", "/vms/api/audit-logs/"):
            self.assertIn(self.get(path).status_code, (401, 403), path)

    def test_me_reports_roles(self):
        roles = self.get("/vms/api/me/", user=self.security).data["roles"]
        self.assertEqual(roles["security"][0]["gate"], "MAIN")
        self.assertFalse(roles["super_admin"])
        self.assertTrue(self.get("/vms/api/me/", user=self.host_user).data["roles"]["host"])

    def test_public_host_lookup_hides_contact_details(self):
        response = self.get("/vms/api/public/hosts/", {"q": "Asha"})
        self.assertEqual(response.data[0]["id"], self.host.pk)
        self.assertNotIn("email", response.data[0])
        self.assertEqual(self.get("/vms/api/public/hosts/", {"q": "student1"}).data, [])

    def test_staff_views_never_expose_visitor_credentials(self):
        visit, _ = self.active_visit()
        detail = self.get("/vms/api/visits/{}/".format(visit.reference), user=self.security).data
        self.assertNotIn("qr_token", detail["visit_pass"])
        self.assertNotIn("otp", detail["visit_pass"])
        self.assertTrue(detail["visitor"]["id_doc_number"].startswith("*"))

    def test_visit_detail_restricted_to_involved_staff(self):
        visit, _ = self.pending_visit()
        self.assertEqual(self.get("/vms/api/visits/{}/".format(visit.reference), user=self.other_host_user).status_code, 403)
        self.assertEqual(self.get("/vms/api/visits/{}/".format(visit.reference), user=self.host_user).status_code, 200)


class TestIntegrations(VmsTestBase):
    def key(self, name):
        return self.post("/vms/api/superadmin/integrations/{}/rotate-key/".format(name), user=self.superadmin).data["api_key"]

    def test_acs_door_reader_validates_against_zone_policy(self):
        visit, _ = self.on_site_visit(requested_zones=["LABS"])
        key = self.key("ACCESS_CONTROL")
        response = self.post("/vms/api/integrations/acs/validate/", {
            "credential_type": "QR", "credential": visit.visit_pass.qr_token, "zone": "LABS", "device_id": "DOOR-7"},
            integration_key=key)
        self.assertEqual(response.data, {"allowed": True, "basis": "PASS_PERMISSION"})

    def test_wrong_key_rejected(self):
        self.key("ACCESS_CONTROL")
        response = self.post("/vms/api/integrations/acs/validate/", {"credential_type": "QR", "credential": "x",
                                                                     "zone": "LABS"}, integration_key="wrong")
        self.assertEqual(response.status_code, 401)

    def test_hostel_feed_shares_only_hostel_area_logs(self):
        visit, _ = self.active_visit(requested_zones=["HOSTEL"])
        self.scan(visit, gate="HOSTEL_GATE", user=self.hostel_guard)
        other, _ = self.active_visit(full_name="Other", id_doc_number="OTH-1", phone="9555555555")
        self.scan(other)
        response = self.get("/vms/api/integrations/hostel/visit-logs/", integration_key=self.key("HOSTEL_MANAGEMENT"))
        self.assertEqual([r["reference"] for r in response.data["results"]], [visit.reference])

    def test_non_keyed_integration_cannot_get_key(self):
        response = self.post("/vms/api/superadmin/integrations/EMAIL/rotate-key/", user=self.superadmin)
        self.assertEqual(response.status_code, 400)
