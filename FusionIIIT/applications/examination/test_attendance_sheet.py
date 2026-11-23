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
    course_in_scope, courses_for, instructor_names, roll_list, section_wise,
    term_year)
from applications.globals.models import ExtraInfo, Faculty
from applications.programme_curriculum.models import (
    Batch, Course, CourseInstructor, CourseSlot, Curriculum, Discipline,
    Programme, Semester)
from applications.examination.models import ExamAttendancePlan, ExamAttendanceRoom
import datetime


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
