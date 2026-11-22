"""The admission Withdrawal / Not reported / Pending and delete are for
students who never joined: they delete the academic record, so they are
refused once the student has registrations or grades."""
import json

from django.test import TestCase
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, token_for,
)
from applications.academic_procedures.models import course_registration
from applications.programme_curriculum.models import Course, CourseSlot, Semester
from applications.programme_curriculum.models_student_management import StudentBatchUpload

API = '/programme_curriculum/api/'
REFUSED = ('23BEC020 has course registrations or grades. Use Withdraw on the Student '
           'Status page instead; nothing was changed.')


class AdmissionWithdrawalGuardTests(TestCase):
    def setUp(self):
        batch = make_batch(2023, 'ECE')
        self.student = make_student('23BEC020', batch=batch, semester=4)
        semester = Semester.objects.create(curriculum=batch.curriculum, semester_no=4)
        course_registration.objects.create(
            student_id=self.student, semester_id=semester,
            course_id=Course.objects.create(code='EC4001', name='Signals', credit=4,
                                            syllabus='', ref_books=''),
            course_slot_id=CourseSlot.objects.create(semester=semester, name='EC', type='Core'),
            registration_type='Regular', semester_type='Even Semester', session='2024-25')
        self.upload = self.admission('23BEC020')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(make_staff()))

    @staticmethod
    def admission(roll):
        return StudentBatchUpload.objects.create(
            name='Asha Rao', father_name='F', mother_name='M', gender='Female', category='GEN',
            address='Somewhere', branch='Electronics and Communication Engineering',
            programme_type='ug', roll_number=roll, reported_status='REPORTED')

    def assert_untouched(self):
        self.assertTrue(Student.objects.filter(pk='23BEC020').exists())
        self.assertEqual(course_registration.objects.filter(student_id='23BEC020').count(), 1)
        self.upload.refresh_from_db()
        self.assertEqual(self.upload.reported_status, 'REPORTED')

    def test_single_withdrawal_refused(self):
        response = self.client.post(API + 'update_student_status/',
                                    {'studentId': self.upload.id, 'reportedStatus': 'WITHDRAWAL'},
                                    format='json')
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(response.json()['message'], REFUSED)
        self.assert_untouched()

    def test_bulk_reports_the_row(self):
        response = self.client.post(API + 'bulk_update_student_status/',
                                    {'student_ids': [self.upload.id],
                                     'reported_status': 'NOT_REPORTED'}, format='json')
        self.assertIn(REFUSED, response.content.decode())
        self.assert_untouched()

    def test_crud_update_refused(self):
        response = self.client.put(API + f'students/{self.upload.id}/update_status/',
                                   json.dumps({'reported_status': 'WITHDRAWAL'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400, response.content)
        self.assert_untouched()

    def test_delete_refused(self):
        response = self.client.post(API + f'student/{self.upload.id}/delete/')
        self.assertEqual(response.status_code, 400, response.content)
        self.assertTrue(StudentBatchUpload.objects.filter(pk=self.upload.id).exists())
        self.assert_untouched()

    def test_a_student_without_records_still_reverts(self):
        make_student('23BEC099', batch=self.student.batch_id)
        upload = self.admission('23BEC099')
        response = self.client.post(API + 'update_student_status/',
                                    {'studentId': upload.id, 'reportedStatus': 'NOT_REPORTED'},
                                    format='json')
        # The revert itself goes on as before (it then fails in this test
        # database on a table that only exists in production); only the
        # guard is under test here.
        self.assertNotIn('has course registrations', response.content.decode())
