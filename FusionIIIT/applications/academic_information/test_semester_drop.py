from django.db import transaction
from django.test import TestCase

from applications.academic_information.models import SemesterDrop, Student
from applications.academic_information.semester_drop import (
    DropRefused, cancel_drop, drop_blockers, live_drop_semesters, not_dropped_q, record_drop,
)
from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, set_status,
)
from applications.academic_information.student_status import StudentLocked
from applications.academic_procedures.models import (
    FinalRegistration, InitialRegistration, course_registration,
)
from applications.programme_curriculum.models import Course, CourseSlot, Semester


class SemesterDropTests(TestCase):
    def setUp(self):
        batch = make_batch(2023, 'ECE')
        self.sem4 = Semester.objects.create(curriculum=batch.curriculum, semester_no=4)
        self.sem5 = Semester.objects.create(curriculum=batch.curriculum, semester_no=5)
        self.course = Course.objects.create(code='EC5001', name='Antennas', credit=4,
                                            syllabus='', ref_books='')
        self.slot = CourseSlot.objects.create(semester=self.sem5, name='EC5', type='Core')
        self.student = make_student('23BEC030', batch=batch, semester=4)
        self.office = make_staff()

    def drop(self, semester_no=5, year='2025-26', reason='Medical leave'):
        return record_drop(self.student, semester_no, year, reason, self.office)

    def test_records_a_drop(self):
        drop = self.drop()
        self.assertEqual(
            (drop.student_id, drop.semester_no, drop.academic_year, drop.reason,
             drop.recorded_by, drop.cancelled_at),
            ('23BEC030', 5, '2025-26', 'Medical leave', self.office, None))
        self.assertEqual(live_drop_semesters(self.student), {5})

    def test_a_reason_is_required(self):
        with self.assertRaises(DropRefused):
            self.drop(reason='  ')
        self.assertFalse(SemesterDrop.objects.exists())

    def test_the_academic_year_must_be_a_session(self):
        for year in ('2025', '2025-27', 'abcd-ef', ''):
            with self.assertRaises(DropRefused, msg=year):
                self.drop(year=year)

    def test_the_semester_must_be_in_the_curriculum(self):
        with self.assertRaises(DropRefused) as caught:
            self.drop(semester_no=9)
        self.assertIn('semester 9', str(caught.exception.detail))

    def test_a_second_live_drop_of_the_same_semester_is_refused(self):
        self.drop()
        with self.assertRaises(DropRefused) as caught:
            self.drop(reason='again')
        self.assertIn('already', str(caught.exception.detail))

    def test_a_registration_of_that_semester_blocks(self):
        course_registration.objects.create(
            student_id=self.student, semester_id=self.sem5, course_id=self.course,
            course_slot_id=self.slot, registration_type='Regular',
            semester_type='Odd Semester', session='2025-26')
        self.assertEqual(drop_blockers(self.student, 5)['registrations'], ['EC5001'])
        with self.assertRaises(DropRefused) as caught:
            self.drop()
        self.assertEqual(caught.exception.blockers['registrations'], ['EC5001'])
        self.assertFalse(SemesterDrop.objects.exists())

    def test_pre_and_final_registration_of_that_semester_block(self):
        InitialRegistration.objects.create(
            student_id=self.student, semester_id=self.sem5, course_id=self.course,
            course_slot_id=self.slot, priority=1)
        FinalRegistration.objects.create(
            student_id=self.student, semester_id=self.sem5, course_id=self.course,
            course_slot_id=self.slot)
        blockers = drop_blockers(self.student, 5)
        self.assertEqual((blockers['pre_registration'], blockers['final_registration']),
                         (True, True))
        with self.assertRaises(DropRefused):
            self.drop()

    def test_other_semesters_do_not_block(self):
        course_registration.objects.create(
            student_id=self.student, semester_id=self.sem4, course_id=self.course,
            course_slot_id=self.slot, registration_type='Regular',
            semester_type='Even Semester', session='2024-25')
        self.assertEqual(drop_blockers(self.student, 5),
                         {'registrations': [], 'pre_registration': False,
                          'final_registration': False})
        self.drop()

    def test_cancel_keeps_the_drop_with_who_when_and_why(self):
        drop = self.drop()
        cancelled = cancel_drop(self.student, drop.id, 'Recorded by mistake', self.office)
        self.assertEqual((cancelled.cancelled_by, cancelled.cancel_reason),
                         (self.office, 'Recorded by mistake'))
        self.assertIsNotNone(cancelled.cancelled_at)
        self.assertEqual(SemesterDrop.objects.count(), 1)
        self.assertEqual(live_drop_semesters(self.student), set())
        # The semester can be dropped again afterwards.
        self.drop(reason='Medical leave, confirmed')
        self.assertEqual(live_drop_semesters(self.student), {5})

    def test_cancel_needs_a_reason_and_a_live_drop_of_that_student(self):
        drop = self.drop()
        with self.assertRaises(DropRefused):
            cancel_drop(self.student, drop.id, ' ', self.office)
        other = make_student('23BEC031', batch=self.student.batch_id, semester=4)
        with self.assertRaises(DropRefused):
            cancel_drop(other, drop.id, 'x', self.office)
        cancel_drop(self.student, drop.id, 'x', self.office)
        with self.assertRaises(DropRefused):
            cancel_drop(self.student, drop.id, 'x', self.office)

    def test_a_locked_student_is_refused(self):
        set_status(self.student, 'WITHDRAWN')
        with self.assertRaises(StudentLocked), transaction.atomic():
            self.drop()

    def test_not_dropped_q_filters_only_the_dropped_semester(self):
        other = make_student('23BEC031', batch=self.student.batch_id, semester=4)
        self.drop()
        rolls = lambda n: set(Student.objects.filter(  # noqa: E731
            not_dropped_q('', n), batch=2023).values_list('id_id', flat=True))
        self.assertEqual(rolls(5), {other.id_id})
        self.assertEqual(rolls(6), {other.id_id, '23BEC030'})
        self.assertEqual(rolls('Summer'), {other.id_id, '23BEC030'})
