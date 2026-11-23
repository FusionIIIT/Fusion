from django.db import IntegrityError, transaction
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from django.contrib.auth.models import User

from applications.academic_information.models import Student
from applications.academic_information.status_test_utils import (
    make_batch, make_student, set_status)
from applications.academic_procedures.models import course_registration
from applications.examination.attendance_sheet import (
    PlanChanged, PlanRefused, copy_plan, course_in_scope, courses_for,
    instructor_names, overview, plan_body, roll_list, save_plan,
    section_wise, term_year)
from applications.globals.models import ExtraInfo, Faculty
from applications.programme_curriculum.models import (
    Batch, Course, CourseInstructor, CourseSlot, Curriculum, Discipline,
    Programme, Semester)
from applications.examination.models import ExamAttendancePlan, ExamAttendanceRoom
import datetime
from unittest import mock


def make_course():
    return Course.objects.create(
        code='CS8004', name='Deep Learning and Applications',
        credit=3, syllabus='', ref_books='')


class PlanModelTests(TestCase):
    def test_one_plan_per_course_term_and_exam(self):
        course = make_course()
        kw = dict(course=course, academic_year='2026-27',
                  semester_type='Odd Semester', roll_count=40)
        ExamAttendancePlan.objects.create(exam='MID', **kw)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExamAttendancePlan.objects.create(exam='MID', **kw)
        ExamAttendancePlan.objects.create(exam='END', **kw)

    def test_rooms_come_back_in_position_order(self):
        plan = ExamAttendancePlan.objects.create(
            course=make_course(), academic_year='2026-27',
            semester_type='Odd Semester', exam='MID', roll_count=40)
        for room, pos in (('L104', 2), ('L201', 1)):
            ExamAttendanceRoom.objects.create(
                plan=plan, position=pos, from_sno=1, to_sno=20, room=room,
                date=datetime.date(2026, 11, 30),
                start_time=datetime.time(9, 0), end_time=datetime.time(11, 0))
        self.assertEqual([r.room for r in plan.rooms.all()], ['L201', 'L104'])


ODD = 'Odd Semester'
TERM = ('2026-27', ODD)


def make_pg_batch(year, acronym, category, name):
    programme, _ = Programme.objects.get_or_create(
        category=category, name=name, defaults={'programme_begin_year': year})
    curriculum, _ = Curriculum.objects.get_or_create(
        programme=programme, name='%s %s' % (name, year),
        defaults={'no_of_semester': 4})
    discipline, _ = Discipline.objects.get_or_create(
        acronym=acronym, defaults={'name': 'Discipline %s' % acronym})
    return Batch.objects.get_or_create(
        name=name, year=year, discipline=discipline, curriculum=curriculum)[0]


def make_faculty(username, first, last):
    user = User.objects.create_user(
        username=username, password='x', first_name=first, last_name=last)
    extra = ExtraInfo.objects.create(id=username, user=user, user_type='faculty')
    return Faculty.objects.create(id=extra)


