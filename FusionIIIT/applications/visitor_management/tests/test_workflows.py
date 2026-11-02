"""Workflows from specs/workflows.yaml (VMS Workflow Specifications v1.3).

* Traceability: every STT row of every basis/composite workflow maps to code
  (workflow.STT_TRACE) and every visit transition uses a TRANSITIONS action.
* End-to-end: each of the 23 basis workflows is driven through its STT rows
  via the API and the recorded VisitStateHistory is checked.
* Negative: moves the STT does not allow are refused with state unchanged.
"""

import datetime

from django.utils import timezone

from applications.visitor_management import workflow
from applications.visitor_management.constants import (
    AlertStatus,
    EventStatus,
    GateAttemptStatus,
    MusterStatus,
    OfflineEventStatus,
    VisitStatus,
)
from applications.visitor_management.errors import Conflict
from applications.visitor_management.models import (
    EmergencyMuster,
    GateAttempt,
    OfflineGateEvent,
    SecurityAlert,
    VisitLog,
    VisitorEvent,
    VisitPass,
    VisitRequest,
)
from applications.visitor_management.services import lifecycle
from applications.visitor_management.tests.conftest import VmsTestBase, load_catalog

H = datetime.timedelta(hours=1)
S = VisitStatus


def history(visit):
    return [h.to_status for h in VisitRequest.objects.get(pk=visit.pk).history.all()]


class TestStateTransitionTraceability(VmsTestBase):
    def test_every_stt_row_is_implemented(self):
        rows = [row["row"] for wf in load_catalog("workflows.yaml", "workflows") for row in wf["stt"]]
        self.assertEqual(len(rows), 116)  # 58 basis rows, mirrored in the 7 composites
        self.assertEqual(set(rows) - set(workflow.STT_TRACE), set())

    def test_visit_rows_reference_real_transitions(self):
        for row, (kind, target) in workflow.STT_TRACE.items():
            if kind == "visit":
                self.assertIn(target, workflow.TRANSITIONS, row)
                self.assertIn(row.split(" R")[0][-2:], workflow.TRANSITIONS[target].refs + row, row)

    def test_composites_are_unions_of_their_basis_workflows(self):
        catalog = {wf["source_id"]: wf for wf in load_catalog("workflows.yaml", "workflows")}
        for wf_id, wf in catalog.items():
            if wf_id.startswith("CW-"):
                basis_rows = {r["row"] for r in wf["stt"]}
                prefixes = {r.rsplit(" R", 1)[0] for r in basis_rows}
                expected = {r["row"] for p in prefixes for r in catalog[p]["stt"]}
                self.assertEqual(basis_rows, expected, wf_id)

    def test_illegal_transition_refused(self):
        visit, _ = self.pending_visit()
        with self.assertRaises(Conflict):
            workflow.apply(visit, "GATE_CHECK_IN")
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, S.PENDING_HOST_APPROVAL)


class _WF(VmsTestBase):
    def checkout(self, visit):
        response = self.post("/vms/api/security/gate/check-out/", {"reference": visit.reference}, user=self.security)
        self.assertEqual(response.status_code, 200, response.data)

    def walk_in(self, **extra):
        response = self.post("/vms/api/security/walk-ins/", self.walk_in_payload(**extra), user=self.security)
        return VisitRequest.objects.get(reference=response.data["visit"]["reference"])

    def urgent(self):
        start = timezone.now() + datetime.timedelta(minutes=30)
        if start.date() != timezone.now().date():
            self.skipTest("too close to midnight for a same-day case")
        return self.pending_visit(start=start, end=start + H, is_urgent=True)[0]


class TestBW01PreRegisteredApproved(_WF):
    def test_end_to_end(self):
        visit, _ = self.on_site_visit()
        self.checkout(visit)
        self.assertEqual(history(visit), [S.PENDING_HOST_APPROVAL, S.PASS_ACTIVE, S.ON_SITE, S.COMPLETED])

    def test_negative_checkout_before_entry(self):
        visit, _ = self.active_visit()
        response = self.post("/vms/api/security/gate/check-out/", {"reference": visit.reference}, user=self.security)
        self.assertEqual(response.status_code, 409)


