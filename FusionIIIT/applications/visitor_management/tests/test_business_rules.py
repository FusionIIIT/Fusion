"""Business rules from specs/business_rules.yaml (VMS BR Specifications v1.3): one valid and one invalid case each."""

import datetime

from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils import timezone

from applications.visitor_management.constants import (
    ExtensionStatus,
    PassType,
    PolicyStatus,
    VisitStatus,
)
from applications.visitor_management.models import (
    AccessPolicy,
    ExtensionRequest,
    GateAttempt,
    SecurityAlert,
    VisitLog,
    VisitPass,
    VisitRequest,
    VmsNotification,
    VmsRoleAssignment,
)
from applications.visitor_management.services import lifecycle
from applications.visitor_management.tests.conftest import VmsTestBase, load_catalog

H = datetime.timedelta(hours=1)


class TestBusinessRuleCatalog(VmsTestBase):
    def test_all_47_rules_catalogued_with_valid_and_invalid(self):
        rules = load_catalog("business_rules.yaml", "business_rules")
        self.assertEqual(len(rules), 47)
        for rule in rules:
            self.assertEqual(sorted(rule["scenarios"]), ["invalid", "valid"])

    def test_every_rule_has_a_test_class_here(self):
        rules = {r["id"] for r in load_catalog("business_rules.yaml", "business_rules")}
        tested = {name[4:9] for name in globals() if name.startswith("Test") and name[4:6] == "BR"}
        self.assertEqual(rules - tested, set())


def walk_in(case, **extra):
    response = case.post("/vms/api/security/walk-ins/", case.walk_in_payload(**extra), user=case.security)
    return response, (VisitRequest.objects.get(reference=response.data["visit"]["reference"])
                      if response.status_code == 201 else None)


def publish_policy(case, **values):
    draft = case.post("/vms/api/admin/policies/", values, user=case.admin)
    case.assertEqual(draft.status_code, 201, draft.data)
    case.post("/vms/api/admin/policies/{}/publish/".format(draft.data["version"]), {}, user=case.admin)
    return draft.data["version"]


class TestBR037MandatoryValidation(VmsTestBase):
    def test_valid(self):
        self.assertEqual(self.pre_register().status_code, 201)

    def test_invalid(self):
        response = self.pre_register(full_name="", phone="")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(VisitRequest.objects.exists())


class TestBR038DuplicateCheck(VmsTestBase):
    def test_valid_non_overlapping(self):
        self.pending_visit()
        later = timezone.now() + 30 * H
        self.assertEqual(self.pre_register(start=later, end=later + H).status_code, 201)

    def test_invalid_overlapping_duplicate(self):
        self.pending_visit()
        response = self.pre_register(phone="98765-43210")  # same visitor by normalised phone
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "duplicate_request")