class RollListTests(TestCase):
    def setUp(self):
        self.course = make_course()
        batch = make_batch(2023)
        self.semester = Semester.objects.create(
            curriculum=batch.curriculum, semester_no=5)
        self.slot = CourseSlot.objects.create(
            semester=self.semester, name='EL', type='Core')

    def register(self, student, course=None, session='2026-27',
                 sem_type=ODD, offering=None):
        return course_registration.objects.create(
            student_id=student, semester_id=self.semester,
            course_id=course or self.course, course_slot_id=self.slot,
            registration_type='Regular', semester_type=sem_type,
            session=session, course_instructor=offering)

    def offering(self, section, faculty, year=2026, sem_type=ODD, course=None):
        return CourseInstructor.objects.create(
            course_id=course or self.course, instructor_id=faculty, year=year,
            semester_type=sem_type, section_label=section)

    def student(self, roll, programme='B.Tech', section=None, batch=None):
        student = make_student(roll, batch=batch)
        student.programme = programme
        student.section = section
        student.save()
        return student

    def test_order_is_programme_then_section_then_roll(self):
        fa = make_faculty('fa', 'Asha', 'Rao')
        fb = make_faculty('fb', 'Ravi', 'Kumar')
        off_a = self.offering('A', fa)
        off_b = self.offering('B', fb)
        mtech = make_pg_batch(2026, 'CSE', 'PG', 'M.Tech')
        phd = make_pg_batch(2025, 'CSE', 'PHD', 'PhD')
        self.register(self.student('23BCS002', section='B'), offering=off_b)
        self.register(self.student('23BCS001', section='A'), offering=off_a)
        self.register(self.student('26MCSA01', 'M.Tech', batch=mtech))
        self.register(self.student('25PCSV01', 'PhD', batch=phd))
        rows = roll_list(self.course, *TERM)
        self.assertEqual([r['roll_no'] for r in rows],
                         ['23BCS001', '23BCS002', '26MCSA01', '25PCSV01'])
        self.assertEqual([r['sno'] for r in rows], [1, 2, 3, 4])
        self.assertEqual([r['section'] for r in rows], ['A', 'B', '', ''])
        self.assertEqual(rows[0]['programme'], 'B.Tech')
        self.assertEqual(rows[0]['discipline'], 'CSE')

    def test_an_elective_has_no_sections(self):
        self.offering(None, make_faculty('fa', 'Asha', 'Rao'))
        self.assertFalse(section_wise(self.course, *TERM))
        self.register(self.student('23BCS002', section='A'))
        self.register(self.student('23BCS001', section='B'))
        rows = roll_list(self.course, *TERM)
        self.assertEqual([r['roll_no'] for r in rows], ['23BCS001', '23BCS002'])
        self.assertEqual([r['section'] for r in rows], ['', ''])

    def test_withdrawn_students_are_left_out(self):
        gone = self.student('23BCS001')
        self.register(gone)
        self.register(self.student('23BCS002'))
        set_status(gone, 'WITHDRAWN')
        self.assertEqual([r['roll_no'] for r in roll_list(self.course, *TERM)],
                         ['23BCS002'])

    def test_other_terms_are_left_out(self):
        student = self.student('23BCS001')
        self.register(student, session='2025-26')
        self.assertEqual(roll_list(self.course, *TERM), [])

    def test_instructor_names_by_section(self):
        self.offering('A', make_faculty('fa', 'Asha', 'Rao'))
        self.offering('B', make_faculty('fb', 'Ravi', 'Kumar'))
        self.assertEqual(instructor_names(self.course, *TERM), {
            'by_section': {'A': 'PROF. ASHA RAO', 'B': 'PROF. RAVI KUMAR'},
            'all': ['PROF. ASHA RAO', 'PROF. RAVI KUMAR']})

    def test_even_semester_instructors_use_the_second_year(self):
        even = 'Even Semester'
        self.offering('A', make_faculty('fa', 'Asha', 'Rao'),
                      year=2027, sem_type=even)
        self.offering('B', make_faculty('fb', 'Ravi', 'Kumar'),
                      year=2026, sem_type=even)
        self.assertEqual(
            instructor_names(self.course, '2026-27', even)['all'],
            ['PROF. ASHA RAO'])

    def test_term_year_refuses_summer_and_bad_sessions(self):
        self.assertEqual(term_year('2026-27', ODD), 2026)
        self.assertEqual(term_year('2026-27', 'Even Semester'), 2027)
        with self.assertRaises(ValueError):
            term_year('2026-27', 'Summer Semester')
        with self.assertRaises(ValueError):
            term_year('2026', ODD)

    def test_course_in_scope_needs_every_student_in_scope(self):
        pg = make_pg_batch(2026, 'CSE', 'PG', 'M.Tech')
        ug_only = Course.objects.create(
            code='CS1001', name='Intro', credit=3, syllabus='', ref_books='')
        self.register(self.student('23BCS001'))
        self.register(self.student('23BCS002'), course=ug_only)
        self.register(self.student('26MCSA01', 'M.Tech', batch=pg))
        self.assertFalse(course_in_scope(self.course, *TERM, frozenset({'UG'})))
        self.assertTrue(course_in_scope(self.course, *TERM, None))
        self.assertTrue(course_in_scope(self.course, *TERM, frozenset({'UG', 'PG'})))
        self.assertTrue(course_in_scope(ug_only, *TERM, frozenset({'UG'})))

    def test_courses_for_lists_saved_plans(self):
        other = Course.objects.create(
            code='CS1001', name='Intro', credit=3, syllabus='', ref_books='')
        self.register(self.student('23BCS001'))
        self.register(self.student('23BCS002'), course=other)
        ExamAttendancePlan.objects.create(
            course=self.course, academic_year='2026-27', semester_type=ODD,
            exam='MID', roll_count=1)
        rows = courses_for('2026-27', ODD, frozenset({'UG'}))
        self.assertEqual(rows, [
            {'id': other.id, 'code': 'CS1001', 'name': 'Intro', 'plans': []},
            {'id': self.course.id, 'code': 'CS8004',
             'name': 'Deep Learning and Applications', 'plans': ['MID']}])

    def test_a_student_without_a_category_is_out_of_scope(self):
        self.register(self.student('23BCS001'))
        orphan = self.student('23BCS002')
        Student.objects.filter(pk=orphan.pk).update(batch_id=None)
        orphan = Student.objects.get(pk=orphan.pk)
        self.register(orphan)
        ug = frozenset({'UG'})
        self.assertFalse(course_in_scope(self.course, *TERM, ug))
        self.assertTrue(course_in_scope(self.course, *TERM, None))
        self.assertEqual(courses_for('2026-27', ODD, ug), [])
        self.assertEqual(len(courses_for('2026-27', ODD, None)), 1)

    def test_courses_for_refuses_summer(self):
        with self.assertRaises(ValueError):
            courses_for('2026-27', 'Summer Semester', None)
        with self.assertRaises(ValueError):
            courses_for('2026', ODD, frozenset({'UG'}))

    def test_courses_for_query_count_does_not_grow_with_courses(self):
        def count():
            with CaptureQueriesContext(connection) as ctx:
                courses_for('2026-27', ODD, frozenset({'UG'}))
            return len(ctx)

        self.register(self.student('23BCS001'))
        other = Course.objects.create(
            code='CS1001', name='Intro', credit=3, syllabus='', ref_books='')
        self.register(self.student('23BCS002'), course=other)
        two = count()
        for i in range(3):
            extra = Course.objects.create(
                code='CS20%02d' % i, name='X%d' % i, credit=3,
                syllabus='', ref_books='')
            self.register(self.student('23BCS01%d' % i), course=extra)
        self.assertEqual(count(), two)


