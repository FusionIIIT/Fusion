"""Use-case scenarios from specs/use_cases.yaml (VMS Use Case Specifications v1.3).

Every active UC has a happy path and an exception path; alternate paths are
covered where the UC defines a distinct alternative outcome.
"""

import datetime
import io

from django.core import mail
from django.utils import timezone

from applications.visitor_management.constants import (
    AlertStatus,
    GateAttemptStatus,
    MusterStatus,
    OfflineEventStatus,
    PassType,
    RollCallStatus,
    VisitStatus,
    VmsRole,
)
from applications.visitor_management.models import (
    AuditLog,
    EmergencyMuster,
    ExtensionRequest,
    GateAttempt,
    IntegrationConfig,
    OfflineGateEvent,
    SecurityAlert,
    VipPermission,
    VisitLog,
    VisitPass,
    VisitRequest,
    VmsNotification,
    VmsRoleAssignment,
)
from applications.visitor_management.services import gate as gate_services
from applications.visitor_management.services import lifecycle
from applications.visitor_management.tests.conftest import VmsTestBase, load_catalog

H = datetime.timedelta(hours=1)


class TestUseCaseCatalog(VmsTestBase):
    def test_every_active_use_case_is_catalogued_with_three_scenarios(self):
        catalog = load_catalog("use_cases.yaml", "use_cases")
        ids = {uc["source_id"] for uc in catalog}
        expected = {"VMS-UC-{:03d}".format(n) for n in range(1, 41)} - {"VMS-UC-029"}
        self.assertEqual(ids, expected)  # 39 active UCs, UC-029 retired
        for uc in catalog:
            self.assertEqual(sorted(uc["scenarios"]), ["alternate_path", "exception_path", "happy_path"])
            self.assertTrue(uc["endpoint"])


# ----------------------------------------------------------------- Super Admin

class TestUC001ConfigureRoles(VmsTestBase):
    def test_happy_super_admin_assigns_time_bound_role(self):
        response = self.post("/vms/api/superadmin/roles/", {
            "user": "staffhost", "role": "SECURITY", "scope_type": "GATE", "gate": "HOSTEL_GATE",
            "valid_until": self.fmt(timezone.now() + 10 * H)}, user=self.superadmin)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(AuditLog.objects.filter(action="ROLE_ASSIGNED").exists())

    def test_alternate_reassignment_hands_off_pending_work(self):
        visit_response = self.post("/vms/api/security/walk-ins/", self.walk_in_payload(host_unavailable=True),
                                   user=self.security)
        visit = VisitRequest.objects.get(reference=visit_response.data["visit"]["reference"])
        self.assertEqual(visit.assigned_admin, self.admin)
        assignment = VmsRoleAssignment.objects.get(user=self.admin, role=VmsRole.ADMIN)
        response = self.post("/vms/api/superadmin/roles/{}/reassign/".format(assignment.pk), {"user": "staffhost"},
                             user=self.superadmin)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["handoff"]["visit_requests"], 1)
        visit.refresh_from_db()
        self.assertEqual(visit.assigned_admin, self.other_host_user)

    def test_exception_unresolvable_directory_user(self):
        response = self.post("/vms/api/superadmin/roles/", {
            "user": "ghost", "role": "ADMIN", "scope_type": "CAMPUS",
            "valid_until": self.fmt(timezone.now() + H)}, user=self.superadmin)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(VmsRoleAssignment.objects.filter(user__username="ghost").exists())


class TestUC002IntegrationBoundaries(VmsTestBase):
    def test_happy_configuration_recorded(self):
        response = self.put("/vms/api/superadmin/integrations/EMAIL/", {"endpoint_url": "https://mail.iiitdmj.ac.in",
                                                                        "settings": {"from": "vms"}}, user=self.superadmin)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(AuditLog.objects.filter(action="INTEGRATION_CONFIGURED").exists())

    def test_alternate_unavailable_service_saved_but_not_used(self):
        response = self.put("/vms/api/superadmin/integrations/CAMPUS_ID/", {"status": "UNAVAILABLE"},
                            user=self.superadmin)
        self.assertEqual(response.status_code, 200)
        lookup = self.get("/vms/api/public/hosts/", {"q": "Asha"})
        self.assertEqual(lookup.status_code, 503)

    def test_exception_invalid_endpoint_rejected_and_logged(self):
        response = self.put("/vms/api/superadmin/integrations/SMS/", {"endpoint_url": "not a url"}, user=self.superadmin)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(AuditLog.objects.filter(action="INTEGRATION_CONFIG_REJECTED").exists())
        self.assertFalse(IntegrationConfig.objects.filter(key="SMS").exists())


class TestUC003VipPermissions(VmsTestBase):
    def vip(self, **extra):
        data = {"full_name": "Dr VIP", "id_doc_number": "VIP-0001", "zone_scope": "ALL",
                "valid_until": self.fmt(timezone.now() + 48 * H)}
        data.update(extra)
        return self.post("/vms/api/superadmin/vip/", data, user=self.superadmin)

    def test_happy_vip_permission_recorded_and_applied(self):
        self.assertEqual(self.vip().status_code, 201)
        response = self.pre_register(id_doc_number="VIP-0001", full_name="Dr VIP")
        self.assertEqual(response.data["visit"]["status"], VisitStatus.PASS_ACTIVE)
        self.assertEqual(response.data["visit"]["visit_pass"]["pass_type"], PassType.VIP)

    def test_alternate_revoke(self):
        permission = self.vip().data
        response = self.post("/vms/api/superadmin/vip/{}/revoke/".format(permission["id"]), {}, user=self.superadmin)
        self.assertEqual(response.status_code, 200)
        visit = self.pre_register(id_doc_number="VIP-0001").data["visit"]
        self.assertEqual(visit["status"], VisitStatus.PENDING_HOST_APPROVAL)  # no bypass once revoked

    def test_exception_expired_or_unauthorized(self):
        self.assertEqual(self.vip(valid_until=self.fmt(timezone.now() - H)).status_code, 400)
        response = self.post("/vms/api/superadmin/vip/", {"id_doc_number": "X1",
                                                          "valid_until": self.fmt(timezone.now() + H)}, user=self.admin)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(VipPermission.objects.exists())