class TestBR049ContingencyAuthorization(VmsTestBase):
    def test_valid_relevant_admin(self):
        _, visit = walk_in(self, host_unavailable=True)
        response = self.post("/vms/api/admin/contingency/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.admin)
        self.assertEqual(response.status_code, 200)

    def test_invalid_security_is_not_the_approver(self):
        _, visit = walk_in(self, host_unavailable=True)
        response = self.post("/vms/api/admin/contingency/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.security)
        self.assertEqual(response.status_code, 403)


class TestBR050ContingencySla(VmsTestBase):
    def test_valid_within_window(self):
        _, visit = walk_in(self, host_unavailable=True)
        self.assertGreater(visit.contingency_deadline, timezone.now())
        response = self.post("/vms/api/admin/contingency/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.admin)
        self.assertEqual(response.data["status"], VisitStatus.PASS_ACTIVE)

    def test_invalid_after_window(self):
        _, visit = walk_in(self, host_unavailable=True)
        VisitRequest.objects.filter(pk=visit.pk).update(contingency_deadline=timezone.now() - H)
        response = self.post("/vms/api/admin/contingency/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.admin)
        self.assertEqual(response.data["code"], "contingency_sla_elapsed")


class TestBR051BlacklistRegistrationRejection(VmsTestBase):
    def test_valid_clean_identity_accepted(self):
        self.publish_blacklist()
        self.assertEqual(self.pre_register().status_code, 201)

    def test_invalid_match_rejected_with_alert(self):
        self.publish_blacklist(id_doc_number="ABCD12345678")  # same document, different punctuation
        response = self.pre_register()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(VisitRequest.objects.count(), 0)
        self.assertTrue(SecurityAlert.objects.filter(alert_type="BLACKLIST_MATCH").exists())


class TestBR052HostApprovalRequirement(VmsTestBase):
    def test_valid_pass_only_after_host_approval(self):
        visit, _ = self.pending_visit()
        self.assertFalse(VisitPass.objects.filter(visit=visit).exists())
        self.approve(visit)
        self.assertTrue(VisitPass.objects.filter(visit=visit, is_active=True).exists())

    def test_invalid_non_host_cannot_approve(self):
        visit, _ = self.pending_visit()
        for user in (self.other_host_user, self.security, self.admin):
            response = self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                                 user=user)
            self.assertEqual(response.status_code, 403)
        self.assertFalse(VisitPass.objects.filter(visit=visit).exists())


class TestBR053WalkInPassDuration(VmsTestBase):
    def test_valid_configured_duration_applied(self):
        publish_policy(self, walk_in_pass_duration_minutes=90)
        _, visit = walk_in(self)
        self.approve(visit)
        span = visit.visit_pass.valid_until - visit.visit_pass.valid_from
        self.assertEqual(span, datetime.timedelta(minutes=90))

    def test_invalid_host_cannot_exceed_walk_in_duration(self):
        _, visit = walk_in(self)
        response = self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {
            "decision": "APPROVE", "valid_until": self.fmt(timezone.now() + 6 * H)}, user=self.host_user)
        self.assertEqual(response.status_code, 400)


class TestBR062PendingApprovalTimeout(VmsTestBase):
    def test_valid_default_24h_window(self):
        visit, _ = self.pending_visit()
        self.assertEqual(visit.approval_deadline - visit.submitted_at, datetime.timedelta(hours=24))

    def test_invalid_pending_past_window_expires(self):
        visit, _ = self.pending_visit()
        VisitRequest.objects.filter(pk=visit.pk).update(approval_deadline=timezone.now() - H)
        lifecycle.expire_pending_requests()
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, VisitStatus.EXPIRED)


class TestBR073EarlyTerminationAuthorization(VmsTestBase):
    def test_valid_host_and_admin_traceable(self):
        visit, _ = self.active_visit()
        self.post("/vms/api/admin/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"}, user=self.admin)
        visit.refresh_from_db()
        self.assertEqual((visit.status, visit.termination_reason), (VisitStatus.TERMINATED, "Breach"))
        self.assertIn("TERMINATED", visit.visit_pass.deactivation_reason)

    def test_invalid_unauthorized_actor(self):
        visit, _ = self.active_visit()
        response = self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "x"},
                             user=self.student)
        self.assertEqual(response.status_code, 403)


class TestBR077ActivePassGateRule(VmsTestBase):
    def test_valid_active_pass_enters(self):
        visit, _ = self.active_visit()
        self.assertTrue(self.scan(visit).data["allowed"])

    def test_invalid_inactive_pass_blocked(self):
        visit, _ = self.active_visit()
        VisitPass.objects.filter(visit=visit).update(is_active=False)
        response = self.scan(visit)
        self.assertIn("PASS_INACTIVE", response.data["failure_reasons"])


class TestBR082GateValidationFailure(VmsTestBase):
    def test_valid_failure_blocks_and_records_reason(self):
        visit, _ = self.pending_visit()
        self.approve(visit)
        response = self.scan(visit)
        attempt = GateAttempt.objects.get(pk=response.data["attempt_id"])
        self.assertEqual(attempt.failure_reasons, ["OUTSIDE_VALIDITY_WINDOW"])
        self.assertTrue(VisitLog.objects.filter(visit=visit, log_type="ACCESS_DENIED").exists())
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, VisitStatus.PASS_ACTIVE)

    def test_invalid_entry_without_override_refused(self):
        visit, _ = self.pending_visit()
        self.approve(visit)
        self.scan(visit)
        response = self.post("/vms/api/security/gate/manual-log/", {"reference": visit.reference,
                                                                    "log_type": "CHECK_IN", "gate": "MAIN"},
                             user=self.security)
        self.assertEqual(response.status_code, 409)