class PlanSaveTests(TestCase):
    def setUp(self):
        self.course = make_course()
        batch = make_batch(2023)
        semester = Semester.objects.create(
            curriculum=batch.curriculum, semester_no=5)
        slot = CourseSlot.objects.create(
            semester=semester, name='EL', type='Core')
        for n in range(1, 46):
            student = make_student('23BCS%03d' % n, batch=batch)
            course_registration.objects.create(
                student_id=student, semester_id=semester,
                course_id=self.course, course_slot_id=slot,
                registration_type='Regular', semester_type=ODD,
                session='2026-27')
        self.user = User.objects.create_user('exam', password='x')

    def room(self, a, b, name='L201', start='15:00', end='17:00'):
        return {'from_sno': a, 'to_sno': b, 'room': name,
                'date': '2026-09-22', 'start_time': start, 'end_time': end,
                'instructor_text': ''}

    def save(self, rooms, exam='MID', updated_at=None):
        return save_plan(self.course, '2026-27', ODD, exam, rooms,
                         self.user, updated_at)

    def errors(self, rooms):
        with self.assertRaises(PlanRefused) as ctx:
            self.save(rooms)
        return ctx.exception.errors

    def test_save_then_update_replaces_rooms(self):
        plan = self.save([self.room(1, 20), self.room(21, 45, 'L104')])
        self.assertEqual(plan.rooms.count(), 2)
        self.assertEqual(plan.roll_count, 45)
        plan = self.save([self.room(1, 45)], updated_at=plan.updated_at.isoformat())
        self.assertEqual(plan.rooms.count(), 1)

    def test_save_refuses_a_range_past_the_end(self):
        self.assertIn('Room 1: S.No must be between 1 and 45.',
                      self.errors([self.room(1, 46)]))

    def test_save_refuses_overlap(self):
        self.assertIn('Rooms 1 and 2 overlap.',
                      self.errors([self.room(1, 20), self.room(20, 45)]))

    def test_save_refuses_end_not_after_start(self):
        self.assertIn('Room 1: the exam must end after it starts.',
                      self.errors([self.room(1, 45, end='15:00')]))

    def test_save_refuses_empty_and_reversed_and_missing(self):
        self.assertEqual(self.errors([]), ['Add at least one room.'])
        self.assertIn('Room 1: from S.No must not be after to S.No.',
                      self.errors([self.room(20, 10)]))
        self.assertIn('Room 1: room, date, start and end time are required.',
                      self.errors([self.room(1, 45, name='')]))
        self.assertIn('Room 1: room, date, start and end time are required.',
                      self.errors([self.room(1, 45, start='soon')]))

    def test_save_refuses_a_room_name_or_instructor_text_too_long(self):
        long_name = self.room(1, 45, name='L' * 31)
        self.assertIn('Room 1: room name must be at most 30 characters.',
                      self.errors([long_name]))
        long_text = dict(self.room(1, 45), instructor_text='P' * 501)
        self.assertIn(
            'Room 1: instructor text must be at most 500 characters.',
            self.errors([long_text]))
        at_limit = dict(self.room(1, 45, name='L' * 30),
                        instructor_text='P' * 500)
        plan = self.save([at_limit])
        room = plan.rooms.get()
        self.assertEqual((len(room.room), len(room.instructor_text)), (30, 500))

    def test_gaps_are_allowed(self):
        plan = self.save([self.room(1, 20), self.room(30, 45)])
        self.assertEqual(plan.rooms.count(), 2)

    def test_a_stale_save_is_refused(self):
        plan = self.save([self.room(1, 20), self.room(21, 45)])
        with self.assertRaises(PlanChanged):
            self.save([self.room(1, 45)],
                      updated_at='2000-01-01T00:00:00+00:00')
        self.assertEqual(plan.rooms.count(), 2)

    def test_copy_mid_to_end(self):
        self.save([self.room(1, 20), self.room(21, 45, 'L104')])
        copy_plan(self.course, '2026-27', ODD, 'MID', 'END', self.user, False)
        mid = ExamAttendancePlan.objects.get(exam='MID')
        end = ExamAttendancePlan.objects.get(exam='END')
        self.assertEqual(plan_body(end)['rooms'], plan_body(mid)['rooms'])
        self.assertEqual(mid.rooms.count(), 2)
        self.assertEqual(end.roll_count, 45)

    def test_copy_asks_before_replacing(self):
        self.save([self.room(1, 20), self.room(21, 45, 'L104')])
        self.save([self.room(1, 45)], exam='END')
        with self.assertRaises(PlanChanged):
            copy_plan(self.course, '2026-27', ODD, 'MID', 'END', self.user, False)
        copy_plan(self.course, '2026-27', ODD, 'MID', 'END', self.user, True)
        mid = ExamAttendancePlan.objects.get(exam='MID')
        end = ExamAttendancePlan.objects.get(exam='END')
        self.assertEqual(plan_body(end)['rooms'], plan_body(mid)['rooms'])

    def test_copy_without_a_source_is_refused(self):
        with self.assertRaises(PlanRefused):
            copy_plan(self.course, '2026-27', ODD, 'MID', 'END', self.user, False)

    def test_copy_onto_itself_is_refused(self):
        self.save([self.room(1, 45)])
        with self.assertRaises(PlanRefused):
            copy_plan(self.course, '2026-27', ODD, 'MID', 'MID', self.user, True)

    def test_plan_body_shape(self):
        body = plan_body(self.save([self.room(1, 45)]))
        self.assertEqual(body['updated_by'], 'exam')
        self.assertEqual(body['rooms'][0]['date'], '2026-09-22')
        self.assertEqual(body['rooms'][0]['start_time'], '15:00')

    def rival(self, exam):
        return ExamAttendancePlan.objects.create(
            course=self.course, academic_year='2026-27', semester_type=ODD,
            exam=exam, roll_count=45)

    def first_unaware_of(self, exam):
        """QuerySet.first that cannot see the rival's plan, as in a race."""
        from django.db.models import QuerySet
        real_first = QuerySet.first

        def first(qs):
            row = real_first(qs)
            return None if row is not None and row.exam == exam else row
        return mock.patch.object(QuerySet, 'first', first)

    def test_a_racing_first_save_is_a_conflict_not_a_crash(self):
        self.rival('MID')
        with self.first_unaware_of('MID'):
            with self.assertRaises(PlanChanged):
                self.save([self.room(1, 45)])
        self.assertEqual(ExamAttendancePlan.objects.count(), 1)

    def test_a_racing_first_copy_is_a_conflict_not_a_crash(self):
        self.save([self.room(1, 45)])
        self.rival('END')
        with self.first_unaware_of('END'):
            with self.assertRaises(PlanChanged):
                copy_plan(self.course, '2026-27', ODD, 'MID', 'END',
                          self.user, False)
        self.assertEqual(ExamAttendancePlan.objects.filter(exam='END').count(), 1)


