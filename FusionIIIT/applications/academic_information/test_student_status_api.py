from django.test import TestCase
from rest_framework.test import APIClient

from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, token_for,
)
from applications.academic_procedures.models import course_registration
from applications.globals.models import ExtraInfo
from applications.programme_curriculum.models import Course, CourseSlot, Semester

URL = '/aims/api/student-status/'


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(user))
    return client


class StudentStatusApiTests(TestCase):
    def setUp(self):
        self.batch = make_batch(2023, 'ECE')
        self.student = make_student('23BEC020', batch=self.batch, semester=4)
        self.office = client_for(make_staff())

    def test_get_shows_the_student_and_their_history(self):
        response = self.office.get(URL, {'roll_no': '23bec020'})
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(
            {k: data[k] for k in ('roll_no', 'discipline', 'batch', 'semester', 'status')},
            {'roll_no': '23BEC020', 'discipline': 'B.Tech ECE', 'batch': 2023,
             'semester': 4, 'status': 'PRESENT'})
        self.assertEqual(data['blockers'],
                         {'ungraded': [], 'unverified': [], 'pre_registration': [],
                          'final_registration': []})
        self.assertEqual(data['history'], [])

    def test_withdraw_then_readmit(self):
        response = self.office.post(URL + 'withdraw/',
                                    {'roll_no': '23BEC020', 'reason': 'Left'}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['status'], 'WITHDRAWN')
        history = response.json()['history']
        self.assertEqual(
            {k: history[0][k] for k in ('action', 'previous_status', 'new_status', 'reason',
                                        'semester_no', 'performed_by')},
            {'action': 'withdraw', 'previous_status': 'PRESENT', 'new_status': 'WITHDRAWN',
             'reason': 'Left', 'semester_no': 4, 'performed_by': 'status_admin'})
        response = self.office.post(URL + 'readmit/',
                                    {'roll_no': '23BEC020', 'reason': 'Back'}, format='json')
        self.assertEqual(response.json()['status'], 'PRESENT')
        self.assertEqual([h['action'] for h in response.json()['history']],
                         ['readmit', 'withdraw'])

    def test_refusal_lists_what_is_in_the_way(self):
        semester = Semester.objects.create(curriculum=self.batch.curriculum, semester_no=4)
        course = Course.objects.create(code='EC4001', name='Signals', credit=4,
                                       syllabus='', ref_books='')
        course_registration.objects.create(
            student_id=self.student, semester_id=semester, course_id=course,
            course_slot_id=CourseSlot.objects.create(semester=semester, name='EC', type='Core'),
            registration_type='Regular', semester_type='Even Semester', session='2024-25')
        response = self.office.post(URL + 'withdraw/',
                                    {'roll_no': '23BEC020', 'reason': 'Left'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['blockers']['ungraded'], ['EC4001'])
        self.assertIn('still has an open semester', response.json()['detail'])
        self.assertEqual(ExtraInfo.objects.get(pk='23BEC020').user_status, 'PRESENT')

    def test_a_programme_admin_sees_only_their_programme(self):
        pg_admin = client_for(make_staff('pg_admin', 'Acad PG'))
        self.assertEqual(pg_admin.get(URL, {'roll_no': '23BEC020'}).status_code, 404)
        response = pg_admin.post(URL + 'withdraw/',
                                 {'roll_no': '23BEC020', 'reason': 'Left'}, format='json')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(ExtraInfo.objects.get(pk='23BEC020').user_status, 'PRESENT')
        ug_admin = client_for(make_staff('ug_admin', 'Acad UG'))
        self.assertEqual(ug_admin.get(URL, {'roll_no': '23BEC020'}).status_code, 200)

    def test_faculty_are_refused(self):
        faculty = client_for(make_staff('prof', 'Professor'))
        self.assertEqual(faculty.get(URL, {'roll_no': '23BEC020'}).status_code, 403)

    def test_unknown_roll_number(self):
        self.assertEqual(self.office.get(URL, {'roll_no': 'NOPE'}).status_code, 404)