class TestUC004AuditTrails(VmsTestBase):
    def test_happy_super_admin_reviews_audit(self):
        self.pending_visit()
        response = self.get("/vms/api/audit-logs/", {"action": "VISIT_PRE_REGISTERED"}, user=self.superadmin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_alternate_no_match_is_empty(self):
        response = self.get("/vms/api/audit-logs/", {"action": "NOPE"}, user=self.superadmin)
        self.assertEqual(response.data["count"], 0)

    def test_exception_unauthorized_denied(self):
        self.assertEqual(self.get("/vms/api/audit-logs/", user=self.host_user).status_code, 403)


# ----------------------------------------------------------------------- Admin

class TestUC005AccessPolicies(VmsTestBase):
    def test_happy_create_and_publish(self):
        draft = self.post("/vms/api/admin/policies/", {"max_visit_duration_minutes": 360,
                                                       "restricted_zones": ["LABS"]}, user=self.admin)
        self.assertEqual(draft.status_code, 201, draft.data)
        published = self.post("/vms/api/admin/policies/{}/publish/".format(draft.data["version"]), {}, user=self.admin)
        self.assertEqual(published.data["status"], "PUBLISHED")
        current = self.get("/vms/api/admin/policies/current/", user=self.admin)
        self.assertEqual(current.data["runtime_values"]["max_visit_duration_minutes"], 360)

    def test_alternate_draft_does_not_affect_runtime(self):
        self.post("/vms/api/admin/policies/", {"max_visit_duration_minutes": 30}, user=self.admin)
        response = self.pre_register()  # 2-hour visit, baseline max 8h still applies
        self.assertEqual(response.status_code, 201)

    def test_exception_invalid_values_or_unauthorized(self):
        bad = self.post("/vms/api/admin/policies/", {"walk_in_pass_duration_minutes": 900}, user=self.admin)
        self.assertEqual(bad.status_code, 400)
        zone_only = self.post("/vms/api/admin/policies/", {}, user=self.zone_admin)
        self.assertEqual(zone_only.status_code, 403)


class TestUC006Registry(VmsTestBase):
    def test_happy_publish_makes_entry_live(self):
        self.publish_blacklist()
        response = self.pre_register(id_doc_number="BAN-9999")
        self.assertEqual(response.status_code, 403)

    def test_alternate_safelist_requires_expiry(self):
        no_expiry = self.post("/vms/api/admin/registry/", {"list_type": "SAFELIST", "id_doc_number": "SAFE-1"},
                              user=self.admin)
        self.assertEqual(no_expiry.status_code, 400)
        ok = self.post("/vms/api/admin/registry/", {"list_type": "SAFELIST", "id_doc_number": "SAFE-1",
                                                   "expires_at": self.fmt(timezone.now() + 24 * H)}, user=self.admin)
        self.assertEqual(ok.status_code, 201)

    def test_exception_duplicate_flagged(self):
        self.post("/vms/api/admin/registry/", {"list_type": "BLACKLIST", "id_doc_number": "DUP-1", "reason": "x"},
                  user=self.admin)
        dup = self.post("/vms/api/admin/registry/", {"list_type": "BLACKLIST", "id_doc_number": "dup 1", "reason": "y"},
                        user=self.admin)
        self.assertEqual(dup.status_code, 409)


class TestUC007Reports(VmsTestBase):
    def test_happy_report_and_exports(self):
        self.on_site_visit()
        report = self.get("/vms/api/admin/reports/visitor_volume/", user=self.admin)
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.data["summary"]["total_check_ins"], 1)
        csv_resp = self.get("/vms/api/admin/reports/peak_hours/", {"export": "csv"}, user=self.admin)
        self.assertEqual(csv_resp["Content-Type"], "text/csv")
        pdf = self.get("/vms/api/admin/reports/daily_summary/", {"export": "pdf"}, user=self.admin)
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_alternate_anonymized_view(self):
        self.on_site_visit()
        report = self.get("/vms/api/admin/reports/frequent_visitors/", {"anonymize": "true"}, user=self.admin)
        self.assertTrue(report.data["rows"][0]["visitor"].startswith("V-"))
        self.assertNotIn("Meera", str(report.data))

    def test_exception_invalid_filters_or_unauthorized(self):
        self.assertEqual(self.get("/vms/api/admin/reports/visitor_volume/", {"date_from": "bad"},
                                  user=self.admin).status_code, 400)
        self.assertEqual(self.get("/vms/api/admin/reports/visitor_volume/", user=self.security).status_code, 403)


class TestUC008BulkLists(VmsTestBase):
    def event(self):
        return self.post("/vms/api/admin/events/", {
            "name": "Placement Drive", "host_id": self.host.pk, "starts_at": self.fmt(timezone.now() - H),
            "ends_at": self.fmt(timezone.now() + 6 * H), "venue_zones": ["ACAD"], "external_event_ref": "EVT-1"},
            user=self.admin).data

    def test_happy_csv_upload_creates_passes(self):
        event = self.event()
        csv_text = ("full_name,phone,email,id_doc_type,id_doc_number\n"
                    "Asha One,9000000011,a1@x.com,NATIONAL_ID,EVT-0001\n"
                    "Bala Two,9000000012,b2@x.com,PASSPORT,EVT-0002\n")
        upload = io.BytesIO(csv_text.encode())
        upload.name = "attendees.csv"
        response = self.post("/vms/api/admin/bulk-lists/", {"kind": "EVENT", "event_id": event["id"], "file": upload},
                             user=self.admin, fmt="multipart")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["rows_accepted"], 2)
        self.assertEqual(VisitPass.objects.filter(visit__event_id=event["id"], pass_type=PassType.PRE_REGISTERED).count(), 2)

    def test_alternate_invalid_rows_rejected_valid_rows_continue(self):
        event = self.event()
        rows = [{"full_name": "Good", "phone": "9000000013", "id_doc_type": "PASSPORT", "id_doc_number": "EVT-0003"},
                {"full_name": "", "phone": "9000000014", "id_doc_type": "PASSPORT", "id_doc_number": "EVT-0004"}]
        response = self.post("/vms/api/admin/bulk-lists/", {"kind": "EVENT", "event_id": event["id"], "rows": rows},
                             user=self.admin)
        self.assertEqual((response.data["rows_accepted"], response.data["rows_rejected"]), (1, 1))

    def test_exception_missing_event_context(self):
        response = self.post("/vms/api/admin/bulk-lists/", {"kind": "EVENT", "rows": [{"full_name": "x"}]},
                             user=self.admin)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(VisitPass.objects.count(), 0)


