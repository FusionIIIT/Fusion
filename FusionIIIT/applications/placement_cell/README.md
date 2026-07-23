# Placement Cell

The Placement Cell module manages the full campus placement lifecycle for
IIITDM Jabalpur — company drives, student applications and offers, interview
rounds, statistics and reports, debarments and restrictions, an interactive
placement calendar, an alumni network, and off-campus / published-CPI tracking.

It is an API-only Django app (`applications/placement_cell`) consumed by the
React placement module in `Fusion-client` (`src/Modules/PlacementCell`).

---

## Roles

The module recognises four roles (the user's selected designation, exposed to
the frontend as `state.user.role`):

| Role (designation)   | Capabilities |
|----------------------|--------------|
| `placement officer`  | TPO: schedules/drives, applications, interview rounds, statistics, reports, debarments, restrictions, fields, notifications, off-campus records, published-CPI export, calendar management, announcements |
| `placement chairman` | Admin oversight: officer capabilities plus placement policies |
| `student`            | Browse drives, apply, manage placement profile, view offers/timeline, download CV, read announcements/calendar, alumni network |
| `alumni`             | Alumni profile, post job referrals, mentorship sessions, student network |

**How roles resolve**

- **Backend** authorizes via `HoldsDesignation(working=user, designation__name=…)`.
  `selectors.is_tpo` is true for `placement officer` / `placement chairman`;
  officer/chairman-only endpoints return `403` with `{ "detail": … }`.
- **Sidebar visibility** comes from `ModuleAccess.placement_cell` for the
  designation.
- **Frontend** chooses the tab set in `PlacementCellPage` from `state.user.role`.

---

## Features

### Students
- **Placement Schedule** — browse drives as a chronological **Agenda**
  (Today / This Week / Upcoming / Closed) or a filterable **card** view, with
  per-drive eligibility and deadline countdowns; apply, withdraw, track status.
- **My Applications / My Offers** — application timeline; accept/decline offers.
- **Placement Calendar** — read-only, colour-coded view of drives, tests,
  interviews and deadlines.
- **Announcements** — read placement-cell announcements.
- **Download CV**, placement profile, notification preferences.
- **Alumni Network** — connect with alumni, browse referrals, mentorship.

### Placement Officer / Chairman
- **Add / edit drives** with eligibility (min CPI, branches from the live
  department list, passout year, gender) and custom **application fields**
  (creatable inline).
