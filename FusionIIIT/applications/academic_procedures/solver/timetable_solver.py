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
from collections import defaultdict
from dataclasses import dataclass, field
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
    curriculum_id: int
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


@dataclass
class SolverResult:
    status: str              # 'OPTIMAL' | 'FEASIBLE' | 'INFEASIBLE' | 'ERROR'
    version_id: Optional[int] = None
    slots_created: int = 0
    solve_time_sec: float = 0.0
    conflicts: List[dict] = field(default_factory=list)
    message: str = ''


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
                 capacity_buffer: float = CAPACITY_BUFFER):
        self.academic_year = academic_year
        self.semester_type = semester_type
        self.capacity_buffer = capacity_buffer

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

        # ── Step 2: FC-01 data ingestion & domain pruning ─────────────── #
        try:
            rooms, sessions, baskets, faculty_prefs, cohort_sizes, ci_to_faculty_pk = (
                self._ingest_and_prune(version)
            )
        except CapacityBottleneck as exc:
            self._mark_infeasible(version, str(exc))
            elapsed = time.perf_counter() - t0
            return SolverResult(
                status='INFEASIBLE',
                version_id=version.id,
                solve_time_sec=elapsed,
                message=str(exc),
                conflicts=exc.conflicts,
            )

        if not sessions:
            self._mark_infeasible(version, 'No floated curricula found for this term.')
            return SolverResult(
                status='INFEASIBLE',
                version_id=version.id,
                message='No floated curricula found for this term.',
            )

        # ── Step 3: FC-02 build & solve CP-SAT model ──────────────────── #
        result = self._build_and_solve(
            version, rooms, sessions, baskets, faculty_prefs,
            cohort_sizes, ci_to_faculty_pk, timeout_seconds, num_workers,
        )
        result.solve_time_sec = time.perf_counter() - t0

        # ── Step 4: persist metrics to version record ──────────────────── #
        version.solve_time_seconds = result.solve_time_sec
        version.slots_created = result.slots_created
        version.save(update_fields=['solve_time_seconds', 'slots_created', 'status'])

        return result

    # ------------------------------------------------------------------ #
    # FC-01: Data ingestion & domain pruning                              #
    # ------------------------------------------------------------------ #

    def _ingest_and_prune(self, version):
        """
        Query the database, build SessionRecord objects, and prune domains.
        Returns (rooms_dict, sessions, baskets, faculty_prefs, cohort_sizes).
        """
        from applications.academic_procedures.models import (
            Classroom, CourseWeeklyRequirement, TimetableSlot,
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
        cohort_sizes: Dict[Tuple, int] = {}
        students_qs = Student.objects.select_related('id__department')
        for stu in students_qs:
            key = (stu.batch, stu.programme, '', stu.section or '')
            cohort_sizes[key] = cohort_sizes.get(key, 0) + 1

        # ── Floated curricula ─────────────────────────────────────────── #
        floated = Curriculum.objects.filter(floated=True).select_related('course_id')

        # ── Instructor mappings ───────────────────────────────────────── #
        instructors_by_curriculum: Dict[int, List[int]] = defaultdict(list)
        for ci in Curriculum_Instructor.objects.select_related('instructor_id').all():
            instructors_by_curriculum[ci.curriculum_id_id].append(ci.pk)

        # ── Weekly requirements (default fallback if not configured) ───── #
        req_map: Dict[int, object] = {}
        for req in CourseWeeklyRequirement.objects.all():
            req_map[req.curriculum_id] = req

        # ── Locked slots from an existing version (incremental resched) ── #
        locked_map: Dict[str, dict] = {}  # session_id → {day, hour, room}
        for slot in TimetableSlot.objects.filter(
            version__academic_year=self.academic_year,
            version__semester_type=self.semester_type,
            is_locked=True,
        ).select_related('curriculum'):
            key = (
                f"{slot.curriculum_id}-{slot.slot_type}"
                f"-{slot.batch}-{slot.programme}-{slot.branch}-{slot.section}"
            )
            locked_map[key] = {
                'day': slot.day_of_week,
                'hour': slot.start_hour,
                'room': slot.classroom_id,
            }

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
            branch = curr.branch if curr.branch else 'Common'
            # For single-section or unsectioned curricula: section=''
            section = ''
            cohort_key = (batch, programme, branch, section)

            raw_size = cohort_sizes.get(cohort_key, 30)
            eff_size = math.ceil(raw_size * self.capacity_buffer)

            inst_ids = instructors_by_curriculum.get(curr.curriculum_id)
            ci_id = inst_ids[0] if inst_ids else None  # primary instructor

            def _make_sessions(count, stype, bsize=1):
                for _ in range(count):
                    session_counter[curr.curriculum_id] += 1
                    sid = (
                        f"cur{curr.curriculum_id}-{stype[:1]}"
                        f"{session_counter[curr.curriculum_id]}"
                        f"-b{batch}-{programme}-{branch}-{section}"
                    )
                    # Eligible rooms (domain pruning BR-HC-07 + BR-HC-08)
                    allowed_types = (
                        [pref_room] if pref_room != 'any'
                        else SLOT_ROOM_AFFINITY.get(stype, [])
                    )
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
                    lock_key = (
                        f"{curr.curriculum_id}-{stype}"
                        f"-{batch}-{programme}-{branch}-{section}"
                    )
                    lock = locked_map.get(lock_key)

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
                    ))

            _make_sessions(lec, LECTURE)
            _make_sessions(tut, TUTORIAL)
            for _ in range(pra):
                _make_sessions(1, PRACTICAL, bsize=blk)

        # Write prune conflicts
        if prune_conflicts:
            from applications.academic_procedures.models import TimetableConflictLog
            TimetableConflictLog.objects.bulk_create([
                TimetableConflictLog(
                    version=version,
                    severity=c['severity'],
                    error_code=c['error_code'],
                    description=c['description'],
                    curriculum_id_ref=c.get('curriculum_id_ref'),
                )
                for c in prune_conflicts
            ])
            critical = [c for c in prune_conflicts if c['severity'] == 'CRITICAL']
            if critical:
                raise CapacityBottleneck(
                    f"{len(critical)} critical capacity bottlenecks found. "
                    f"First: {critical[0]['description']}",
                    conflicts=prune_conflicts,
                )

        # ── Elective baskets ──────────────────────────────────────────── #
        baskets = list(
            ElectiveBasket.objects.filter(
                academic_year=self.academic_year,
                semester_type=self.semester_type,
            ).prefetch_related('electivebasketcurriculum_set')
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

        return rooms, sessions, baskets, faculty_prefs, cohort_sizes, ci_to_faculty_pk

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
                valid_starts = HOURS if sess.block_size == 1 else (
                    LAB_STARTS_2H if sess.block_size == 2 else LAB_STARTS_3H
                )
                for day in DAYS:
                    for hour in valid_starts:
                        # Verify all block hours are valid (no lunch crossing)
                        block_hours = list(range(hour, hour + sess.block_size))
                        if not all(h in HOURS for h in block_hours):
                            continue
                        for room_id in sess.eligible_rooms:
                            key = (day, hour, room_id)
                            v = model.NewBoolVar(
                                f'x_{sess.session_id}_d{day}h{hour}r{room_id}'
                            )
                            x[sess.session_id][key] = v
                            all_vars[sess.session_id].append(v)

        # ── BR-HC-03: Exactly one slot per session ─────────────────────── #
        for sess in sessions:
            if not all_vars[sess.session_id]:
                logger.warning("Session %s has zero valid (day, hour, room) combinations.",
                               sess.session_id)
                continue
            model.AddExactlyOne(all_vars[sess.session_id])

            # Force locked variable = 1
            if sess.locked_day is not None:
                key = (sess.locked_day, sess.locked_hour, sess.locked_room)
                if key in x[sess.session_id]:
                    model.Add(x[sess.session_id][key] == 1)

        # ── Build resource-conflict index maps ─────────────────────────── #
        # room_vars[(day, hour, room_id)]  → list of BoolVars (one per block_hour)
        room_vars: Dict[Tuple, List] = defaultdict(list)
        # faculty_vars[(faculty_ci_id, day, hour)] → list of BoolVars
        faculty_vars: Dict[Tuple, List] = defaultdict(list)
        # cohort_vars[(cohort_key, day, hour)] → list of BoolVars
        cohort_vars: Dict[Tuple, List] = defaultdict(list)

        for sess in sessions:
            cohort_key = (sess.batch, sess.programme, sess.branch, sess.section)
            for (day, start_hour, room_id), var in x[sess.session_id].items():
                for bh in range(sess.block_size):
                    actual_hour = start_hour + bh
                    if actual_hour == 13:  # skip lunch (should not occur)
                        continue
                    room_vars[(day, actual_hour, room_id)].append(var)
                    if sess.curriculum_instructor_id:
                        faculty_vars[(sess.curriculum_instructor_id, day, actual_hour)].append(var)
                    cohort_vars[(cohort_key, day, actual_hour)].append(var)

        # ── BR-HC-04: Room exclusivity ─────────────────────────────────── #
        for var_list in room_vars.values():
            if len(var_list) > 1:
                model.AddAtMostOne(var_list)

        # ── BR-HC-05: Instructor clash-freedom ────────────────────────── #
        for var_list in faculty_vars.values():
            if len(var_list) > 1:
                model.AddAtMostOne(var_list)

        # ── BR-HC-06: Cohort clash-freedom ────────────────────────────── #
        for var_list in cohort_vars.values():
            if len(var_list) > 1:
                model.AddAtMostOne(var_list)

        # ── BR-HC-09: Lab continuity (implicit through block_size) ─────── #
        # Already enforced by block_hours validation during variable creation.

        # ── BR-HC-10: Elective basket synchronization ──────────────────── #
        self._add_elective_constraints(model, sessions, x, baskets)

        # ── BR-SC-01: Day spread – penalise same course on same day ────── #
        # Group session vars by (curriculum_id, batch, prog, branch, section, day)
        course_day_sessions: Dict[Tuple, List] = defaultdict(list)
        for sess in sessions:
            for (day, hour, room_id), var in x[sess.session_id].items():
                key = (sess.curriculum_id, sess.batch, sess.programme, sess.branch,
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
        # Group session vars by (faculty_pk, day, hour) so each preference
        # only penalises sessions actually taught by that faculty member.
        faculty_hour_vars: Dict[Tuple, List] = defaultdict(list)
        for sess in sessions:
            fac_pk = ci_to_faculty_pk.get(sess.curriculum_instructor_id)
            if fac_pk is None:
                continue
            for (day, hour, room_id), var in x[sess.session_id].items():
                faculty_hour_vars[(fac_pk, day, hour)].append(var)

        for pref in faculty_prefs:
            if pref.preference_type != 'Unavailable':
                continue
            for h in range(pref.start_hour, pref.end_hour):
                if h not in HOURS:
                    continue
                for var in faculty_hour_vars.get((pref.faculty_id, pref.day_of_week, h), []):
                    penalty_terms.append((var, WEIGHT_FAC_PREF))

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
            cp_model.UNKNOWN: 'INFEASIBLE',
        }
        status_str = status_map.get(status_code, 'ERROR')

        if status_str in ('INFEASIBLE', 'ERROR'):
            from applications.academic_procedures.models import TimetableConflictLog
            TimetableConflictLog.objects.create(
                version=version,
                severity='CRITICAL',
                error_code='SOLVER_INFEASIBLE' if status_str == 'INFEASIBLE' else 'SOLVER_ERROR',
                description=(
                    f'CP-SAT returned {status_str} after {solver.WallTime():.1f}s. '
                    f'Objective bound: {solver.BestObjectiveBound():.1f}'
                ),
            )
            version.status = 'Infeasible'
            version.save(update_fields=['status'])
            return SolverResult(
                status=status_str,
                version_id=version.id,
                message=f'Solver returned {status_str}.',
            )

        # ── Extract solution & persist ─────────────────────────────────── #
        slot_records = self._extract_and_persist(solver, x, sessions, version)

        version.status = 'Draft'
        return SolverResult(
            status=status_str,
            version_id=version.id,
            slots_created=slot_records,
            message=(
                f'Whole-college generation complete: {slot_records} slots allocated '
                f'in {solver.WallTime():.1f}s (objective={solver.ObjectiveValue():.0f}).'
            ),
        )

    # ------------------------------------------------------------------ #
    # Elective basket constraints (FC-03)                                  #
    # ------------------------------------------------------------------ #

    def _add_elective_constraints(self, model, sessions, x, baskets):
        """BR-HC-10: Force same (day, hour) for all curricula in a basket."""
        from applications.academic_procedures.models import ElectiveBasketCurriculum

        # Build curriculum_id → [session_ids] index
        cur_to_sessions: Dict[int, List[str]] = defaultdict(list)
        for sess in sessions:
            cur_to_sessions[sess.curriculum_id].append(sess.session_id)

        for basket in baskets:
            members = list(
                ElectiveBasketCurriculum.objects.filter(basket=basket)
                .values_list('curriculum_id', flat=True)
            )
            if len(members) < 2:
                continue

            # For each pair (ca, cb) enforce sum_r x[ca,d,h,r] == sum_r x[cb,d,h,r]
            ref_cur = members[0]
            for other_cur in members[1:]:
                ref_sids = cur_to_sessions.get(ref_cur, [])
                oth_sids = cur_to_sessions.get(other_cur, [])
                if not ref_sids or not oth_sids:
                    continue

                for day in DAYS:
                    for hour in HOURS:
                        ref_active = [
                            var
                            for sid in ref_sids
                            for (d, h, r), var in x[sid].items()
                            if d == day and h == hour
                        ]
                        oth_active = [
                            var
                            for sid in oth_sids
                            for (d, h, r), var in x[sid].items()
                            if d == day and h == hour
                        ]
                        if ref_active and oth_active:
                            model.Add(sum(ref_active) == sum(oth_active))

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
            if assigned is None:
                continue

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
                    classroom_id=room_id,
                    batch=sess.batch,
                    programme=sess.programme,
                    branch=sess.branch,
                    section=sess.section,
                    day_of_week=day,
                    start_hour=actual_hour,
                    slot_type=sess.slot_type,
                    lab_block_id=block_id,
                    is_locked=False,
                ))

        with transaction.atomic():
            TimetableSlot.objects.bulk_create(slot_objs, batch_size=500)

        return len(slot_objs)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _create_version_record(self):
        from applications.academic_procedures.models import TimetableVersion

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

        version = TimetableVersion.objects.create(
            academic_year=self.academic_year,
            semester_type=self.semester_type,
            version_number=next_v,
            status='Draft',
        )
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


class CapacityBottleneck(Exception):
    """Raised during domain-pruning when a session has no eligible room."""

    def __init__(self, message, conflicts=None):
        super().__init__(message)
        self.conflicts = conflicts or []


# ── Convenience function (called from Django shell / management cmd) ─────────

def run_whole_college_timetable_generation(
    academic_year: int,
    semester_type: str = 'Odd Semester',
    timeout_seconds: int = 60,
) -> Tuple[bool, str]:
    """
    Convenience wrapper used in Section 8 (Step 4) of the deployment guide.

    Returns (success: bool, message: str).
    """
    solver = WholeCollegeTimetableSolver(academic_year, semester_type)
    result = solver.solve(timeout_seconds=timeout_seconds)
    success = result.status in ('OPTIMAL', 'FEASIBLE')
    return success, result.message