class TestUC009SpecialEventHandling(VmsTestBase):
    def ready_event(self):
        event = TestUC008BulkLists.event(self)
        self.post("/vms/api/admin/bulk-lists/", {"kind": "EVENT", "event_id": event["id"], "rows": [
            {"full_name": "Fast Lane", "phone": "9000000021", "id_doc_type": "PASSPORT", "id_doc_number": "EVT-0101"}]},
            user=self.admin)
        return event

    def test_happy_controls_active_and_fast_lane_scans(self):
        event = self.ready_event()
        response = self.post("/vms/api/admin/events/{}/controls/".format(event["id"]), {"fast_lane_enabled": True},
                             user=self.admin)
        self.assertEqual(response.data["status"], "CONTROLS_ACTIVE")
        visit = VisitRequest.objects.get(event_id=event["id"])
        scan = self.scan(visit, lane="FAST")
        self.assertTrue(scan.data["allowed"], scan.data)
        detail = self.get("/vms/api/admin/events/{}/".format(event["id"]), user=self.admin)
        self.assertEqual(detail.data["attendance"]["attended"], 1)

    def test_alternate_disabled_controls_stay_inactive(self):
        event = self.ready_event()
        self.post("/vms/api/admin/events/{}/controls/".format(event["id"]), {"fast_lane_enabled": False}, user=self.admin)
        visit = VisitRequest.objects.get(event_id=event["id"])
        self.assertEqual(self.scan(visit, lane="FAST").status_code, 400)

    def test_exception_invalid_settings_rejected(self):
        event = self.ready_event()
        response = self.post("/vms/api/admin/events/{}/controls/".format(event["id"]),
                             {"overflow_walk_in_enabled": True}, user=self.admin)
        self.assertEqual(response.status_code, 400)


# --------------------------------------------------------------------- Visitor

class TestUC010PreRegister(VmsTestBase):
    def test_happy_pending_request_and_host_notified(self):
        response = self.pre_register()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["visit"]["status"], VisitStatus.PENDING_HOST_APPROVAL)
        self.assertIn("visitor_token", response.data)
        self.assertTrue(VmsNotification.objects.filter(recipient_user=self.host_user,
                                                       event_type="REQUEST_PENDING_FOR_HOST").exists())

    def test_alternate_same_day_urgent_routes_to_admin(self):
        start = timezone.now() + datetime.timedelta(minutes=30)
        if start.date() != timezone.now().date():
            self.skipTest("too close to midnight for a same-day case")
        response = self.pre_register(start=start, end=start + H, is_urgent=True)
        self.assertEqual(response.data["visit"]["status"], VisitStatus.PENDING_ADMIN_EXCEPTION)

    def test_exception_invalid_data_creates_nothing(self):
        response = self.pre_register(id_doc_type="LIBRARY_CARD")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(VisitRequest.objects.count(), 0)


class TestUC011TrackStatus(VmsTestBase):
    def test_happy_visitor_sees_own_requests(self):
        visit, token = self.pending_visit()
        response = self.get("/vms/api/visitor/visits/", visitor_token=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["reference"], visit.reference)

    def test_alternate_returning_visitor_history_accumulates(self):
        _, token = self.pending_visit()
        second = self.pre_register(token=token, start=timezone.now() + 30 * H)
        self.assertNotIn("visitor_token", second.data)
        self.assertEqual(len(self.get("/vms/api/visitor/visits/", visitor_token=token).data["results"]), 2)

    def test_exception_other_visitors_records_denied(self):
        visit, _ = self.pending_visit()
        _, other_token = self.pending_visit(full_name="Other", id_doc_number="OTHER-1", phone="9111111111")
        response = self.get("/vms/api/visitor/visits/{}/".format(visit.reference), visitor_token=other_token)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.get("/vms/api/visitor/visits/").status_code, 401)


class TestUC012AccessDigitalPass(VmsTestBase):
    def test_happy_pass_with_credentials(self):
        visit, token = self.active_visit()
        response = self.get("/vms/api/visitor/visits/{}/pass/".format(visit.reference), visitor_token=token)
        self.assertEqual(response.status_code, 200)
        for key in ("qr_token", "otp", "valid_from", "valid_until", "pass_type", "permitted_zones"):
            self.assertIn(key, response.data)

    def test_alternate_pdf_and_email_channel(self):
        visit, token = self.active_visit()
        pdf = self.get("/vms/api/visitor/visits/{}/pass/pdf/".format(visit.reference), visitor_token=token)
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.assertTrue(any("visitor pass" in m.subject.lower() for m in mail.outbox))

    def test_exception_no_pass_yet(self):
        visit, token = self.pending_visit()
        response = self.get("/vms/api/visitor/visits/{}/pass/".format(visit.reference), visitor_token=token)
        self.assertEqual(response.status_code, 404)


# ------------------------------------------------------------------------ Host

class TestUC013DecideVisitRequest(VmsTestBase):
    def test_happy_approve_with_restrictions(self):
        visit, _ = self.pending_visit(requested_zones=["ACAD", "HOSTEL"])
        self.approve(visit, permitted_zones=["ACAD"], special_instructions="Report to room 101")
        self.assertEqual(visit.status, VisitStatus.PASS_ACTIVE)
        self.assertEqual(list(visit.visit_pass.permitted_zones.values_list("code", flat=True)), ["ACAD"])
        self.assertEqual(visit.special_instructions, "Report to room 101")
        self.assertTrue(VmsNotification.objects.filter(recipient_visitor=visit.visitor,
                                                       event_type="REQUEST_APPROVED").exists())

    def test_alternate_bulk_approval(self):
        first, _ = self.pending_visit()
        second, _ = self.pending_visit(full_name="Second", id_doc_number="SEC-0002", phone="9222222222")
        response = self.post("/vms/api/host/requests/bulk-decide/",
                             {"references": [first.reference, second.reference], "decision": "APPROVE"},
                             user=self.host_user)
        self.assertTrue(all(r["ok"] for r in response.data["results"]))
        self.assertEqual(VisitRequest.objects.filter(status=VisitStatus.PASS_ACTIVE).count(), 2)

    def test_exception_decision_on_expired_request(self):
        visit, _ = self.pending_visit()
        VisitRequest.objects.filter(pk=visit.pk).update(approval_deadline=timezone.now() - H)
        response = self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.host_user)
        self.assertEqual(response.status_code, 409)
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitStatus.EXPIRED)
        self.assertFalse(VisitPass.objects.filter(visit=visit).exists())


