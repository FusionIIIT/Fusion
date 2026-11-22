"""The office's later adds of a dropped semester's courses are Backlog."""
from io import BytesIO

import xlwt
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from applications.academic_information.semester_drop import dropped_semester_course, record_drop
from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, token_for,
)
from applications.academic_procedures.models import CourseAddRequest, course_registration
from applications.programme_curriculum.models import Course, CourseSlot, Semester


def course(code):
    return Course.objects.create(code=code, name=code, credit=4, syllabus='',
                                 ref_books='', max_seats=100)


class DroppedSemesterBacklogTests(TestCase):
    def setUp(self):
        self.batch = make_batch(2023, 'ECE')
        curriculum = self.batch.curriculum
        self.sem5 = Semester.objects.create(curriculum=curriculum, semester_no=5)
        self.sem7 = Semester.objects.create(curriculum=curriculum, semester_no=7)
        self.core5 = course('EC5001')
        self.elective = course('OE4001')   # offered in semester 5 and 7
        self.core7 = course('EC7001')
        self.slot5 = CourseSlot.objects.create(semester=self.sem5, name='EC5', type='Core')
        self.slot5.courses.add(self.core5)
        self.oe5 = CourseSlot.objects.create(semester=self.sem5, name='OE5', type='Open Elective')
        self.oe5.courses.add(self.elective)
        self.slot7 = CourseSlot.objects.create(semester=self.sem7, name='EC7', type='Core')
        self.slot7.courses.add(self.core7)
        self.oe7 = CourseSlot.objects.create(semester=self.sem7, name='OE7', type='Open Elective')
        self.oe7.courses.add(self.elective)
        self.student = make_student('23BEC030', batch=self.batch, semester=7)
        self.other = make_student('23BEC031', batch=self.batch, semester=7)
        office = make_staff()
        record_drop(self.student, 5, '2025-26', 'Medical leave', office)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(office))

    def add(self, semester, slot, chosen, registration_type='Regular'):
        return self.client.post('/academic-procedures/api/acad/addCourse/', {
            'roll_no': '23BEC030', 'semester_id': semester.id, 'courseslot_id': slot.id,
            'course_id': chosen.id, 'academic_year': '2026-27',
            'registration_type': registration_type, 'semester_type': 'Odd Semester',
        }, format='json')

    def type_of(self, chosen, roll='23BEC030'):
        return course_registration.objects.get(student_id=roll, course_id=chosen).registration_type

    def test_rule(self):
        self.assertEqual(dropped_semester_course(self.student, self.core5), 5)
        self.assertEqual(dropped_semester_course(self.student, self.core5, self.slot5), 5)
        self.assertIsNone(dropped_semester_course(self.student, self.core7, self.slot7))
        self.assertIsNone(dropped_semester_course(self.student, self.elective, self.oe7))
        self.assertIsNone(dropped_semester_course(self.other, self.core5, self.slot5))

    def test_add_into_the_dropped_semesters_slot_is_backlog(self):
        response = self.add(self.sem5, self.slot5, self.core5)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['message'],
                         'Course added as Backlog: 23BEC030 dropped semester 5.')
        self.assertEqual(self.type_of(self.core5), 'Backlog')

    def test_add_of_a_dropped_semester_course_through_a_later_slot_is_backlog(self):
        response = self.add(self.sem7, self.slot7, self.core5)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.type_of(self.core5), 'Backlog')

    def test_an_elective_of_both_semesters_added_through_the_later_slot_stays_regular(self):
        response = self.add(self.sem7, self.oe7, self.elective)
        self.assertEqual((response.status_code, response.json()['message']),
                         (200, 'Course added successfully'))
        self.assertEqual(self.type_of(self.elective), 'Regular')

    def test_another_chosen_type_is_kept(self):
        self.add(self.sem5, self.slot5, self.core5, 'Audit')
        self.assertEqual(self.type_of(self.core5), 'Audit')

    def sheet(self, rows):
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Courses')
        for column, value in enumerate(('Roll Number', 'Slot', 'Course Code')):
            sheet.write(0, column, value)
        for row, values in enumerate(rows, start=1):
            for column, value in enumerate(values):
                sheet.write(row, column, value)
        content = BytesIO()
        workbook.save(content)
        return SimpleUploadedFile('a.xls', content.getvalue(),
                                  content_type='application/vnd.ms-excel')

    def test_allot_courses_refuses_the_dropped_semester_row_only(self):
        response = self.client.post('/academic-procedures/api/acad/allot_courses', {
            'batch': str(self.batch.pk), 'semester': '5', 'semester_type': 'Odd Semester',
            'academic_year': '2025-26',
            'allotedCourses': self.sheet([('23BEC030', 'EC5', 'EC5001'),
                                          ('23BEC031', 'EC5', 'EC5001')]),
        }, format='multipart')
        self.assertEqual(response.status_code, 207, response.content)
        self.assertIn('23BEC030 dropped semester 5', response.content.decode())
        self.assertEqual(list(course_registration.objects.values_list('student_id', flat=True)),
                         ['23BEC031'])

    def test_approved_add_request_of_a_dropped_semester_course_is_backlog(self):
        add_request = CourseAddRequest.objects.create(
            student=self.student, academic_year='2026-27', semester_type='Odd Semester',
            course_slot=self.slot5, course=self.core5)
        response = self.client.post('/academic-procedures/api/acad/add-requests/approve/',
                                    {'request_ids': [add_request.id], 'action': 'approve'},
                                    format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.type_of(self.core5), 'Backlog')