class TestBR085ManualOverrideAuthorization(VmsTestBase):
    def blocked(self):
        visit, _ = self.pending_visit()
        self.approve(visit)
        return self.scan(visit).data["attempt_id"]

    def test_valid_admin_with_justification(self):
        response = self.post("/vms/api/admin/gate/attempts/{}/override/".format(self.blocked()),
                             {"decision": "AUTHORIZE", "justification": "Host present"}, user=self.admin)
        self.assertEqual(response.data["override_justification"], "Host present")

    def test_invalid_security_cannot_override(self):
        response = self.post("/vms/api/admin/gate/attempts/{}/override/".format(self.blocked()),
                             {"decision": "AUTHORIZE", "justification": "x"}, user=self.security)
        self.assertEqual(response.status_code, 403)


class TestBR096ElevationTimeBox(VmsTestBase):
    def test_valid_explicit_expiry(self):
        visit, _ = self.on_site_visit()
        response = self.post("/vms/api/admin/visits/{}/elevations/".format(visit.reference), {
            "zones": ["LABS"], "valid_until": self.fmt(timezone.now() + H), "reason": "Demo"}, user=self.admin)
        self.assertEqual(response.status_code, 201)

    def test_invalid_indefinite_elevation(self):
        visit, _ = self.on_site_visit()
        response = self.post("/vms/api/admin/visits/{}/elevations/".format(visit.reference),
                             {"zones": ["LABS"], "reason": "Demo"}, user=self.admin)
        self.assertEqual(response.status_code, 400)


class TestBR101AutomaticCheckoutTrigger(VmsTestBase):
    def test_valid_expired_validity_auto_checks_out(self):
        visit, _ = self.on_site_visit()
        VisitPass.objects.filter(visit=visit).update(valid_until=timezone.now() - H)
        lifecycle.auto_check_out()
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, VisitStatus.COMPLETED)

    def test_invalid_valid_pass_untouched(self):
        visit, _ = self.on_site_visit()
        lifecycle.auto_check_out()
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, VisitStatus.ON_SITE)


class TestBR105VisitCompletion(VmsTestBase):
    def test_valid_exit_records_in_and_out(self):
        visit, _ = self.on_site_visit()
        self.post("/vms/api/security/gate/check-out/", {"reference": visit.reference}, user=self.security)
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitStatus.COMPLETED)
        self.assertTrue(visit.check_in_at <= visit.check_out_at)

    def test_invalid_deactivation_is_not_checkout(self):
        visit, _ = self.on_site_visit()
        self.post("/vms/api/host/visits/{}/terminate/".format(visit.reference), {"reason": "Breach"},
                  user=self.host_user)
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitStatus.ON_SITE_PENDING_EXIT)
        self.assertIsNone(visit.check_out_at)


class TestBR112BlacklistCheckpoints(VmsTestBase):
    def test_valid_all_three_checkpoints_enforced(self):
        self.publish_blacklist(id_doc_number="ABCD-1234-5678")
        self.assertEqual(self.pre_register().status_code, 403)
        self.assertEqual(walk_in(self, id_doc_number="ABCD-1234-5678")[0].status_code, 403)
        checkpoints = set(SecurityAlert.objects.values_list("checkpoint", flat=True))
        self.assertEqual(checkpoints, {"PRE_REGISTRATION", "WALK_IN"})

    def test_invalid_listed_after_approval_caught_at_gate(self):
        visit, _ = self.active_visit()
        self.publish_blacklist(id_doc_number="ABCD-1234-5678")
        self.assertIn("BLACKLIST_MATCH", self.scan(visit).data["failure_reasons"])


class TestBR116BlacklistEntryDenial(VmsTestBase):
    def test_valid_unlisted_enters(self):
        self.publish_blacklist()
        visit, _ = self.active_visit()
        self.assertTrue(self.scan(visit).data["allowed"])

    def test_invalid_listed_denied(self):
        visit, _ = self.active_visit()
        self.publish_blacklist(phone="9876543210", id_doc_number="")
        response = self.scan(visit)
        self.assertFalse(response.data["allowed"])
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, VisitStatus.PASS_ACTIVE)