class TestUC014PreAuthorize(VmsTestBase):
    def preauth(self, **extra):
        data = {"full_name": "Vendor Vik", "id_doc_number": "VEN-0001", "phone": "9333333333",
                "valid_until": self.fmt(timezone.now() + 72 * H), "permitted_zones": ["ACAD"]}
        data.update(extra)
        return self.post("/vms/api/host/preauthorizations/", data, user=self.host_user)

    def test_happy_preauthorization_bypasses_host_decision(self):
        self.assertEqual(self.preauth().status_code, 201)
        response = self.pre_register(full_name="Vendor Vik", id_doc_number="VEN-0001", phone="9333333333")
        self.assertEqual(response.data["visit"]["status"], VisitStatus.PASS_ACTIVE)
        self.assertEqual(response.data["visit"]["visit_pass"]["pass_type"], PassType.PRE_REGISTERED)

    def test_alternate_outside_scope_needs_standard_approval(self):
        self.preauth(valid_until=self.fmt(timezone.now() + 4 * H))
        later = timezone.now() + 30 * H
        response = self.pre_register(id_doc_number="VEN-0001", start=later, end=later + H)
        self.assertEqual(response.data["visit"]["status"], VisitStatus.PENDING_HOST_APPROVAL)

    def test_exception_invalid_preauthorization(self):
        self.assertEqual(self.preauth(valid_until=self.fmt(timezone.now() - H)).status_code, 400)
        self.assertEqual(self.post("/vms/api/host/preauthorizations/", {"full_name": "x",
                                                                        "valid_until": self.fmt(timezone.now() + H)},
                                   user=self.student).status_code, 403)


class TestUC015ArrivalUpdates(VmsTestBase):
    def test_happy_host_sees_arrival(self):
        visit, _ = self.on_site_visit()
        response = self.get("/vms/api/host/arrivals/", user=self.host_user)
        self.assertEqual(response.data["arrivals_today"][0]["reference"], visit.reference)
        self.assertEqual(response.data["updates"][0]["event_type"], "VISITOR_CHECKED_IN")

    def test_alternate_event_recorded_even_without_delivery(self):
        IntegrationConfig.objects.create(key="IN_APP", is_enabled=False)
        self.on_site_visit()
        note = VmsNotification.objects.get(recipient_user=self.host_user, event_type="VISITOR_CHECKED_IN")
        self.assertEqual(note.delivery["in_app"], "NOT_CONFIGURED")

    def test_exception_viewing_does_not_change_state(self):
        visit, _ = self.on_site_visit()
        self.get("/vms/api/host/arrivals/", user=self.host_user)
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitStatus.ON_SITE)
        self.assertEqual(self.get("/vms/api/host/arrivals/", user=self.student).status_code, 403)


class TestUC016HostTerminatesEarly(VmsTestBase):
    def test_happy_terminate_before_check_in(self):
        visit, _ = self.active_visit()
        response = self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "Policy breach"},
                             user=self.host_user)
        self.assertEqual(response.data["status"], VisitStatus.TERMINATED)
        self.assertFalse(response.data["visit_pass"]["is_active"])

    def test_alternate_on_site_visitor_stays_pending_exit(self):
        visit, _ = self.on_site_visit()
        response = self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"},
                             user=self.host_user)
        self.assertEqual(response.data["status"], VisitStatus.ON_SITE_PENDING_EXIT)
        self.assertIsNone(response.data["check_out_at"])

    def test_exception_other_host_or_inactive(self):
        visit, _ = self.active_visit()
        self.assertEqual(self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "x"},
                                   user=self.other_host_user).status_code, 403)
        self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "x"}, user=self.host_user)
        again = self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "x"},
                          user=self.host_user)
        self.assertEqual(again.status_code, 409)


# ---------------------------------------------------------- Security Personnel

class TestUC017WalkIn(VmsTestBase):
    def test_happy_host_available_creates_quick_approval(self):
        response = self.post("/vms/api/security/walk-ins/", self.walk_in_payload(), user=self.security)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["visit"]["status"], VisitStatus.PENDING_HOST_APPROVAL)
        self.assertTrue(VmsNotification.objects.filter(recipient_user=self.host_user).exists())

    def test_alternate_host_unavailable_routes_to_admin(self):
        self.put("/vms/api/host/availability/", {"is_available": False}, user=self.host_user)
        response = self.post("/vms/api/security/walk-ins/", self.walk_in_payload(), user=self.security)
        self.assertEqual(response.data["visit"]["status"], VisitStatus.PENDING_ADMIN_CONTINGENCY)

    def test_exception_blacklisted_walk_in_blocked(self):
        self.publish_blacklist(id_doc_number="WALK-0001")
        response = self.post("/vms/api/security/walk-ins/", self.walk_in_payload(), user=self.security)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(VisitRequest.objects.count(), 0)
        self.assertTrue(SecurityAlert.objects.filter(alert_type="BLACKLIST_MATCH", checkpoint="WALK_IN").exists())


class TestUC018ValidatePassAtGate(VmsTestBase):
    def test_happy_valid_pass_checks_in(self):
        visit, _ = self.active_visit()
        response = self.scan(visit)
        self.assertTrue(response.data["allowed"])
        log = VisitLog.objects.get(visit=visit, log_type="CHECK_IN")
        self.assertEqual((log.gate.code, log.device_id), ("MAIN", "GATE-SCANNER-1"))

    def test_alternate_otp_manual_verification_is_one_time(self):
        visit, _ = self.active_visit()
        payload = {"credential_type": "OTP", "credential": visit.visit_pass.pass_number,
                   "otp": visit.visit_pass.otp, "gate": "MAIN"}
        first = self.post("/vms/api/security/gate/validate/", payload, user=self.security)
        self.assertTrue(first.data["allowed"])
        second = self.post("/vms/api/security/gate/validate/", payload, user=self.security)
        self.assertIn("OTP_ALREADY_USED", second.data["failure_reasons"])

    def test_exception_unknown_credential_blocked(self):
        response = self.post("/vms/api/security/gate/validate/", {"credential_type": "QR", "credential": "nope",
                                                                  "gate": "MAIN"}, user=self.security)
        self.assertFalse(response.data["allowed"])
        self.assertEqual(response.data["failure_reasons"], ["UNKNOWN_CREDENTIAL"])
        self.assertTrue(VisitLog.objects.filter(log_type="ACCESS_DENIED").exists())


class TestUC019ManualOverride(VmsTestBase):
    def blocked_attempt(self):
        visit, _ = self.pending_visit()
        self.approve(visit)  # pass valid only in the future -> OUTSIDE_VALIDITY_WINDOW
        response = self.scan(visit)
        self.assertFalse(response.data["allowed"])
        return visit, GateAttempt.objects.get(pk=response.data["attempt_id"])

    def test_happy_admin_authorizes_with_justification(self):
        _, attempt = self.blocked_attempt()
        response = self.post("/vms/api/admin/gate/attempts/{}/override/".format(attempt.pk),
                             {"decision": "AUTHORIZE", "justification": "Host confirmed early arrival"}, user=self.admin)
        self.assertEqual(response.data["status"], GateAttemptStatus.OVERRIDE_AUTHORIZED)
        self.assertTrue(AuditLog.objects.filter(action="GATE_OVERRIDE_AUTHORIZE").exists())

    def test_alternate_ineligible_failure_cannot_be_overridden(self):
        self.publish_blacklist(id_doc_number="ABCD-1234-5678")
        visit, _ = self.pending_visit(id_doc_number="SAFE-ID-1")
        self.approve(visit)
        self.make_valid_now(visit)
        visit.visitor.id_doc_number = "ABCD-1234-5678"
        visit.visitor.save()
        response = self.scan(visit)
        self.assertIn("BLACKLIST_MATCH", response.data["failure_reasons"])
        self.assertFalse(response.data["override_eligible"])
        override = self.post("/vms/api/admin/gate/attempts/{}/override/".format(response.data["attempt_id"]),
                             {"decision": "AUTHORIZE", "justification": "x"}, user=self.admin)
        self.assertEqual(override.status_code, 409)

    def test_exception_missing_justification_rejected(self):
        _, attempt = self.blocked_attempt()
        response = self.post("/vms/api/admin/gate/attempts/{}/override/".format(attempt.pk),
                             {"decision": "AUTHORIZE", "justification": ""}, user=self.admin)
        self.assertEqual(response.status_code, 400)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, GateAttemptStatus.BLOCKED)