class OverviewTests(TestCase):
    """Every saved room of a term's exam, the unplanned courses, and rooms
    two courses have at the same time."""

    def setUp(self):
        self.batch = make_batch(2023)
        self.semester = Semester.objects.create(
            curriculum=self.batch.curriculum, semester_no=5)
        self.slot = CourseSlot.objects.create(
            semester=self.semester, name='EL', type='Core')
        self.user = User.objects.create_user('exam', password='x')
        self.dl = make_course()
        self.intro = self.course('CS1001', 'Intro')
        self.vlsi = self.course('EC2002', 'VLSI')
        self.enrol(self.dl, ['23BCS%03d' % n for n in range(1, 5)])
        self.enrol(self.intro, ['23BCS%03d' % n for n in range(11, 14)])
        self.enrol(self.vlsi, ['23BEC%03d' % n for n in range(1, 3)])

    def course(self, code, name):
        return Course.objects.create(
            code=code, name=name, credit=3, syllabus='', ref_books='')

    def enrol(self, course, rolls, batch=None, programme='B.Tech'):
        for roll in rolls:
            student = Student.objects.filter(id_id=roll).first()
            if student is None:
                student = make_student(roll, batch=batch or self.batch)
                student.programme = programme
                student.save()
            course_registration.objects.create(
                student_id=student, semester_id=self.semester,
                course_id=course, course_slot_id=self.slot,
                registration_type='Regular', semester_type=ODD,
                session='2026-27')

    @staticmethod
    def room(a, b, name, date='2026-09-22', start='09:00', end='11:00',
             instructor=''):
        return {'from_sno': a, 'to_sno': b, 'room': name, 'date': date,
                'start_time': start, 'end_time': end,
                'instructor_text': instructor}

    def plan(self, course, rooms, exam='MID'):
        save_plan(course, '2026-27', ODD, exam, rooms, self.user, None)

    def test_rooms_by_date_and_time_and_the_unplanned_courses(self):
        self.plan(self.dl, [
            self.room(1, 2, 'L201', date='2026-09-23', instructor='PROF. A'),
            self.room(3, 4, 'L202', start='15:00', end='17:00')])
        self.plan(self.intro, [self.room(1, 3, 'L105')])
        self.plan(self.vlsi, [self.room(1, 2, 'L301')], exam='END')

        data = overview('2026-27', ODD, 'MID', None)

        self.assertEqual((data['courses'], data['planned']), (3, 2))
        self.assertEqual(data['unplanned'], [
            {'id': self.vlsi.id, 'code': 'EC2002', 'name': 'VLSI'}])
        self.assertEqual(
            [(r['room'], r['course']['code'], r['students'])
             for r in data['rooms']],
            [('L105', 'CS1001', 3), ('L202', 'CS8004', 2),
             ('L201', 'CS8004', 2)])
        self.assertEqual(data['rooms'][2], {
            'course': {'id': self.dl.id, 'code': 'CS8004',
                       'name': 'Deep Learning and Applications'},
            'room': 'L201', 'date': '2026-09-23',
            'start_time': '09:00', 'end_time': '11:00',
            'from_sno': 1, 'to_sno': 2, 'students': 2,
            'instructor_text': 'PROF. A', 'roll_changed': False,
            'shares_with': []})

    def test_a_room_two_courses_hold_at_overlapping_times(self):
        self.plan(self.dl, [self.room(1, 4, 'L201')])
        self.plan(self.intro, [self.room(1, 3, ' l201', start='10:00',
                                         end='12:00')])
        # Back to back is not a clash; another day is not either.
        self.plan(self.vlsi, [
            self.room(1, 1, 'L201', start='11:00', end='13:00'),
            self.room(2, 2, 'L201', date='2026-09-23')])

        rows = {(r['course']['code'], r['date'], r['start_time']):
                r['shares_with']
                for r in overview('2026-27', ODD, 'MID', None)['rooms']}

        self.assertEqual(rows, {
            ('CS8004', '2026-09-22', '09:00'): ['CS1001'],
            ('CS1001', '2026-09-22', '10:00'): ['CS8004', 'EC2002'],
            ('EC2002', '2026-09-22', '11:00'): ['CS1001'],
            ('EC2002', '2026-09-23', '09:00'): []})

    def test_marks_a_plan_whose_roll_list_changed_since_saving(self):
        self.plan(self.dl, [self.room(1, 4, 'L201')])
        self.plan(self.intro, [self.room(1, 3, 'L105')])
        self.enrol(self.dl, ['23BCS099'])
        set_status(Student.objects.get(id_id='23BCS011'), 'WITHDRAWN')

        rows = {r['course']['code']: r['roll_changed']
                for r in overview('2026-27', ODD, 'MID', None)['rooms']}

        self.assertEqual(rows, {'CS8004': True, 'CS1001': True})

    def test_a_programme_admin_sees_only_their_courses(self):
        pg = make_pg_batch(2026, 'CSE', 'PG', 'M.Tech')
        thesis = self.course('CS6001', 'Research Methods')
        self.enrol(thesis, ['26MCSA01'], batch=pg, programme='M.Tech')
        self.plan(thesis, [self.room(1, 1, 'L201')])
        self.plan(self.dl, [self.room(1, 4, 'L201')])

        data = overview('2026-27', ODD, 'MID', frozenset({'UG'}))

        self.assertEqual((data['courses'], data['planned']), (3, 1))
        self.assertEqual([r['course']['code'] for r in data['rooms']],
                         ['CS8004'])
        # The room is still shown as taken by the other programme's course.
        self.assertEqual(data['rooms'][0]['shares_with'], ['CS6001'])

    def test_query_count_does_not_grow_with_plans(self):
        def count():
            with CaptureQueriesContext(connection) as ctx:
                overview('2026-27', ODD, 'MID', frozenset({'UG'}))
            return len(ctx)

        self.plan(self.dl, [self.room(1, 4, 'L201')])
        one = count()
        self.plan(self.intro, [self.room(1, 1, 'L105'),
                               self.room(2, 3, 'L106')])
        self.plan(self.vlsi, [self.room(1, 2, 'L301')])
        self.assertEqual(count(), one)

    def test_refuses_summer(self):
        with self.assertRaises(ValueError):
            overview('2026-27', 'Summer Semester', 'MID', None)
