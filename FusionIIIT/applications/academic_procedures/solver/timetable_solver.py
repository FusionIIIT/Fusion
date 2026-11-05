"""
Whole-College Semester Timetable Solver
=======================================
Powered by Google OR-Tools CP-SAT.

Architecture follows the blueprint in Section 3 (hard/soft constraints) and
Section 5 (FC-01 / FC-02 / FC-03 flowcharts).

Public interface::

    from applications.academic_procedures.solver.timetable_solver import (
        WholeCollegeTimetableSolver,
    )

    solver = WholeCollegeTimetableSolver(academic_year=2026,
                                         semester_type='Odd Semester')
    result = solver.solve(timeout_seconds=60)
    # result.status in {'OPTIMAL', 'FEASIBLE', 'INFEASIBLE', 'ERROR'}

The solver is completely stateless with respect to the Django ORM; it reads
data at the start of ``solve()`` and bulk-inserts results at the end.  It
never modifies any pre-existing table.
"""

from __future__ import annotations

import logging
import math
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── OR-Tools import guard ────────────────────────────────────────────────────
try:
    from ortools.sat.python import cp_model
    _ORTOOLS_AVAILABLE = True
except ImportError:
    _ORTOOLS_AVAILABLE = False
    logger.warning(
        "google-ortools is not installed.  Install it with: pip install ortools\n"
        "The solver will return an error status until it is available."
    )

# ── Constants ────────────────────────────────────────────────────────────────

# Monday=1 … Friday=5 (no weekends)
DAYS = list(range(1, 6))

# 09:00–18:00 excluding 13:00 (lunch)
HOURS = [9, 10, 11, 12, 14, 15, 16, 17]

# Slot types
LECTURE = 'Lecture'
TUTORIAL = 'Tutorial'
PRACTICAL = 'Practical'

# Default slot-type → permitted room types
SLOT_ROOM_AFFINITY: Dict[str, List[str]] = {
    LECTURE:   ['Lecture Hall', 'Tutorial Room', 'Seminar Room'],
    TUTORIAL:  ['Tutorial Room', 'Seminar Room', 'Lecture Hall'],
    PRACTICAL: ['Computer Lab', 'Hardware Lab', 'Mechanical Workshop'],
}

# Capacity buffer factor (BR-HC-07 / Section 6.3)
CAPACITY_BUFFER = 1.10

# Curriculum.branch value meaning "every branch of the batch"
WHOLE_BATCH_BRANCH = 'Common'

# Students assumed when no enrolment data matches a cohort
DEFAULT_COHORT_SIZE = 30

# Design courses are stored in Curriculum as programme 'B.Tech', branch
# 'DESIGN', while Design students are stored as programme 'B.Des'.  This maps
# a student programme to the (programme, branch) its courses are filed under.
# Whether B.Des students also attend 'Common' B.Tech courses is not recorded
# anywhere, so they are not added to those cohorts.
STUDENT_PROGRAMME_ALIASES = {'B.Des': ('B.Tech', 'DESIGN')}

# Soft-constraint penalty weights (BR-SC-*)
WEIGHT_DAY_SPREAD    = 100  # BR-SC-01
WEIGHT_DAILY_LOAD    = 60   # BR-SC-02
WEIGHT_STU_FATIGUE   = 50   # BR-SC-03
WEIGHT_FAC_FATIGUE   = 50   # BR-SC-04
WEIGHT_SEAT_WASTE    = 10   # BR-SC-05
WEIGHT_FAC_PREF      = 30   # BR-SC-06

# Valid lab-block start hours (must not cross lunch)
LAB_STARTS_2H = [9, 10, 11, 14, 15, 16]   # block of 2 consecutive hours
LAB_STARTS_3H = [9, 10, 14, 15]            # block of 3 consecutive hours


# ── Data containers ──────────────────────────────────────────────────────────

@dataclass
class SessionRecord:
    """One atomic scheduling unit passed into the solver."""
    session_id: str          # Unique key, e.g. "cur123-L1"
    curriculum_id: Optional[int]
    curriculum_instructor_id: Optional[int]
    course_code: str
    course_name: str
    slot_type: str           # Lecture | Tutorial | Practical
    block_size: int          # 1 for L/T, 2 or 3 for practicals

    # Cohort
    batch: int
    programme: str
    branch: str
    section: str             # '' means whole-batch (no section split)

    # Approximate cohort size after capacity buffer applied
    effective_size: int

    # Pre-pruned list of eligible room IDs
    eligible_rooms: List[str]

    # Locked assignment (None if not locked)
    locked_day: Optional[int] = None
    locked_hour: Optional[int] = None
    locked_room: Optional[str] = None

    # Other Curriculum_Instructor ids teaching this course.  They occupy the
    # same hours as the primary instructor, so they take part in clash checks.
    co_instructor_ids: List[int] = field(default_factory=list)

    # Modern registered-course source. Legacy sessions leave these empty.
    course_id: Optional[int] = None
    course_instructor_id: Optional[int] = None
    faculty_ids: List[object] = field(default_factory=list)
    student_ids: List[str] = field(default_factory=list)
    room_label: str = ''

    @property
    def subject_key(self):
        if self.course_id is not None:
            return f'course:{self.course_id}'
        return f'curriculum:{self.curriculum_id}'


@dataclass
class SolverResult:
    # 'OPTIMAL' | 'FEASIBLE' | 'INFEASIBLE' (proven) | 'TIMEOUT' (no solution
    # found in time, NOT a proof of infeasibility) | 'ERROR'
    status: str
    version_id: Optional[int] = None
    slots_created: int = 0
    courses_scheduled: int = 0
    solve_time_sec: float = 0.0
    conflicts: List[dict] = field(default_factory=list)
    message: str = ''


# ── Pure helpers (no Django, no OR-Tools; unit-testable on their own) ────────

def valid_block_starts(block_size: int) -> List[int]:
    """Start hours from which ``block_size`` consecutive hours fit in HOURS.

    13:00 is not in HOURS, so a block can never cross the lunch break.
    """
    if block_size < 1:
        return []
    return [h for h in HOURS if all(h + i in HOURS for i in range(block_size))]


def eligible_room_types(slot_type: str, preferred_room_type: str) -> List[str]:
    """Room types a session may use (BR-HC-08); an empty list means any type."""
    if preferred_room_type and preferred_room_type != 'any':
        return [preferred_room_type]
    return SLOT_ROOM_AFFINITY.get(slot_type, [])


def count_cohort_students(students) -> Dict[Tuple, int]:
    """Student counts keyed by (batch, programme, branch, section).

    Branch is the student's department name, which is what Curriculum.branch
    and the my-schedule API compare against.  ``students`` should be fetched
    with ``select_related('id__department')``.
    """
    counts: Dict[Tuple, int] = defaultdict(int)
    for stu in students:
        department = stu.id.department
        key = (stu.batch, stu.programme,
               department.name if department else '', stu.section or '')
        counts[key] += 1
    return dict(counts)