class TestUC020ManualVisitLog(VmsTestBase):
    def test_happy_manual_check_in_after_override(self):
        visit, attempt = TestUC019ManualOverride.blocked_attempt(self)
        self.post("/vms/api/admin/gate/attempts/{}/override/".format(attempt.pk),
                  {"decision": "AUTHORIZE", "justification": "ok"}, user=self.admin)
        response = self.post("/vms/api/security/gate/manual-log/", {
            "reference": visit.reference, "log_type": "CHECK_IN", "attempt_id": attempt.pk, "gate": "MAIN"},
            user=self.security)
        self.assertEqual(response.status_code, 201, response.data)
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitStatus.ON_SITE)

    def test_alternate_access_denied_event_recorded(self):
        visit, _ = self.active_visit()
        response = self.post("/vms/api/security/gate/manual-log/", {
            "reference": visit.reference, "log_type": "ACCESS_DENIED", "gate": "MAIN", "detail": "No ID shown"},
            user=self.security)
        self.assertEqual(response.data["log_type"], "ACCESS_DENIED")

    def test_exception_no_fabricated_entry(self):
        visit, _ = self.active_visit()
        response = self.post("/vms/api/security/gate/manual-log/", {
            "reference": visit.reference, "log_type": "CHECK_IN", "gate": "MAIN"}, user=self.security)
        self.assertEqual(response.status_code, 409)
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitStatus.PASS_ACTIVE)


class TestUC021GateCheckOut(VmsTestBase):
    def test_happy_checkout_completes_visit(self):
        visit, _ = self.on_site_visit()
        response = self.post("/vms/api/security/gate/check-out/", {"credential_type": "QR",
                                                                   "credential": visit.visit_pass.qr_token,
                                                                   "gate": "MAIN"}, user=self.security)
        self.assertEqual(response.data["status"], VisitStatus.COMPLETED)
        self.assertIsNotNone(response.data["check_in_at"])
        self.assertIsNotNone(response.data["check_out_at"])

    def test_alternate_auto_checkout_handles_missed_exit(self):
        visit, _ = self.on_site_visit()
        VisitPass.objects.filter(visit=visit).update(valid_until=timezone.now() - datetime.timedelta(minutes=1))
        self.assertEqual(lifecycle.auto_check_out(), 1)
        visit.refresh_from_db()
        self.assertEqual(visit.checkout_method, "AUTO")

    def test_exception_unknown_visit(self):
        response = self.post("/vms/api/security/gate/check-out/", {"reference": "VMS-NOPE"}, user=self.security)
        self.assertEqual(response.status_code, 404)


class TestUC022LiveDashboard(VmsTestBase):
    def test_happy_roster_and_movements(self):
        visit, _ = self.on_site_visit()
        response = self.get("/vms/api/dashboard/", user=self.security)
        self.assertEqual(response.data["on_site_count"], 1)
        self.assertEqual(response.data["roster"][0]["reference"], visit.reference)
        self.assertTrue(response.data["recent_movements"])

    def test_alternate_empty_state(self):
        response = self.get("/vms/api/dashboard/", user=self.admin)
        self.assertEqual((response.data["on_site_count"], response.data["roster"]), (0, []))

    def test_exception_not_for_hosts(self):
        self.assertEqual(self.get("/vms/api/dashboard/", user=self.host_user).status_code, 403)


class TestUC023ValidateZoneAccess(VmsTestBase):
    def zone_scan(self, visit, zone="LABS", user=None):
        return self.post("/vms/api/security/zones/validate/", {"credential_type": "QR",
                                                               "credential": visit.visit_pass.qr_token, "zone": zone},
                         user=user or self.zone_guard)

    def test_happy_permitted_zone_granted(self):
        visit, _ = self.on_site_visit(requested_zones=["LABS"])
        response = self.zone_scan(visit)
        self.assertTrue(response.data["allowed"])
        visit.refresh_from_db()
        self.assertEqual(visit.last_seen_zone.code, "LABS")

    def test_alternate_elevation_permits_revalidation(self):
        visit, _ = self.on_site_visit()
        self.assertFalse(self.zone_scan(visit).data["allowed"])
        self.post("/vms/api/admin/visits/{}/elevations/".format(visit.reference), {
            "zones": ["LABS"], "valid_until": self.fmt(timezone.now() + H), "reason": "Lab demo"}, user=self.zone_admin)
        self.assertTrue(self.zone_scan(visit).data["allowed"])

    def test_exception_unauthorized_zone_denied_and_alerted(self):
        visit, _ = self.on_site_visit()
        response = self.zone_scan(visit)
        self.assertFalse(response.data["allowed"])
        self.assertTrue(SecurityAlert.objects.filter(alert_type="ZONE_VIOLATION", visit=visit).exists())
        self.assertEqual(self.zone_scan(visit, user=self.security).status_code, 403)  # gate guard, wrong zone


class TestUC024TemporaryZoneElevation(VmsTestBase):
    def test_happy_time_boxed_elevation(self):
        visit, _ = self.on_site_visit()
        response = self.post("/vms/api/admin/visits/{}/elevations/".format(visit.reference), {
            "zones": ["LABS"], "valid_until": self.fmt(timezone.now() + H), "reason": "Demo"}, user=self.admin)
        self.assertEqual(response.status_code, 201)

    def test_alternate_expired_elevation_stops_applying(self):
        visit, _ = self.on_site_visit()
        self.post("/vms/api/admin/visits/{}/elevations/".format(visit.reference), {
            "zones": ["LABS"], "valid_until": self.fmt(timezone.now() + H), "reason": "Demo"}, user=self.admin)
        visit.zone_elevations.update(valid_until=timezone.now() - datetime.timedelta(minutes=1))
        response = TestUC023ValidateZoneAccess.zone_scan(self, visit)
        self.assertFalse(response.data["allowed"])

    def test_exception_non_time_boxed_or_out_of_scope(self):
        visit, _ = self.on_site_visit()
        url = "/vms/api/admin/visits/{}/elevations/".format(visit.reference)
        self.assertEqual(self.post(url, {"zones": ["LABS"], "reason": "x"}, user=self.admin).status_code, 400)
        self.assertEqual(self.post(url, {"zones": ["HOSTEL"], "valid_until": self.fmt(timezone.now() + H),
                                         "reason": "x"}, user=self.zone_admin).status_code, 403)