class TestBR117BlacklistMatchAlert(VmsTestBase):
    def test_valid_match_alerts_security_authorities(self):
        self.publish_blacklist(id_doc_number="ABCD-1234-5678")
        self.pre_register()
        self.assertTrue(VmsNotification.objects.filter(event_type="BLACKLIST_MATCH", recipient_user=self.admin).exists())

    def test_invalid_no_match_no_alert(self):
        self.publish_blacklist()
        self.pre_register()
        self.assertFalse(SecurityAlert.objects.exists())


class TestBR118SafeListScope(VmsTestBase):
    def safelist(self, scope):
        self.post("/vms/api/admin/registry/", {"list_type": "SAFELIST", "id_doc_number": "ABCD-1234-5678",
                                               "expires_at": self.fmt(timezone.now() + 24 * H),
                                               "safelist_scope": scope}, user=self.admin)
        self.publish_blacklist(list_type="WATCHLIST", id_doc_number="ABCD-1234-5678")

    @override_settings(VMS_WATCHLIST_REJECTS=True)
    def test_valid_safelist_exempts_within_scope(self):
        self.safelist("REGISTRATION")
        self.assertEqual(self.pre_register().status_code, 201)

    @override_settings(VMS_WATCHLIST_REJECTS=True)
    def test_invalid_outside_scope_not_exempt(self):
        self.safelist("GATE")
        self.assertEqual(self.pre_register().status_code, 403)


class TestBR119SafeListExpiry(VmsTestBase):
    def test_valid_entry_with_expiry(self):
        response = self.post("/vms/api/admin/registry/", {"list_type": "SAFELIST", "phone": "9000000099",
                                                          "expires_at": self.fmt(timezone.now() + H)}, user=self.admin)
        self.assertEqual(response.status_code, 201)

    def test_invalid_entry_without_expiry(self):
        response = self.post("/vms/api/admin/registry/", {"list_type": "SAFELIST", "phone": "9000000099"},
                             user=self.admin)
        self.assertIn("expires_at", response.data["errors"])


class TestBR120PublishedBlacklistSource(VmsTestBase):
    def test_valid_published_entry_used(self):
        self.publish_blacklist(id_doc_number="ABCD-1234-5678")
        self.assertEqual(self.pre_register().status_code, 403)

    def test_invalid_draft_entry_ignored(self):
        self.post("/vms/api/admin/registry/", {"list_type": "BLACKLIST", "id_doc_number": "ABCD-1234-5678",
                                               "reason": "draft"}, user=self.admin)
        self.assertEqual(self.pre_register().status_code, 201)


class TestBR125PolicyVersioning(VmsTestBase):
    def test_valid_versions_preserved(self):
        v1 = publish_policy(self, max_visit_duration_minutes=400)
        v2 = publish_policy(self, max_visit_duration_minutes=300)
        self.assertEqual(v2, v1 + 1)
        self.assertEqual(AccessPolicy.objects.get(version=v1).status, PolicyStatus.SUPERSEDED)

    def test_invalid_rejected_values_create_no_version(self):
        self.post("/vms/api/admin/policies/", {"max_visit_duration_minutes": 0}, user=self.admin)
        self.assertFalse(AccessPolicy.objects.exists())


class TestBR126PolicyPublication(VmsTestBase):
    def test_valid_published_takes_effect(self):
        publish_policy(self, max_visit_duration_minutes=60, walk_in_pass_duration_minutes=60)
        self.assertEqual(self.pre_register().status_code, 400)  # 2h visit now too long

    def test_invalid_draft_has_no_effect(self):
        self.post("/vms/api/admin/policies/", {"max_visit_duration_minutes": 60}, user=self.admin)
        self.assertEqual(self.pre_register().status_code, 201)


class TestBR127PublishedPolicyRuntimeSource(VmsTestBase):
    def test_valid_runtime_uses_published_restricted_zones(self):
        publish_policy(self, restricted_zones=["LABS"])
        visit, _ = self.on_site_visit(requested_zones=["LABS"])
        response = self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                                   "credential": visit.visit_pass.qr_token},
                             user=self.zone_guard)
        self.assertFalse(response.data["allowed"])

    def test_invalid_draft_restriction_not_applied(self):
        self.post("/vms/api/admin/policies/", {"restricted_zones": ["LABS"]}, user=self.admin)
        visit, _ = self.on_site_visit(requested_zones=["LABS"])
        response = self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                                   "credential": visit.visit_pass.qr_token},
                             user=self.zone_guard)
        self.assertTrue(response.data["allowed"])


