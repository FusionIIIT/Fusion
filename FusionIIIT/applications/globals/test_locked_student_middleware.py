"""A locked student's own requests that would change data are refused."""
from django.test import TestCase
from rest_framework.test import APIClient

from applications.globals.models import ExtraInfo
from applications.academic_information.status_test_utils import (
    make_staff, make_student, set_status, token_for,
)

READ_ONLY = 'Your account is read-only because you are Alumni.'


class LockedStudentMiddlewareTests(TestCase):
    def setUp(self):
        self.alumnus = make_student('21BCS001', status='ALUMNI')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(self.alumnus.id.user))

    def test_alumnus_post_refused(self):
        response = self.client.post('/academic-procedures/api/stu/preregistration/submit/',
                                    {}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'detail': READ_ONLY})

    def test_alumnus_put_patch_delete_refused(self):
        for method in (self.client.put, self.client.patch, self.client.delete):
            response = method('/api/profile_update/', {}, format='json')
            self.assertEqual(response.status_code, 403, method)

    def test_alumnus_get_allowed(self):
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, 200, response.content)

    def test_alumnus_check_result_allowed(self):
        response = self.client.post('/examination/api/check_result/',
                                    {'semester_no': 1, 'semester_type': 'Odd Semester'},
                                    format='json')
        self.assertNotEqual(response.status_code, 403, response.content)

    def test_alumnus_result_pdf_allowed(self):
        response = self.client.post('/examination/api/generate_student_result_pdf/', {},
                                    format='json')
        self.assertNotEqual(response.status_code, 403, response.content)

    def test_alumnus_logout_allowed(self):
        response = self.client.post('/api/auth/logout/')
        self.assertNotEqual(response.status_code, 403, response.content)

    def test_alumnus_marks_notifications_read(self):
        response = self.client.post('/api/notificationread', {'id': 1}, format='json')
        self.assertNotEqual(response.status_code, 403, response.content)

    def test_present_student_post_passes(self):
        set_status(self.alumnus, 'PRESENT')
        response = self.client.post('/academic-procedures/api/stu/preregistration/submit/',
                                    {}, format='json')
        self.assertNotEqual(response.json().get('detail'), READ_ONLY)

    def test_staff_post_passes(self):
        staff = make_staff()
        # Even a staff account with an odd status is not a locked student.
        ExtraInfo.objects.filter(user=staff).update(user_status='ALUMNI')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(staff))
        response = client.post('/academic-procedures/api/acad/promote/apply/', [],
                               format='json')
        self.assertEqual(response.status_code, 200, response.content)

    def test_bad_token_passes_through(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token nope')
        response = client.post('/academic-procedures/api/stu/preregistration/submit/', {})
        self.assertEqual(response.status_code, 401)

    def test_unknown_url_not_500(self):
        response = self.client.post('/no/such/path/', {})
        self.assertEqual(response.status_code, 404)