class TestUC025HandleZoneAlert(VmsTestBase):
    def alert(self):
        visit, _ = self.on_site_visit()
        return TestUC023ValidateZoneAccess.zone_scan(self, visit).data["alert_id"]

    def test_happy_handled_and_original_log_kept(self):
        alert_id = self.alert()
        response = self.post("/vms/api/security/alerts/{}/handle/".format(alert_id),
                             {"outcome": "HANDLED", "note": "Escorted back"}, user=self.zone_guard)
        self.assertEqual(response.data["status"], AlertStatus.HANDLED)
        self.assertTrue(VisitLog.objects.filter(log_type="ACCESS_DENIED", zone__code="LABS").exists())

    def test_alternate_false_alarm_and_escalation(self):
        alert_id = self.alert()
        escalated = self.post("/vms/api/security/alerts/{}/handle/".format(alert_id),
                              {"outcome": "ESCALATED", "note": "Needs admin"}, user=self.zone_guard)
        self.assertTrue(escalated.data["escalated_to_admin"])
        closed = self.post("/vms/api/security/alerts/{}/handle/".format(alert_id),
                           {"outcome": "FALSE_ALARM", "note": "Reader fault"}, user=self.admin)
        self.assertEqual(closed.data["status"], AlertStatus.FALSE_ALARM)

    def test_exception_unresolved_alert_remains_open(self):
        alert_id = self.alert()
        response = self.post("/vms/api/security/alerts/{}/handle/".format(alert_id), {"outcome": "HANDLED", "note": ""},
                             user=self.zone_guard)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SecurityAlert.objects.get(pk=alert_id).status, AlertStatus.OPEN)


class TestUC026AdminTriggersMuster(VmsTestBase):
    def test_happy_muster_with_roster_and_alerts(self):
        visit, _ = self.on_site_visit()
        response = self.post("/vms/api/muster/", {"assembly_instructions": "Go to the football ground"},
                             user=self.admin)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["triggered_by_role"], VmsRole.ADMIN)
        entry = response.data["roster"][0]
        self.assertEqual((entry["reference"], entry["visitor_phone"]), (visit.reference, visit.visitor.phone))
        self.assertTrue(VmsNotification.objects.filter(recipient_visitor=visit.visitor,
                                                       event_type="EMERGENCY_MUSTER").exists())

    def test_alternate_cached_roster_reconciled(self):
        visit, _ = self.on_site_visit()
        response = self.post("/vms/api/muster/", {"cached_roster": [visit.reference, "VMS-UNKNOWN"]}, user=self.admin)
        self.assertEqual(response.data["roster_source"], "CACHED")
        self.assertTrue(response.data["roster_incomplete"])

    def test_exception_unauthorized_or_duplicate(self):
        self.assertEqual(self.post("/vms/api/muster/", {}, user=self.host_user).status_code, 403)
        self.post("/vms/api/muster/", {}, user=self.admin)
        self.assertEqual(self.post("/vms/api/muster/", {}, user=self.admin).status_code, 409)


class TestUC027RollCall(VmsTestBase):
    def muster(self):
        self.visit, _ = self.on_site_visit()
        return self.post("/vms/api/muster/", {}, user=self.security).data

    def test_happy_roll_call_and_report(self):
        muster = self.muster()
        self.post("/vms/api/muster/{}/roll-call/".format(muster["id"]),
                  {"updates": [{"reference": self.visit.reference, "status": "ACCOUNTED"}]}, user=self.security)
        final = self.post("/vms/api/muster/{}/finalize/".format(muster["id"]), {}, user=self.security)
        self.assertEqual(final.data["status"], MusterStatus.COMPLETED)
        self.assertEqual(final.data["report"]["counts"]["ACCOUNTED"], 1)

    def test_alternate_unaccounted_stay_pending(self):
        muster = self.muster()
        final = self.post("/vms/api/muster/{}/finalize/".format(muster["id"]), {}, user=self.security)
        self.assertEqual(final.data["report"]["unresolved"][0]["reference"], self.visit.reference)
        self.assertEqual(final.data["roster"][0]["status"], RollCallStatus.PENDING)

    def test_exception_cached_update_never_overwrites_newer(self):
        muster = self.muster()
        url = "/vms/api/muster/{}/roll-call/".format(muster["id"])
        self.post(url, {"updates": [{"reference": self.visit.reference, "status": "ACCOUNTED"}]}, user=self.security)
        stale = self.post(url, {"source": "cached", "updates": [{
            "reference": self.visit.reference, "status": "PENDING",
            "recorded_at": self.fmt(timezone.now() - H)}]}, user=self.security)
        self.assertEqual(len(stale.data["skipped"]), 1)
        self.assertEqual(EmergencyMuster.objects.get().roster.get().status, RollCallStatus.ACCOUNTED)


class TestUC028OfflineGateEntry(VmsTestBase):
    def upload(self, visit, event_type="CHECK_IN", client_id="evt-1", occurred=None):
        return self.post("/vms/api/security/gate/offline-events/", {"gate": "MAIN", "device_id": "TAB-1", "events": [{
            "client_event_id": client_id, "event_type": event_type, "credential_type": "QR",
            "credential": visit.visit_pass.qr_token, "occurred_at": self.fmt(occurred or timezone.now())}]},
            user=self.security)

    def test_happy_cached_entry_recorded_and_reconciled(self):
        visit, _ = self.active_visit()
        snapshot = self.get("/vms/api/security/gate/offline-snapshot/", {"gate": "MAIN"}, user=self.security)
        self.assertEqual(snapshot.data["passes"][0]["qr_token"], visit.visit_pass.qr_token)
        response = self.upload(visit)
        self.assertEqual(response.data["results"][0]["status"], OfflineEventStatus.RECONCILED)
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitStatus.ON_SITE)

    def test_alternate_reupload_is_idempotent(self):
        visit, _ = self.active_visit()
        self.upload(visit)
        self.upload(visit)
        self.assertEqual(OfflineGateEvent.objects.count(), 1)
        self.assertEqual(VisitLog.objects.filter(visit=visit, log_type="CHECK_IN").count(), 1)

    def test_exception_unauthorised_gate(self):
        visit, _ = self.active_visit()
        response = self.post("/vms/api/security/gate/offline-events/", {"gate": "MAIN", "events": []},
                             user=self.hostel_guard)
        self.assertEqual(response.status_code, 403)