def effective_cohort_size(
    cohort_sizes: Dict[Tuple, int], batch: int, programme: str,
    branch: str, section: str, buffer: float = CAPACITY_BUFFER,
) -> int:
    """Seats needed for a cohort, including the capacity buffer.

    ``cohort_sizes`` holds student counts keyed by
    (batch, programme, branch, section).  An empty section spans every
    section; see ``student_in_cohort`` for programme and branch matching.
    """
    total = sum(
        count for (b, p, br, sec), count in cohort_sizes.items()
        if b == batch and student_in_cohort(p, br, programme, branch)
        and (not section or sec == section)
    )
    return math.ceil((total or DEFAULT_COHORT_SIZE) * buffer)


def student_in_cohort(student_programme: str, student_branch: str,
                      programme: str, branch: str) -> bool:
    """Whether a student (programme, department) attends courses filed under
    the curriculum (programme, branch).

    A 'Common' branch spans every branch of the programme.  Branches compare
    case-insensitively (department 'Design' vs branch 'DESIGN').  Programmes
    in STUDENT_PROGRAMME_ALIASES also match the one (programme, branch) their
    courses are filed under, but not that programme's 'Common' courses.
    """
    if student_programme == programme:
        return branch == WHOLE_BATCH_BRANCH or student_branch.casefold() == branch.casefold()
    alias = STUDENT_PROGRAMME_ALIASES.get(student_programme)
    return (alias is not None and alias[0] == programme
            and alias[1].casefold() == branch.casefold())


def student_programmes_for(programme: str) -> List[str]:
    """Student programmes that can attend courses filed under ``programme``."""
    return [programme] + [p for p, (filed_as, _) in STUDENT_PROGRAMME_ALIASES.items()
                          if filed_as == programme]


def faculty_keys(sess: SessionRecord, ci_to_faculty_pk: Dict[int, object]) -> set:
    """Identities of the real people teaching a session.

    Curriculum_Instructor is unique per (curriculum, instructor), so one
    professor teaching two courses has two different ids.  Clash checks must
    use the person, not the row.  An id with no known person falls back to
    itself so it still clashes with itself.
    """
    if sess.faculty_ids:
        return set(sess.faculty_ids)
    keys = set()
    for ci_id in [sess.curriculum_instructor_id, *sess.co_instructor_ids]:
        if ci_id is not None:
            keys.add(ci_to_faculty_pk.get(ci_id, ('ci', ci_id)))
    return keys


def build_cohort_index(sessions: List[SessionRecord]):
    """Concrete branches / sections present, used to expand wildcard cohorts.

    Sections are collected per (batch, programme), not per branch: a section
    seen only on a 'Common' course still splits every branch's students, so a
    whole-branch class must cover it too.
    """
    branches: Dict[Tuple, set] = defaultdict(set)
    sections: Dict[Tuple, set] = defaultdict(set)
    for s in sessions:
        if s.branch != WHOLE_BATCH_BRANCH:
            branches[(s.batch, s.programme)].add(s.branch)
        if s.section:
            sections[(s.batch, s.programme)].add(s.section)
    return branches, sections


def cohort_atoms(sess: SessionRecord, index) -> set:
    """The (batch, programme, branch, section) groups of students in a session.

    A 'Common' session involves every branch of its batch and an unsectioned
    session involves every section, so such sessions clash with the narrower
    cohorts they contain.  A narrow cohort only occupies its own atom.
    """
    branches, sections = index
    if sess.branch == WHOLE_BATCH_BRANCH:
        branch_options = branches.get((sess.batch, sess.programme), set()) | {sess.branch}
    else:
        branch_options = {sess.branch}
    atoms = set()
    for branch in branch_options:
        if sess.section:
            section_options = {sess.section}
        else:
            section_options = sections.get((sess.batch, sess.programme), set()) | {''}
        for section in section_options:
            atoms.add((sess.batch, sess.programme, branch, section))
    return atoms


def lock_key(subject, slot_type, batch, programme, branch, section) -> str:
    subject = str(subject)
    if not subject.startswith(('curriculum:', 'course:')):
        subject = f'curriculum:{subject}'
    return f'{subject}-{slot_type}-{batch}-{programme}-{branch}-{section}'


def pick_lock_source(versions) -> Optional[int]:
    """Version whose locks a new run inherits.

    ``versions`` are (version_id, version_number, slot_count) for the earlier
    versions of the same term.  The newest one that has any slots wins, even
    if none of its slots are locked: picking "the newest version with locks"
    instead would revive locks an admin removed in a later version.
    """
    with_slots = [v for v in versions if v[2] > 0]
    if not with_slots:
        return None
    return max(with_slots, key=lambda v: v[1])[0]


def build_locked_map(locked_slots) -> Dict[str, List[dict]]:
    """Group locked TimetableSlot rows into per-session assignments.

    A course has several sessions of one type, so each key maps to a list of
    assignments that are handed out one per session.  A multi-hour block is
    stored as one row per hour; it becomes one assignment anchored at its
    first hour.
    """
    locked_map: Dict[str, List[dict]] = defaultdict(list)
    seen_blocks = set()
    for slot in sorted(locked_slots, key=lambda s: (s.day_of_week, s.start_hour)):
        if slot.lab_block_id is not None:
            if slot.lab_block_id in seen_blocks:
                continue
            seen_blocks.add(slot.lab_block_id)
        course_id = getattr(slot, 'course_id', None)
        subject = f'course:{course_id}' if course_id else f'curriculum:{slot.curriculum_id}'
        key = lock_key(subject, slot.slot_type, slot.batch,
                       slot.programme, slot.branch, slot.section)
        locked_map[key].append({
            'day': slot.day_of_week,
            'hour': slot.start_hour,
            'room': slot.classroom_id,
        })
    return dict(locked_map)


def basket_mismatches(groups: List[List[int]], sessions: List[SessionRecord]) -> List[dict]:
    """Baskets whose courses can never be synchronised.

    Basket courses must occupy the same (day, hour)s, which is only possible
    when every course has the same number of weekly sessions.  Reporting this
    up front gives a precise reason instead of a generic INFEASIBLE.
    """
    counts: Dict[int, int] = defaultdict(int)
    codes: Dict[int, str] = {}
    for s in sessions:
        counts[s.curriculum_id] += 1
        codes[s.curriculum_id] = s.course_code
    problems = []
    for members in groups:
        if len({counts[c] for c in members}) > 1:
            detail = ', '.join(f'{codes[c]}={counts[c]}' for c in members)
            problems.append({
                'severity': 'CRITICAL',
                'error_code': 'BASKET_MISMATCH',
                'description': (
                    f'Elective basket courses must have the same number of weekly '
                    f'sessions to run in parallel ({detail}).'
                ),
                'curriculum_id_ref': members[0],
            })
    return problems


