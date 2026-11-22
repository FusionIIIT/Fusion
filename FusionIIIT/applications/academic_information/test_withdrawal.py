from django.test import TestCase

from applications.academic_information.models import StudentStatusHistory
from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, set_status,
)
from applications.academic_information.withdrawal import (
    WithdrawalRefused, readmit, withdraw, withdrawal_blockers,
)
from applications.academic_procedures.models import (
    FinalRegistration, InitialRegistration, course_registration,
)
from applications.examination.models import Student_grades
from applications.globals.models import ExtraInfo
from applications.programme_curriculum.models import Course, CourseSlot, Semester


class WithdrawalTests(TestCase):
    def setUp(self):
        batch = make_batch(2023, 'ECE')
        self.sem4 = Semester.objects.create(curriculum=batch.curriculum, semester_no=4)
        self.sem5 = Semester.objects.create(curriculum=batch.curriculum, semester_no=5)
        self.course = Course.objects.create(code='EC4001', name='Signals', credit=4,
                                            syllabus='', ref_books='')
        self.slot = CourseSlot.objects.create(semester=self.sem4, name='EC', type='Core')
        self.student = make_student('23BEC020', batch=batch, semester=4)
        self.office = make_staff()

    def status(self):
        return ExtraInfo.objects.get(pk='23BEC020').user_status

    def register(self, semester, session='2024-25', sem_type='Even Semester'):
        return course_registration.objects.create(
            student_id=self.student, semester_id=semester, course_id=self.course,
            course_slot_id=self.slot, registration_type='Regular',
            semester_type=sem_type, session=session)

    def grade(self, academic_year='2024-25', sem_type='Even Semester', verified=True):
        Student_grades.objects.create(
            course_id=self.course, semester=4, year=2025, roll_no='23BEC020', grade='B',
            batch=2023, academic_year=academic_year, semester_type=sem_type,
            verified=verified)

    def test_withdraw_locks_the_student_and_records_it(self):
        entry = withdraw(self.student, 'Left for a job', self.office)
        self.assertEqual(self.status(), 'WITHDRAWN')
        self.assertEqual(
            (entry.action, entry.previous_status, entry.new_status, entry.reason,
             entry.semester_no, entry.performed_by),
            ('withdraw', 'PRESENT', 'WITHDRAWN', 'Left for a job', 4, self.office))

    def test_a_reason_is_required(self):
        with self.assertRaises(WithdrawalRefused):
            withdraw(self.student, '  ', self.office)
        self.assertEqual(self.status(), 'PRESENT')

    def test_only_a_present_student_can_be_withdrawn(self):
        set_status(self.student, 'ALUMNI')
        with self.assertRaises(WithdrawalRefused) as caught:
            withdraw(self.student, 'x', self.office)
        self.assertIn('Alumni', str(caught.exception.detail))

    def test_ungraded_registration_of_the_current_semester_blocks(self):
        self.register(self.sem4)
        self.assertEqual(withdrawal_blockers(self.student)['ungraded'], ['EC4001'])
        with self.assertRaises(WithdrawalRefused) as caught:
            withdraw(self.student, 'x', self.office)
        self.assertEqual(caught.exception.blockers['ungraded'], ['EC4001'])
        self.assertEqual(self.status(), 'PRESENT')

    def test_a_graded_registration_does_not_block_whatever_the_term_type(self):
        # A retake filed under the other term type of the same year still counts.
        self.register(self.sem4)
        self.grade(sem_type='Odd Semester')
        self.assertEqual(withdrawal_blockers(self.student)['ungraded'], [])

    def test_older_semesters_do_not_block(self):
        self.student.curr_semester_no = 5
        self.student.save()
        self.register(self.sem4)
        self.assertEqual(withdrawal_blockers(self.student)['ungraded'], [])

    def test_pending_pre_and_final_registration_block(self):
        InitialRegistration.objects.create(student_id=self.student, semester_id=self.sem5,
                                           course_id=self.course, priority=1)
        FinalRegistration.objects.create(student_id=self.student, semester_id=self.sem5,
                                         course_id=self.course)
        self.assertEqual(withdrawal_blockers(self.student),
                         {'ungraded': [], 'unverified': [], 'pre_registration': [5],
                          'final_registration': [5]})

    def test_readmit_restores_and_records_it(self):
        withdraw(self.student, 'Left', self.office)
        entry = readmit(self.student, 'Came back', self.office)
        self.assertEqual(self.status(), 'PRESENT')
        self.assertEqual((entry.action, entry.previous_status, entry.new_status),
                         ('readmit', 'WITHDRAWN', 'PRESENT'))
        self.assertEqual(
            list(StudentStatusHistory.objects.filter(student=self.student)
                 .values_list('action', flat=True)),
            ['readmit', 'withdraw'])

    def test_only_a_withdrawn_student_can_be_readmitted(self):
        with self.assertRaises(WithdrawalRefused):
            readmit(self.student, 'x', self.office)
        set_status(self.student, 'ALUMNI')
        with self.assertRaises(WithdrawalRefused):
            readmit(self.student, 'x', self.office)

    def test_a_grade_not_yet_verified_blocks(self):
        # Verification saves every row of the course; a locked student's row
        # would stop it for the whole class.
        self.register(self.sem4)
        self.grade(verified=False)
        blockers = withdrawal_blockers(self.student)
        self.assertEqual((blockers['ungraded'], blockers['unverified']), ([], ['EC4001']))

    def test_current_semester_choices_block_before_registration(self):
        # A first-semester student (or PG registering into the semester they
        # are in) chooses courses for their current semester.
        InitialRegistration.objects.create(student_id=self.student, semester_id=self.sem4,
                                           course_id=self.course, priority=1)
        self.assertEqual(withdrawal_blockers(self.student)['pre_registration'], [4])
        self.register(self.sem4)
        self.grade()
        self.assertEqual(withdrawal_blockers(self.student)['pre_registration'], [])