class TestUC030VisitorNotifications(VmsTestBase):
    def test_happy_visitor_sees_notifications(self):
        visit, token = self.active_visit()
        response = self.get("/vms/api/visitor/notifications/", visitor_token=token)
        events = {n["event_type"] for n in response.data}
        self.assertTrue({"REQUEST_SUBMITTED", "REQUEST_APPROVED", "PASS_ISSUED"} <= events)

    def test_alternate_delivery_failure_recorded(self):
        IntegrationConfig.objects.create(key="EMAIL", is_enabled=False)
        _, token = self.pending_visit()
        note = VmsNotification.objects.get(event_type="REQUEST_SUBMITTED")
        self.assertEqual(note.delivery["email"], "NOT_CONFIGURED")
        self.assertEqual(len(self.get("/vms/api/visitor/notifications/", visitor_token=token).data), 1)

    def test_exception_state_unchanged_without_infrastructure(self):
        IntegrationConfig.objects.create(key="EMAIL", is_enabled=False)
        visit, _ = self.active_visit()
        self.assertEqual(visit.status, VisitStatus.PASS_ACTIVE)


class TestUC031SelfCheckout(VmsTestBase):
    def test_happy_app_self_checkout(self):
        visit, token = self.on_site_visit()
        response = self.post("/vms/api/visitor/visits/{}/check-out/".format(visit.reference), visitor_token=token)
        self.assertEqual(response.data["status"], VisitStatus.COMPLETED)
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).checkout_method, "APP")

    def test_alternate_kiosk_checkout(self):
        visit, _ = self.on_site_visit()
        response = self.post("/vms/api/kiosk/check-out/", {"qr_token": visit.visit_pass.qr_token})
        self.assertEqual(response.data["status"], VisitStatus.COMPLETED)

    def test_exception_not_on_site(self):
        visit, token = self.active_visit()
        response = self.post("/vms/api/visitor/visits/{}/check-out/".format(visit.reference), visitor_token=token)
        self.assertEqual(response.status_code, 409)


class TestUC032SecurityTriggersMuster(VmsTestBase):
    def test_happy_security_trigger(self):
        self.on_site_visit()
        response = self.post("/vms/api/muster/", {}, user=self.security)
        self.assertEqual(response.data["triggered_by_role"], VmsRole.SECURITY)
        self.assertEqual(len(response.data["roster"]), 1)

    def test_alternate_empty_roster_is_valid(self):
        response = self.post("/vms/api/muster/", {}, user=self.security)
        self.assertEqual((response.status_code, response.data["roster"]), (201, []))

    def test_exception_expired_role_cannot_trigger(self):
        VmsRoleAssignment.objects.filter(user=self.security).update(valid_until=timezone.now() - H)
        self.assertEqual(self.post("/vms/api/muster/", {}, user=self.security).status_code, 403)


# ---------------------------------------------------------- Admin exceptions

