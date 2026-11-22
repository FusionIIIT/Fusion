"""auth/me tells the client a student's status and, for a locked student,
offers only the modules they can still use."""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from applications.academic_information.status_test_utils import (
    make_staff, make_student, set_status, token_for,
)
from applications.globals.models import Designation, HoldsDesignation, ModuleAccess


class AuthStatusTests(TestCase):
    def setUp(self):
        self.student = make_student('21BCS001')
        user = self.student.id.user
        HoldsDesignation.objects.create(
            user=user, working=user, held_at=timezone.now(),
            designation=Designation.objects.get_or_create(name='student')[0])
        ModuleAccess.objects.create(designation='student', course_registration=True,
                                    examinations=True, program_and_curriculum=True,
                                    thesis_research=True, placement_cell=True)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(user))

    def me(self):
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_auth_me_status_present(self):
        data = self.me()
        self.assertEqual(data['student_status'], 'PRESENT')
        self.assertTrue(data['accessible_modules']['student']['thesis_research'])

    def test_auth_me_alumni_trims_modules(self):
        set_status(self.student, ' alumni')
        data = self.me()
        self.assertEqual(data['student_status'], 'ALUMNI')
        self.assertEqual(data['accessible_modules'],
                         {'student': {'course_registration': True, 'examinations': True}})
        self.assertEqual(data['plugged_navigation'], {})

    def test_faculty_status_null(self):
        staff = make_staff()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(staff))
        self.assertIsNone(client.get('/api/auth/me').json()['student_status'])
