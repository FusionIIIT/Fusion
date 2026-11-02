# Visitor Management System (VMS)

API-only Django app (`applications/visitor_management`) implementing the frozen VMS specification bundle:

| Artifact | Version | Covered |
|---|---|---|
| Problem Statement | v1.2 | all functional scope 3.1 to 3.15 |
| CFR/AFR Registry | v1.3 | 33 CFRs / 225 AFRs |
| Use Cases | v1.3 | 39 active UCs (UC-029 retired) |
| Business Rules | v1.3 | 47 BRs |
| Workflows | v1.3 | 23 basis + 7 composite, 116 STT rows |

Mounted at `/vms/`, so every route is `/vms/api/...`. DRF with Fusion's Token/Session auth.

## Setup

Already wired in this branch: `applications.visitor_management` in `INSTALLED_APPS`, `url(r'^vms/', ...)` in
`Fusion/urls.py`, and a Celery beat entry `vms-lifecycle-task` (every 5 minutes).

```bash
cd FusionIIIT
python manage.py migrate visitor_management
python manage.py setup_vms_roles --password '<password>'      # zones, gates, demo accounts per role
python manage.py vms_run_scheduled_tasks                       # run once; schedule via cron if no Celery beat
```

`setup_vms_roles` creates zones (COMMON, ACAD, ADMIN, LABS, HOSTEL), gates (MAIN, HOSTEL_GATE) and the accounts
`vms_superadmin`, `vms_admin` (campus), `vms_security` (MAIN gate), `vms_host` (faculty). `--topology-only` skips
accounts. Without Celery: `*/5 * * * * cd FusionIIIT && python manage.py vms_run_scheduled_tasks`.

## Roles

| Role | How it resolves |
|---|---|
| Super Admin | `HoldsDesignation` with designation `vms_super_admin` (setting `VMS_SUPER_ADMIN_DESIGNATIONS`), or Django superuser |
| Admin | active, unexpired `VmsRoleAssignment(role=ADMIN)`, scope CAMPUS or ZONE (BR-181/184) |
| Security Personnel | active, unexpired `VmsRoleAssignment(role=SECURITY)`, scope GATE or ZONE |
| Host | implicit: `ExtraInfo.user_type` is `faculty` or `staff` (BR-185) |
| Visitor | no Fusion account. Gets a secret token at registration, sent as `X-Visitor-Token` |
| External systems | ACS, Hostel and Event Management call with `X-VMS-Integration-Key` (rotated by Super Admin) |

Super Admin does not inherit Admin/Security operations (PS 2.1). Campus-wide configuration (policies, registry,
events, bulk lists, zones) needs a CAMPUS-scoped Admin; decisions on a visit need an Admin whose scope covers the
visit's zones or gate.

## Visit lifecycle (CW-VMS-01/02/03/05/07)

```
ONLINE   --> PENDING_HOST_APPROVAL --(host approve)--> PASS_ACTIVE --(gate)--> ON_SITE --(checkout)--> COMPLETED
         --> PENDING_ADMIN_EXCEPTION --(admin)--> PENDING_HOST_APPROVAL          (same-day urgent, BR-203)
         --> PASS_ACTIVE                                                         (pre-authorised / VIP bypass)
WALK-IN  --> PENDING_HOST_APPROVAL | PENDING_ADMIN_CONTINGENCY --> PASS_ACTIVE (WALK_IN)
BULK     --> PASS_ACTIVE
PENDING_HOST_APPROVAL --(timeout, System)--> EXPIRED      --(reject)--> REJECTED
PASS_ACTIVE --(terminate)--> TERMINATED      ON_SITE --(terminate)--> ON_SITE_PENDING_EXIT --(checkout)--> COMPLETED
```

All moves go through `workflow.apply()`, which refuses anything the STT does not allow and writes a
`VisitStateHistory` row naming the STT row (for example `BW-VMS-22 R2`). `workflow.STT_TRACE` maps all 58 basis rows
to code; `tests/test_workflows.py` checks it against the spec.

## Endpoints by use case