class TestUC033ContingencyApproval(VmsTestBase):
    def contingency(self):
        response = self.post("/vms/api/security/walk-ins/", self.walk_in_payload(host_unavailable=True),
                             user=self.security)
        return VisitRequest.objects.get(reference=response.data["visit"]["reference"])

    def test_happy_admin_approves_walk_in_pass(self):
        visit = self.contingency()
        response = self.post("/vms/api/admin/contingency/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.admin)
        self.assertEqual(response.data["status"], VisitStatus.PASS_ACTIVE)
        self.assertEqual(response.data["visit_pass"]["pass_type"], PassType.WALK_IN)

    def test_alternate_timed_out_request_cannot_get_pass(self):
        visit = self.contingency()
        VisitRequest.objects.filter(pk=visit.pk).update(contingency_deadline=timezone.now() - H)
        response = self.post("/vms/api/admin/contingency/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.admin)
        self.assertEqual(response.status_code, 409)
        self.assertFalse(VisitPass.objects.filter(visit=visit).exists())

    def test_exception_unauthorized_admin(self):
        visit = self.contingency()
        response = self.post("/vms/api/admin/contingency/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.zone_admin)
        self.assertEqual(response.status_code, 403)


class TestUC034VisitExtension(VmsTestBase):
    def test_happy_admin_approves_beyond_max(self):
        visit, _ = self.on_site_visit()
        target = visit.visit_pass.valid_from + datetime.timedelta(hours=10)
        request = self.post("/vms/api/visits/{}/extension/".format(visit.reference),
                            {"requested_valid_until": self.fmt(target), "reason": "Workshop overran"},
                            user=self.host_user)
        self.assertEqual(request.status_code, 201, request.data)
        decided = self.post("/vms/api/admin/extensions/{}/decide/".format(request.data["extension"]["id"]),
                            {"decision": "APPROVE"}, user=self.admin)
        self.assertEqual(decided.data["status"], "APPROVED")
        self.assertEqual(VisitPass.objects.get(visit=visit).valid_until.replace(microsecond=0), target.replace(microsecond=0))

    def test_alternate_within_max_needs_no_admin(self):
        visit, _ = self.on_site_visit()
        target = visit.visit_pass.valid_until + H
        response = self.post("/vms/api/visits/{}/extension/".format(visit.reference),
                             {"requested_valid_until": self.fmt(target)}, user=self.host_user)
        self.assertTrue(response.data["applied"])
        self.assertFalse(ExtensionRequest.objects.exists())

    def test_exception_unauthorized_approval(self):
        visit, _ = self.on_site_visit()
        request = self.post("/vms/api/visits/{}/extension/".format(visit.reference), {
            "requested_valid_until": self.fmt(visit.visit_pass.valid_from + datetime.timedelta(hours=12)),
            "reason": "x"}, user=self.host_user)
        response = self.post("/vms/api/admin/extensions/{}/decide/".format(request.data["extension"]["id"]),
                             {"decision": "APPROVE"}, user=self.host_user)
        self.assertEqual(response.status_code, 403)


class TestUC035SameDayException(VmsTestBase):
    def urgent(self):
        start = timezone.now() + datetime.timedelta(minutes=30)
        if start.date() != timezone.now().date():
            self.skipTest("too close to midnight for a same-day case")
        return self.pending_visit(start=start, end=start + H, is_urgent=True)[0]

    def test_happy_approved_exception_goes_to_host(self):
        visit = self.urgent()
        response = self.post("/vms/api/admin/exceptions/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.admin)
        self.assertEqual(response.data["status"], VisitStatus.PENDING_HOST_APPROVAL)

    def test_alternate_rejected_exception_stops(self):
        visit = self.urgent()
        response = self.post("/vms/api/admin/exceptions/{}/decide/".format(visit.reference),
                             {"decision": "REJECT", "note": "Not urgent"}, user=self.admin)
        self.assertEqual(response.data["status"], VisitStatus.REJECTED)

    def test_exception_unauthorized(self):
        visit = self.urgent()
        response = self.post("/vms/api/admin/exceptions/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.security)
        self.assertEqual(response.status_code, 403)


class TestUC036AdminTerminatesEarly(VmsTestBase):
    def test_happy_admin_terminates(self):
        visit, _ = self.active_visit()
        response = self.post("/vms/api/admin/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"},
                             user=self.admin)
        self.assertEqual(response.data["status"], VisitStatus.TERMINATED)

    def test_alternate_on_site_then_exit(self):
        visit, _ = self.on_site_visit()
        self.post("/vms/api/admin/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"}, user=self.admin)
        out = self.post("/vms/api/security/gate/check-out/", {"reference": visit.reference}, user=self.security)
        self.assertEqual(out.data["status"], VisitStatus.COMPLETED)

    def test_exception_unauthorized(self):
        visit, _ = self.active_visit()
        response = self.post("/vms/api/admin/visits/{}/terminate/".format(visit.reference), {"reason": "x"},
                             user=self.security)
        self.assertEqual(response.status_code, 403)


# ----------------------------------------------------- Event-triggered services

class TestUC037ExpirePending(VmsTestBase):
    def test_happy_timeout_expires_and_notifies(self):
        visit, _ = self.pending_visit()
        VisitRequest.objects.filter(pk=visit.pk).update(approval_deadline=timezone.now() - H)
        self.assertEqual(lifecycle.expire_pending_requests(), 1)
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitStatus.EXPIRED)
        self.assertTrue(VmsNotification.objects.filter(recipient_visitor=visit.visitor,
                                                       event_type="REQUEST_EXPIRED").exists())

    def test_alternate_not_yet_due(self):
        self.pending_visit()
        self.assertEqual(lifecycle.expire_pending_requests(), 0)

    def test_exception_already_decided_not_expired(self):
        visit, _ = self.pending_visit()
        self.approve(visit)
        VisitRequest.objects.filter(pk=visit.pk).update(approval_deadline=timezone.now() - H)
        self.assertEqual(lifecycle.expire_pending_requests(), 0)
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, VisitStatus.PASS_ACTIVE)


class TestUC038AutoCheckout(VmsTestBase):
    def test_happy_auto_checkout_at_validity_end(self):
        visit, _ = self.on_site_visit()
        end = timezone.now() - datetime.timedelta(minutes=5)
        VisitPass.objects.filter(visit=visit).update(valid_until=end)
        lifecycle.auto_check_out()
        visit.refresh_from_db()
        self.assertEqual((visit.status, visit.checkout_method), (VisitStatus.COMPLETED, "AUTO"))
        self.assertEqual(visit.check_out_at.replace(microsecond=0), end.replace(microsecond=0))

    def test_alternate_no_second_checkout(self):
        visit, _ = self.on_site_visit()
        self.post("/vms/api/security/gate/check-out/", {"reference": visit.reference}, user=self.security)
        VisitPass.objects.filter(visit=visit).update(valid_until=timezone.now() - H)
        self.assertEqual(lifecycle.auto_check_out(), 0)
        self.assertEqual(VisitLog.objects.filter(visit=visit, log_type="CHECK_OUT").count(), 1)

    def test_exception_pass_still_valid(self):
        self.on_site_visit()
        self.assertEqual(lifecycle.auto_check_out(), 0)


class TestUC039ReconcileOffline(VmsTestBase):
    def test_happy_pending_events_reconciled(self):
        visit, _ = self.active_visit()
        OfflineGateEvent.objects.create(client_event_id="c1", gate=self.main_gate, credential_type="QR",
                                        credential_value=visit.visit_pass.qr_token, event_type="CHECK_IN",
                                        occurred_at=timezone.now(), uploaded_by=self.security)
        processed = gate_services.reconcile_offline_events()
        self.assertEqual(processed[0].status, OfflineEventStatus.RECONCILED)

    def test_alternate_nothing_pending(self):
        self.assertEqual(gate_services.reconcile_offline_events(), [])

    def test_exception_conflict_flagged_not_overwritten(self):
        visit, _ = self.active_visit()
        self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"}, user=self.host_user)
        OfflineGateEvent.objects.create(client_event_id="c2", gate=self.main_gate, credential_type="QR",
                                        credential_value=visit.visit_pass.qr_token, event_type="CHECK_IN",
                                        occurred_at=timezone.now(), uploaded_by=self.security)
        processed = gate_services.reconcile_offline_events()
        self.assertEqual(processed[0].status, OfflineEventStatus.CONFLICT)
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, VisitStatus.TERMINATED)
        review = self.post("/vms/api/admin/offline-conflicts/{}/review/".format(processed[0].pk),
                           {"note": "Guard admitted before termination"}, user=self.admin)
        self.assertEqual(review.data["status"], OfflineEventStatus.REVIEWED)


class TestUC040PendingReminder(VmsTestBase):
    def configure_reminders(self, offsets):
        draft = self.post("/vms/api/admin/policies/", {"reminder_offsets_minutes": offsets}, user=self.admin)
        self.post("/vms/api/admin/policies/{}/publish/".format(draft.data["version"]), {}, user=self.admin)

    def test_happy_configured_reminder_sent_once(self):
        self.configure_reminders([60])
        visit, _ = self.pending_visit()
        VisitRequest.objects.filter(pk=visit.pk).update(
            approval_deadline=timezone.now() + datetime.timedelta(minutes=24 * 60 - 61))
        self.assertEqual(lifecycle.send_pending_reminders(), 1)
        self.assertEqual(lifecycle.send_pending_reminders(), 0)
        self.assertTrue(VmsNotification.objects.filter(recipient_user=self.host_user,
                                                       event_type="APPROVAL_REMINDER").exists())

    def test_alternate_no_reminder_without_configuration(self):
        visit, _ = self.pending_visit()
        VisitRequest.objects.filter(pk=visit.pk).update(approval_deadline=timezone.now() + H)
        self.assertEqual(lifecycle.send_pending_reminders(), 0)  # ISS-VMS-018: no hard-coded 12h/20h

    def test_exception_suppressed_when_no_longer_pending(self):
        self.configure_reminders([60])
        visit, _ = self.pending_visit()
        self.approve(visit)
        self.assertEqual(lifecycle.send_pending_reminders(), 0)