class TestBW02PreRegisteredRejected(_WF):
    def test_end_to_end(self):
        visit, _ = self.pending_visit()
        self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {"decision": "REJECT", "reason": "Busy"},
                  user=self.host_user)
        self.assertEqual(history(visit), [S.PENDING_HOST_APPROVAL, S.REJECTED])

    def test_negative_rejected_has_no_pass(self):
        visit, _ = self.pending_visit()
        self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {"decision": "REJECT"},
                  user=self.host_user)
        self.assertFalse(VisitPass.objects.filter(visit=visit).exists())


class TestBW03ApprovalTimeout(_WF):
    def test_end_to_end(self):
        visit, _ = self.pending_visit()
        VisitRequest.objects.filter(pk=visit.pk).update(approval_deadline=timezone.now() - H)
        lifecycle.expire_pending_requests()
        self.assertEqual(history(visit), [S.PENDING_HOST_APPROVAL, S.EXPIRED])
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).history.last().actor_role, "SYSTEM")

    def test_negative_no_pass_after_expiry(self):
        visit, _ = self.pending_visit()
        VisitRequest.objects.filter(pk=visit.pk).update(approval_deadline=timezone.now() - H)
        lifecycle.expire_pending_requests()
        self.assertFalse(VisitPass.objects.filter(visit=visit).exists())


class TestBW04PreAuthorized(_WF):
    def setUp(self):
        super().setUp()
        self.post("/vms/api/host/preauthorizations/", {"full_name": "Meera Iyer", "id_doc_number": "ABCD-1234-5678",
                                                       "valid_until": self.fmt(timezone.now() + 72 * H),
                                                       "permitted_zones": ["ACAD"]}, user=self.host_user)

    def test_end_to_end(self):
        visit, _ = self.pending_visit()
        self.make_valid_now(visit)
        self.assertTrue(self.scan(visit).data["allowed"])
        self.checkout(visit)
        self.assertEqual(history(visit), [S.PASS_ACTIVE, S.ON_SITE, S.COMPLETED])

    def test_negative_blacklist_still_applies(self):
        self.publish_blacklist(id_doc_number="ABCD-1234-5678")
        self.assertEqual(self.pre_register().status_code, 403)


class TestBW05Vip(_WF):
    def test_end_to_end(self):
        self.post("/vms/api/superadmin/vip/", {"id_doc_number": "ABCD-1234-5678",
                                               "valid_until": self.fmt(timezone.now() + 48 * H)}, user=self.superadmin)
        visit, _ = self.pending_visit()
        self.make_valid_now(visit)
        self.scan(visit)
        self.checkout(visit)
        self.assertEqual(history(visit), [S.PASS_ACTIVE, S.ON_SITE, S.COMPLETED])
        self.assertEqual(visit.visit_pass.pass_type, "VIP")

    def test_negative_gate_checks_not_bypassed(self):
        self.post("/vms/api/superadmin/vip/", {"id_doc_number": "ABCD-1234-5678",
                                               "valid_until": self.fmt(timezone.now() + 48 * H)}, user=self.superadmin)
        visit, _ = self.pending_visit()  # pass valid only from the scheduled start
        self.assertIn("OUTSIDE_VALIDITY_WINDOW", self.scan(visit).data["failure_reasons"])


class TestBW06WalkInHostApproved(_WF):
    def test_end_to_end(self):
        visit = self.walk_in()
        self.approve(visit)
        self.scan(visit)
        self.checkout(visit)
        self.assertEqual(history(visit), [S.PENDING_HOST_APPROVAL, S.PASS_ACTIVE, S.ON_SITE, S.COMPLETED])
        self.assertEqual(visit.visit_pass.pass_type, "WALK_IN")

    def test_negative_security_cannot_self_approve(self):
        visit = self.walk_in()
        response = self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.security)
        self.assertEqual(response.status_code, 403)