| UC | Actor | Endpoint |
|---|---|---|
| 001 Configure roles | Super Admin | `GET/POST superadmin/roles/`, `POST superadmin/roles/<id>/reassign/`, `.../revoke/` |
| 002 Integration boundaries | Super Admin | `GET superadmin/integrations/`, `PUT superadmin/integrations/<KEY>/`, `POST .../rotate-key/` |
| 003 VIP permissions | Super Admin | `GET/POST superadmin/vip/`, `PATCH superadmin/vip/<id>/`, `POST .../revoke/` |
| 004 Audit trails | Super Admin, Admin | `GET audit-logs/?visitor=&action=&date_from=&date_to=` |
| 005 Access policies | Admin | `GET/POST admin/policies/`, `GET admin/policies/current/`, `PATCH admin/policies/<v>/`, `POST .../publish/` |
| 006 Registry | Admin | `GET/POST admin/registry/`, `PATCH admin/registry/<id>/`, `POST .../discard/`, `POST admin/registry/publish/` |
| 007 Reports | Admin | `GET admin/reports/<type>/?date_from=&date_to=&anonymize=true&export=csv\|pdf` |
| 008 Bulk lists | Admin | `GET/POST admin/events/`, `POST admin/bulk-lists/` (CSV/XLSX `file` or JSON `rows`) |
| 009 Special-event handling | Admin | `POST admin/events/<id>/controls/`, `GET admin/events/<id>/` (attendance, throughput) |
| 010 Pre-register | Visitor | `GET public/hosts/?q=`, `GET public/zones/`, `POST public/visits/` |
| 011 Status and history | Visitor | `GET visitor/visits/`, `GET visitor/visits/<ref>/` |
| 012 Digital pass | Visitor | `GET visitor/visits/<ref>/pass/`, `GET .../pass/pdf/` (QR + barcode) |
| 013 Decide request | Host | `GET host/requests/`, `POST host/requests/<ref>/decide/`, `POST host/requests/bulk-decide/` |
| 014 Pre-authorise | Host | `GET/POST host/preauthorizations/`, `POST .../<id>/revoke/` |
| 015 Arrival updates | Host | `GET host/arrivals/` |
| 016 Terminate early | Host | `POST host/visits/<ref>/terminate/` |
| 017 Walk-in | Security | `POST security/walk-ins/` (`host_unavailable`, `event_id`, `lane=OVERFLOW`) |
| 018 Validate pass | Security | `POST security/gate/validate/` (QR, BARCODE, BADGE, OTP; `lane=FAST`) |
| 019 Manual override | Admin | `POST security/gate/attempts/<id>/refer/`, `GET admin/gate/overrides/`, `POST admin/gate/attempts/<id>/override/` |
| 020 Manual visit log | Security | `POST security/gate/manual-log/` |
| 021 Gate checkout | Security | `POST security/gate/check-out/` |
| 022 Live dashboard | Security, Admin | `GET dashboard/` |
| 023 Zone access | Security / ACS | `POST security/zones/validate/`, `POST integrations/acs/validate/` |
| 024 Zone elevation | Admin | `POST admin/visits/<ref>/elevations/` |
| 025 Zone alert | Security | `GET security/alerts/`, `POST security/alerts/<id>/handle/`, `POST security/alerts/escalate/` |
| 026 / 032 Trigger muster | Admin / Security | `POST muster/` |
| 027 Roll-call | Security | `POST muster/<id>/roll-call/`, `POST muster/<id>/finalize/`, `GET muster/<id>/report/?export=csv\|pdf` |
| 028 Offline entry | Security | `GET security/gate/offline-snapshot/?gate=`, `POST security/gate/offline-events/` |
| 030 Notifications | Visitor | `GET visitor/notifications/` (staff: `GET notifications/`) |
| 031 Self-checkout | Visitor | `POST visitor/visits/<ref>/check-out/`, `POST kiosk/check-out/` |
| 033 Contingency approval | Admin | `GET admin/contingency/`, `POST admin/contingency/<ref>/decide/` |
| 034 Visit extension | Admin | `POST visits/<ref>/extension/` (Host/Admin), `GET admin/extensions/`, `POST admin/extensions/<id>/decide/` |
| 035 Same-day exception | Admin | `GET admin/exceptions/`, `POST admin/exceptions/<ref>/decide/` |
| 036 Terminate early | Admin | `POST admin/visits/<ref>/terminate/` |
| 037 Expire pending | System | `services.lifecycle.expire_pending_requests` (also applied before any late host decision) |
| 038 Auto checkout | System | `services.lifecycle.auto_check_out` |
| 039 Reconcile offline | System | `services.gate.reconcile_offline_events` (on upload and on schedule); `GET admin/offline-conflicts/` |
| 040 Approval reminder | System | `services.lifecycle.send_pending_reminders` |

Also: `GET me/` (VMS roles of the caller), `GET visits/?q=`, `GET visits/<ref>/` (history + logs),
`GET security/expected-arrivals/`, `GET/POST admin/zones/`, `POST admin/gates/`,
`GET integrations/hostel/visit-logs/?since=`, `GET integrations/events/<ref>/attendance/`.