class TestBR128ModificationCreatesVersion(VmsTestBase):
    def test_valid_new_version_based_on_published(self):
        v1 = publish_policy(self, max_visit_duration_minutes=400)
        response = self.post("/vms/api/admin/policies/", {"based_on_version": v1, "contingency_sla_minutes": 15},
                             user=self.admin)
        self.assertEqual((response.data["based_on"], response.data["max_visit_duration_minutes"]), (v1, 400))

    def test_invalid_published_not_mutated(self):
        v1 = publish_policy(self)
        response = self.patch("/vms/api/admin/policies/{}/".format(v1), {"max_visit_duration_minutes": 100},
                              user=self.admin)
        self.assertEqual(response.status_code, 409)


class TestBR129PolicyNonRetroactivity(VmsTestBase):
    def test_valid_active_visit_keeps_its_policy(self):
        visit, _ = self.on_site_visit(requested_zones=["LABS"])
        publish_policy(self, restricted_zones=["LABS"])
        response = self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                                   "credential": visit.visit_pass.qr_token},
                             user=self.zone_guard)
        self.assertTrue(response.data["allowed"])

    def test_invalid_new_visits_follow_new_policy(self):
        publish_policy(self, restricted_zones=["LABS"])
        visit, _ = self.pending_visit(requested_zones=["LABS"])
        self.assertEqual(visit.policy_snapshot["restricted_zone_ids"], [self.labs.pk])


class TestBR130MusterAuthorization(VmsTestBase):
    def test_valid_admin_or_security(self):
        self.assertEqual(self.post("/vms/api/muster/", {}, user=self.security).status_code, 201)

    def test_invalid_host_cannot_trigger(self):
        self.assertEqual(self.post("/vms/api/muster/", {}, user=self.host_user).status_code, 403)


class TestBR174NotificationChannels(VmsTestBase):
    def test_valid_configured_channel_used(self):
        self.pending_visit()
        note = VmsNotification.objects.get(recipient_user=self.host_user)
        self.assertEqual(note.delivery["email"], "SENT")

    def test_invalid_unconfigured_channel_still_records_event(self):
        from applications.visitor_management.models import IntegrationConfig
        IntegrationConfig.objects.create(key="EMAIL", is_enabled=False)
        self.active_visit()
        note = VmsNotification.objects.get(event_type="PASS_ISSUED")
        self.assertEqual((note.delivery["email"], note.delivery["sms"]), ("NOT_CONFIGURED", "NOT_CONFIGURED"))


class TestBR181TimeBoundRoles(VmsTestBase):
    def test_valid_assignment_has_validity(self):
        response = self.post("/vms/api/superadmin/roles/", {"user": "staffhost", "role": "ADMIN", "scope_type": "CAMPUS",
                                                            "valid_until": self.fmt(timezone.now() + H)},
                             user=self.superadmin)
        self.assertIsNotNone(response.data["valid_until"])

    def test_invalid_expired_role_grants_nothing(self):
        VmsRoleAssignment.objects.filter(user=self.admin).update(valid_until=timezone.now() - H)
        self.assertEqual(self.get("/vms/api/admin/policies/", user=self.admin).status_code, 403)
        missing = self.post("/vms/api/superadmin/roles/", {"user": "staffhost", "role": "ADMIN",
                                                           "scope_type": "CAMPUS"}, user=self.superadmin)
        self.assertEqual(missing.status_code, 400)


class TestBR182ImmediateReassignment(VmsTestBase):
    def reassign(self):
        assignment = VmsRoleAssignment.objects.get(user=self.security)
        return self.post("/vms/api/superadmin/roles/{}/reassign/".format(assignment.pk), {"user": "staffhost"},
                         user=self.superadmin)

    def test_valid_new_holder_acts_immediately(self):
        self.reassign()
        visit, _ = self.active_visit()
        self.assertTrue(self.scan(visit, user=self.other_host_user).data["allowed"])

    def test_invalid_previous_holder_loses_access(self):
        self.reassign()
        visit, _ = self.active_visit()
        self.assertEqual(self.scan(visit, user=self.security).status_code, 403)