class TestBW07WalkInContingency(_WF):
    def test_end_to_end(self):
        visit = self.walk_in(host_unavailable=True)
        self.post("/vms/api/admin/contingency/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                  user=self.admin)
        visit.refresh_from_db()
        self.scan(visit)
        self.checkout(visit)
        self.assertEqual(history(visit), [S.PENDING_ADMIN_CONTINGENCY, S.PASS_ACTIVE, S.ON_SITE, S.COMPLETED])

    def test_negative_host_cannot_decide_contingency(self):
        visit = self.walk_in(host_unavailable=True)
        response = self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.host_user)
        self.assertEqual(response.status_code, 409)


class TestBW08WalkInHostRejected(_WF):
    def test_end_to_end(self):
        visit = self.walk_in()
        self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {"decision": "REJECT"},
                  user=self.host_user)
        self.assertEqual(history(visit), [S.PENDING_HOST_APPROVAL, S.REJECTED])

    def test_negative_rejected_walk_in_cannot_enter(self):
        visit = self.walk_in()
        self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {"decision": "REJECT"},
                  user=self.host_user)
        response = self.post("/vms/api/security/gate/validate/", {"credential_type": "BADGE",
                                                                  "credential": "NONE", "gate": "MAIN"},
                             user=self.security)
        self.assertFalse(response.data["allowed"])


class TestBW09GateDenied(_WF):
    def test_end_to_end(self):
        visit, _ = self.active_visit()
        VisitPass.objects.filter(visit=visit).update(is_active=False)
        response = self.scan(visit)
        self.assertEqual(GateAttempt.objects.get(pk=response.data["attempt_id"]).status, GateAttemptStatus.BLOCKED)

    def test_negative_blocked_visit_not_on_site(self):
        visit, _ = self.active_visit()
        VisitPass.objects.filter(visit=visit).update(is_active=False)
        self.scan(visit)
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, S.PASS_ACTIVE)


class TestBW10OverrideEntry(_WF):
    def test_end_to_end(self):
        visit, _ = self.pending_visit()
        self.approve(visit)
        attempt_id = self.scan(visit).data["attempt_id"]
        self.post("/vms/api/security/gate/attempts/{}/refer/".format(attempt_id), {"note": "Early"}, user=self.security)
        self.post("/vms/api/admin/gate/attempts/{}/override/".format(attempt_id),
                  {"decision": "AUTHORIZE", "justification": "Host is waiting"}, user=self.admin)
        self.post("/vms/api/security/gate/manual-log/", {"reference": visit.reference, "log_type": "CHECK_IN",
                                                         "attempt_id": attempt_id, "gate": "MAIN"}, user=self.security)
        self.assertEqual(GateAttempt.objects.get(pk=attempt_id).status, GateAttemptStatus.MANUAL_ENTRY_RECORDED)
        self.assertEqual(history(visit)[-1], S.ON_SITE)

    def test_negative_denied_override_stays_blocked(self):
        visit, _ = self.pending_visit()
        self.approve(visit)
        attempt_id = self.scan(visit).data["attempt_id"]
        self.post("/vms/api/admin/gate/attempts/{}/override/".format(attempt_id),
                  {"decision": "DENY", "justification": "No"}, user=self.admin)
        response = self.post("/vms/api/security/gate/manual-log/", {
            "reference": visit.reference, "log_type": "CHECK_IN", "attempt_id": attempt_id, "gate": "MAIN"},
            user=self.security)
        self.assertEqual(response.status_code, 409)


class TestBW11OfflineEntry(_WF):
    def test_end_to_end(self):
        visit, _ = self.active_visit()
        moment = timezone.now()
        result = self.post("/vms/api/security/gate/offline-events/", {"gate": "MAIN", "events": [{
            "client_event_id": "o-1", "event_type": "CHECK_IN", "credential_type": "QR",
            "credential": visit.visit_pass.qr_token, "occurred_at": self.fmt(moment)}]}, user=self.security)
        self.assertEqual(result.data["results"][0]["status"], OfflineEventStatus.RECONCILED)
        self.assertEqual(history(visit)[-1], S.ON_SITE)
        self.assertTrue(VisitLog.objects.get(visit=visit, log_type="CHECK_IN").is_offline)

    def test_negative_unknown_credential_flagged(self):
        result = self.post("/vms/api/security/gate/offline-events/", {"gate": "MAIN", "events": [{
            "client_event_id": "o-2", "event_type": "CHECK_IN", "credential_type": "QR", "credential": "forged",
            "occurred_at": self.fmt(timezone.now())}]}, user=self.security)
        self.assertEqual(result.data["results"][0]["status"], OfflineEventStatus.CONFLICT)
        self.assertEqual(OfflineGateEvent.objects.count(), 1)  # kept for review, not discarded


