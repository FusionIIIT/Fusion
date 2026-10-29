"""Regression tests for the whole-college timetable solver.

These drive the real CP-SAT model built by ``_build_and_solve``.  Only the
database edges are replaced (persisting slots, logging failures, reading
basket members); no constraint is mocked.  Clash tests pin sessions with
locked slots so that a missing constraint shows up as a wrong status, instead
of passing because the solver happened to pick different hours.

They need ``ortools`` but neither Django settings nor a database::

    python -m unittest applications.academic_procedures.test_timetable_solver

(run from the FusionIIIT directory), or via ``manage.py test`` with the other
module tests.
"""

import unittest
from types import SimpleNamespace
from unittest import mock

from applications.academic_procedures.solver import timetable_solver as ts

FREE = ('OPTIMAL', 'FEASIBLE')


class _Version:
    id = 1
    status = 'Draft'
    remarks = ''

    def save(self, **kwargs):
        pass


class _Solver(ts.WholeCollegeTimetableSolver):
    """Real model and constraints; DB reads/writes replaced by in-memory state."""

    def __init__(self, basket_members=None):
        super().__init__(academic_year=2026, semester_type='Odd Semester')
        self.basket_members = basket_members or {}
        self.assigned = None
        self.failure = None

    def _basket_member_ids(self, basket):
        return self.basket_members[basket]

    def _extract_and_persist(self, solver, x, sessions, version):
        self.assigned = {
            sess.session_id: [key for key, var in x[sess.session_id].items()
                              if solver.Value(var) == 1]
            for sess in sessions
        }
        return len(self.assigned)

    def _record_solver_failure(self, version, status_str, message, conflicts=None):
        self.failure = (status_str, message, conflicts or [])


def room(room_id, capacity=60, room_type='Lecture Hall'):
    return SimpleNamespace(room_id=room_id, capacity=capacity, room_type=room_type)


def session(n, ci=None, batch=2024, branch='CSE', section='', rooms=('R1',),
            lock=None, block=1, slot_type=ts.LECTURE, co=(), curriculum=None):
    day, hour, room_id = lock if lock else (None, None, None)
    return ts.SessionRecord(
        session_id=f's{n}',
        curriculum_id=curriculum if curriculum is not None else n,
        curriculum_instructor_id=ci,
        course_code=f'C{n}',
        course_name=f'Course {n}',
        slot_type=slot_type,
        block_size=block,
        batch=batch, programme='B.Tech', branch=branch, section=section,
        effective_size=40,
        eligible_rooms=list(rooms),
        locked_day=day, locked_hour=hour, locked_room=room_id,
        co_instructor_ids=list(co),
    )


def solve(sessions, rooms=('R1', 'R2'), ci_to_faculty=None, baskets=(),
          basket_members=None, timeout=10, prefs=()):
    solver = _Solver(basket_members)
    result = solver._build_and_solve(
        _Version(), {r: room(r) for r in rooms}, sessions, list(baskets), list(prefs),
        {}, ci_to_faculty or {}, timeout, 1,
    )
    return result, solver


def pref(faculty_id, day, start, end, kind='Unavailable'):
    return SimpleNamespace(faculty_id=faculty_id, day_of_week=day, start_hour=start,
                           end_hour=end, preference_type=kind)


