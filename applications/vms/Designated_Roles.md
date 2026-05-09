# Module Name: Visitor Management System (VMS)

This document lists the user roles recognised by the VMS module, the
permissions each role holds, and the concrete enforcement points in the
codebase. Role levels are stored on the `HostAuthority` model
(`applications/vms/models.py`) and enforced by the permission classes in
`applications/vms/permissions.py`.

## Designated User Roles & Permissions

### 1. Role Name: Super Admin
* **Description:** Top-level administrator responsible for VMS system
  configuration, feature toggles, and policy decisions. Backed by
  `HostAuthority.LEVEL_SUPER` and the `IsSuperAdmin` permission class.
* **Permissions:**
    * Create, read, update system configuration entries (`SystemConfig`)
      and view the full `ConfigChangeLog` audit trail (BR-057–BR-062).
    * All capabilities of the VMS Admin role (inherits downward).
    * Assign / upgrade authority levels on `HostAuthority` records.
    * Approve high-severity escalations that require system-wide acknowledgement.
* **Enforced at:**
    * `SystemConfigView`, `ConfigChangeHistoryView` (`api/views.py`) —
      `permission_classes = [IsAuthenticated, IsSuperAdmin]`.

---

### 2. Role Name: VMS Admin
* **Description:** Module administrator responsible for blacklist management,
  reporting, data export/import, access-zone configuration, and visiting
  hours. Backed by `HostAuthority.LEVEL_ADMIN` (or `LEVEL_SUPER` which
  inherits) and the `IsVmsAdmin` / `CanRemoveBlacklist` permission classes.
* **Permissions:**
    * Full CRUD on `BlacklistEntry` (add, remove, list, audit).
    * Generate visitor / incident / VIP / audit reports (BR-025–BR-029).
    * Export and import visitor data (BR-067–BR-074).
    * Configure visiting hours (`VisitingHours`) and access zones
      (`AccessZone`) (BR-063, BR-064).
    * View full visitor history (PII-bearing) and incident history for any
      visitor (BR-030, BR-031).
    * View blacklist audit trail.
* **Enforced at:**
    * `BlacklistView.post`, `VisitingHoursView.post`, `AccessZoneView.post`
      — gated via `get_permissions()` → `[IsAuthenticated, IsVmsAdmin]`.
    * `BlacklistRemoveView` — `[IsAuthenticated, CanRemoveBlacklist]`.
    * `ReportGenerationView`, `DataExportView`, `DataImportView`,
      `DataOperationsView`, `VisitorHistoryView`,
      `VisitorHistoryByVisitView`, `IncidentHistoryView`,
      `BlacklistAuditView` — `[IsAuthenticated, IsVmsAdmin]`.
    * `VIPProcessView`, `VIPVisitorsView`, `VIPActivityView` —
      `[IsAuthenticated, IsVmsAdmin]`. Admin-only because VIP flagging
      changes pass validity and triggers notifications.
    * `EscortAssignView`, `EscortReleaseView`, `AvailableEscortsView` —
      moved down to `[IsAuthenticated]` (Security Staff tier) so gate
      officers can assign / release escorts directly when a high-level
      VIP arrives (BR-046). See Security Staff permissions below.

---

### 3. Role Name: Security Supervisor / Host with Approval Authority
* **Description:** Faculty or departmental host with authority to approve
  incoming visit requests, and (optionally) to bypass the standard VIP
  verification flow for pre-cleared guests. Backed by
  `HostAuthority.LEVEL_DEPARTMENT` or above, with
  `can_approve_vip = True` for the VIP bypass capability.
* **Permissions:**
    * Approve visitor requests targeting the host or the host's department
      (BR-011).
    * Bypass standard verification for recognised VIP visitors (BR-043)
      when `can_approve_vip` is set on the user's `HostAuthority` row.
    * Request escort assignments for high-profile visits (BR-046).
    * View visits where they are the named host.
* **Enforced at:**
    * `HasHostApprovalAuthority` permission class — defined but currently
      unused pending a dedicated approval endpoint.
    * `VIPProcessView.post` — base gate is `IsVmsAdmin`. When the request
      body carries `bypass_approval: true`, the inline check additionally
      requires `CanBypassVIPApproval` (the `can_approve_vip` flag);
      otherwise `PermissionDenied` is raised.

---

### 4. Role Name: Security Staff / Gate Officer
* **Description:** Standard operational user at a gate or checkpoint.
  Executes the day-to-day visitor workflow: register, verify, issue pass,
  record movement, deny entry, scan passes, log incidents.
  Backed by any authenticated Fusion user (throttled) — a dedicated
  `SecurityStaffRole` table is a planned follow-up.