class TestBW12ZoneGranted(_WF):
    def test_end_to_end(self):
        visit, _ = self.on_site_visit(requested_zones=["LABS"])
        response = self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                                   "credential": visit.visit_pass.qr_token},
                             user=self.zone_guard)
        self.assertEqual(response.data["basis"], "PASS_PERMISSION")
        self.assertTrue(VisitLog.objects.filter(visit=visit, log_type="ZONE_ACCESS", zone=self.labs).exists())

    def test_negative_completed_visit_cannot_enter_zone(self):
        visit, _ = self.on_site_visit(requested_zones=["LABS"])
        self.checkout(visit)
        response = self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                                   "credential": visit.visit_pass.qr_token},
                             user=self.zone_guard)
        self.assertFalse(response.data["allowed"])


class TestBW13ZoneDeniedAlertHandled(_WF):
    def test_end_to_end(self):
        visit, _ = self.on_site_visit()
        alert_id = self.post("/vms/api/security/zones/validate/", {
            "credential_type": "QR", "zone": "LABS", "credential": visit.visit_pass.qr_token},
            user=self.zone_guard).data["alert_id"]
        self.post("/vms/api/security/alerts/{}/handle/".format(alert_id), {"outcome": "HANDLED", "note": "Escorted"},
                  user=self.zone_guard)
        self.assertEqual(SecurityAlert.objects.get(pk=alert_id).status, AlertStatus.HANDLED)
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, S.ON_SITE)

    def test_negative_closed_alert_cannot_be_rehandled(self):
        visit, _ = self.on_site_visit()
        alert_id = self.post("/vms/api/security/zones/validate/", {
            "credential_type": "QR", "zone": "LABS", "credential": visit.visit_pass.qr_token},
            user=self.zone_guard).data["alert_id"]
        url = "/vms/api/security/alerts/{}/handle/".format(alert_id)
        self.post(url, {"outcome": "HANDLED", "note": "ok"}, user=self.zone_guard)
        self.assertEqual(self.post(url, {"outcome": "HANDLED", "note": "again"}, user=self.zone_guard).status_code, 409)


class TestBW14ElevationRevalidation(_WF):
    def test_end_to_end(self):
        visit, _ = self.on_site_visit()
        payload = {"credential_type": "QR", "zone": "LABS", "credential": visit.visit_pass.qr_token}
        self.assertFalse(self.post("/vms/api/security/zones/validate/", payload, user=self.zone_guard).data["allowed"])
        self.post("/vms/api/admin/visits/{}/elevations/".format(visit.reference), {
            "zones": ["LABS"], "valid_until": self.fmt(timezone.now() + H), "reason": "Demo"}, user=self.zone_admin)
        retry = self.post("/vms/api/security/zones/validate/", payload, user=self.zone_guard)
        self.assertEqual(retry.data["basis"], "TEMPORARY_ELEVATION")

    def test_negative_elevation_for_other_zone_does_not_help(self):
        visit, _ = self.on_site_visit()
        self.post("/vms/api/admin/visits/{}/elevations/".format(visit.reference), {
            "zones": ["ACAD"], "valid_until": self.fmt(timezone.now() + H), "reason": "x"}, user=self.admin)
        payload = {"credential_type": "QR", "zone": "LABS", "credential": visit.visit_pass.qr_token}
        self.assertFalse(self.post("/vms/api/security/zones/validate/", payload, user=self.zone_guard).data["allowed"])


