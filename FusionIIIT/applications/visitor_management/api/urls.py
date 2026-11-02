from django.conf.urls import url

from . import views as v

app_name = "vms"

R = r"(?P<reference>[A-Za-z0-9\-]+)"

urlpatterns = [
    # Notification URL name used by notifications (``vms:vms``)
    url(r"^$", v.module_root, name="vms"),

    # Shared
    url(r"^api/me/$", v.me, name="me"),
    url(r"^api/zones/$", v.zones_list, name="zones"),
    url(r"^api/gates/$", v.gates_list, name="gates"),
    url(r"^api/notifications/$", v.my_notifications, name="notifications"),
    url(r"^api/notifications/(?P<notification_id>\d+)/read/$", v.mark_notification_read, name="notification_read"),
    url(r"^api/visits/$", v.visit_search, name="visit_search"),
    url(r"^api/visits/" + R + r"/$", v.visit_detail, name="visit_detail"),
    url(r"^api/visits/" + R + r"/extension/$", v.request_extension, name="request_extension"),
    url(r"^api/dashboard/$", v.dashboard, name="dashboard"),
    url(r"^api/audit-logs/$", v.audit_logs, name="audit_logs"),

    # Public + visitor portal (UC-010/011/012/030/031)
    url(r"^api/public/hosts/$", v.public_hosts, name="public_hosts"),
    url(r"^api/public/zones/$", v.public_zones, name="public_zones"),
    url(r"^api/public/visits/$", v.public_pre_register, name="public_pre_register"),
    url(r"^api/visitor/visits/$", v.visitor_visits, name="visitor_visits"),
    url(r"^api/visitor/visits/" + R + r"/$", v.visitor_visit_detail, name="visitor_visit_detail"),
    url(r"^api/visitor/visits/" + R + r"/pass/$", v.visitor_pass, name="visitor_pass"),
    url(r"^api/visitor/visits/" + R + r"/pass/pdf/$", v.visitor_pass_pdf, name="visitor_pass_pdf"),
    url(r"^api/visitor/visits/" + R + r"/check-out/$", v.visitor_self_check_out, name="visitor_self_check_out"),
    url(r"^api/visitor/notifications/$", v.visitor_notifications, name="visitor_notifications"),
    url(r"^api/kiosk/check-out/$", v.kiosk_check_out, name="kiosk_check_out"),

    # Host (UC-013/014/015/016)
    url(r"^api/host/requests/$", v.host_pending_requests, name="host_pending_requests"),
    url(r"^api/host/requests/bulk-decide/$", v.host_bulk_decide, name="host_bulk_decide"),
    url(r"^api/host/requests/" + R + r"/decide/$", v.host_decide, name="host_decide"),
    url(r"^api/host/visits/$", v.host_visits, name="host_visits"),
    url(r"^api/host/visits/" + R + r"/terminate/$", v.host_terminate, name="host_terminate"),
    url(r"^api/host/arrivals/$", v.host_arrivals, name="host_arrivals"),
    url(r"^api/host/preauthorizations/$", v.host_preauthorizations, name="host_preauthorizations"),
    url(r"^api/host/preauthorizations/(?P<preauth_id>\d+)/revoke/$", v.host_revoke_preauthorization,
        name="host_revoke_preauthorization"),
    url(r"^api/host/availability/$", v.host_availability, name="host_availability"),

    # Security Personnel (UC-017..028)
    url(r"^api/security/walk-ins/$", v.security_walk_in, name="security_walk_in"),
    url(r"^api/security/gate/validate/$", v.security_gate_validate, name="security_gate_validate"),
    url(r"^api/security/gate/attempts/(?P<attempt_id>\d+)/refer/$", v.security_refer_attempt,
        name="security_refer_attempt"),
    url(r"^api/security/gate/manual-log/$", v.security_manual_log, name="security_manual_log"),
    url(r"^api/security/gate/check-out/$", v.security_check_out, name="security_check_out"),
    url(r"^api/security/gate/offline-snapshot/$", v.security_offline_snapshot, name="security_offline_snapshot"),
    url(r"^api/security/gate/offline-events/$", v.security_offline_upload, name="security_offline_upload"),
    url(r"^api/security/zones/validate/$", v.security_zone_validate, name="security_zone_validate"),
    url(r"^api/security/alerts/$", v.security_alerts, name="security_alerts"),
    url(r"^api/security/alerts/escalate/$", v.security_escalate, name="security_escalate"),
    url(r"^api/security/alerts/(?P<alert_id>\d+)/handle/$", v.security_handle_alert, name="security_handle_alert"),
    url(r"^api/security/expected-arrivals/$", v.security_expected_arrivals, name="security_expected_arrivals"),

    # Emergency muster (UC-026/027/032)
    url(r"^api/muster/$", v.muster_trigger, name="muster_trigger"),
    url(r"^api/muster/active/$", v.muster_active, name="muster_active"),
    url(r"^api/muster/roster-snapshot/$", v.muster_roster_snapshot, name="muster_roster_snapshot"),
    url(r"^api/muster/(?P<muster_id>\d+)/$", v.muster_detail, name="muster_detail"),
    url(r"^api/muster/(?P<muster_id>\d+)/roll-call/$", v.muster_roll_call, name="muster_roll_call"),
    url(r"^api/muster/(?P<muster_id>\d+)/finalize/$", v.muster_finalize, name="muster_finalize"),
    url(r"^api/muster/(?P<muster_id>\d+)/report/$", v.muster_report, name="muster_report"),

    # Admin (UC-005..009, 019, 024, 033..036)
    url(r"^api/admin/exceptions/$", v.admin_exception_queue, name="admin_exception_queue"),
    url(r"^api/admin/exceptions/" + R + r"/decide/$", v.admin_decide_exception, name="admin_decide_exception"),
    url(r"^api/admin/contingency/$", v.admin_contingency_queue, name="admin_contingency_queue"),
    url(r"^api/admin/contingency/" + R + r"/decide/$", v.admin_decide_contingency, name="admin_decide_contingency"),
    url(r"^api/admin/gate/overrides/$", v.admin_override_queue, name="admin_override_queue"),
    url(r"^api/admin/gate/attempts/(?P<attempt_id>\d+)/override/$", v.admin_override, name="admin_override"),
    url(r"^api/admin/visits/" + R + r"/terminate/$", v.admin_terminate, name="admin_terminate"),
    url(r"^api/admin/visits/" + R + r"/elevations/$", v.admin_zone_elevation, name="admin_zone_elevation"),
    url(r"^api/admin/extensions/$", v.admin_extension_queue, name="admin_extension_queue"),
    url(r"^api/admin/extensions/(?P<extension_id>\d+)/decide/$", v.admin_decide_extension, name="admin_decide_extension"),
    url(r"^api/admin/policies/$", v.admin_policies, name="admin_policies"),
    url(r"^api/admin/policies/current/$", v.admin_current_policy, name="admin_current_policy"),
    url(r"^api/admin/policies/(?P<version>\d+)/$", v.admin_policy_detail, name="admin_policy_detail"),
    url(r"^api/admin/policies/(?P<version>\d+)/publish/$", v.admin_publish_policy, name="admin_publish_policy"),
    url(r"^api/admin/registry/$", v.admin_registry, name="admin_registry"),
    url(r"^api/admin/registry/publish/$", v.admin_registry_publish, name="admin_registry_publish"),
    url(r"^api/admin/registry/publications/$", v.admin_registry_publications, name="admin_registry_publications"),
    url(r"^api/admin/registry/(?P<entry_id>\d+)/$", v.admin_registry_entry, name="admin_registry_entry"),
    url(r"^api/admin/registry/(?P<entry_id>\d+)/discard/$", v.admin_registry_discard, name="admin_registry_discard"),
    url(r"^api/admin/reports/(?P<report_type>[a-z_]+)/$", v.admin_report, name="admin_report"),
    url(r"^api/admin/events/$", v.admin_events, name="admin_events"),
    url(r"^api/admin/events/(?P<event_id>\d+)/$", v.admin_event_detail, name="admin_event_detail"),
    url(r"^api/admin/events/(?P<event_id>\d+)/controls/$", v.admin_event_controls, name="admin_event_controls"),
    url(r"^api/admin/bulk-lists/$", v.admin_bulk_lists, name="admin_bulk_lists"),
    url(r"^api/admin/offline-conflicts/$", v.admin_offline_conflicts, name="admin_offline_conflicts"),
    url(r"^api/admin/offline-conflicts/(?P<event_id>\d+)/review/$", v.admin_review_offline_conflict,
        name="admin_review_offline_conflict"),
    url(r"^api/admin/zones/$", v.admin_zones, name="admin_zones"),
    url(r"^api/admin/zones/(?P<code>[A-Za-z0-9_\-]+)/$", v.admin_zone_detail, name="admin_zone_detail"),
    url(r"^api/admin/gates/$", v.admin_gates, name="admin_gates"),

    # Super Admin (UC-001/002/003)
    url(r"^api/superadmin/roles/$", v.super_roles, name="super_roles"),
    url(r"^api/superadmin/roles/(?P<assignment_id>\d+)/reassign/$", v.super_reassign_role, name="super_reassign_role"),
    url(r"^api/superadmin/roles/(?P<assignment_id>\d+)/revoke/$", v.super_revoke_role, name="super_revoke_role"),
    url(r"^api/superadmin/integrations/$", v.super_integrations, name="super_integrations"),
    url(r"^api/superadmin/integrations/(?P<key>[A-Z_]+)/$", v.super_integration_detail, name="super_integration_detail"),
    url(r"^api/superadmin/integrations/(?P<key>[A-Z_]+)/rotate-key/$", v.super_rotate_integration_key,
        name="super_rotate_integration_key"),
    url(r"^api/superadmin/vip/$", v.super_vip, name="super_vip"),
    url(r"^api/superadmin/vip/(?P<permission_id>\d+)/$", v.super_vip_detail, name="super_vip_detail"),
    url(r"^api/superadmin/vip/(?P<permission_id>\d+)/revoke/$", v.super_vip_revoke, name="super_vip_revoke"),

    # External integrations (key-authenticated)
    url(r"^api/integrations/acs/validate/$", v.integration_acs_validate, name="integration_acs_validate"),
    url(r"^api/integrations/hostel/visit-logs/$", v.integration_hostel_logs, name="integration_hostel_logs"),
    url(r"^api/integrations/events/(?P<external_ref>[A-Za-z0-9_\-]+)/attendance/$", v.integration_event_attendance,
        name="integration_event_attendance"),
]