- **Student CPI** — per-batch published CPI (computed from the examination
  module's announced results), with off-campus companies and **Excel export**.
- **Off-Campus Placements** — record offers students received off campus
  (company autocomplete from registered companies).
- **Placement Statistics & Reports** — stats, report generation and export.
- **Debarred Students** and **Restrictions** (institute-wide eligibility bars).
- **Send Notifications**, **Company Registration**, **Fields** management.
- **Placement Calendar** — Google-Calendar-style: click a date/slot to add an
  event, edit/delete events; merged with drives and deadlines.
- **Announcements** — post / pin / delete.
- **Placement Appeals**, **Higher Studies**, **Alumni Verification**.

### Chairman
- All officer capabilities plus **Placement Policies**.

---

## Backend

- **Models** (`models.py`, ~45): profiles & academic info (Education, Skill,
  Experience, …), `NotifyStudent`, `PlacementSchedule`, `PlacementApplication`,
  `PlacementStatus`, `PlacementRound`, `PlacementRecord`, `StudentRecord`,
  `PlacementRestriction`, `PlacementPolicy`, `PlacementAppeal`, alumni models,
  and the additive `PlacementAnnouncement`, `OffCampusPlacement`,
  `PlacementCalendarEvent`.
- **API** (`api/urls.py`, `api/views.py`, `api/serializers.py`): DRF, Token
  authentication. URLs are mounted under `placement/` (see `Fusion/urls.py`),
  so routes are `…/placement/api/<route>/`.

### Endpoint groups

| Area | Routes |
|------|--------|
| Drives & schedule | `api/placement/`, `api/placement/<id>/`, `api/calender/`, `api/timeline/<id>/`, `api/nextround/<id>/` |
| Applications & offers | `api/apply-for-placement/`, `api/my-applications/`, `api/my-offers/`, `api/offer/<id>/`, `api/offer/<id>/respond/`, `api/student-applications/<id>/`, `api/application-detail/<id>/`, `api/download-applications/<id>/` |
| Statistics & reports | `api/statistics/`, `api/delete-statistics/<id>/`, `api/reports/`, `api/reports/export/`, `api/report-schedules/`, `api/higher-studies/` |
| Eligibility & policy | `api/restrictions/`, `api/policies/`, `api/branches/` |
| Debarment | `api/debared-students/`, `api/debared-status/<roll_no>/` |
| Fields & profile | `api/add-field/`, `api/form-fields/`, `api/profile/`, `api/notification-preferences/`, `api/registration/`, `api/generate-cv/` |
| Notifications | `api/send-notification/` |
| Announcements | `api/announcements/`, `api/announcements/<id>/` |
| Off-campus | `api/offcampus/`, `api/offcampus/<id>/` |
| Published CPI | `api/cpi-batches/`, `api/cpi-students/` (`?batch_id=` , `?export=excel`) |
| Calendar events | `api/calendar-events/`, `api/calendar-events/<id>/` |
| Appeals | `api/placement-appeals/`, `api/placement-appeals/<id>/` |
| Alumni | `api/alumni/profile/`, `api/alumni/directory/`, `api/alumni/verification/`, `api/alumni/referrals/`, `api/alumni/connections/`, `api/alumni/sessions/` |

**Authorization** — all endpoints require authentication; write/sensitive
operations are gated on `selectors.is_tpo` (officer/chairman). Server-controlled
fields (`created_by`, `added_by`, `posted_by`) are never client-settable.

### Published CPI

`selectors.get_student_published_cpi` derives a student's CPI from the
examination module's latest **announced** `ResultAnnouncement` (not the static
`Student.cpi`). The per-batch view memoises each student's computed CPI in the
cache (keyed by roll number + semester), so reloading a batch is near-instant.

---

## Frontend (`Fusion-client/src/Modules/PlacementCell`)

- React 18 + Vite, Mantine v7, Redux Toolkit, axios, `mantine-react-table`,
  `react-big-calendar`.
- `pages/PlacementCellPage.jsx` renders the shared `ModuleTabs` navbar and the
  role-specific tab set. **Every tab is lazy-loaded** behind a `Suspense`
  boundary so opening the module only downloads the active tab's code; Vite
  `manualChunks` splits the heavy vendors into cacheable chunks.
- `api.js` (+ `services/api.js` re-export) holds `placementApi` with one method
  per endpoint and `buildAuthConfig()` for the token header.
- Date inputs use native `datetime-local` / `date` controls for reliability.

---

## Setup — role accounts

`manage.py setup_placement_roles` creates one idempotent login per role and
enables `ModuleAccess.placement_cell`. The password is supplied at runtime and
is **not** stored in the repo:

```bash
cd FusionIIIT
python manage.py setup_placement_roles --password '<password>'
# or set PLACEMENT_ROLE_PASSWORD
```

| Username             | Role               |
|----------------------|--------------------|
| `placement_officer`  | placement officer  |
| `placement_chairman` | placement chairman |
| `placement_student`  | student            |
| `placement_alumni`   | alumni             |

---

## Tests

See [`tests/README.md`](tests/README.md). Run with the dedicated settings
(migrations disabled so the historical chain cannot block test-DB creation):

```bash
cd FusionIIIT
python manage.py test \
    applications.placement_cell.tests.test_placement_api \
    applications.placement_cell.tests.test_use_cases \
    applications.placement_cell.tests.test_business_rules \
    applications.placement_cell.tests.test_workflows \
    applications.placement_cell.tests.test_module \
    --settings=test_settings
```

`test_placement_api` covers schema regressions, API-only URL wiring,
authentication and role authorization (including announcements, off-campus,
published-CPI export and calendar-event CRUD).