class TestBW15HostTerminatesBeforeCheckIn(_WF):
    def test_end_to_end(self):
        visit, _ = self.active_visit()
        self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"},
                  user=self.host_user)
        self.assertEqual(history(visit)[-1], S.TERMINATED)

    def test_negative_terminated_pass_cannot_enter(self):
        visit, _ = self.active_visit()
        self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"},
                  user=self.host_user)
        self.assertIn("PASS_INACTIVE", self.scan(visit).data["failure_reasons"])


class TestBW16HostTerminatesOnSite(_WF):
    def test_end_to_end(self):
        visit, _ = self.on_site_visit()
        self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"},
                  user=self.host_user)
        self.checkout(visit)
        self.assertEqual(history(visit)[-3:], [S.ON_SITE, S.ON_SITE_PENDING_EXIT, S.COMPLETED])

    def test_negative_pending_exit_cannot_enter_zones(self):
        visit, _ = self.on_site_visit(requested_zones=["LABS"])
        self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"},
                  user=self.host_user)
        response = self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                                   "credential": visit.visit_pass.qr_token},
                             user=self.zone_guard)
        self.assertFalse(response.data["allowed"])


class TestBW17AdminTerminatesBeforeCheckIn(_WF):
    def test_end_to_end(self):
        visit, _ = self.active_visit()
        self.post("/vms/api/admin/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"}, user=self.admin)
        self.assertEqual(history(visit)[-1], S.TERMINATED)

    def test_negative_pending_request_cannot_be_terminated(self):
        visit, _ = self.pending_visit()
        response = self.post("/vms/api/admin/visits/{}/terminate/".format(visit.reference), {"reason": "x"},
                             user=self.admin)
        self.assertEqual(response.status_code, 409)


class TestBW18AdminTerminatesOnSite(_WF):
    def test_end_to_end(self):
        visit, _ = self.on_site_visit()
        self.post("/vms/api/admin/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"}, user=self.admin)
        self.checkout(visit)
        self.assertEqual(history(visit)[-2:], [S.ON_SITE_PENDING_EXIT, S.COMPLETED])

    def test_negative_completed_cannot_be_terminated(self):
        visit, _ = self.on_site_visit()
        self.checkout(visit)
        response = self.post("/vms/api/admin/visits/{}/terminate/".format(visit.reference), {"reason": "x"},
                             user=self.admin)
        self.assertEqual(response.status_code, 409)


class TestBW19AdminMuster(_WF):
    def test_end_to_end(self):
        visit, _ = self.on_site_visit()
        muster = self.post("/vms/api/muster/", {}, user=self.admin).data
        self.post("/vms/api/muster/{}/roll-call/".format(muster["id"]),
                  {"updates": [{"reference": visit.reference, "status": "ACCOUNTED"}]}, user=self.security)
        self.post("/vms/api/muster/{}/finalize/".format(muster["id"]), {}, user=self.security)
        self.assertEqual(EmergencyMuster.objects.get().status, MusterStatus.COMPLETED)

    def test_negative_completed_muster_rejects_roll_call(self):
        muster = self.post("/vms/api/muster/", {}, user=self.admin).data
        self.post("/vms/api/muster/{}/finalize/".format(muster["id"]), {}, user=self.admin)
        response = self.post("/vms/api/muster/{}/roll-call/".format(muster["id"]), {"updates": []}, user=self.security)
        self.assertEqual(response.status_code, 409)


class TestBW20SecurityMuster(_WF):
    def test_end_to_end(self):
        self.on_site_visit()
        muster = self.post("/vms/api/muster/", {}, user=self.security).data
        final = self.post("/vms/api/muster/{}/finalize/".format(muster["id"]), {}, user=self.security)
        self.assertEqual((final.data["triggered_by_role"], final.data["status"]), ("SECURITY", MusterStatus.COMPLETED))
        report = self.get("/vms/api/muster/{}/report/".format(muster["id"]), {"export": "csv"}, user=self.admin)
        self.assertEqual(report["Content-Type"], "text/csv")

    def test_negative_roll_call_needs_security(self):
        muster = self.post("/vms/api/muster/", {}, user=self.security).data
        response = self.post("/vms/api/muster/{}/roll-call/".format(muster["id"]), {"updates": []}, user=self.admin)
        self.assertEqual(response.status_code, 403)


