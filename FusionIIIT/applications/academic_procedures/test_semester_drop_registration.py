"""A dropped semester is closed to the student: no registration of any kind."""
import datetime

from django.db import transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from applications.academic_information.semester_drop import DropRefused, record_drop
from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, token_for,
)
from applications.academic_information.utils import allocation_progress, publish_allocations
from applications.academic_procedures.api.views import registration_semester
from applications.globals.models import Designation, HoldsDesignation
from applications.academic_procedures.models import (
    FinalRegistration, InitialRegistration, course_registration,
)
from applications.programme_curriculum.models import Course, CourseSlot, Semester

DROPPED = 'You dropped semester 5 (2025-26); there is no registration for it.'


class DroppedSemesterClosedTests(TestCase):
    def setUp(self):
        self.batch = make_batch(2023, 'ECE')
        self.sem4 = Semester.objects.create(curriculum=self.batch.curriculum, semester_no=4)
        self.sem5 = Semester.objects.create(curriculum=self.batch.curriculum, semester_no=5)
        self.sem6 = Semester.objects.create(curriculum=self.batch.curriculum, semester_no=6)
        self.course = Course.objects.create(code='EC5001', name='Antennas', credit=4,
                                            syllabus='', ref_books='')
        self.slot5 = CourseSlot.objects.create(semester=self.sem5, name='EC5', type='Core')
        self.slot5.courses.add(self.course)
        self.student = make_student('23BEC030', batch=self.batch, semester=4)
        user = self.student.id.user
        HoldsDesignation.objects.create(
            user=user, working=user, held_at=timezone.now(),
            designation=Designation.objects.get_or_create(name='student')[0])
        self.office = make_staff()
        record_drop(self.student, 5, '2025-26', 'Medical leave', self.office)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(self.student.id.user))

    def registration(self, semester, registration_type='Regular'):
        return course_registration(
            student_id=self.student, semester_id=semester, course_id=self.course,
            course_slot_id=self.slot5, registration_type=registration_type,
            semester_type='Odd Semester', session='2026-27')

    def test_pre_registration_page_says_the_semester_was_dropped(self):
        response = self.client.get('/academic-procedures/api/stu/preregistration/')
        self.assertEqual((response.status_code, response.json()), (400, {'error': DROPPED}))

    def test_pre_registration_submit_is_refused(self):
        response = self.client.post('/academic-procedures/api/stu/preregistration/submit/',
                                    {'registrations': [{'slot_id': self.slot5.id,
                                                        'course_id': self.course.id,
                                                        'priority': 1}]},
                                    format='json')
        self.assertEqual((response.status_code, response.json()), (400, {'error': DROPPED}))
        self.assertFalse(InitialRegistration.objects.exists())

    def test_add_request_is_refused_while_in_the_dropped_semester(self):
        self.student.curr_semester_no = 5
        self.student.save()
        response = self.client.post('/academic-procedures/api/stu/add_course/',
                                    {'course_id': self.course.id, 'slot_id': self.slot5.id},
                                    format='json')
        self.assertEqual((response.status_code, response.json()), (400, {'error': DROPPED}))

    def test_pg_and_phd_registration_semester_is_refused(self):
        self.student.curr_semester_no = 5
        self.student.save()
        semester_no, refusal = registration_semester(self.student, datetime.datetime(2025, 7, 20))
        self.assertEqual(semester_no, 5)
        self.assertEqual(refusal.status_code, 400)
        self.assertIn(b'You dropped semester 5', refusal.content)

    def test_guard_refuses_pre_and_final_registration_rows(self):
        for model in (InitialRegistration, FinalRegistration):
            with self.assertRaises(DropRefused, msg=model.__name__), transaction.atomic():
                model.objects.create(student_id=self.student, semester_id=self.sem5,
                                     course_id=self.course, course_slot_id=self.slot5)
        # Another semester is open as before.
        InitialRegistration.objects.create(student_id=self.student, semester_id=self.sem6,
                                           course_id=self.course, course_slot_id=self.slot5)

    def test_guard_refuses_a_regular_registration_and_allows_a_backlog_one(self):
        with self.assertRaises(DropRefused) as caught, transaction.atomic():
            self.registration(self.sem5).save()
        self.assertIn('Backlog', str(caught.exception.detail))
        self.registration(self.sem5, 'Backlog').save()
        self.registration(self.sem6).save()
        self.assertEqual(course_registration.objects.count(), 2)

    def test_allocation_leaves_the_student_out(self):
        # A choice that slipped in by a bulk write is still not allotted.
        InitialRegistration.objects.bulk_create([InitialRegistration(
            student_id=self.student, semester_id=self.sem5, course_id=self.course,
            course_slot_id=self.slot5, priority=1)])
        FinalRegistration.objects.bulk_create([FinalRegistration(
            student_id=self.student, semester_id=self.sem5, course_id=self.course,
            course_slot_id=self.slot5)])
        self.assertEqual(allocation_progress(2023, 5, 'UG')['total_allocations'], 0)
        publish_allocations(2023, 5, 2025, 'UG')
        self.assertFalse(course_registration.objects.exists())

    def test_auth_me_lists_the_live_drops(self):
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.json()['student_info']['dropped_semesters'], [5])
