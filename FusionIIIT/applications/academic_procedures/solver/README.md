# Whole-College Semester Timetable Generation

Automated, whole-institute class scheduling for IIITDM Jabalpur, powered by
[Google OR-Tools CP-SAT](https://developers.google.com/optimization/cp). Given
all floated curricula for a term, the solver assigns every lecture/tutorial/
practical session a `(day, hour, room)` slot such that rooms, faculty, and
student cohorts never clash, while minimising soft-constraint penalties
(day-spread, seat wastage, faculty time preferences, …).

It is an API-only Django feature
(`applications/academic_procedures/solver/timetable_solver.py` +
`applications/academic_procedures/api/timetable_api.py`) consumed by the
React admin console in `Fusion-client`
(`src/Modules/Academic/AdminSemesterTimetable.jsx`).

---

## Architecture

| Layer | File |
|---|---|
| Solver engine (CP-SAT model) | `solver/timetable_solver.py` |
| REST API | `api/timetable_api.py`, routed in `api/urls.py` under `/academic-procedures/api/timetable/…` |
| Data model | `models.py` (8 additive tables, migration `0061_timetable_models.py`) |
| Admin UI | `Fusion-client/src/Modules/Academic/AdminSemesterTimetable.jsx` |

### Tables (all new, zero changes to existing production tables)

| Table | Purpose |
|---|---|
| `Classroom` | Physical rooms: capacity, type (Lecture Hall / Lab / Workshop / …), active flag |
| `CourseWeeklyRequirement` | Per-curriculum weekly session breakdown (lectures/tutorials/practicals, lab block size, preferred room type). Falls back to 3L/1T/0P if not configured |
| `TimetableVersion` | One row per solver run: `Draft → UnderReview → Approved → Published → Archived`, or `Infeasible` |
| `TimetableSlot` | One scheduled hour (curriculum, instructor, room, cohort, day, hour). Multi-hour practicals share a `lab_block_id` |
| `ElectiveBasket` / `ElectiveBasketCurriculum` | Groups of parallel electives forced to the same `(day, hour)` so students can choose between them |
| `FacultyPreference` | Faculty-declared `Unavailable`/`Preferred` time windows |
| `TimetableConflictLog` | Diagnostics written when pruning or solving fails (`CRITICAL` / `WARNING` / `INFO`) |

### Solver pipeline (`WholeCollegeTimetableSolver.solve()`)

1. **Ingest & prune** (`_ingest_and_prune`) — reads floated curricula, rooms,
   weekly requirements, elective baskets, faculty preferences, and any
   `is_locked` slots from a prior version (for incremental rescheduling).
   Builds one `SessionRecord` per lecture/tutorial/practical occurrence and
   prunes its eligible-room domain by capacity + room-type affinity. If any
   session has zero eligible rooms, this raises `CapacityBottleneck` and the
   run is marked `Infeasible` without ever calling the solver.
2. **Build & solve** (`_build_and_solve`) — one boolean variable per
   `(session, day, hour, room)` combination; hard constraints via
   `AddExactlyOne` / `AddAtMostOne`; soft constraints folded into a weighted
   `Minimize` objective; solved with CP-SAT (`max_time_in_seconds`,
   `num_search_workers` configurable per call).
3. **Persist** (`_extract_and_persist`) — bulk-inserts the winning assignment
   as `TimetableSlot` rows under the new `TimetableVersion`.

Hard constraints: room/faculty/cohort mutual exclusion, lab-block continuity
(no crossing the 13:00 lunch break), elective-basket synchronisation, room
capacity/type eligibility, and respecting locked slots.

Soft constraints (weighted penalties): same course on the same day twice
(`WEIGHT_DAY_SPREAD`), seat wastage (`WEIGHT_SEAT_WASTE`), and faculty
"Unavailable" preference windows (`WEIGHT_FAC_PREF`).

---

## API endpoints

All under `/academic-procedures/api/timetable/`:

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `generate/` | acadadmin / Dean Academic | Trigger a full solver run |
| GET | `versions/` | any authenticated user | List `TimetableVersion`s |
| GET | `slots/` | any authenticated user | Filtered slot list (version/cohort/faculty/day) |
| POST | `slot/override/` | acadadmin | Manually move one slot, with live conflict validation |
| PATCH | `version/<id>/publish/` | Dean Academic | Promote a Draft/Approved version to Published (archives the previous one) |
| GET | `my-schedule/` | any authenticated user | Personalised weekly grid (student or faculty, inferred from profile) |
| GET | `room-utilization/` | any authenticated user | Day×hour heatmap for one room |
| GET | `conflict-log/` | any authenticated user | Diagnostics for a version |
| GET/POST | `classrooms/`, `classrooms/<room_id>/` | read: anyone, write: acadadmin | Classroom CRUD |
| GET/POST | `weekly-requirements/` | read: anyone, write: acadadmin | Per-curriculum session counts |
| GET/POST | `elective-baskets/` | read: anyone, write: acadadmin | Elective synchronisation groups |
| GET/POST | `faculty-preferences/` | read: anyone, write: self or acadadmin | Faculty time preferences |

---

## How to run timetable generation

### Prerequisites

1. `ortools` must be installed (now in `requirements.txt` / `Pipfile` — run
   `pip install -r requirements.txt` or `pipenv install` after pulling).
2. Migration `0061_timetable_models` must be applied:
   ```bash
   python manage.py migrate academic_procedures
   ```
3. Seed classroom inventory — the solver has nothing to assign rooms from
   until `Classroom` rows exist. Either via Django admin, or via the API:
   ```bash
   curl -X POST $HOST/academic-procedures/api/timetable/classrooms/ \
     -H "Authorization: Token $ACADADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"room_id":"L101","building":"Main","capacity":250,"room_type":"Lecture Hall"}'
   ```
4. (Optional) Set per-curriculum session counts via `weekly-requirements/` —
   any curriculum without one defaults to 3 lectures + 1 tutorial + 0
   practicals per week.
5. Log in as a user holding the `acadadmin` (or `Dean Academic`) designation —
   `generate_timetable` is gated on this role.

### Option A — Admin Console (recommended)

Fusion-client → **Calendar & Feedback → Semester Timetable**
(`AdminSemesterTimetable.jsx`, slug `semester-timetable`):

1. Set **Academic Year**, **Semester**, and solver **Timeout (s)**.
2. Click **Generate Schedule**. Success shows solver status, slot count, and
   solve time; infeasibility shows the reason and opens the **Conflict Log**
   tab with the specific capacity/constraint bottleneck.
3. Browse the result in **Weekly Grid** or **Slot List**, filter by
   batch/programme/branch/section.
4. Click a slot's edit icon to **override** it (day/hour/room), optionally
   locking it so future regenerations preserve the manual placement.
5. Use **Room Heatmap** to check utilisation, **Conflict Log** for
   diagnostics.
6. Once satisfied, click **Publish** (Dean Academic role) to make the version
   the one returned by `my-schedule/` and `slots/` (default) for everyone.

### Option B — REST API

```bash
curl -X POST $HOST/academic-procedures/api/timetable/generate/ \
  -H "Authorization: Token $ACADADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"academic_year": 2026, "semester_type": "Odd Semester", "timeout_seconds": 60}'
```
Returns `200` with `version_id`/`slots_created`/`solve_time_sec` on success,
`422` with `conflicts: [...]` if infeasible, `400` for bad input.

### Option C — Django shell / management script

```python
from applications.academic_procedures.solver.timetable_solver import (
    run_whole_college_timetable_generation,
)
success, message = run_whole_college_timetable_generation(
    academic_year=2026, semester_type='Odd Semester', timeout_seconds=60,
)
print(success, message)
```

### Interpreting results

- `OPTIMAL` / `FEASIBLE` — slots were created under the new `TimetableVersion`
  (status `Draft`).
- `INFEASIBLE` — no valid assignment exists. Check `conflict-log/` for the
  `CRITICAL` entry. The most common cause is **insufficient room-hour
  capacity**: total required session-hours (floated curricula × weekly
  lectures/tutorials/practicals) must not exceed `active rooms × 40
  slots/week` (5 days × 8 teaching hours, excluding the 13:00 lunch hour).
  Fix by seeding more classrooms, marking fewer curricula as floated for the
  term, or configuring lighter `CourseWeeklyRequirement`s.

---

## Recent changes

- **Added `ortools` to `requirements.txt`/`Pipfile`.** It was already used by
  the solver but was missing from the dependency manifests, so a fresh
  environment would silently fall back to the `ERROR` status
  ("google-ortools is not installed").
- **Fixed the faculty-preference soft constraint (BR-SC-06).** It previously
  built a `curriculum_instructor → faculty` lookup but never used it, and
  instead penalised *any* instructor's session during a time window that a
  *different* faculty member had marked `Unavailable`. It now correctly maps
  each session's `Curriculum_Instructor` to the owning `Faculty` row
  (`Faculty.id` is a `OneToOneField` onto the same `ExtraInfo` row referenced
  by `Curriculum_Instructor.instructor_id`) and only penalises that faculty
  member's own sessions.
- Removed a no-op branch in the objective-building loop
  (`isinstance(item, int)` always took the same path as its `else`).

### Known limitation (not fixed — pre-existing, low impact)

`_is_dean` / `_is_faculty` in `timetable_api.py` check for designation names
`'Associate Dean Academic Affairs'` and `'faculty'`, neither of which exists
as a `Designation` row in this database (other modules check faculty status
via `ExtraInfo.user_type == 'faculty'` instead). This doesn't break the
Dean-publish gate — `'Dean Academic'` is a real designation and still
matches — but `_is_faculty` is effectively dead code today.