class TestBR183PendingWorkHandoff(VmsTestBase):
    def test_valid_pending_alert_moves(self):
        visit, _ = self.on_site_visit()
        self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                        "credential": visit.visit_pass.qr_token}, user=self.zone_guard)
        assignment = VmsRoleAssignment.objects.get(user=self.zone_guard)
        response = self.post("/vms/api/superadmin/roles/{}/reassign/".format(assignment.pk), {"user": "staffhost"},
                             user=self.superadmin)
        self.assertEqual(response.data["handoff"]["alerts"], 1)
        self.assertEqual(SecurityAlert.objects.get().assigned_to, self.other_host_user)

    def test_invalid_closed_work_not_moved(self):
        visit, _ = self.on_site_visit()
        alert_id = self.post("/vms/api/security/zones/validate/", {
            "credential_type": "QR", "zone": "LABS", "credential": visit.visit_pass.qr_token},
            user=self.zone_guard).data["alert_id"]
        self.post("/vms/api/security/alerts/{}/handle/".format(alert_id), {"outcome": "HANDLED", "note": "ok"},
                  user=self.zone_guard)
        assignment = VmsRoleAssignment.objects.get(user=self.zone_guard)
        response = self.post("/vms/api/superadmin/roles/{}/reassign/".format(assignment.pk), {"user": "staffhost"},
                             user=self.superadmin)
        self.assertEqual(response.data["handoff"]["alerts"], 0)


class TestBR184RoleHierarchy(VmsTestBase):
    def test_valid_super_admin_governs(self):
        response = self.post("/vms/api/superadmin/roles/", {"user": "staffhost", "role": "SECURITY",
                                                            "scope_type": "ZONE", "zone": "HOSTEL",
                                                            "valid_until": self.fmt(timezone.now() + H)},
                             user=self.superadmin)
        self.assertEqual(response.status_code, 201)

    def test_invalid_admin_cannot_assign_or_wrong_scope(self):
        payload = {"user": "staffhost", "role": "SECURITY", "scope_type": "GATE", "gate": "MAIN",
                   "valid_until": self.fmt(timezone.now() + H)}
        self.assertEqual(self.post("/vms/api/superadmin/roles/", payload, user=self.admin).status_code, 403)
        payload.update(scope_type="CAMPUS")
        self.assertEqual(self.post("/vms/api/superadmin/roles/", payload, user=self.superadmin).status_code, 400)


class TestBR185ImplicitHostRole(VmsTestBase):
    def test_valid_staff_is_a_host_without_assignment(self):
        self.assertEqual(self.pre_register(host_id=self.other_host_user.extrainfo.pk).status_code, 201)

    def test_invalid_student_is_not_a_host(self):
        response = self.pre_register(host_id=self.student.extrainfo.pk)
        self.assertIn("host_id", response.data["errors"])


class TestBR186ValidIdentityDocument(VmsTestBase):
    def test_valid_document_number(self):
        self.assertEqual(self.pre_register(id_doc_number="P1234567").status_code, 201)

    def test_invalid_missing_document_number(self):
        self.assertEqual(self.pre_register(id_doc_number="12").status_code, 400)


class TestBR187DocumentTypes(VmsTestBase):
    def test_valid_all_four_types(self):
        for index, doc_type in enumerate(["PASSPORT", "NATIONAL_ID", "DRIVERS_LICENSE", "OTHER"]):
            start = timezone.now() + (3 + 10 * index) * H
            response = self.pre_register(id_doc_type=doc_type, start=start, end=start + H)
            self.assertEqual(response.status_code, 201, response.data)

    def test_invalid_type_outside_domain(self):
        self.assertEqual(self.pre_register(id_doc_type="COLLEGE_ID").status_code, 400)


class TestBR190PassValidityWindow(VmsTestBase):
    def test_valid_inside_window(self):
        visit, _ = self.active_visit()
        self.assertTrue(self.scan(visit).data["allowed"])

    def test_invalid_outside_window(self):
        visit, _ = self.active_visit()
        VisitPass.objects.filter(visit=visit).update(valid_until=timezone.now() - datetime.timedelta(minutes=1))
        self.assertIn("OUTSIDE_VALIDITY_WINDOW", self.scan(visit).data["failure_reasons"])


