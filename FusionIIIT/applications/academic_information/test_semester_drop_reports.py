"""A semester's lists and reports leave out a student who dropped it."""
from django.test import TestCase
from rest_framework.test import APIClient

from applications.academic_information.semester_drop import record_drop
from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, set_status, token_for,
)
from applications.academic_procedures.models import InitialRegistration
from applications.globals.models import DepartmentInfo, ExtraInfo
from applications.programme_curriculum.models import Course, CourseSlot, Semester


class DroppedSemesterReportTests(TestCase):
    def setUp(self):
        self.batch = make_batch(2023, 'ECE')
        curriculum = self.batch.curriculum
        self.sem5 = Semester.objects.create(curriculum=curriculum, semester_no=5)
        Semester.objects.create(curriculum=curriculum, semester_no=6)
        self.dropped = make_student('23BEC030', batch=self.batch, semester=5)
        self.present = make_student('23BEC031', batch=self.batch, semester=5)
        self.alumnus = make_student('23BEC032', batch=self.batch, semester=5)
        set_status(self.alumnus, 'ALUMNI')
        ExtraInfo.objects.filter(pk__startswith='23BEC').update(
            department=DepartmentInfo.objects.create(name='ECE'))
        office = make_staff()
        record_drop(self.dropped, 5, '2025-26', 'Medical leave', office)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(office))

    def spi_rolls(self, semester):
        response = self.client.get('/aims/api/database/spi-cpi/',
                                   {'batch': 2023, 'semester': semester})
        self.assertEqual(response.status_code, 200, response.content)
        return sorted(r['roll_no'] for r in response.json()['rows'])

    def test_spi_cpi_leaves_the_student_out_of_the_dropped_semester_only(self):
        self.assertEqual(self.spi_rolls(5), ['23BEC031', '23BEC032'])
        self.assertEqual(self.spi_rolls(6), ['23BEC030', '23BEC031', '23BEC032'])

    def test_pre_registration_report_not_registered_list(self):
        course = Course.objects.create(code='EC5001', name='Antennas', credit=4,
                                       syllabus='', ref_books='')
        slot = CourseSlot.objects.create(semester=self.sem5, name='EC5', type='Core')
        InitialRegistration.objects.create(student_id=self.present, semester_id=self.sem5,
                                           course_id=course, course_slot_id=slot, priority=1)
        response = self.client.post('/aims/api/generate_preregistration_report/', {
            'semester_no': 5, 'batch_branch': self.batch.id, 'preview_only': True,
            'status_filter': 'Not Registered'}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        # Neither the student who dropped semester 5 nor the alumnus is missing.
        self.assertNotIn('23BEC030', response.content.decode())
        self.assertNotIn('23BEC032', response.content.decode())

    def test_grade_sheet_form_leaves_the_student_out(self):
        response = self.client.post('/examination/api/generate_gradesheet_form/', {
            'batch': self.batch.id, 'semester': 5}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(sorted(s['id_id'] for s in response.json()['students']),
                         ['23BEC031', '23BEC032'])

    def test_result_sheet_leaves_the_student_out(self):
        from io import BytesIO

        import openpyxl

        from applications.examination.models import Student_grades
        course = Course.objects.create(code='EC5001', name='Antennas', credit=4,
                                       syllabus='', ref_books='')
        Student_grades.objects.create(
            course_id=course, semester=5, year=2025, roll_no='23BEC031', grade='B',
            batch=2023, academic_year='2025-26', semester_type='Odd Semester', verified=True)
        response = self.client.post('/examination/api/generate_result/', {
            'batch': self.batch.id, 'semester': 5, 'semester_type': 'Odd Semester'},
            format='json')
        self.assertEqual(response.status_code, 200, response.content[:300])
        book = openpyxl.load_workbook(BytesIO(response.content))
        cells = {str(c.value) for row in book.active.iter_rows() for c in row}
        self.assertIn('23BEC031', cells)
        self.assertNotIn('23BEC030', cells)

    def test_summer_result_sheet_of_a_dropped_even_semester_keeps_the_student(self):
        from io import BytesIO

        import openpyxl

        from applications.examination.models import Student_grades
        record_drop(self.dropped, 6, '2025-26', 'Medical leave', make_staff('office2'))
        course = Course.objects.create(code='EC3001', name='Circuits', credit=4,
                                       syllabus='', ref_books='')
        Student_grades.objects.create(
            course_id=course, semester=6, year=2026, roll_no='23BEC030', grade='C',
            batch=2023, academic_year='2025-26', semester_type='Summer Semester',
            verified=True)
        response = self.client.post('/examination/api/generate_result/', {
            'batch': self.batch.id, 'semester': 6, 'semester_type': 'Summer Semester'},
            format='json')
        self.assertEqual(response.status_code, 200, response.content[:300])
        book = openpyxl.load_workbook(BytesIO(response.content))
        self.assertIn('23BEC030', {str(c.value) for row in book.active.iter_rows() for c in row})