@unittest.skipUnless(ts._ORTOOLS_AVAILABLE, 'ortools is not installed')
class SolverHardConstraintTests(unittest.TestCase):

    def assertScheduledOnce(self, solver, sessions):
        for s in sessions:
            self.assertEqual(len(solver.assigned[s.session_id]), 1, s.session_id)

    def test_single_session_gets_one_valid_slot(self):
        s = session(1, ci=10)
        result, solver = solve([s], rooms=('R1',))
        self.assertIn(result.status, FREE)
        [(day, hour, room_id)] = solver.assigned['s1']
        self.assertIn(day, ts.DAYS)
        self.assertIn(hour, ts.HOURS)
        self.assertEqual(room_id, 'R1')

    def test_same_cohort_forced_together_is_infeasible(self):
        a = session(1, ci=10, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=20, rooms=('R2',), lock=(1, 10, 'R2'))
        result, solver = solve([a, b])
        self.assertEqual(result.status, 'INFEASIBLE')
        self.assertEqual(solver.failure[0], 'INFEASIBLE')

    def test_same_cohort_is_spread_when_free(self):
        sessions = [session(i, ci=10 + i, rooms=('R1', 'R2')) for i in range(1, 6)]
        result, solver = solve(sessions)
        self.assertIn(result.status, FREE)
        self.assertScheduledOnce(solver, sessions)
        times = [solver.assigned[s.session_id][0][:2] for s in sessions]
        self.assertEqual(len(times), len(set(times)))

    def test_same_room_forced_together_is_infeasible(self):
        a = session(1, ci=10, batch=2023, lock=(1, 10, 'R1'))
        b = session(2, ci=20, batch=2024, lock=(1, 10, 'R1'))
        result, _ = solve([a, b])
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_room_capacity_of_week_is_a_hard_limit(self):
        week = len(ts.DAYS) * len(ts.HOURS)
        fits = [session(i, ci=i, batch=2000 + i) for i in range(week)]
        result, solver = solve(fits, rooms=('R1',), timeout=30)
        self.assertIn(result.status, FREE)
        used = [solver.assigned[s.session_id][0] for s in fits]
        self.assertEqual(len(used), len(set(used)))

        too_many = [session(i, ci=i, batch=2000 + i) for i in range(week + 1)]
        result, _ = solve(too_many, rooms=('R1',), timeout=30)
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_same_instructor_id_forced_together_is_infeasible(self):
        a = session(1, ci=10, batch=2023, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=10, batch=2024, rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([a, b], ci_to_faculty={10: 1})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_same_person_with_two_curriculum_instructor_ids_is_infeasible(self):
        # Regression: the clash rule used the Curriculum_Instructor row id, so
        # one professor teaching two courses could be booked twice at once.
        a = session(1, ci=10, batch=2023, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=11, batch=2024, rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([a, b], ci_to_faculty={10: 1, 11: 1})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_different_people_may_share_an_hour(self):
        a = session(1, ci=10, batch=2023, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=20, batch=2024, rooms=('R2',), lock=(1, 10, 'R2'))
        result, solver = solve([a, b], ci_to_faculty={10: 1, 20: 2})
        self.assertIn(result.status, FREE)
        self.assertEqual(solver.assigned['s1'], [(1, 10, 'R1')])
        self.assertEqual(solver.assigned['s2'], [(1, 10, 'R2')])

    def test_co_instructor_is_booked_for_the_course(self):
        # Person 1 is primary on course 1 and co-instructor on course 2.
        a = session(1, ci=10, batch=2023, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=20, co=(11,), batch=2024, rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([a, b], ci_to_faculty={10: 1, 11: 1, 20: 2})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_unknown_faculty_mapping_still_clashes_on_same_id(self):
        a = session(1, ci=10, batch=2023, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=10, batch=2024, rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([a, b], ci_to_faculty={})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_common_course_clashes_with_branch_course(self):
        # Regression: 'Common' and 'CSE' were treated as unrelated cohorts.
        common = session(1, ci=10, branch='Common', rooms=('R1',), lock=(1, 10, 'R1'))
        cse = session(2, ci=20, branch='CSE', rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([common, cse])
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_different_branches_may_share_an_hour(self):
        cse = session(1, ci=10, branch='CSE', rooms=('R1',), lock=(1, 10, 'R1'))
        ece = session(2, ci=20, branch='ECE', rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([cse, ece])
        self.assertIn(result.status, FREE)

    def test_unsectioned_class_clashes_with_a_section(self):
        whole = session(1, ci=10, section='', rooms=('R1',), lock=(1, 10, 'R1'))
        sec_a = session(2, ci=20, section='A', rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([whole, sec_a])
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_whole_branch_class_clashes_with_common_section_class(self):
        # Regression: sections were indexed per branch, so a section that only
        # appeared on a 'Common' course was invisible to whole-branch classes.
        whole_cse = session(1, ci=10, branch='CSE', rooms=('R1',), lock=(1, 10, 'R1'))
        common_a = session(2, ci=20, branch='Common', section='A',
                           rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([whole_cse, common_a])
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_different_sections_may_share_an_hour(self):
        sec_a = session(1, ci=10, section='A', rooms=('R1',), lock=(1, 10, 'R1'))
        sec_b = session(2, ci=20, section='B', rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([sec_a, sec_b])
        self.assertIn(result.status, FREE)

    def test_common_course_does_not_span_programmes(self):
        btech = session(1, ci=10, branch='Common', rooms=('R1',), lock=(1, 10, 'R1'))
        mtech = session(2, ci=20, branch='CSE', rooms=('R2',), lock=(1, 10, 'R2'))
        mtech.programme = 'M.Tech'
        result, _ = solve([btech, mtech])
        self.assertIn(result.status, FREE)

    def test_sessions_without_instructor_do_not_clash_with_each_other(self):
        # A missing instructor is "nobody", not one shared person.
        a = session(1, ci=None, batch=2023, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=None, batch=2024, rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([a, b])
        self.assertIn(result.status, FREE)

    def test_partially_overlapping_lab_blocks_clash(self):
        lab_a = session(1, ci=10, block=2, slot_type=ts.PRACTICAL, rooms=('L1',), lock=(1, 9, 'L1'))
        lab_b = session(2, ci=20, block=2, slot_type=ts.PRACTICAL, rooms=('L2',), lock=(1, 10, 'L2'))
        result, _ = solve([lab_a, lab_b], rooms=('L1', 'L2'))
        self.assertEqual(result.status, 'INFEASIBLE')

        lab_b = session(2, ci=20, block=2, slot_type=ts.PRACTICAL, rooms=('L2',), lock=(1, 11, 'L2'))
        lab_a = session(1, ci=10, block=2, slot_type=ts.PRACTICAL, rooms=('L1',), lock=(1, 9, 'L1'))
        result, _ = solve([lab_a, lab_b], rooms=('L1', 'L2'))
        self.assertIn(result.status, FREE)

    def test_preferences_outside_teaching_hours_are_ignored(self):
        prefs = [pref(1, 1, 13, 14), pref(1, 1, 18, 20)]
        result, _ = solve([session(1, ci=10)], ci_to_faculty={10: 1}, prefs=prefs)
        self.assertIn(result.status, FREE)

    def test_lab_block_occupies_every_hour(self):
        lab = session(1, ci=10, block=3, slot_type=ts.PRACTICAL,
                      rooms=('LAB',), lock=(1, 9, 'LAB'))
        lecture_inside = session(2, ci=20, rooms=('R1',), lock=(1, 11, 'R1'))
        result, _ = solve([lab, lecture_inside], rooms=('LAB', 'R1'))
        self.assertEqual(result.status, 'INFEASIBLE')

        lab = session(1, ci=10, block=3, slot_type=ts.PRACTICAL,
                      rooms=('LAB',), lock=(1, 9, 'LAB'))
        lecture_after = session(2, ci=20, rooms=('R1',), lock=(1, 12, 'R1'))
        result, _ = solve([lab, lecture_after], rooms=('LAB', 'R1'))
        self.assertIn(result.status, FREE)

    def test_lab_block_holds_room_and_instructor_for_every_hour(self):
        def lab():
            return session(1, ci=10, block=3, slot_type=ts.PRACTICAL,
                           rooms=('LAB',), lock=(1, 9, 'LAB'))
        other_cohort_same_room = session(2, ci=20, batch=2023, rooms=('LAB',),
                                         lock=(1, 11, 'LAB'))
        result, _ = solve([lab(), other_cohort_same_room], rooms=('LAB', 'R1'))
        self.assertEqual(result.status, 'INFEASIBLE')

        other_cohort_same_teacher = session(2, ci=10, batch=2023, rooms=('R1',),
                                            lock=(1, 11, 'R1'))
        result, _ = solve([lab(), other_cohort_same_teacher], rooms=('LAB', 'R1'),
                          ci_to_faculty={10: 1})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_lab_blocks_never_cross_lunch(self):
        labs = [session(i, ci=10 + i, batch=2000 + i, block=3,
                        slot_type=ts.PRACTICAL, rooms=('LAB',)) for i in range(8)]
        result, solver = solve(labs, rooms=('LAB',))
        self.assertIn(result.status, FREE)
        for s in labs:
            [(_day, start, _room)] = solver.assigned[s.session_id]
            hours = range(start, start + 3)
            self.assertTrue(all(h in ts.HOURS for h in hours), (s.session_id, start))

    def test_session_without_any_valid_slot_fails_instead_of_vanishing(self):
        # Regression: such sessions were skipped and the run reported OPTIMAL.
        impossible = session(1, ci=10, block=5, slot_type=ts.PRACTICAL)
        result, solver = solve([impossible, session(2, ci=20, batch=2023)])
        self.assertEqual(result.status, 'INFEASIBLE')
        self.assertEqual(solver.failure[2][0]['error_code'], 'NO_VALID_SLOT')

    def test_same_person_with_text_faculty_pk_is_infeasible(self):
        # ExtraInfo (and so Faculty) primary keys are text, e.g. roll numbers.
        a = session(1, ci=10, batch=2023, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=11, batch=2024, rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([a, b], ci_to_faculty={10: 'FAC01', 11: 'FAC01'})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_unavailable_windows_are_avoided(self):
        # Person 1 is unavailable everywhere except Friday 17:00.
        prefs = [pref(1, day, 9, 18) for day in (1, 2, 3, 4)] + [pref(1, 5, 9, 17)]
        result, solver = solve([session(1, ci=10, rooms=('R1',))], rooms=('R1',),
                               ci_to_faculty={10: 1}, prefs=prefs)
        self.assertIn(result.status, FREE)
        self.assertEqual(solver.assigned['s1'], [(5, 17, 'R1')])

    def test_preferred_window_is_rewarded(self):
        prefs = [pref(1, 2, 14, 15, kind='Preferred')]
        result, solver = solve([session(1, ci=10, rooms=('R1',))], rooms=('R1',),
                               ci_to_faculty={10: 1}, prefs=prefs)
        self.assertIn(result.status, FREE)
        self.assertEqual(solver.assigned['s1'], [(2, 14, 'R1')])

    def test_timeout_is_not_reported_as_infeasible(self):
        # Only the solver's status code is faked; the model is still built.
        with mock.patch.object(ts.cp_model.CpSolver, 'Solve',
                               return_value=ts.cp_model.UNKNOWN):
            result, solver = solve([session(1, ci=10)])
        self.assertEqual(result.status, 'TIMEOUT')
        self.assertEqual(solver.failure[0], 'TIMEOUT')
        self.assertIn('does not prove', result.message)


@unittest.skipUnless(ts._ORTOOLS_AVAILABLE, 'ortools is not installed')
class ElectiveBasketTests(unittest.TestCase):

    def test_basket_courses_for_one_cohort_run_together(self):
        # Regression: cohort exclusivity made every same-cohort basket infeasible.
        a = session(1, ci=10, rooms=('R1', 'R2'))
        b = session(2, ci=20, rooms=('R1', 'R2'))
        result, solver = solve([a, b], baskets=['B'], basket_members={'B': [1, 2]})
        self.assertIn(result.status, FREE)
        self.assertEqual(solver.assigned['s1'][0][:2], solver.assigned['s2'][0][:2])

    def test_basket_courses_cannot_be_pinned_apart(self):
        a = session(1, ci=10, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=20, rooms=('R2',), lock=(1, 11, 'R2'))
        result, _ = solve([a, b], baskets=['B'], basket_members={'B': [1, 2]})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_basket_course_still_clashes_with_non_basket_course(self):
        a = session(1, ci=10, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=20, rooms=('R2',), lock=(1, 10, 'R2'))
        core = session(3, ci=30, rooms=('R3',), lock=(1, 10, 'R3'))
        result, _ = solve([a, b, core], rooms=('R1', 'R2', 'R3'),
                          baskets=['B'], basket_members={'B': [1, 2]})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_two_lectures_of_one_basket_course_do_not_overlap(self):
        a1 = session(1, ci=10, curriculum=1, rooms=('R1',), lock=(1, 10, 'R1'))
        a2 = session(2, ci=11, curriculum=1, rooms=('R2',), lock=(1, 10, 'R2'))
        b1 = session(3, ci=20, curriculum=2, rooms=('R3',))
        b2 = session(4, ci=21, curriculum=2, rooms=('R4',))
        result, _ = solve([a1, a2, b1, b2], rooms=('R1', 'R2', 'R3', 'R4'),
                          baskets=['B'], basket_members={'B': [1, 2]})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_basket_does_not_exempt_a_shared_teacher(self):
        a = session(1, ci=10, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=11, rooms=('R2',), lock=(1, 10, 'R2'))
        result, _ = solve([a, b], ci_to_faculty={10: 1, 11: 1},
                          baskets=['B'], basket_members={'B': [1, 2]})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_basket_does_not_exempt_a_shared_room(self):
        a = session(1, ci=10, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=20, batch=2023, rooms=('R1',), lock=(1, 10, 'R1'))
        result, _ = solve([a, b], baskets=['B'], basket_members={'B': [1, 2]})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_basket_across_cohorts_is_still_synchronised(self):
        cse = session(1, ci=10, branch='CSE', rooms=('R1',), lock=(1, 10, 'R1'))
        ece = session(2, ci=20, branch='ECE', rooms=('R2',), lock=(2, 10, 'R2'))
        result, _ = solve([cse, ece], baskets=['B'], basket_members={'B': [1, 2]})
        self.assertEqual(result.status, 'INFEASIBLE')

    def test_three_course_basket_runs_together(self):
        sessions = [session(i, ci=10 + i, rooms=('R1', 'R2', 'R3')) for i in (1, 2, 3)]
        result, solver = solve(sessions, rooms=('R1', 'R2', 'R3'),
                               baskets=['B'], basket_members={'B': [1, 2, 3]})
        self.assertIn(result.status, FREE)
        times = {solver.assigned[s.session_id][0][:2] for s in sessions}
        self.assertEqual(len(times), 1)

    def test_basket_with_uneven_session_counts_reports_why(self):
        s = [session(i, ci=10 + i, curriculum=1, rooms=('R1', 'R2')) for i in range(3)]
        s += [session(10 + i, ci=30 + i, curriculum=2, rooms=('R1', 'R2')) for i in range(2)]
        result, solver = solve(s, baskets=['B'], basket_members={'B': [1, 2]})
        self.assertEqual(result.status, 'INFEASIBLE')
        self.assertEqual([c['error_code'] for c in solver.failure[2]], ['BASKET_MISMATCH'])

    def test_unscheduled_first_member_does_not_disable_basket(self):
        # Regression: a non-floated first member made the basket be ignored.
        a = session(1, ci=10, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=20, rooms=('R2',), lock=(1, 11, 'R2'))
        result, _ = solve([a, b], baskets=['B'], basket_members={'B': [999, 1, 2]})
        self.assertEqual(result.status, 'INFEASIBLE')


class PureHelperTests(unittest.TestCase):

    def test_valid_block_starts(self):
        self.assertEqual(ts.valid_block_starts(1), ts.HOURS)
        self.assertEqual(ts.valid_block_starts(2), ts.LAB_STARTS_2H)
        self.assertEqual(ts.valid_block_starts(3), ts.LAB_STARTS_3H)
        self.assertEqual(ts.valid_block_starts(5), [])
        self.assertEqual(ts.valid_block_starts(0), [])

    def test_effective_cohort_size(self):
        counts = {
            (2024, 'B.Tech', 'CSE', 'A'): 50,
            (2024, 'B.Tech', 'CSE', 'B'): 50,
            (2024, 'B.Tech', 'ECE', ''): 60,
            (2023, 'B.Tech', 'CSE', ''): 99,
        }
        size = ts.effective_cohort_size
        self.assertEqual(size(counts, 2024, 'B.Tech', 'CSE', '', 1.0), 100)
        self.assertEqual(size(counts, 2024, 'B.Tech', 'CSE', 'A', 1.0), 50)
        self.assertEqual(size(counts, 2024, 'B.Tech', 'Common', '', 1.0), 160)
        self.assertEqual(size(counts, 2024, 'B.Tech', 'ME', '', 1.0),
                         ts.DEFAULT_COHORT_SIZE)
        self.assertEqual(size(counts, 2024, 'B.Tech', 'ECE', ''), 66)
        # Curriculum.branch 'DESIGN' vs department 'Design'
        self.assertEqual(size({(2024, 'B.Tech', 'Design', ''): 40}, 2024, 'B.Tech',
                              'DESIGN', '', 1.0), 40)

    def test_design_students_fill_design_courses(self):
        # Regression (from the fusionlab dump): Design courses are filed as
        # B.Tech/DESIGN but the 2022 Design students are B.Des/Design, so the
        # course was sized for the 30-student default instead of 61.
        counts = {(2022, 'B.Des', 'Design', ''): 61, (2022, 'B.Tech', 'CSE', ''): 70}
        size = ts.effective_cohort_size
        self.assertEqual(size(counts, 2022, 'B.Tech', 'DESIGN', '', 1.0), 61)
        self.assertEqual(size(counts, 2022, 'B.Des', 'Design', '', 1.0), 61)
        self.assertEqual(size(counts, 2022, 'B.Tech', 'CSE', '', 1.0), 70)

    def test_design_students_are_not_added_to_btech_common_courses(self):
        # Current, deliberate behaviour pending a decision: nothing records
        # whether B.Des students attend B.Tech 'Common' courses.
        counts = {(2022, 'B.Des', 'Design', ''): 61, (2022, 'B.Tech', 'CSE', ''): 70}
        self.assertEqual(ts.effective_cohort_size(counts, 2022, 'B.Tech', 'Common', '', 1.0), 70)

    def test_student_in_cohort(self):
        match = ts.student_in_cohort
        self.assertTrue(match('B.Tech', 'CSE', 'B.Tech', 'CSE'))
        self.assertTrue(match('B.Tech', 'CSE', 'B.Tech', 'Common'))
        self.assertTrue(match('B.Tech', 'Design', 'B.Tech', 'DESIGN'))
        self.assertTrue(match('B.Des', 'Design', 'B.Tech', 'DESIGN'))
        self.assertTrue(match('B.Des', 'Design', 'B.Des', 'Common'))
        self.assertFalse(match('B.Des', 'Design', 'B.Tech', 'Common'))
        self.assertFalse(match('B.Des', 'Design', 'B.Tech', 'CSE'))
        self.assertFalse(match('M.Des', 'Design', 'B.Tech', 'DESIGN'))
        self.assertFalse(match('B.Tech', 'ECE', 'B.Tech', 'CSE'))
        self.assertEqual(ts.student_programmes_for('B.Tech'), ['B.Tech', 'B.Des'])
        self.assertEqual(ts.student_programmes_for('M.Tech'), ['M.Tech'])

    def test_build_locked_map(self):
        def row(cur, stype, day, hour, room_id, block=None):
            return SimpleNamespace(curriculum_id=cur, slot_type=stype, batch=2024,
                                   programme='B.Tech', branch='CSE', section='',
                                   day_of_week=day, start_hour=hour,
                                   classroom_id=room_id, lab_block_id=block)
        locked = ts.build_locked_map([
            row(1, 'Lecture', 3, 9, 'R1'),
            row(1, 'Lecture', 1, 9, 'R1'),
            row(1, 'Practical', 2, 15, 'LAB', block='b1'),
            row(1, 'Practical', 2, 14, 'LAB', block='b1'),
        ])
        lectures = ts.lock_key(1, 'Lecture', 2024, 'B.Tech', 'CSE', '')
        labs = ts.lock_key(1, 'Practical', 2024, 'B.Tech', 'CSE', '')
        # Every lecture lock survives (old code kept only the last one).
        self.assertEqual([(a['day'], a['hour']) for a in locked[lectures]], [(1, 9), (3, 9)])
        # One assignment per lab block, anchored at its first hour.
        self.assertEqual(locked[labs], [{'day': 2, 'hour': 14, 'room': 'LAB'}])

    def test_lock_source_is_newest_version_with_slots(self):
        # (version_id, version_number, slot_count)
        self.assertEqual(ts.pick_lock_source([(11, 1, 40), (12, 2, 40), (13, 3, 40)]), 13)
        self.assertEqual(ts.pick_lock_source([]), None)
        # Failed or timed-out runs have no slots and are skipped.
        self.assertEqual(ts.pick_lock_source([(11, 1, 40), (12, 2, 0)]), 11)
        self.assertEqual(ts.pick_lock_source([(12, 2, 0)]), None)

    def test_removed_locks_are_not_revived(self):
        # Regression: v2 had locks, the admin unlocked everything in v3.  The
        # next run must take v3 (no locks), not fall back to v2's old locks.
        v2_rows = [SimpleNamespace(curriculum_id=1, slot_type='Lecture', batch=2024,
                                   programme='B.Tech', branch='CSE', section='',
                                   day_of_week=1, start_hour=9, classroom_id='R1',
                                   lab_block_id=None, is_locked=True, version_id=2)]
        v3_rows = [SimpleNamespace(**{**vars(v2_rows[0]), 'is_locked': False, 'version_id': 3})]
        source = ts.pick_lock_source([(2, 2, len(v2_rows)), (3, 3, len(v3_rows))])
        self.assertEqual(source, 3)
        inherited = [r for r in v2_rows + v3_rows if r.version_id == source and r.is_locked]
        self.assertEqual(ts.build_locked_map(inherited), {})

    def test_basket_mismatches(self):
        sessions = [session(1, curriculum=1), session(2, curriculum=1), session(3, curriculum=2)]
        self.assertEqual(len(ts.basket_mismatches([[1, 2]], sessions)), 1)
        sessions.append(session(4, curriculum=2))
        self.assertEqual(ts.basket_mismatches([[1, 2]], sessions), [])

    def test_count_cohort_students_uses_department_as_branch(self):
        def student(batch, dept, section):
            return SimpleNamespace(
                batch=batch, programme='B.Tech', section=section,
                id=SimpleNamespace(department=SimpleNamespace(name=dept) if dept else None),
            )
        counts = ts.count_cohort_students(
            [student(2024, 'CSE', 'A'), student(2024, 'CSE', 'A'), student(2024, None, None)]
        )
        self.assertEqual(counts, {(2024, 'B.Tech', 'CSE', 'A'): 2,
                                  (2024, 'B.Tech', '', ''): 1})

    def test_cohort_atoms(self):
        whole = session(1, branch='CSE')
        common = session(2, branch='Common')
        sec_a = session(3, branch='ECE', section='A')
        index = ts.build_cohort_index([whole, common, sec_a])
        p = (2024, 'B.Tech')
        self.assertEqual(ts.cohort_atoms(sec_a, index), {(*p, 'ECE', 'A')})
        self.assertEqual(ts.cohort_atoms(whole, index), {(*p, 'CSE', ''), (*p, 'CSE', 'A')})
        self.assertEqual(ts.cohort_atoms(common, index), {
            (*p, b, s) for b in ('CSE', 'ECE', 'Common') for s in ('', 'A')})

    def test_lock_without_hour_or_room_is_dropped(self):
        no_hour = session(1, rooms=('R1',), lock=(1, None, 'R1'))
        no_room = session(2, rooms=('R1',), lock=(1, 10, None))
        warnings, conflicts = ts.sanitize_locked_sessions(
            [no_hour, no_room], {'R1': room('R1')}, {})
        self.assertEqual((len(warnings), conflicts), (2, []))
        self.assertIsNone(no_hour.locked_day)
        self.assertIsNone(no_room.locked_day)

    def test_lock_in_a_room_too_small_is_dropped(self):
        s = session(1, rooms=('BIG',), lock=(1, 10, 'SMALL'))
        warnings, _ = ts.sanitize_locked_sessions(
            [s], {'BIG': room('BIG'), 'SMALL': room('SMALL', capacity=5)}, {})
        self.assertIn('too small or the wrong type', warnings[0]['description'])

    def test_eligible_room_types(self):
        self.assertEqual(ts.eligible_room_types(ts.PRACTICAL, 'any'),
                         ts.SLOT_ROOM_AFFINITY[ts.PRACTICAL])
        self.assertEqual(ts.eligible_room_types(ts.LECTURE, 'Computer Lab'), ['Computer Lab'])
        self.assertEqual(ts.eligible_room_types('Seminar', None), [])

    def test_faculty_keys_use_person_not_row(self):
        s = session(1, ci=10, co=(11, 12))
        self.assertEqual(ts.faculty_keys(s, {10: 1, 11: 1}), {1, ('ci', 12)})

    def test_invalid_locks_are_dropped_with_a_warning(self):
        bad_room = session(1, ci=10, rooms=('R1',), lock=(1, 10, 'NOPE'))
        bad_hour = session(2, ci=20, block=2, slot_type=ts.PRACTICAL,
                           rooms=('R1',), lock=(1, 12, 'R1'))
        bad_day = session(3, ci=30, rooms=('R1',), lock=(6, 10, 'R1'))
        warnings, conflicts = ts.sanitize_locked_sessions(
            [bad_room, bad_hour, bad_day], {'R1': room('R1')}, {})
        self.assertEqual(len(warnings), 3)
        self.assertEqual(conflicts, [])
        for s in (bad_room, bad_hour, bad_day):
            self.assertIsNone(s.locked_day)

    def test_clashing_locks_are_reported(self):
        a = session(1, ci=10, batch=2023, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=11, batch=2024, rooms=('R2',), lock=(1, 10, 'R2'))
        _, conflicts = ts.sanitize_locked_sessions(
            [a, b], {'R1': room('R1'), 'R2': room('R2')}, {10: 1, 11: 1})
        self.assertEqual([c['error_code'] for c in conflicts], ['LOCK_CONFLICT'])

    def test_locks_of_one_basket_may_share_a_cohort(self):
        a = session(1, ci=10, rooms=('R1',), lock=(1, 10, 'R1'))
        b = session(2, ci=20, rooms=('R2',), lock=(1, 10, 'R2'))
        rooms = {'R1': room('R1'), 'R2': room('R2')}
        _, conflicts = ts.sanitize_locked_sessions([a, b], rooms, {}, {1: 0, 2: 0})
        self.assertEqual(conflicts, [])
        _, conflicts = ts.sanitize_locked_sessions([a, b], rooms, {})
        self.assertEqual(len(conflicts), 1)

    def test_two_sessions_of_one_basket_course_locked_together_conflict(self):
        a1 = session(1, ci=10, curriculum=1, rooms=('R1',), lock=(1, 10, 'R1'))
        a2 = session(2, ci=11, curriculum=1, rooms=('R2',), lock=(1, 10, 'R2'))
        rooms = {'R1': room('R1'), 'R2': room('R2')}
        _, conflicts = ts.sanitize_locked_sessions([a1, a2], rooms, {}, {1: 0, 2: 0})
        self.assertEqual([c['error_code'] for c in conflicts], ['LOCK_CONFLICT'])


if __name__ == '__main__':
    unittest.main()
