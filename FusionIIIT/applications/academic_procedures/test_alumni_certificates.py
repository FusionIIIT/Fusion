"""Alumni keep Medium of Instruction and Pointer Conversion certificates;
bonafide and the fee letters stay for present students."""
from django.test import TestCase

from applications.academic_information.models import Student
from applications.academic_procedures.api.medium_of_instruction_certificate import (
    medium_of_instruction_context, medium_of_instruction_text,
)
from applications.academic_procedures.models import BonafideCertificate
from applications.academic_procedures.test_pointer_conversion_certificate import (
    PointerConversionCertificateTests,
)
from applications.globals.models import ExtraInfo

API = '/academic-procedures/api/acad/'


class AlumniCertificateTests(TestCase):
    setUp = PointerConversionCertificateTests.setUp

    def mark(self, status):
        ExtraInfo.objects.filter(pk='21BCS032').update(user_status=status)

    def test_pointer_conversion_for_alumnus(self):
        self.mark('ALUMNI')
        response = self.client.get(API + 'pointer-conversion/student/', {'roll_number': '21BCS032'})
        self.assertEqual(response.status_code, 200, response.content)
        response = self.client.post(API + 'pointer-conversion/pdf/',
                                    {'student_id': '21BCS032', 'cpi_text': '7.3', 'min_cpi': '5.0'})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(BonafideCertificate.objects.filter(certificate_type='pointer_conv').exists())

    def test_moi_for_alumnus(self):
        self.mark('ALUMNI')
        response = self.client.get(API + 'medium-of-instruction/student/',
                                   {'roll_number': '21BCS032'})
        self.assertEqual(response.status_code, 200, response.content)
        response = self.client.post(API + 'medium-of-instruction/pdf/', {'student_id': '21BCS032'})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(BonafideCertificate.objects.filter(
            certificate_type='medium_of_instruction').exists())

    def test_withdrawn_gets_them_too(self):
        self.mark('WITHDRAWN')
        response = self.client.get(API + 'pointer-conversion/student/', {'roll_number': '21BCS032'})
        self.assertEqual(response.status_code, 200, response.content)

    def test_archived_does_not(self):
        self.mark('ARCHIVED')
        response = self.client.get(API + 'pointer-conversion/student/', {'roll_number': '21BCS032'})
        self.assertEqual(response.status_code, 404, response.content)

    def test_archived_gets_no_moi_pdf(self):
        self.mark('ARCHIVED')
        response = self.client.post(API + 'medium-of-instruction/pdf/', {'student_id': '21BCS032'})
        self.assertEqual(response.status_code, 404, response.content)

    def test_bonafide_still_refuses_alumnus(self):
        self.mark('ALUMNI')
        response = self.client.get(API + 'bonafide/student/', {'roll_number': '21BCS032'})
        self.assertEqual(response.status_code, 404, response.content)

    def moi_wording(self):
        student = Student.objects.select_related('id').get(pk='21BCS032')
        return medium_of_instruction_text(medium_of_instruction_context(student))

    def test_moi_says_is_for_a_present_student(self):
        self.assertIn(' is a student of ', self.moi_wording())
        response = self.client.get(API + 'medium-of-instruction/student/',
                                   {'roll_number': '21BCS032'})
        self.assertEqual(response.json()['student']['verb'], 'is')

    def test_moi_says_was_for_alumni_and_withdrawn(self):
        for status in ('ALUMNI', 'WITHDRAWN'):
            self.mark(status)
            self.assertIn(' was a student of ', self.moi_wording(), status)
            response = self.client.get(API + 'medium-of-instruction/student/',
                                       {'roll_number': '21BCS032'})
            self.assertEqual(response.json()['student']['verb'], 'was', status)