Report types: `visitor_volume`, `peak_hours`, `frequent_visitors`, `denial_statistics`, `sla_compliance`,
`daily_summary`, `audit_trail`, `zone_access`, `blacklist_hits`. Use `export=` (not `format=`, which DRF reserves).

## Where each business rule is enforced

| BR | Function |
|---|---|
| 037, 186, 187 | `registration._validate_identity` + `PreRegistrationInput` |
| 038 | `registration._duplicate_exists` |
| 049, 050 | `registration.decide_contingency` |
| 051, 112, 116, 117, 118, 119, 120 | `common.registry_check`, `common.raise_registry_alerts` |
| 052, 195, 196, 197, 202, 203 | `registration.pre_register` (path selection), `common.find_preauthorization/find_vip_permission` |
| 053 | `registration._decide_one`, `registration.decide_contingency` |
| 062, 200 | `lifecycle.expire_visit`, `registration._expire_late` |
| 073 | `lifecycle.terminate_visit` |
| 077, 082, 190 | `gate._gate_failures`, `gate.validate_at_gate` |
| 085 | `gate.decide_override`, `conf.override_eligible_failures` |
| 096 | `gate.grant_zone_elevation` |
| 101, 105 | `lifecycle.auto_check_out`, `gate.complete_visit` |
| 125 to 129 | `configuration.create_policy_version/update_policy_draft/publish_policy`, `selectors.policy_snapshot` (stored per visit) |
| 130 | `emergency.trigger_muster` |
| 174 | `notifications` (event stored first, each channel attempted only if configured) |
| 181 to 184 | `configuration.assign_role/reassign_role`, `selectors.active_assignments` |
| 185 | `selectors.host_extrainfo`, `registration.resolve_host` |
| 191, 192 | `common.zone_permission`, `gate.evaluate_zone_access` |
| 193, 194 | `common.validate_schedule`, `lifecycle.request_extension/decide_extension` |
| 211 | `VisitPass.pass_type` choices, set by each issuing path |

## Decisions on open clarifications

The spec leaves these unresolved. Each is a single, documented switch point rather than a hidden assumption.

| Issue | Decision |
|---|---|
| ISS-VMS-016/017 matching | `matching.py` only. Normalised exact match on ID number, phone (last 10 digits) or e-mail; name-only entries match on the casefolded name. No name-variation matching. |
| ISS-VMS-018 reminders | `AccessPolicy.reminder_offsets_minutes`, empty by default. Set `[720, 1200]` to get 12h/20h. |
| ISS-VMS-019 CANCELLED | In the status domain, no transition reaches it. |
| ISS-VMS-023 override vs blacklist | `BLACKLIST_MATCH` is not override-eligible. Eligible by default: validity window, gate zone, used OTP (`VMS_OVERRIDE_ELIGIBLE_FAILURES`). |
| Watchlist effect | BLACKLIST rejects; WATCHLIST flags the visit and alerts security. `VMS_WATCHLIST_REJECTS = True` makes both reject. |
| VIP and blacklist | VIP bypasses host approval and (per its scope) zone restrictions only; blacklist checks still apply (BR-197 "other validations remain"). Use a safe-list entry for blacklist exceptions. |
| Policy before first publish | The frozen PS baseline applies (8h max, 4h walk-in, 24h timeout, 2h advance, 30 min contingency SLA). |
| Restricted zones | Hosts cannot grant policy-restricted zones; those need Admin elevation or VIP scope. |
| Extension requester | Visit's Host or a covering Admin. Within the maximum it applies directly; beyond it creates an Admin request. |
| Auto-checkout out-time | Recorded as the pass `valid_until` (deterministic, independent of scheduler lag). |

## Integration notes

* Frontend sidebar: `globals.ModuleAccess` has no `visitor_management` column. Adding one is a change to the shared
  `globals` app, so it is not part of this module; until then gate the menu with `GET /vms/api/me/`.
* Times: Fusion runs `USE_TZ=False` in Asia/Kolkata. Send naive local times or offset-aware ISO strings (converted to IST).
* `reportlab` 4.x assumes Python 3.9+ `hashlib`; on Python 3.8 pin `reportlab<4` for PDF passes and exports.
* Not part of VMS (PS 3.15): physical door control, evacuation execution, HR master data, notification delivery
  infrastructure. VMS records and triggers; SMS needs `VMS_SMS_BACKEND = "dotted.path.to.send(phone, message)"`.

## Tests

```bash
cd FusionIIIT
python manage.py test \
    applications.visitor_management.tests.test_use_cases \
    applications.visitor_management.tests.test_business_rules \
    applications.visitor_management.tests.test_workflows \
    applications.visitor_management.tests.test_api \
    --settings=test_settings
```

See `tests/README.md`.