class TestBR191UnauthorizedZoneDenial(VmsTestBase):
    def test_valid_permitted_zone(self):
        visit, _ = self.active_visit(requested_zones=["HOSTEL"])
        self.assertTrue(self.scan(visit, gate="HOSTEL_GATE", user=self.hostel_guard).data["allowed"])

    def test_invalid_gate_zone_not_on_pass(self):
        visit, _ = self.active_visit(requested_zones=["ACAD"])
        response = self.scan(visit, gate="HOSTEL_GATE", user=self.hostel_guard)
        self.assertIn("GATE_ZONE_NOT_PERMITTED", response.data["failure_reasons"])


class TestBR192UnauthorizedZoneLogging(VmsTestBase):
    def test_valid_denied_attempt_logged(self):
        visit, _ = self.on_site_visit()
        self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                        "credential": visit.visit_pass.qr_token}, user=self.zone_guard)
        log = VisitLog.objects.get(visit=visit, log_type="ACCESS_DENIED")
        self.assertEqual(log.zone.code, "LABS")

    def test_invalid_granted_access_not_logged_as_denied(self):
        visit, _ = self.on_site_visit(requested_zones=["LABS"])
        self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                        "credential": visit.visit_pass.qr_token}, user=self.zone_guard)
        self.assertFalse(VisitLog.objects.filter(visit=visit, log_type="ACCESS_DENIED").exists())


class TestBR193MaximumVisitDuration(VmsTestBase):
    def test_valid_eight_hours(self):
        start = timezone.now() + 3 * H
        self.assertEqual(self.pre_register(start=start, end=start + 8 * H).status_code, 201)

    def test_invalid_beyond_maximum(self):
        start = timezone.now() + 3 * H
        self.assertEqual(self.pre_register(start=start, end=start + 9 * H).status_code, 400)


class TestBR194ExtensionApproval(VmsTestBase):
    def test_valid_admin_approval_activates(self):
        visit, _ = self.on_site_visit()
        target = visit.visit_pass.valid_from + 10 * H
        ext = self.post("/vms/api/visits/{}/extension/".format(visit.reference),
                        {"requested_valid_until": self.fmt(target), "reason": "Overrun"}, user=self.host_user).data
        self.post("/vms/api/admin/extensions/{}/decide/".format(ext["extension"]["id"]), {"decision": "APPROVE"},
                  user=self.admin)
        self.assertEqual(ExtensionRequest.objects.get().status, ExtensionStatus.APPROVED)

    def test_invalid_host_alone_cannot_exceed_max(self):
        visit, _ = self.on_site_visit()
        before = visit.visit_pass.valid_until
        self.post("/vms/api/visits/{}/extension/".format(visit.reference),
                  {"requested_valid_until": self.fmt(visit.visit_pass.valid_from + 10 * H), "reason": "Overrun"},
                  user=self.host_user)
        self.assertEqual(VisitPass.objects.get(visit=visit).valid_until, before)


class TestBR195PreAuthorizationBypass(VmsTestBase):
    def preauth(self, user):
        self.post("/vms/api/host/preauthorizations/", {"full_name": "Meera Iyer", "id_doc_number": "ABCD-1234-5678",
                                                       "valid_until": self.fmt(timezone.now() + 72 * H),
                                                       "permitted_zones": ["ACAD"]}, user=user)

    def test_valid_matching_preauthorization(self):
        self.preauth(self.host_user)
        self.assertEqual(self.pre_register().data["visit"]["status"], VisitStatus.PASS_ACTIVE)

    def test_invalid_other_hosts_preauthorization(self):
        self.preauth(self.other_host_user)
        self.assertEqual(self.pre_register().data["visit"]["status"], VisitStatus.PENDING_HOST_APPROVAL)


class TestBR196VipAuthorization(VmsTestBase):
    def test_valid_super_admin_grants(self):
        response = self.post("/vms/api/superadmin/vip/", {"id_doc_number": "VIP-1",
                                                          "valid_until": self.fmt(timezone.now() + H)},
                             user=self.superadmin)
        self.assertEqual(response.status_code, 201)

    def test_invalid_admin_cannot_grant(self):
        response = self.post("/vms/api/superadmin/vip/", {"id_doc_number": "VIP-1",
                                                          "valid_until": self.fmt(timezone.now() + H)}, user=self.admin)
        self.assertEqual(response.status_code, 403)


