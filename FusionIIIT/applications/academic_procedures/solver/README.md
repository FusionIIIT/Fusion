# Whole-College Semester Timetable Generation

Automated, whole-institute class scheduling for IIITDM Jabalpur, powered by
[Google OR-Tools CP-SAT](https://developers.google.com/optimization/cp). Given
all floated curricula for a term, the solver assigns every lecture/tutorial/
practical session a `(day, hour, room)` slot such that rooms, faculty, and
student cohorts never clash, while minimising soft-constraint penalties
(day-spread, seat wastage, faculty time preferences, …).

The Django solver and REST API are consumed by the React admin console in
`Fusion-client/src/Modules/Academic/AdminSemesterTimetable.jsx`.

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

1. **Ingest & prune** (`_ingest_and_prune`) — by default reads registered
   courses for the selected working year, term, and semester, including actual
   student enrolments and modern `CourseInstructor` offerings. The legacy
   floated-curriculum source remains available for old versions/tests. It also
   reads rooms, faculty preferences, and any `is_locked` slots from a prior
   version (for incremental rescheduling).
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
preference windows (`WEIGHT_FAC_PREF`: "Unavailable" hours are penalised,
"Preferred" hours rewarded).  `WEIGHT_DAILY_LOAD`, `WEIGHT_STU_FATIGUE` and
`WEIGHT_FAC_FATIGUE` are defined but not implemented yet.

---

## API endpoints

All under `/academic-procedures/api/timetable/`:

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `generate/` | acadadmin / Dean Academic | Trigger a full solver run |
| GET | `versions/` | published: anyone; all statuses: acadadmin / Dean | List `TimetableVersion`s |
| GET | `slots/` | published: anyone; other versions: acadadmin / Dean | Filtered slot list (version/cohort/faculty/day) |
| POST | `slot/override/` | acadadmin / Dean Academic | Move one slot in a non-closed version (a lab block moves as a whole), with conflict validation |
| PATCH | `version/<id>/publish/` | Dean Academic | Promote a Draft/UnderReview/Approved version with slots to Published (archives the term's previous one) |
| GET | `my-schedule/` | any authenticated user | Personalised weekly grid (student or faculty, inferred from profile) |
| GET | `room-utilization/` | published: anyone; other versions: acadadmin / Dean | Day×hour heatmap for one room |
| GET | `conflict-log/` | acadadmin / Dean | Diagnostics for a version |
| GET/POST | `classrooms/`, `classrooms/<room_id>/` | read: anyone, write: acadadmin | Classroom CRUD |
| GET/POST | `weekly-requirements/` | read: anyone, write: acadadmin | Per-curriculum session counts |
| GET/POST | `elective-baskets/` | read: anyone, write: acadadmin | Elective synchronisation groups |
| GET/POST | `faculty-preferences/` | read/write own; acadadmin: anyone's | Faculty time preferences |

Without `version_id`, `slots/`, `my-schedule/` and `room-utilization/` use the
latest published version; pass `academic_year` and `semester_type` to pick a
specific term.

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
   until `Classroom` rows exist. To replace the local room inventory with the
   institute CR/L seating-capacity data (and remove stale generated versions
   that still reference old rooms), run:
   ```bash
   python manage.py seed_timetable_rooms --replace --clear-timetables
   ```
   The class timetable uses each room's physical capacity. `CR` rooms map to
   `Tutorial Room` and `L` rooms map to `Lecture Hall`, matching the solver's
   room-type vocabulary. Rooms can also be added individually via the API:
   ```bash
   curl -X POST $HOST/academic-procedures/api/timetable/classrooms/ \
     -H "Authorization: Token $ACADADMIN_TOKEN" \
     -H "Content-Type: application/json" \
      -d '{"room_id":"L-102","building":"LHTC","capacity":126,"room_type":"Lecture Hall"}'
   ```
4. (Optional) Set per-curriculum session counts via `weekly-requirements/` —
   any curriculum without one defaults to 3 lectures + 1 tutorial + 0
   practicals per week.
5. Log in as a user holding the `acadadmin` (or `Dean Academic`) designation —
   `generate_timetable` is gated on this role.

### Option A — Admin Console

Fusion-client → **Calendar & Feedback → Semester Timetable**
(`AdminSemesterTimetable.jsx`, slug `semester-timetable`):

1. Set **Academic Year**, **Term Type**, **Semester Number**, and solver
   **Timeout (s)**. Odd terms allow semesters 1/3/5/7; even terms allow
   2/4/6/8. Courses are sourced from Fusion registrations for the selected
   working year/term/semester. Until lab inventory is loaded, practical blocks
   appear under the virtual room label `LAB`.
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
   -d '{"academic_year": 2025, "semester_type": "Odd Semester", "semester_number": 3, "course_source": "registered", "timeout_seconds": 120}'
```
Returns `200` with `version_id`/`slots_created`/`solve_time_sec` on success,
`422` with `conflicts: [...]` if infeasible, `504` with `status: "timeout"` if
no timetable was found in time, `400` for bad input (`timeout_seconds` must be
1–600).

### Option C — Django shell / management script

```python
from applications.academic_procedures.solver.timetable_solver import (
    run_whole_college_timetable_generation,
)
success, message = run_whole_college_timetable_generation(
    academic_year=2025, semester_type='Odd Semester', semester_number=3,
    course_source='registered', timeout_seconds=120,
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
  term, or configuring lighter `CourseWeeklyRequirement`s. Other causes:
  `LOCK_CONFLICT` (two locked slots need the same room/person/cohort) and
  `NO_VALID_SLOT` (a session's block size fits no start hour).
- `TIMEOUT` — the time limit ran out before *any* timetable was found. This is
  **not** a proof of infeasibility; retry with a larger `timeout_seconds`. The
  empty version is set to `Archived` with the reason in `remarks`.
- `LOCK_IGNORED` warnings — a locked slot from the previous version could not
  be honoured (room gone, too small, wrong type, or bad hour); that session
  was scheduled freely instead.

### Scheduling rules worth knowing

- **Faculty clashes are per person**, not per `Curriculum_Instructor` row, and
  every instructor listed for a course is booked for its hours.
- **`Common` courses** involve every branch of the batch, and unsectioned
  classes involve every section, so they clash with branch/section classes.
- **Elective-basket courses** for the same cohort run in parallel (students
  pick one); they are exempt from clashing with each other only.  Every
  course in a basket must have the same number of weekly sessions, otherwise
  the run fails with `BASKET_MISMATCH`.
- **Cohort size** is counted from `Student` rows using the student's
  department name as the branch (compared case-insensitively, so department
  `Design` matches branch `DESIGN`); with no matching students it falls back
  to 30.  Design courses are filed as `B.Tech`/`DESIGN` while Design students
  are `B.Des`, so `B.Des` students count toward (and see) `B.Tech`/`DESIGN`
  courses, but not `B.Tech` `Common` courses (not recorded either way).  Courses are not split into sections, so a course needs one room that
  seats the whole branch (or, for `Common`, the whole batch).
- **Locks** are taken from the newest earlier version of the same term that
  has slots, and stay locked in the new version.

### Tests

`test_timetable_solver.py` drives the real CP-SAT model (only DB reads and
writes are replaced) and needs `ortools` but no database:

```bash
cd FusionIIIT
python -m unittest applications.academic_procedures.test_timetable_solver \
    applications.academic_procedures.test_timetable_validation
```

`test_timetable_validation.py` covers the API's input validation
(`api/timetable_validation.py`, kept free of Django imports) and checks that
the API's choice lists and the model `Meta` stay in sync with `models.py` and
migration 0061.

`test_timetable_api.py` covers the REST API, permissions and an end-to-end
generation against the test database.  It needs the full Django environment
and PostgreSQL:

```bash
cd FusionIIIT
python manage.py test applications.academic_procedures.test_timetable_api \
    --settings=Fusion.settings.test_settings
```

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
