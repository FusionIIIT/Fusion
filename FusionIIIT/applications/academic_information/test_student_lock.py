from django.db import transaction
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, set_status, token_for,
)
from applications.academic_information.student_lock import guarded_models
from applications.academic_information.student_status import StudentLocked
from applications.academic_procedures.models import (
    BonafideCertificate, CourseAddRequest, FinalRegistration, InitialRegistration,
    ThesisTopic, backlog_course, course_registration, course_replacement,
)
from applications.examination.models import Student_grades
from applications.programme_curriculum.models import Course, CourseSlot, Semester


class StudentLockTests(TestCase):
    def setUp(self):
        batch = make_batch(2021)
        self.semester = Semester.objects.create(curriculum=batch.curriculum, semester_no=8)
        self.course = Course.objects.create(code='CS4001', name='Capstone', credit=4,
                                            syllabus='', ref_books='')
        self.slot = CourseSlot.objects.create(semester=self.semester, name='CS', type='Core')
        self.alumnus = make_student('21BCS001', status='ALUMNI', batch=batch)
        self.present = make_student('21BCS002', status='PRESENT', batch=batch)
        self.admin = make_staff()

    def register(self, student):
        return course_registration.objects.create(
            student_id=student, semester_id=self.semester, course_id=self.course,
            course_slot_id=self.slot, registration_type='Regular',
            semester_type='Even Semester', session='2024-25')

    def grade(self, roll):
        return Student_grades.objects.create(
            course_id=self.course, semester=8, year=2025, roll_no=roll, grade='A',
            batch=2021, academic_year='2024-25', semester_type='Even Semester')

    def certificate(self, student, certificate_type):
        return BonafideCertificate.objects.create(
            student=student, purpose='Other', custom_purpose='x', issued_by=self.admin,
            certificate_type=certificate_type)

    def test_course_registration_refused_for_alumnus(self):
        with self.assertRaises(StudentLocked):
            self.register(self.alumnus)
        self.assertFalse(course_registration.objects.filter(student_id=self.alumnus).exists())

    def test_course_registration_allowed_for_present(self):
        self.register(self.present)

    def test_update_and_delete_refused(self):
        registration = self.register(self.present)
        set_status(self.present, 'ALUMNI')
        registration.registration_type = 'Backlog'
        with self.assertRaises(StudentLocked):
            registration.save()
        # Django runs pre_delete inside its own atomic block; the savepoint
        # keeps the test's transaction usable after the refusal.
        with self.assertRaises(StudentLocked), transaction.atomic():
            registration.delete()
        with self.assertRaises(StudentLocked), transaction.atomic():
            course_registration.objects.filter(pk=registration.pk).delete()
        self.assertEqual(course_registration.objects.get(pk=registration.pk).registration_type,
                         'Regular')

    def test_moving_a_record_off_an_alumnus_is_refused(self):
        registration = self.register(self.present)
        set_status(self.present, 'ALUMNI')
        other = make_student('21BCS003', status='PRESENT', batch=self.present.batch_id)
        registration.student_id = other
        with self.assertRaises(StudentLocked):
            registration.save()

    def test_student_save_refused(self):
        self.alumnus.curr_semester_no = 9
        with self.assertRaises(StudentLocked):
            self.alumnus.save()
        self.assertEqual(Student.objects.get(pk='21BCS001').curr_semester_no, 8)

    def test_deleting_the_student_is_refused(self):
        with self.assertRaises(StudentLocked), transaction.atomic():
            self.alumnus.id.delete()
        self.assertTrue(Student.objects.filter(pk='21BCS001').exists())

    def test_grade_create_and_update_refused(self):
        with self.assertRaises(StudentLocked):
            self.grade('21BCS001')
        grade = self.grade('21BCS002')
        set_status(self.present, 'ALUMNI')
        grade.grade = 'B'
        with self.assertRaises(StudentLocked):
            grade.save()

    def test_moi_and_pointer_certificates_allowed_bonafide_refused(self):
        self.certificate(self.alumnus, 'medium_of_instruction')
        self.certificate(self.alumnus, 'pointer_conv')
        with self.assertRaises(StudentLocked):
            self.certificate(self.alumnus, 'bonafide')

    def test_restore_unlocks(self):
        set_status(self.alumnus, 'PRESENT')
        self.register(self.alumnus)
        set_status(self.alumnus, 'ALUMNI')
        with self.assertRaises(StudentLocked):
            self.register(self.alumnus)

    def test_guarded_models_cover_known(self):
        guarded = set(guarded_models())
        for model in (Student, course_registration, FinalRegistration, InitialRegistration,
                      backlog_course, CourseAddRequest, ThesisTopic, Student_grades,
                      BonafideCertificate):
            self.assertIn(model, guarded, model.__name__)
        # Linked through a registration, not to the student directly.
        self.assertNotIn(course_replacement, guarded)


class StudentLockApiTests(TransactionTestCase):
    """A real request, outside a test transaction, as in production."""

    def setUp(self):
        StudentLockTests.setUp(self)

    register = StudentLockTests.register

    def test_api_refuses_with_the_message(self):
        set_status(self.alumnus, 'PRESENT')
        registration = self.register(self.alumnus)
        set_status(self.alumnus, 'ALUMNI')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(self.admin))
        response = client.post('/academic-procedures/api/acad/verify_course/drop/',
                               {'id': registration.pk, 'roll_no': '21BCS001'}, format='json')
        self.assertIn(response.status_code, (400, 409))
        self.assertIn('21BCS001 is Alumni', response.content.decode())
        self.assertTrue(course_registration.objects.filter(pk=registration.pk).exists())
