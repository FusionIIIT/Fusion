# Module Name: Notification & Announcement Module (NAM)

## Designated User Roles & Permissions

The notification module exposes its functionality through a REST API guarded by Django REST Framework's `IsAdminUser` and `IsAuthenticated` permissions, plus an explicit `is_staff` / `is_superuser` check inside `services.broadcast_announcement` (BR-NT-03).

---

### 1. Role Name: NAM Admin (Authorized Sender / Module Admin)

* **Description:** Institute-level administrators or designated NAM operators (e.g., Director's office, Dean PnD, Registrar). They have full control over event-type registry, manual broadcasts, and audit reporting.

* **Permissions:**
    * **Full CRUD on Event Types** — `POST /api/notifications/event-types/register/`, list & detail endpoints. (UC-NT-01)
    * **Broadcast Manual Announcements** — orange Broadcast button on the dashboard; `POST /api/notifications/announcements/broadcast/` with audience filters (department / batch / designation / specific users). (UC-NT-03)
    * **Trigger System Notifications** — `POST /api/notifications/trigger/` and the 22 module-specific shortcuts. (UC-NT-02)
    * **View All Announcements** including expired (audit) — `GET /api/notifications/announcements/all/`.
    * **Read audit metadata** — every announcement carries `sender`, `created_at`, and unique `approval_id` UUID (BR-NT-08).
    * **Set priority=Critical** — bypasses user DND + sends email (BR-NT-05).
    * Inherits all NAM Recipient permissions (read own tray, mark read, archive, star).

* **How identified:** `request.user.is_staff` OR `request.user.is_superuser` is `True` in `auth_user`. Also exposed to the React app as `state.user.isStaff` from `/api/auth/me`.

---

### 2. Role Name: External Fusion Module (System Actor)

* **Description:** Other Fusion apps (Leave, Mess, Complaints, Placement, Gymkhana, etc.) that emit notifications on internal events — e.g., a leave is approved, a complaint is filed, a placement drive opens. They are not human users; they invoke NAM through service helpers or the API.

* **Permissions:**
    * **Send module-typed notifications** via:
        * Direct Python: `services.<module>_notif(sender, recipient, type=...)` — 22 helpers (`leave_module_notif`, `central_mess_notif`, `placement_cell_notif`, ...).
        * REST API: `POST /api/notifications/notify/<module>/` — same 22 endpoints, gated by `IsAdminUser` (BR-NT-03).
        * `notification_client.NotificationClient` — the public wrapper class.
    * **Trigger pre-registered events** via `POST /api/notifications/trigger/` with an `event_id` (UUID). Subject to BR-NT-04 60-second dedup.
    * **No direct DB writes** — every send must go through `services._send()` (BR-NT-01 chokepoint).
    * **No read access to other users' notifications.**

* **How identified:** Authenticated with a service-account token whose user has `is_staff=True`. In current setup we reuse the calling user's token; in a future iteration this should be a dedicated per-module service account.

---

### 3. Role Name: NAM Recipient (Student / Faculty / Staff — End User)

* **Description:** Any authenticated Fusion user who receives notifications and announcements through the global navbar bell and the dashboard tabs.

* **Permissions:**
    * **Read own tray** — `GET /api/notifications/`, `GET /api/notifications/unread/`, `GET /api/notifications/unread-count/`. (UC-NT-04)
    * **Mark notifications read / unread** — `PATCH /<id>/mark-read/`, `PATCH /<id>/mark-unread/`, plus the bulk variants `mark-all-read/`, `mark-all-unread/`.
    * **Star / unstar** — `PATCH /<id>/star/` toggles `data.starred`.
    * **Archive (soft-delete)** — `DELETE /<id>/delete/` inserts an `ArchivedNotification` row; original notification preserved 180 days (BR-NT-09).
    * **Open with deep-link** — `GET /<id>/open/` marks read and returns the source-module URL.
    * **Manage preferences** — `GET /preferences/`, `POST /preferences/set/` to opt-out of specific Fusion modules (BR-NT-06).
    * **Read active announcements** — `GET /api/notifications/announcements/` (only non-expired).
    * **Cannot send notifications, broadcast, register events, or permanently delete.**

* **How identified:** Any user with a valid token from `POST /api/auth/login/`. No `is_staff` requirement.

---

## Permission Matrix

| Capability                           | NAM Admin | External Module | Recipient |
|--------------------------------------|:---------:|:---------------:|:---------:|
| Register Event Type (UC-NT-01)       |    ✅     |       ❌        |    ❌     |
| Trigger via Event ID (UC-NT-02)      |    ✅     |       ✅        |    ❌     |
| Use module shortcut endpoints        |    ✅     |       ✅        |    ❌     |
| Broadcast Announcement (UC-NT-03)    |    ✅     |       ❌        |    ❌     |
| Set priority=Critical (BR-NT-05)     |    ✅     |       ✅        |    ❌     |
| View own tray (UC-NT-04)             |    ✅     |       n/a       |    ✅     |
| Mark read / unread / star / archive  |    ✅     |       n/a       |    ✅     |
| View ALL announcements (incl expired)|    ✅     |       ❌        |    ❌     |
| View audit metadata (approval_id)    |    ✅     |       ❌        |    ❌     |
| Permanent deletion                   |    ❌     |       ❌        |    ❌     |

---

## Enforcement Layers (defense in depth)

1. **HTTP layer** — `@permission_classes(IsAdminUser)` on every send/register/trigger endpoint (`api/views.py`).
2. **Service layer** — explicit `if not (sender.is_staff or sender.is_superuser)` check in `services.broadcast_announcement` (raises `UnauthorizedSender`).
3. **Resource layer** — every read query filters by `recipient=request.user`; users cannot read each other's notifications.
4. **UI layer** — Broadcast button on the dashboard renders only when `state.user.isStaff` is True.
5. **DB layer** — `ArchivedNotification` UNIQUE on `(user_id, notification_id)`; `Announcement.approval_id` UNIQUE UUID for audit traceability.