def sanitize_locked_sessions(
    sessions: List[SessionRecord],
    rooms: Dict[str, object],
    ci_to_faculty_pk: Dict[int, object],
    basket_of: Optional[Dict[int, int]] = None,
) -> Tuple[List[dict], List[dict]]:
    """Validate admin-locked assignments before they reach the model.

    * A lock that cannot be honoured on its own (unknown day, a start hour the
      block cannot use, unknown/ineligible room) is dropped, so the session is
      scheduled freely, and reported as a WARNING.
    * Two surviving locks that overlap on a room, a person or a cohort can never
      both hold; they are reported as CRITICAL conflicts.  Members of the same
      elective basket may legitimately share a cohort.

    Mutates ``sessions`` (drops invalid locks); returns (warnings, conflicts).
    """
    basket_of = basket_of or {}
    warnings: List[dict] = []
    conflicts: List[dict] = []

    for s in sessions:
        if s.locked_day is None:
            continue
        if s.locked_day not in DAYS:
            reason = f'day {s.locked_day} is not a teaching day'
        elif s.locked_hour not in valid_block_starts(s.block_size):
            reason = f'hour {s.locked_hour} cannot start a {s.block_size}-hour block'
        elif s.locked_room not in rooms:
            reason = f'room {s.locked_room} does not exist or is inactive'
        elif s.locked_room not in s.eligible_rooms:
            reason = f'room {s.locked_room} is too small or the wrong type'
        else:
            continue
        warnings.append({
            'severity': 'WARNING',
            'error_code': 'LOCK_IGNORED',
            'description': f'Locked slot of {s.course_code} ({s.slot_type}) ignored: {reason}.',
            'curriculum_id_ref': s.curriculum_id,
        })
        s.locked_day = s.locked_hour = s.locked_room = None

    index = build_cohort_index(sessions)
    owners: Dict[Tuple, SessionRecord] = {}
    reported = set()
    for s in sessions:
        if s.locked_day is None:
            continue
        student_resources = (
            [('student', student_id) for student_id in s.student_ids]
            if s.student_ids
            else [('cohort', atom) for atom in cohort_atoms(s, index)]
        )
        resources = (
            [('room', s.locked_room)]
            + [('faculty', k) for k in faculty_keys(s, ci_to_faculty_pk)]
            + student_resources
        )
        for offset in range(s.block_size):
            hour = s.locked_hour + offset
            for resource in resources:
                other = owners.setdefault((resource, s.locked_day, hour), s)
                if other is s:
                    continue
                # Different courses of one basket may share students' hours;
                # two sessions of the same course never may.
                parallel_electives = (
                    resource[0] == 'cohort'
                    and s.curriculum_id != other.curriculum_id
                    and basket_of.get(s.curriculum_id) is not None
                    and basket_of.get(s.curriculum_id) == basket_of.get(other.curriculum_id)
                )
                if parallel_electives:
                    continue
                pair = (other.session_id, s.session_id)
                if pair in reported:
                    continue
                reported.add(pair)
                conflicts.append({
                    'severity': 'CRITICAL',
                    'error_code': 'LOCK_CONFLICT',
                    'description': (
                        f'Locked slots of {other.course_code} and {s.course_code} '
                        f'both need {resource[0]} {resource[1]} on day {s.locked_day} '
                        f'at {hour}:00.'
                    ),
                    'curriculum_id_ref': s.curriculum_id,
                })
    return warnings, conflicts


# ── Main solver class ─────────────────────────────────────────────────────────