class TestBR197VipOverrideEffect(VmsTestBase):
    def vip_visit(self, zone_scope, zones=None):
        self.post("/vms/api/superadmin/vip/", {"id_doc_number": "ABCD-1234-5678", "zone_scope": zone_scope,
                                               "zones": zones or [], "valid_until": self.fmt(timezone.now() + 48 * H)},
                  user=self.superadmin)
        publish_policy(self, restricted_zones=["LABS"])
        response = self.pre_register(requested_zones=[])
        visit = VisitRequest.objects.get(reference=response.data["visit"]["reference"])
        self.make_valid_now(visit)
        self.scan(visit)
        return visit

    def test_valid_bypass_within_scope(self):
        visit = self.vip_visit("LISTED", ["LABS"])
        response = self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                                   "credential": visit.visit_pass.qr_token},
                             user=self.zone_guard)
        self.assertEqual(response.data["basis"], "VIP_OVERRIDE")

    def test_invalid_outside_recorded_scope(self):
        visit = self.vip_visit("NONE")
        self.assertEqual(visit.visit_pass.pass_type, PassType.VIP)  # approval bypassed...
        response = self.post("/vms/api/security/zones/validate/", {"credential_type": "QR", "zone": "LABS",
                                                                   "credential": visit.visit_pass.qr_token},
                             user=self.zone_guard)
        self.assertFalse(response.data["allowed"])  # ...but zone restriction is not


class TestBR200ExpiredRequestState(VmsTestBase):
    def test_valid_timeout_sets_expired(self):
        visit, _ = self.pending_visit()
        VisitRequest.objects.filter(pk=visit.pk).update(approval_deadline=timezone.now() - H)
        lifecycle.expire_pending_requests()
        self.assertEqual(VisitRequest.objects.get(pk=visit.pk).status, VisitStatus.EXPIRED)

    def test_invalid_expired_cannot_be_approved(self):
        visit, _ = self.pending_visit()
        VisitRequest.objects.filter(pk=visit.pk).update(approval_deadline=timezone.now() - H)
        lifecycle.expire_pending_requests()
        response = self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.host_user)
        self.assertEqual(response.status_code, 409)


class TestBR202AdvanceWindow(VmsTestBase):
    def test_valid_two_hours_ahead(self):
        start = timezone.now() + datetime.timedelta(minutes=125)
        self.assertEqual(self.pre_register(start=start, end=start + H).status_code, 201)

    def test_invalid_inside_window_without_exception(self):
        start = timezone.now() + H
        response = self.pre_register(start=start, end=start + H)
        self.assertEqual(response.data["code"], "advance_window")


class TestBR203SameDayUrgentException(VmsTestBase):
    def urgent(self):
        start = timezone.now() + datetime.timedelta(minutes=30)
        if start.date() != timezone.now().date():
            self.skipTest("too close to midnight for a same-day case")
        return self.pending_visit(start=start, end=start + H, is_urgent=True)[0]

    def test_valid_routed_to_admin(self):
        self.assertEqual(self.urgent().status, VisitStatus.PENDING_ADMIN_EXCEPTION)

    def test_invalid_host_cannot_skip_admin_exception(self):
        visit = self.urgent()
        response = self.post("/vms/api/host/requests/{}/decide/".format(visit.reference), {"decision": "APPROVE"},
                             user=self.host_user)
        self.assertEqual(response.status_code, 409)


class TestBR211PassTypeDomain(VmsTestBase):
    def test_valid_type_follows_path(self):
        visit, _ = self.active_visit()
        _, walk = walk_in(self)
        self.approve(walk)
        self.assertEqual((visit.visit_pass.pass_type, walk.visit_pass.pass_type),
                         (PassType.PRE_REGISTERED, PassType.WALK_IN))

    def test_invalid_type_outside_domain_rejected(self):
        visit, _ = self.active_visit()
        visit_pass = visit.visit_pass
        visit_pass.pass_type = "DAY_PASS"
        with self.assertRaises(ValidationError):
            visit_pass.full_clean()
