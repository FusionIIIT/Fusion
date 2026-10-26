from io import BytesIO

import xlwt
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_procedures.models import (
    FinalRegistration,
    InitialRegistration,
    StudentRegistrationChecks,
    course_registration,
)
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.online_cms.models import Student_grades
from applications.programme_curriculum.models import (
    Batch,
    Course,
    CourseSlot,
    Curriculum,
    Discipline,
    Programme,
    Semester,
)


class AllotCourseRepeatTests(TestCase):
    def setUp(self):
        programme = Programme.objects.create(
            category='UG',
            name='Bachelor of Technology',
            programme_begin_year=2024,
        )
        discipline = Discipline.objects.create(
            name='Mechanical Engineering',
            acronym='ME',
        )
        curriculum = Curriculum.objects.create(
            programme=programme,
            name='B.Tech 2024',
            no_of_semester=8,
        )
        self.semester = Semester.objects.create(
            curriculum=curriculum,
            semester_no=4,
        )
        self.batch = Batch.objects.create(
            name='B.Tech',
            discipline=discipline,
            year=2024,
            curriculum=curriculum,
        )
        self.course = Course.objects.create(
            code='PR2002',
            name='Discipline Project',
            credit=2,
            syllabus='',
            ref_books='',
        )
        self.slot = CourseSlot.objects.create(
            semester=self.semester,
            name='PR',
            type='Project',
        )
        self.slot.courses.add(self.course)

        student_user = User.objects.create_user(username='24BME054')
        student_extra = ExtraInfo.objects.create(
            id='24BME054',
            user=student_user,
            user_type='student',
            user_status='PRESENT',
        )
        self.student = Student.objects.create(
            id=student_extra,
            programme='B.Tech',
            batch=2024,
            batch_id=self.batch,
            category='GEN',
            curr_semester_no=4,
        )

        admin = User.objects.create_user(username='academic-admin')
        designation = Designation.objects.create(name='acadadmin')
        HoldsDesignation.objects.create(
            user=admin,
            working=admin,
            designation=designation,
        )
        token = Token.objects.create(user=admin)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def create_previous_registration(self):
        return course_registration.objects.create(
            student_id=self.student,
            semester_id=self.semester,
            course_id=self.course,
            course_slot_id=self.slot,
            registration_type='Regular',
            semester_type='Even Semester',
            session='2025-26',
        )

    def create_grade(self, grade):
        return Student_grades.objects.create(
            course_id=self.course,
            semester=4,
            year=2026,
            roll_no=self.student.pk,
            grade=grade,
            batch=2024,
            academic_year='2025-26',
            semester_type='Even Semester',
            verified=True,
        )

    def upload(self, rows):
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Courses')
        for column, value in enumerate(('Roll Number', 'Slot', 'Course Code')):
            sheet.write(0, column, value)
        for row_number, row in enumerate(rows, start=1):
            for column, value in enumerate(row):
                sheet.write(row_number, column, value)
        content = BytesIO()
        workbook.save(content)
        uploaded = SimpleUploadedFile(
            'allotment.xls',
            content.getvalue(),
            content_type='application/vnd.ms-excel',
        )
        return self.client.post(
            '/academic-procedures/api/acad/allot_courses',
            {
                'batch': str(self.batch.pk),
                'semester': '4',
                'semester_type': 'Summer Semester',
                'academic_year': '2025-26',
                'allotedCourses': uploaded,
            },
            format='multipart',
        )

    def test_cross_term_repeat_without_grade_is_rejected(self):
        self.create_previous_registration()

        response = self.upload([('24BME054', 'PR', 'PR2002')])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(course_registration.objects.count(), 1)
        self.assertFalse(InitialRegistration.objects.exists())
        self.assertFalse(FinalRegistration.objects.exists())
        self.assertFalse(StudentRegistrationChecks.objects.exists())
        self.assertIn('has no grade yet', response.data['reasons'][0])

    def test_failed_cross_term_repeat_becomes_backlog(self):
        self.create_previous_registration()
        self.create_grade('F')

        response = self.upload([('24BME054', 'PR', 'PR2002')])

        self.assertEqual(response.status_code, 200)
        summer = course_registration.objects.get(semester_type='Summer Semester')
        self.assertEqual(summer.registration_type, 'Backlog')
        self.assertEqual(
            InitialRegistration.objects.get().registration_type,
            'Backlog',
        )
        self.assertEqual(
            FinalRegistration.objects.get().registration_type,
            'Backlog',
        )

    def test_low_grade_cross_term_repeat_becomes_improvement(self):
        self.create_previous_registration()
        self.create_grade('C')

        response = self.upload([('24BME054', 'PR', 'PR2002')])

        self.assertEqual(response.status_code, 200)
        summer = course_registration.objects.get(semester_type='Summer Semester')
        self.assertEqual(summer.registration_type, 'Improvement')
        self.assertEqual(
            InitialRegistration.objects.get().registration_type,
            'Improvement',
        )
        self.assertEqual(
            FinalRegistration.objects.get().registration_type,
            'Improvement',
        )

    def test_cleared_course_cannot_be_registered_again(self):
        self.create_previous_registration()
        self.create_grade('B')

        response = self.upload([('24BME054', 'PR', 'PR2002')])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(course_registration.objects.count(), 1)
        self.assertIn('not eligible for repeat', response.data['reasons'][0])

    def test_duplicate_rows_in_one_upload_are_inserted_once(self):
        response = self.upload([
            ('24BME054', 'PR', 'PR2002'),
            ('24BME054', 'PR', 'PR2002'),
        ])

        self.assertEqual(response.status_code, 207)
        self.assertEqual(response.data['inserted_rows'], 1)
        self.assertEqual(response.data['failed_rows_count'], 1)
        self.assertIn('Duplicate row', response.data['reasons'][0])
        self.assertEqual(course_registration.objects.count(), 1)
        self.assertEqual(InitialRegistration.objects.count(), 1)
        self.assertEqual(FinalRegistration.objects.count(), 1)
        self.assertEqual(StudentRegistrationChecks.objects.count(), 1)