class WholeCollegeTimetableSolver:
    """
    CP-SAT-based whole-college timetable solver.

    Lifecycle
    ---------
    1. ``__init__``  – store parameters.
    2. ``solve()``   – orchestrates FC-01 (data ingestion + pruning),
                       FC-02 (model building + solving), and DB persistence.
    """

    def __init__(self, academic_year: int, semester_type: str,
                 capacity_buffer: float = CAPACITY_BUFFER, created_by=None,
                 semester_number: Optional[int] = None,
                 course_source: str = 'legacy'):
        self.academic_year = academic_year
        self.semester_type = semester_type
        self.semester_number = semester_number
        self.course_source = course_source
        self.capacity_buffer = capacity_buffer
        self.created_by = created_by  # auth.User recorded on the version

    # ------------------------------------------------------------------ #
    # Public entry point                                                   #
    # ------------------------------------------------------------------ #

    def solve(self, timeout_seconds: int = 60,
              num_workers: int = 8) -> SolverResult:
        """Run full pipeline and return a SolverResult."""
        if not _ORTOOLS_AVAILABLE:
            return SolverResult(
                status='ERROR',
                message='google-ortools package is not installed. '
                        'Run: pip install ortools',
            )

        t0 = time.perf_counter()

        # ── Step 1: Create version record ─────────────────────────────── #
        version = self._create_version_record()

        try:
            result = self._run_pipeline(version, timeout_seconds, num_workers)
        except Exception:
            # Do not leave a half-built Draft behind that could be published.
            self._abandon_version(version, 'Solver crashed; see server log.')
            raise
        result.solve_time_sec = time.perf_counter() - t0

        # ── Step 4: persist metrics to version record ──────────────────── #
        version.solve_time_seconds = result.solve_time_sec
        version.slots_created = result.slots_created
        version.save(update_fields=['solve_time_seconds', 'slots_created', 'status'])

        return result

    def _run_pipeline(self, version, timeout_seconds: int,
                      num_workers: int) -> SolverResult:
        # ── Step 2: FC-01 data ingestion & domain pruning ─────────────── #
        try:
            rooms, sessions, baskets, faculty_prefs, cohort_sizes, ci_to_faculty_pk = (
                self._ingest_and_prune(version)
            )
        except CapacityBottleneck as exc:
            self._mark_infeasible(version, str(exc))
            return SolverResult(
                status='INFEASIBLE',
                version_id=version.id,
                message=str(exc),
                conflicts=exc.conflicts,
            )

        if not sessions:
            scope = (
                f'semester {self.semester_number}'
                if self.semester_number is not None else 'this term'
            )
            message = f'No floated curricula found for {scope}.'
            self._mark_infeasible(version, message)
            return SolverResult(
                status='INFEASIBLE',
                version_id=version.id,
                message=message,
            )

        # ── Step 3: FC-02 build & solve CP-SAT model ──────────────────── #
        return self._build_and_solve(
            version, rooms, sessions, baskets, faculty_prefs,
            cohort_sizes, ci_to_faculty_pk, timeout_seconds, num_workers,
        )

    # ------------------------------------------------------------------ #
    # FC-01: Data ingestion & domain pruning                              #
    # ------------------------------------------------------------------ #

    def _ingest_and_prune(self, version):
        """
        Query the database, build SessionRecord objects, and prune domains.
        Returns (rooms_dict, sessions, baskets, faculty_prefs, cohort_sizes).
        """
        if self.course_source == 'registered':
            return self._ingest_registered_courses(version)

        from django.db.models import Count
        from applications.academic_procedures.models import (
            Classroom, CourseWeeklyRequirement, TimetableSlot, TimetableVersion,
            ElectiveBasket, FacultyPreference, TimetableConflictLog,
        )
        from applications.academic_information.models import (
            Curriculum, Curriculum_Instructor, Student,
        )

        # ── Rooms ──────────────────────────────────────────────────────── #
        rooms: Dict[str, object] = {
            r.room_id: r
            for r in Classroom.objects.filter(is_active=True)
        }

        # ── Cohort sizes: (batch, programme, branch, section) → count ─── #
        cohort_sizes = count_cohort_students(
            Student.objects.select_related('id__department')
        )

        # ── Floated curricula ─────────────────────────────────────────── #
        floated = Curriculum.objects.filter(floated=True).select_related('course_id')
        if self.semester_number is not None:
            floated = floated.filter(sem=self.semester_number)

        # ── Instructor mappings ───────────────────────────────────────── #
        # Chief instructor first: it becomes the instructor stored on the slot.
        instructors_by_curriculum: Dict[int, List[int]] = defaultdict(list)
        for ci in Curriculum_Instructor.objects.order_by('-chief_inst', 'pk'):
            instructors_by_curriculum[ci.curriculum_id_id].append(ci.pk)

        # ── Weekly requirements (default fallback if not configured) ───── #
        req_map: Dict[int, object] = {}
        for req in CourseWeeklyRequirement.objects.all():
            req_map[req.curriculum_id] = req

        # ── Locked slots from an existing version (incremental resched) ── #
        previous_version_id = pick_lock_source(
            TimetableVersion.objects.filter(
                academic_year=self.academic_year,
                semester_type=self.semester_type,
                semester_number=self.semester_number,
                course_source='legacy',
            ).exclude(pk=version.pk)
            .annotate(slot_count=Count('slots'))
            .values_list('id', 'version_number', 'slot_count')
        )
        locked_map = build_locked_map(
            TimetableSlot.objects.filter(version_id=previous_version_id, is_locked=True)
            if previous_version_id is not None else []
        )

        # ── Build SessionRecord list ───────────────────────────────────── #
        sessions: List[SessionRecord] = []
        prune_conflicts: List[dict] = []
        session_counter: Dict[str, int] = defaultdict(int)

        for curr in floated:
            req = req_map.get(curr.curriculum_id)
            lec = req.lectures_per_week  if req else 3
            tut = req.tutorials_per_week if req else 1
            pra = req.practicals_per_week if req else 0
            blk = req.practical_block_size if req else 2
            pref_room = req.preferred_room_type if req else 'any'

            # Infer cohort key from curriculum metadata
            batch = curr.batch
            programme = curr.programme
            branch = curr.branch if curr.branch else WHOLE_BATCH_BRANCH
            # For single-section or unsectioned curricula: section=''
            section = ''

            eff_size = effective_cohort_size(
                cohort_sizes, batch, programme, branch, section,
                self.capacity_buffer,
            )

            inst_ids = instructors_by_curriculum.get(curr.curriculum_id, [])
            ci_id = inst_ids[0] if inst_ids else None  # primary instructor
            co_ids = inst_ids[1:]

            def _make_sessions(count, stype, bsize=1):
                for _ in range(count):
                    session_counter[curr.curriculum_id] += 1
                    sid = (
                        f"cur{curr.curriculum_id}-{stype[:1]}"
                        f"{session_counter[curr.curriculum_id]}"
                        f"-b{batch}-{programme}-{branch}-{section}"
                    )
                    # Eligible rooms (domain pruning BR-HC-07 + BR-HC-08)
                    allowed_types = eligible_room_types(stype, pref_room)
                    eligible = [
                        r_id for r_id, rm in rooms.items()
                        if rm.capacity >= eff_size
                        and (rm.room_type in allowed_types or not allowed_types)
                    ]
                    if not eligible:
                        prune_conflicts.append({
                            'severity': 'CRITICAL',
                            'error_code': 'NO_ELIGIBLE_ROOM',
                            'description': (
                                f"No active room with capacity≥{eff_size} "
                                f"and type in {allowed_types} for "
                                f"{curr.course_code} ({stype})."
                            ),
                            'curriculum_id_ref': curr.curriculum_id,
                        })
                        return  # skip this session

                    # Locked?
                    pending_locks = locked_map.get(lock_key(
                        curr.curriculum_id, stype, batch, programme, branch, section,
                    ))
                    lock = pending_locks.pop(0) if pending_locks else None

                    sessions.append(SessionRecord(
                        session_id=sid,
                        curriculum_id=curr.curriculum_id,
                        curriculum_instructor_id=ci_id,
                        course_code=curr.course_code,
                        course_name=curr.course_id.course_name,
                        slot_type=stype,
                        block_size=bsize,
                        batch=batch,
                        programme=programme,
                        branch=branch,
                        section=section,
                        effective_size=eff_size,
                        eligible_rooms=eligible,
                        locked_day=lock['day'] if lock else None,
                        locked_hour=lock['hour'] if lock else None,
                        locked_room=lock['room'] if lock else None,
                        co_instructor_ids=list(co_ids),
                    ))

            _make_sessions(lec, LECTURE)
            _make_sessions(tut, TUTORIAL)
            for _ in range(pra):
                _make_sessions(1, PRACTICAL, bsize=blk)

        # Write prune conflicts
        if prune_conflicts:
            self._log_conflicts(version, prune_conflicts)
            critical = [c for c in prune_conflicts if c['severity'] == 'CRITICAL']
            if critical:
                raise CapacityBottleneck(
                    f"{len(critical)} critical capacity bottlenecks found. "
                    f"First: {critical[0]['description']}",
                    conflicts=prune_conflicts,
                )

        # ── Elective baskets ──────────────────────────────────────────── #
        basket_filters = {
            'academic_year': self.academic_year,
            'semester_type': self.semester_type,
        }
        if self.semester_number is not None:
            basket_filters['semester'] = self.semester_number
        baskets = list(
            ElectiveBasket.objects.filter(**basket_filters)
            .prefetch_related('electivebasketcurriculum_set')
        )

        # ── Faculty preferences ───────────────────────────────────────── #
        faculty_prefs = list(
            FacultyPreference.objects.filter(
                academic_year=self.academic_year,
                semester_type=self.semester_type,
            )
        )

        # ── Curriculum_Instructor → Faculty pk map (for BR-SC-06) ───────── #
        # Faculty.id is a OneToOneField onto ExtraInfo, so Faculty pk ==
        # Curriculum_Instructor.instructor_id_id.
        ci_to_faculty_pk: Dict[int, int] = {
            ci.pk: ci.instructor_id_id
            for ci in Curriculum_Instructor.objects.all()
        }

        # ── Admin locks: drop unusable ones, reject mutually exclusive ones ─ #
        groups = self._basket_groups(baskets, sessions)
        basket_of = {cur: i for i, members in enumerate(groups) for cur in members}
        lock_notes, lock_conflicts = sanitize_locked_sessions(
            sessions, rooms, ci_to_faculty_pk, basket_of,
        )
        if lock_notes or lock_conflicts:
            self._log_conflicts(version, lock_notes + lock_conflicts)
        if lock_conflicts:
            raise LockedSlotConflict(
                f"{len(lock_conflicts)} locked slots clash with each other. "
                f"First: {lock_conflicts[0]['description']}",
                conflicts=lock_notes + lock_conflicts,
            )

        return rooms, sessions, baskets, faculty_prefs, cohort_sizes, ci_to_faculty_pk

    def _ingest_registered_courses(self, version):
        """Build sessions from modern, term-specific student registrations.

        A registered course is the source of truth for whether it is active.
        Large enrolments are split into synthetic sections that fit the largest
        real classroom. Practical blocks use a virtual ``LAB`` resource until
        the institute's lab-room inventory is available.
        """
        from django.db.models import Count, Q
        from applications.academic_procedures.models import (
            Classroom, FacultyPreference, TimetableSlot, TimetableVersion,
            TimetableConflictLog, course_registration,
        )
        from applications.programme_curriculum.models import CourseInstructor

        rooms: Dict[str, object] = {
            room.room_id: room
            for room in Classroom.objects.filter(is_active=True)
        }
        physical_rooms = dict(rooms)
        max_capacity = max(
            (room.capacity for room in physical_rooms.values()), default=0,
        )
        max_group_size = math.floor(max_capacity / self.capacity_buffer)

        registration_term = (
            'Summer Semester'
            if self.semester_type == 'Summer Term'
            else self.semester_type
        )
        if registration_term == 'Even Semester':
            session = f'{self.academic_year - 1}-{str(self.academic_year)[-2:]}'
        else:
            session = f'{self.academic_year}-{str(self.academic_year + 1)[-2:]}'

        registration_filter = Q(working_year=self.academic_year) | Q(
            working_year__isnull=True,
            session=session,
        )
        registrations = list(
            course_registration.objects.filter(
                registration_filter,
                semester_type=registration_term,
                semester_id__semester_no=self.semester_number,
            ).select_related(
                'course_id',
                'student_id__id__department',
                'semester_id',
            ).order_by('course_id_id', 'student_id_id', 'pk')
        )

        # A student can have duplicate rows for different registration types;
        # one person still occupies only one seat in that course.
        students_by_course: Dict[int, Dict[str, object]] = defaultdict(dict)
        courses = {}
        for registration in registrations:
            students_by_course[registration.course_id_id][registration.student_id_id] = (
                registration.student_id
            )
            courses[registration.course_id_id] = registration.course_id

        offerings_by_course: Dict[int, List[object]] = defaultdict(list)
        for offering in CourseInstructor.objects.filter(
                course_id_id__in=courses,
                year=self.academic_year,
                semester_type=registration_term,
        ).select_related('instructor_id'):
            offerings_by_course[offering.course_id_id].append(offering)

        previous_version_id = pick_lock_source(
            TimetableVersion.objects.filter(
                academic_year=self.academic_year,
                semester_type=self.semester_type,
                semester_number=self.semester_number,
                course_source='registered',
            ).exclude(pk=version.pk)
            .annotate(slot_count=Count('slots'))
            .values_list('id', 'version_number', 'slot_count')
        )
        locked_map = build_locked_map(
            TimetableSlot.objects.filter(version_id=previous_version_id, is_locked=True)
            if previous_version_id is not None else []
        )

        sessions: List[SessionRecord] = []
        conflicts: List[dict] = []
        session_counter: Dict[Tuple, int] = defaultdict(int)

        def normalise_hours(value):
            value = int(value or 0)
            # Some imported L-T-P values use 20/30 for 2/3 hours.
            if value >= 10 and value % 10 == 0:
                value //= 10
            return value

        def most_common(values, fallback):
            values = [value for value in values if value not in (None, '')]
            return Counter(values).most_common(1)[0][0] if values else fallback

        def split_students(course, students, needs_physical_room):
            students = sorted(students, key=lambda student: student.pk)
            if not needs_physical_room or not max_group_size or len(students) <= max_group_size:
                sections = {student.section or '' for student in students}
                label = sections.pop() if len(sections) == 1 else ''
                return [(label, students)]

            natural: Dict[str, List[object]] = defaultdict(list)
            for student in students:
                natural[student.section or ''].append(student)
            if len(natural) > 1 and all(
                    len(group) <= max_group_size for group in natural.values()):
                return sorted(natural.items())

            groups = []
            for index in range(0, len(students), max_group_size):
                label = chr(ord('A') + len(groups))
                groups.append((label, students[index:index + max_group_size]))
            return groups

        for course_id, student_map in sorted(students_by_course.items()):
            course = courses[course_id]
            lecture_hours = normalise_hours(course.lecture_hours)
            tutorial_hours = normalise_hours(course.tutorial_hours)
            practical_hours = normalise_hours(course.pratical_hours)
            if lecture_hours + tutorial_hours + practical_hours == 0:
                conflicts.append({
                    'severity': 'WARNING',
                    'error_code': 'NO_CONTACT_HOURS',
                    'description': (
                        f'{course.code} has registrations but no L-T-P contact hours; '
                        'it was not placed on the timetable.'
                    ),
                })
                continue

            student_groups = split_students(
                course,
                list(student_map.values()),
                needs_physical_room=bool(lecture_hours or tutorial_hours),
            )
            offerings = offerings_by_course.get(course_id, [])

            for section, students in student_groups:
                offering = next(
                    (item for item in offerings if item.section_label == section),
                    None,
                ) or next(
                    (item for item in offerings if not item.section_label),
                    None,
                ) or (offerings[0] if offerings else None)

                student_ids = [student.pk for student in students]
                batch = most_common((student.batch for student in students), 0)
                programme = str(most_common(
                    (student.programme for student in students), 'Unknown',
                ))[:15]
                branches = {
                    student.id.department.name
                    for student in students
                    if student.id.department is not None
                }
                branch = next(iter(branches)) if len(branches) == 1 else WHOLE_BATCH_BRANCH
                branch = str(branch)[:15]
                effective_size = math.ceil(len(student_ids) * self.capacity_buffer)
                faculty_ids = [offering.instructor_id_id] if offering else []
                subject = f'course:{course_id}'

                def make_sessions(count, slot_type, block_size=1, eligible=None,
                                  room_label=''):
                    for _ in range(count):
                        counter_key = (course_id, section, slot_type)
                        session_counter[counter_key] += 1
                        pending_locks = locked_map.get(lock_key(
                            subject, slot_type, batch, programme, branch, section,
                        ))
                        lock = pending_locks.pop(0) if pending_locks else None
                        sessions.append(SessionRecord(
                            session_id=(
                                f'course{course_id}-{slot_type[:1]}'
                                f'{session_counter[counter_key]}-s{section or "all"}'
                            ),
                            curriculum_id=None,
                            curriculum_instructor_id=None,
                            course_id=course_id,
                            course_instructor_id=offering.pk if offering else None,
                            faculty_ids=faculty_ids,
                            student_ids=student_ids,
                            course_code=course.code,
                            course_name=course.name,
                            slot_type=slot_type,
                            block_size=block_size,
                            batch=batch,
                            programme=programme,
                            branch=branch,
                            section=section,
                            effective_size=effective_size,
                            eligible_rooms=list(eligible or []),
                            room_label=room_label,
                            locked_day=lock['day'] if lock else None,
                            locked_hour=lock['hour'] if lock else None,
                            locked_room=lock['room'] if lock else None,
                        ))

                for slot_type, count in (
                        (LECTURE, lecture_hours), (TUTORIAL, tutorial_hours)):
                    if not count:
                        continue
                    allowed_types = eligible_room_types(slot_type, 'any')
                    eligible = [
                        room_id for room_id, room in physical_rooms.items()
                        if room.capacity >= effective_size
                        and room.room_type in allowed_types
                    ]
                    if not eligible:
                        conflicts.append({
                            'severity': 'CRITICAL',
                            'error_code': 'NO_ELIGIBLE_ROOM',
                            'description': (
                                f'No active room with capacity≥{effective_size} for '
                                f'{course.code} section {section or "all"} ({slot_type}).'
                            ),
                        })
                    else:
                        make_sessions(count, slot_type, eligible=eligible)

                if practical_hours:
                    block_size = 3 if practical_hours % 3 == 0 else min(2, practical_hours)
                    practical_count = math.ceil(practical_hours / block_size)
                    virtual_lab = f'__LAB__{course_id}_{section or "all"}'
                    rooms[virtual_lab] = SimpleNamespace(
                        room_id=virtual_lab,
                        capacity=effective_size,
                        room_type='Computer Lab',
                        is_active=True,
                        is_virtual=True,
                    )
                    make_sessions(
                        practical_count,
                        PRACTICAL,
                        block_size=block_size,
                        eligible=[virtual_lab],
                        room_label='LAB',
                    )

        if conflicts:
            self._log_conflicts(version, conflicts)
            critical = [item for item in conflicts if item['severity'] == 'CRITICAL']
            if critical:
                raise CapacityBottleneck(
                    f'{len(critical)} active course groups have no eligible room. '
                    f'First: {critical[0]["description"]}',
                    conflicts=conflicts,
                )

        faculty_prefs = list(FacultyPreference.objects.filter(
            academic_year=self.academic_year,
            semester_type=self.semester_type,
        ))
        lock_notes, lock_conflicts = sanitize_locked_sessions(
            sessions, rooms, {}, {},
        )
        if lock_notes or lock_conflicts:
            self._log_conflicts(version, lock_notes + lock_conflicts)
        if lock_conflicts:
            raise LockedSlotConflict(
                f'{len(lock_conflicts)} locked slots clash with each other.',
                conflicts=lock_notes + lock_conflicts,
            )

        return rooms, sessions, [], faculty_prefs, {}, {}

    # ------------------------------------------------------------------ #
    # FC-02 / FC-03: Build & solve CP-SAT model                           #
    # ------------------------------------------------------------------ #

    def _build_and_solve(
        self, version, rooms, sessions, baskets, faculty_prefs,
        cohort_sizes, ci_to_faculty_pk, timeout_seconds, num_workers,
    ) -> SolverResult:

        model = cp_model.CpModel()
        penalty_terms: List[Tuple[object, int]] = []  # (BoolVar, weight)

        # ── Decision variables ──────────────────────────────────────────── #
        # x[sid][day][hour][room_id] = BoolVar "session sid at (d,h,r)"
        # For lab blocks: sid anchors the START hour; block occupies h, h+1 [, h+2]

        x: Dict[str, Dict] = {}   # sid → {(day, hour, room_id): BoolVar}
        all_vars: Dict[str, List] = {}  # sid → list of all BoolVars

        for sess in sessions:
            x[sess.session_id] = {}
            all_vars[sess.session_id] = []

            if sess.locked_day is not None:
                # Locked: one single forced variable
                key = (sess.locked_day, sess.locked_hour, sess.locked_room)
                v = model.NewBoolVar(f'x_{sess.session_id}_{key}')
                x[sess.session_id][key] = v
                all_vars[sess.session_id].append(v)
            else:
                for day in DAYS:
                    for hour in valid_block_starts(sess.block_size):
                        for room_id in sess.eligible_rooms:
                            key = (day, hour, room_id)
                            v = model.NewBoolVar(
                                f'x_{sess.session_id}_d{day}h{hour}r{room_id}'
                            )
                            x[sess.session_id][key] = v
                            all_vars[sess.session_id].append(v)

        # ── BR-HC-03: Exactly one slot per session ─────────────────────── #
        # A session with no possible slot must fail the run, not vanish from it.
        unschedulable = [s for s in sessions if not all_vars[s.session_id]]
        conflicts = [{
            'severity': 'CRITICAL',
            'error_code': 'NO_VALID_SLOT',
            'description': (
                f'{s.course_code} ({s.slot_type}, {s.block_size}h block) has no '
                f'valid (day, hour, room) combination.'
            ),
            'curriculum_id_ref': s.curriculum_id,
        } for s in unschedulable]
        groups = self._basket_groups(baskets, sessions)
        conflicts += basket_mismatches(groups, sessions)
        if conflicts:
            message = (
                f'{len(conflicts)} problems make this timetable impossible. '
                f'First: {conflicts[0]["description"]}'
            )
            self._record_solver_failure(version, 'INFEASIBLE', message, conflicts)
            return SolverResult(status='INFEASIBLE', version_id=version.id,
                                message=message, conflicts=conflicts)

        for sess in sessions:
            model.AddExactlyOne(all_vars[sess.session_id])
            # A locked session has a single variable, so ExactlyOne forces it.

        # ── Build resource-conflict index maps ─────────────────────────── #
        # Every hour a (lab) block covers is registered, so overlaps between a
        # block and other sessions are caught at every hour, not only at starts.
        room_vars: Dict[Tuple, List] = defaultdict(list)     # (day, hour, room)
        faculty_vars: Dict[Tuple, List] = defaultdict(list)  # (person, day, hour)

        for sess in sessions:
            people = faculty_keys(sess, ci_to_faculty_pk)
            for (day, start_hour, room_id), var in x[sess.session_id].items():
                for offset in range(sess.block_size):
                    hour = start_hour + offset
                    room_vars[(day, hour, room_id)].append(var)
                    for person in people:
                        faculty_vars[(person, day, hour)].append(var)

        # ── BR-HC-04: Room exclusivity ─────────────────────────────────── #
        for var_list in room_vars.values():
            if len(var_list) > 1:
                model.AddAtMostOne(var_list)

        # ── BR-HC-05: Instructor clash-freedom (per real person) ──────── #
        for var_list in faculty_vars.values():
            if len(var_list) > 1:
                model.AddAtMostOne(var_list)

        # ── BR-HC-06 / BR-HC-10: Cohort clash-freedom & elective baskets ─ #
        basket_of = {cur: i for i, members in enumerate(groups) for cur in members}
        self._add_cohort_constraints(model, sessions, x, basket_of)
        self._add_elective_constraints(model, sessions, x, groups)

        # ── BR-HC-09: Lab continuity ───────────────────────────────────── #
        # Enforced by construction: only valid_block_starts() get variables.

        # ── BR-SC-01: Day spread – penalise same course on same day ────── #
        # Group session vars by (curriculum_id, batch, prog, branch, section, day)
        course_day_sessions: Dict[Tuple, List] = defaultdict(list)
        for sess in sessions:
            for (day, hour, room_id), var in x[sess.session_id].items():
                key = (sess.subject_key, sess.batch, sess.programme, sess.branch,
                       sess.section, day)
                course_day_sessions[key].append(var)

        for key, var_list in course_day_sessions.items():
            if len(var_list) > 1:
                surplus = model.NewIntVar(0, len(var_list), f'surplus_spread_{key}')
                total = model.NewIntVar(0, len(var_list), f'total_day_{key}')
                model.Add(total == sum(var_list))
                model.AddMaxEquality(surplus, [total - 1, model.NewConstant(0)])
                penalty_lit = model.NewBoolVar(f'pen_spread_{key}')
                model.Add(surplus > 0).OnlyEnforceIf(penalty_lit)
                model.Add(surplus == 0).OnlyEnforceIf(penalty_lit.Not())
                penalty_terms.append((penalty_lit, WEIGHT_DAY_SPREAD))

        # ── BR-SC-05: Seat wastage minimization ───────────────────────── #
        for sess in sessions:
            for (day, hour, room_id), var in x[sess.session_id].items():
                room = rooms.get(room_id)
                if room:
                    waste = room.capacity - sess.effective_size
                    if waste > 0:
                        penalty_terms.append((var, waste * WEIGHT_SEAT_WASTE))

        # ── BR-SC-06: Faculty preference adherence ────────────────────── #
        # faculty_vars is keyed by Faculty pk and covers every hour of a block,
        # so each preference only affects that person's teaching hours.
        # 'Unavailable' windows are penalised and 'Preferred' ones rewarded, as
        # documented on the FacultyPreference model.
        for pref in faculty_prefs:
            if pref.preference_type == 'Unavailable':
                weight = WEIGHT_FAC_PREF
            elif pref.preference_type == 'Preferred':
                weight = -WEIGHT_FAC_PREF
            else:
                continue
            for h in range(pref.start_hour, pref.end_hour):
                if h not in HOURS:
                    continue
                for var in faculty_vars.get((pref.faculty_id, pref.day_of_week, h), []):
                    penalty_terms.append((var, weight))

        # ── Objective: minimise total weighted penalties ───────────────── #
        if penalty_terms:
            model.Minimize(sum(item * weight for item, weight in penalty_terms))

        # ── Solve ──────────────────────────────────────────────────────── #
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout_seconds
        solver.parameters.num_search_workers = num_workers
        solver.parameters.log_search_progress = False

        status_code = solver.Solve(model)
        status_map = {
            cp_model.OPTIMAL: 'OPTIMAL',
            cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE',
            cp_model.MODEL_INVALID: 'ERROR',
            # UNKNOWN = time limit hit before any solution was found.  That is
            # not a proof that no timetable exists.
            cp_model.UNKNOWN: 'TIMEOUT',
        }
        status_str = status_map.get(status_code, 'ERROR')

        if status_str not in ('OPTIMAL', 'FEASIBLE'):
            if status_str == 'TIMEOUT':
                message = (
                    f'No timetable found within {timeout_seconds}s. This does not prove '
                    f'that none exists; retry with a larger timeout_seconds.'
                )
            else:
                message = f'Solver returned {status_str} after {solver.WallTime():.1f}s.'
            self._record_solver_failure(version, status_str, message)
            return SolverResult(status=status_str, version_id=version.id, message=message)

        # ── Extract solution & persist ─────────────────────────────────── #
        slot_records = self._extract_and_persist(solver, x, sessions, version)
        courses_scheduled = len({session.subject_key for session in sessions})

        version.status = 'Draft'
        quality = '' if status_str == 'OPTIMAL' else ' (time limit reached; not proven optimal)'
        return SolverResult(
            status=status_str,
            version_id=version.id,
            slots_created=slot_records,
            courses_scheduled=courses_scheduled,
            message=(
                f'Whole-college generation complete: {slot_records} slots allocated '
                f'for {courses_scheduled} active courses '
                f'in {solver.WallTime():.1f}s (objective={solver.ObjectiveValue():.0f})'
                f'{quality}.'
            ),
        )

    # ------------------------------------------------------------------ #
    # Cohort and elective basket constraints (BR-HC-06, FC-03)             #
    # ------------------------------------------------------------------ #

    def _add_cohort_constraints(self, model, sessions, x, basket_of):
        """BR-HC-06: a group of students attends at most one class per hour.

        Different courses of one elective basket run in parallel on purpose
        (students pick one), so they may share an hour; each basket counts as
        one occupant, and sessions of the same course still exclude each other.
        """
        index = build_cohort_index(sessions)
        singles: Dict[Tuple, List] = defaultdict(list)
        in_basket: Dict[Tuple, Dict] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        for sess in sessions:
            basket = basket_of.get(sess.curriculum_id)
            atoms = cohort_atoms(sess, index) if not sess.student_ids else []
            for (day, start_hour, _room), var in x[sess.session_id].items():
                for offset in range(sess.block_size):
                    if sess.student_ids:
                        for student_id in sess.student_ids:
                            key = (('student', student_id), day, start_hour + offset)
                            singles[key].append(var)
                        continue
                    for atom in atoms:
                        key = (atom, day, start_hour + offset)
                        if basket is None:
                            singles[key].append(var)
                        else:
                            in_basket[key][basket][sess.curriculum_id].append(var)

        for key in set(singles) | set(in_basket):
            occupants = list(singles.get(key, []))
            for basket, by_course in in_basket.get(key, {}).items():
                basket_vars = []
                for course_vars in by_course.values():
                    if len(course_vars) > 1:
                        model.AddAtMostOne(course_vars)
                    basket_vars.extend(course_vars)
                if len(by_course) == 1:
                    occupants.extend(basket_vars)
                    continue
                busy = model.NewBoolVar(f'basket{basket}_{key}')
                for var in basket_vars:
                    model.AddImplication(var, busy)
                occupants.append(busy)
            if len(occupants) > 1:
                model.AddAtMostOne(occupants)

    def _basket_groups(self, baskets, sessions) -> List[List[int]]:
        """Curriculum ids per elective basket, limited to scheduled courses.

        Courses that are not floated have no sessions; keeping them would let a
        non-floated first member silently disable the whole basket.
        """
        scheduled = {s.curriculum_id for s in sessions}
        groups = []
        for basket in baskets:
            members = [c for c in self._basket_member_ids(basket) if c in scheduled]
            if len(members) >= 2:
                groups.append(members)
        return groups

    def _basket_member_ids(self, basket) -> List[int]:
        from applications.academic_procedures.models import ElectiveBasketCurriculum
        return list(
            ElectiveBasketCurriculum.objects.filter(basket=basket)
            .order_by('pk').values_list('curriculum_id', flat=True)
        )

    def _add_elective_constraints(self, model, sessions, x, groups):
        """BR-HC-10: courses in a basket occupy exactly the same (day, hour)s."""
        sessions_of: Dict[int, List[str]] = defaultdict(list)
        for sess in sessions:
            sessions_of[sess.curriculum_id].append(sess.session_id)

        def vars_by_slot(curriculum_id):
            by_slot: Dict[Tuple, List] = defaultdict(list)
            for sid in sessions_of.get(curriculum_id, []):
                for (day, hour, _room), var in x[sid].items():
                    by_slot[(day, hour)].append(var)
            return by_slot

        for members in groups:
            reference = vars_by_slot(members[0])
            for other_cur in members[1:]:
                other = vars_by_slot(other_cur)
                # Include slots only one side can use: there both must be 0.
                for slot in set(reference) | set(other):
                    model.Add(sum(reference.get(slot, [])) == sum(other.get(slot, [])))

    # ------------------------------------------------------------------ #
    # Extract solution and bulk-create TimetableSlot rows                  #
    # ------------------------------------------------------------------ #

    def _extract_and_persist(self, solver, x, sessions, version) -> int:
        from django.db import transaction
        from applications.academic_procedures.models import TimetableSlot

        slot_objs = []

        for sess in sessions:
            assigned = None
            for (day, hour, room_id), var in x[sess.session_id].items():
                if solver.Value(var) == 1:
                    assigned = (day, hour, room_id)
                    break
            if assigned is None:  # impossible under AddExactlyOne
                raise RuntimeError(f'Session {sess.session_id} has no assignment.')

            day, start_hour, room_id = assigned
            block_id = uuid.uuid4() if sess.block_size > 1 else None

            for bh in range(sess.block_size):
                actual_hour = start_hour + bh
                # Skip lunch (safety; should never trigger)
                if actual_hour == 13:
                    continue
                slot_objs.append(TimetableSlot(
                    version=version,
                    curriculum_id=sess.curriculum_id,
                    curriculum_instructor_id=sess.curriculum_instructor_id,
                    course_id=sess.course_id,
                    course_instructor_id=sess.course_instructor_id,
                    classroom_id=None if room_id.startswith('__LAB__') else room_id,
                    room_label=sess.room_label,
                    batch=sess.batch,
                    programme=sess.programme,
                    branch=sess.branch,
                    section=sess.section,
                    enrollment_count=len(sess.student_ids),
                    student_ids=sess.student_ids,
                    day_of_week=day,
                    start_hour=actual_hour,
                    slot_type=sess.slot_type,
                    lab_block_id=block_id,
                    # Carry admin pins forward so the next run keeps them too.
                    is_locked=sess.locked_day is not None,
                ))

        with transaction.atomic():
            TimetableSlot.objects.bulk_create(slot_objs, batch_size=500)

        return len(slot_objs)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _create_version_record(self, attempts: int = 3):
        from django.db import IntegrityError, transaction
        from applications.academic_procedures.models import TimetableVersion

        # Two concurrent runs can pick the same next number; the
        # unique_together on (year, semester, number) rejects the loser, which
        # then retries with a fresh number.
        for attempt in range(attempts):
            last = (
                TimetableVersion.objects
                .filter(
                    academic_year=self.academic_year,
                    semester_type=self.semester_type,
                )
                .order_by('-version_number')
                .first()
            )
            next_v = (last.version_number + 1) if last else 1
            try:
                with transaction.atomic():
                    version = TimetableVersion.objects.create(
                        academic_year=self.academic_year,
                        semester_type=self.semester_type,
                        semester_number=self.semester_number,
                        course_source=self.course_source,
                        version_number=next_v,
                        status='Draft',
                        created_by=self.created_by,
                    )
                break
            except IntegrityError:
                if attempt == attempts - 1:
                    raise
        logger.info(
            'TimetableVersion %s created (year=%s, sem=%s, v=%s)',
            version.id, self.academic_year, self.semester_type, next_v,
        )
        return version

    def _mark_infeasible(self, version, message: str):
        from applications.academic_procedures.models import TimetableConflictLog
        version.status = 'Infeasible'
        version.save(update_fields=['status'])
        TimetableConflictLog.objects.create(
            version=version,
            severity='CRITICAL',
            error_code='INFEASIBLE',
            description=message,
        )

    def _log_conflicts(self, version, conflicts: List[dict]):
        from applications.academic_procedures.models import TimetableConflictLog
        TimetableConflictLog.objects.bulk_create([
            TimetableConflictLog(
                version=version,
                severity=c['severity'],
                error_code=c['error_code'],
                description=c['description'],
                curriculum_id_ref=c.get('curriculum_id_ref'),
            )
            for c in conflicts
        ])

    def _record_solver_failure(self, version, status_str: str, message: str,
                               conflicts: Optional[List[dict]] = None):
        """Persist an unsuccessful run.

        Only a proven INFEASIBLE marks the version 'Infeasible'.  A timeout or
        solver error proves nothing about the data, so the empty version is
        archived (never publishable) with the reason in ``remarks``; this
        reuses existing statuses and needs no migration.
        """
        if status_str == 'INFEASIBLE':
            version.status = 'Infeasible'
        else:
            version.status = 'Archived'
            version.remarks = message
        version.save(update_fields=['status', 'remarks'])
        self._log_conflicts(version, conflicts or [{
            'severity': 'CRITICAL',
            'error_code': f'SOLVER_{status_str}',
            'description': message,
        }])

    def _abandon_version(self, version, message: str):
        version.status = 'Archived'
        version.remarks = message
        version.save(update_fields=['status', 'remarks'])


class CapacityBottleneck(Exception):
    """Raised during domain-pruning when a session has no eligible room."""

    def __init__(self, message, conflicts=None):
        super().__init__(message)
        self.conflicts = conflicts or []


class LockedSlotConflict(CapacityBottleneck):
    """Raised during ingestion when admin-locked slots clash with each other."""


# ── Convenience function (called from Django shell / management cmd) ─────────

def run_whole_college_timetable_generation(
    academic_year: int,
    semester_type: str = 'Odd Semester',
    semester_number: Optional[int] = None,
    course_source: str = 'registered',
    timeout_seconds: int = 60,
) -> Tuple[bool, str]:
    """
    Convenience wrapper used in Section 8 (Step 4) of the deployment guide.

    Returns (success: bool, message: str).
    """
    solver = WholeCollegeTimetableSolver(
        academic_year,
        semester_type,
        semester_number=semester_number,
        course_source=course_source,
    )
    result = solver.solve(timeout_seconds=timeout_seconds)
    success = result.status in ('OPTIMAL', 'FEASIBLE')
    return success, result.message
