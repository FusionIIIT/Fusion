"""Alumni are left out of allocation, promotion and bulk updates."""
from io import BytesIO

import xlwt
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, set_status, token_for,
)
from applications.academic_information.utils import (
    allocation_progress, publish_allocations, random_algo,
)
from applications.academic_procedures.models import (
    FinalRegistration, InitialRegistration, TeachingCreditRegistration, course_registration,
)
from applications.examination.api.views import reset_resubmit_for_roster
from applications.examination.models import (
    PublishedResultStudent, ResultAnnouncement, Student_grades,
)
from applications.programme_curriculum.models import (
    Course, CourseSlot, Semester, TeachingCreditSlot,
)


class AlumniBulkPathTests(TestCase):
    def setUp(self):
        self.batch = make_batch(2021)
        curriculum = self.batch.curriculum
        self.sem5 = Semester.objects.create(curriculum=curriculum, semester_no=5)
        self.sem6 = Semester.objects.create(curriculum=curriculum, semester_no=6)
        self.course = Course.objects.create(code='OE5001', name='Elective', credit=3,
                                            syllabus='', ref_books='', max_seats=100)
        self.slot = CourseSlot.objects.create(semester=self.sem5, name='OE1',
                                              type='Open Elective')
        self.slot.courses.add(self.course)
        # Both made their choices while still students; one has since graduated.
        self.alumnus = make_student('21BCS001', batch=self.batch, semester=5)
        self.present = make_student('21BCS002', batch=self.batch, semester=5)
        for student in (self.alumnus, self.present):
            InitialRegistration.objects.create(
                student_id=student, semester_id=self.sem5, course_id=self.course,
                course_slot_id=self.slot, priority=1, registration_type='Regular')
        set_status(self.alumnus, 'ALUMNI')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(make_staff()))

    def final_rolls(self):
        return sorted(FinalRegistration.objects.values_list('student_id_id', flat=True))

    # Allocation ---------------------------------------------------------

    def test_random_algo_skips_alumni(self):
        random_algo(2021, 5, 2023, [self.slot.id], 'UG')
        self.assertEqual(self.final_rolls(), ['21BCS002'])

    def test_allocation_progress_ignores_alumni_choices(self):
        random_algo(2021, 5, 2023, [self.slot.id], 'UG')
        progress = allocation_progress(2021, 5, 'UG')
        self.assertEqual(progress['remaining_students'], 0)

    def test_publish_allocations_skips_alumni(self):
        set_status(self.alumnus, 'PRESENT')
        for student in (self.alumnus, self.present):
            FinalRegistration.objects.create(
                student_id=student, semester_id=self.sem5, course_id=self.course,
                course_slot_id=self.slot, registration_type='Regular')
        set_status(self.alumnus, 'ALUMNI')
        publish_allocations(2021, 5, 2023, 'UG')
        self.assertEqual(
            sorted(course_registration.objects.values_list('student_id_id', flat=True)),
            ['21BCS002'])
        self.assertFalse(FinalRegistration.objects.get(student_id='21BCS001').verified)

    # Registration -------------------------------------------------------

    def test_verify_registration_refuses_alumni(self):
        response = self.client.post(
            '/academic-procedures/api/acad/verify_registration',
            {'status_req': 'accept', 'student_id': '21BCS001'}, format='json')
        self.assertEqual(response.status_code, 409, response.content)
        self.assertIn('21BCS001 is Alumni', response.content.decode())

    def test_allot_courses_reports_the_alumni_row(self):
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Courses')
        for column, value in enumerate(('Roll Number', 'Slot', 'Course Code')):
            sheet.write(0, column, value)
        for row, roll in enumerate(('21BCS001', '21BCS002'), start=1):
            for column, value in enumerate((roll, 'OE1', 'OE5001')):
                sheet.write(row, column, value)
        content = BytesIO()
        workbook.save(content)
        response = self.client.post(
            '/academic-procedures/api/acad/allot_courses',
            {'batch': str(self.batch.pk), 'semester': '5', 'semester_type': 'Odd Semester',
             'academic_year': '2023-24',
             'allotedCourses': SimpleUploadedFile('a.xls', content.getvalue(),
                                                  content_type='application/vnd.ms-excel')},
            format='multipart')
        # 207: the upload's existing answer when some rows went in and some failed.
        self.assertEqual(response.status_code, 207, response.content)
        self.assertIn('21BCS001 is Alumni', response.content.decode())
        self.assertEqual(
            sorted(course_registration.objects.values_list('student_id_id', flat=True)),
            ['21BCS002'])

    # Promotion ----------------------------------------------------------

    def test_promotion_list_has_status(self):
        response = self.client.get('/academic-procedures/api/acad/promote/students/',
                                   {'batch_id': self.batch.pk})
        self.assertEqual({r['id']: r['status'] for r in response.json()},
                         {'21BCS001': 'ALUMNI', '21BCS002': 'PRESENT'})

    def test_promote_mixed_batch(self):
        response = self.client.post('/academic-procedures/api/acad/promote/apply/',
                                    ['21BCS001', '21BCS002'], format='json')
        self.assertEqual(response.status_code, 207, response.content)
        self.assertEqual(response.json()['errors'],
                         [{'index': 0, 'detail': '21BCS001 is Alumni; not promoted.'}])
        self.assertEqual(Student.objects.get(pk='21BCS001').curr_semester_no, 5)
        self.assertEqual(Student.objects.get(pk='21BCS002').curr_semester_no, 6)

    def test_demote_skips_alumni(self):
        response = self.client.post('/academic-procedures/api/acad/demote/apply/',
                                    ['21BCS001'], format='json')
        self.assertEqual(response.json()['errors'],
                         [{'index': 0, 'detail': '21BCS001 is Alumni; not moved back.'}])
        self.assertEqual(Student.objects.get(pk='21BCS001').curr_semester_no, 5)

    # Results and PhD bulk updates ----------------------------------------

    def test_publish_result_refuses_changing_alumni(self):
        announcement = ResultAnnouncement.objects.create(
            batch=self.batch, semester=5, semester_type='Odd Semester')
        response = self.client.post('/examination/api/publish-result-selected/',
                                    {'id': announcement.pk, 'Role': 'acadadmin',
                                     'roll_numbers': ['21BCS001', '21BCS002']}, format='json')
        self.assertEqual(response.status_code, 409, response.content)
        self.assertFalse(PublishedResultStudent.objects.exists())

    def test_publish_result_for_present_students_only_is_allowed(self):
        announcement = ResultAnnouncement.objects.create(
            batch=self.batch, semester=5, semester_type='Odd Semester')
        response = self.client.post('/examination/api/publish-result-selected/',
                                    {'id': announcement.pk, 'Role': 'acadadmin',
                                     'roll_numbers': ['21BCS002']}, format='json')
        self.assertEqual(response.status_code, 200, response.content)

    def test_teaching_credit_verify_refuses_alumni(self):
        slot = TeachingCreditSlot.objects.create(semester=self.sem5, name='TW')
        set_status(self.alumnus, 'PRESENT')
        registration = TeachingCreditRegistration.objects.create(
            student=self.alumnus, teaching_credit_slot=slot, semester=self.sem5)
        set_status(self.alumnus, 'ALUMNI')
        response = self.client.post(
            '/academic-procedures/api/acadadmin/teaching-credit-enrollments/verify/',
            {'ids': [registration.pk]}, format='json')
        self.assertEqual(response.status_code, 409, response.content)
        registration.refresh_from_db()
        self.assertEqual(registration.status, 'pending')

    # Section assignment and grade upload -----------------------------------

    def test_assign_section_skips_alumni(self):
        response = self.client.post('/aims/api/section/assign/',
                                    {'roll_numbers': ['21BCS001', '21BCS002'], 'section': 'B'},
                                    format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['skipped'], ['21BCS001'])
        self.assertIsNone(Student.objects.get(pk='21BCS001').section)
        self.assertEqual(Student.objects.get(pk='21BCS002').section, 'B')

    def test_grade_upload_reset_leaves_alumni_rows(self):
        set_status(self.alumnus, 'PRESENT')
        for roll in ('21BCS001', '21BCS002'):
            Student_grades.objects.create(
                course_id=self.course, semester=5, year=2023, roll_no=roll, grade='B',
                batch=2021, academic_year='2023-24', semester_type='Odd Semester',
                reSubmit=True)
        set_status(self.alumnus, 'ALUMNI')
        reset_resubmit_for_roster(self.course.id, '2023-24', 'Odd Semester',
                                  ['21BCS001', '21BCS002'])
        self.assertEqual(
            dict(Student_grades.objects.values_list('roll_no', 'reSubmit')),
            {'21BCS001': True, '21BCS002': False})