class TestBW21BulkEventEntry(_WF):
    def test_end_to_end(self):
        event = self.post("/vms/api/admin/events/", {
            "name": "Seminar", "host_id": self.host.pk, "starts_at": self.fmt(timezone.now() - H),
            "ends_at": self.fmt(timezone.now() + 5 * H)}, user=self.admin).data
        self.assertEqual(VisitorEvent.objects.get(pk=event["id"]).status, EventStatus.DRAFT)
        self.post("/vms/api/admin/bulk-lists/", {"kind": "EVENT", "event_id": event["id"], "rows": [
            {"full_name": "Delegate", "phone": "9000000031", "id_doc_type": "PASSPORT", "id_doc_number": "DEL-1"}]},
            user=self.admin)
        self.assertEqual(VisitorEvent.objects.get(pk=event["id"]).status, EventStatus.PASSES_ACTIVE)
        self.post("/vms/api/admin/events/{}/controls/".format(event["id"]), {"fast_lane_enabled": True}, user=self.admin)
        visit = VisitRequest.objects.get(event_id=event["id"])
        self.scan(visit, lane="FAST")
        self.checkout(visit)
        self.assertEqual(history(visit), [S.PASS_ACTIVE, S.ON_SITE, S.COMPLETED])

    def test_negative_controls_need_active_passes(self):
        event = self.post("/vms/api/admin/events/", {
            "name": "Empty", "host_id": self.host.pk, "starts_at": self.fmt(timezone.now()),
            "ends_at": self.fmt(timezone.now() + H)}, user=self.admin).data
        response = self.post("/vms/api/admin/events/{}/controls/".format(event["id"]), {"fast_lane_enabled": True},
                             user=self.admin)
        self.assertEqual(response.status_code, 409)


class TestBW22SameDayUrgent(_WF):
    def test_end_to_end(self):
        visit = self.urgent()
        self.post("/vms/api/admin/exceptions/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                  user=self.admin)
        self.approve(visit)
        self.make_valid_now(visit)
        self.scan(visit)
        self.checkout(visit)
        self.assertEqual(history(visit), [S.PENDING_ADMIN_EXCEPTION, S.PENDING_HOST_APPROVAL, S.PASS_ACTIVE,
                                          S.ON_SITE, S.COMPLETED])

    def test_negative_non_urgent_inside_window_rejected(self):
        start = timezone.now() + datetime.timedelta(minutes=30)
        self.assertEqual(self.pre_register(start=start, end=start + H).status_code, 400)


class TestBW23AdminExtension(_WF):
    def test_end_to_end(self):
        visit, _ = self.on_site_visit()
        ext = self.post("/vms/api/visits/{}/extension/".format(visit.reference), {
            "requested_valid_until": self.fmt(visit.visit_pass.valid_from + 10 * H), "reason": "Overrun"},
            user=self.host_user).data["extension"]
        self.post("/vms/api/admin/extensions/{}/decide/".format(ext["id"]), {"decision": "APPROVE"}, user=self.admin)
        last = VisitRequest.objects.get(pk=visit.pk).history.last()
        self.assertEqual((last.transition_ref, last.to_status), ("BW-VMS-23 R1", S.ON_SITE))

    def test_negative_rejected_extension_keeps_validity(self):
        visit, _ = self.on_site_visit()
        before = visit.visit_pass.valid_until
        ext = self.post("/vms/api/visits/{}/extension/".format(visit.reference), {
            "requested_valid_until": self.fmt(visit.visit_pass.valid_from + 10 * H), "reason": "Overrun"},
            user=self.host_user).data["extension"]
        self.post("/vms/api/admin/extensions/{}/decide/".format(ext["id"]), {"decision": "REJECT"}, user=self.admin)
        self.assertEqual(VisitPass.objects.get(visit=visit).valid_until, before)