* **Permissions:**
    * Register new visitors (BR-001–BR-007) — rate-limited via
      `VmsRegisterThrottle` (30 req/min/user).
    * Verify visitor ID manually or biometrically (BR-008–BR-012).
    * Issue a visitor pass and generate its QR code (BR-013–BR-017).
    * Record entry and exit movements at gates (BR-018–BR-024).
    * Scan visitor passes at checkpoints and perform manual fallback
      verification (BR-019–BR-023).
    * Deny entry with reason codes and escalate if required.
    * Log security incidents (any severity) against the current visit or
      as a standalone checkpoint incident. Incident logging lives on the
      Security Staff console (`VmsStaffPage`) — gate officers are the
      ones who witness incidents, so creation is a staff-tier action.
    * View active visitors, recent visits, and incident feed
      (list responses use `VisitorPublicSerializer`, which masks
      `id_number` and omits contact fields).
    * Assign and release escort personnel for VIP visits (BR-046).
      Escort coordination is a gate-side action: the service-layer rule
      in `services.assign_escort` requires `visit.is_vip = True`, so
      Staff cannot attach an escort to a non-VIP visit. The numeric
      `escort_threshold` config remains the *auto*-escort trigger
      inside `process_vip_visit` (admin-initiated).
* **Enforced at:**
    * `RegisterVisitorView`, `VerifyVisitorView`, `IssuePassView`,
      `RecordEntryView`, `RecordExitView`, `DenyEntryView`,
      `ActiveVisitorsView`, `RecentVisitsView`, `ScanPassView`,
      `ManualVerificationView`, `SecurityIncidentView` — all require
      `IsAuthenticated` only (the baseline role for this tier).
    * `EscortAssignView`, `EscortReleaseView`, `AvailableEscortsView`
      — `[IsAuthenticated]`. Business-rule enforcement
      (`vip_level >= escort_threshold`, availability check, no
      duplicate active assignment) is handled in
      `services.assign_escort`.

---

### 5. Role Name: Host (Faculty / Department Member)
* **Description:** Any Fusion user who may be named as the host of an
  incoming visit. Holds a `HostAuthority` record at `LEVEL_BASIC`
  (default). Hosts do not invoke the gate workflow themselves; they
  receive notifications and confirmations.
* **Permissions:**
    * Receive notifications when a visitor is registered against them
      (BR-006, notifications pipeline).
    * View visits where they are the named host.
    * Cannot approve visits at the department level without being
      upgraded to `LEVEL_DEPARTMENT` or above.
* **Enforced at:**
    * `notifications.notify_host_visitor_request()` (called from
      `services.register_visitor`).
    * Read-only visibility is scoped by `host_name` / `host_contact`
      fields on the `Visit` model.

---

### 6. Role Name: Visitor / End-User
* **Description:** The external individual visiting the campus. Visitors
  do not log into Fusion; they are registered at the gate by Security
  Staff and interact with the system only via a printed / issued
  `VisitorPass`.
* **Permissions:**
    * No direct API access.
    * May present a `VisitorPass` (QR or pass number) at any configured
      checkpoint. The QR payload contains only the opaque
      `pass_number`, `visit_id`, and `valid_until` — visitor identity
      is resolved server-side on scan so that a consumer QR reader
      cannot harvest PII from a printed pass.
    * Identity and contact fields are stored under the `Visitor` model
      and accessed only by Security Staff or VMS Admin roles above.
* **Enforced at:**
    * `ScanPassView` — accepts the pass, looks up the `Visit`
      server-side, and validates authenticity, expiry, and zone access
      via `permissions.check_zone_access`.

---

## Role-to-Permission Matrix (Summary)

| Capability                                   | Visitor | Host | Security Staff | Security Supervisor | VMS Admin | Super Admin |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Present pass at checkpoint                    |  Yes  |  —   |   —    |    —     |   —     |    —    |
| Receive host notifications                    |  —    | Yes  |   —    |   Yes    |  Yes    |   Yes   |
| Register / verify / issue pass / entry / exit |  —    |  —   |  Yes   |   Yes    |  Yes    |   Yes   |
| Scan pass / log incident                      |  —    |  —   |  Yes   |   Yes    |  Yes    |   Yes   |
| Assign / release VIP escort                   |  —    |  —   |  Yes   |   Yes    |  Yes    |   Yes   |
| Approve visit request                         |  —    |  —   |   —    |   Yes    |  Yes    |   Yes   |
| VIP approval bypass                           |  —    |  —   |   —    |   Yes*   |  Yes    |   Yes   |
| Add to blacklist                               |  —    |  —   |   —    |    —     |  Yes    |   Yes   |
| Remove from blacklist                          |  —    |  —   |   —    |    —     |  Yes    |   Yes   |
| View visitor history (full PII)                |  —    |  —   |   —    |    —     |  Yes    |   Yes   |
| Generate reports / export / import             |  —    |  —   |   —    |    —     |  Yes    |   Yes   |
| Configure visiting hours / access zones        |  —    |  —   |   —    |    —     |  Yes    |   Yes   |
| System configuration (`SystemConfig`)          |  —    |  —   |   —    |    —     |   —     |   Yes   |

\* Security Supervisors require `HostAuthority.can_approve_vip = True`.

---

## Implementation References

| Concern                         | File                                           |
|---|---|
| Role storage                    | `applications/vms/models.py` (`HostAuthority`) |
| Permission classes              | `applications/vms/permissions.py`              |
| View-level enforcement          | `applications/vms/api/views.py`                |
| List-response PII masking       | `applications/vms/api/serializers.py` (`VisitorPublicSerializer`) |
| Pass QR minimisation            | `applications/vms/services.py` (`_generate_pass_qr`) |
| Throttling                      | `applications/vms/api/views.py` (`VmsRegisterThrottle`) |
