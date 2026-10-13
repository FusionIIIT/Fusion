from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_procedures.api import pointer_conversion_certificate as pcc
from applications.academic_procedures.models import BonafideCertificate
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.programme_curriculum.models import Batch, Curriculum, Discipline, Programme


class PointerConversionCertificateTests(TestCase):
    def setUp(self):
        self.programme = Programme.objects.create(
            category='UG', name='Bachelor of Technology', programme_begin_year=2026)
        self.discipline = Discipline.objects.create(
            name='Computer Science and Engineering', acronym='CSE')
        self.curriculum = Curriculum.objects.create(
            programme=self.programme,
            name='B.Tech CSE 2026',
            no_of_semester=8,
        )
        self.batch = Batch.objects.create(
            name='B.Tech',
            discipline=self.discipline,
            year=2026,
            curriculum=self.curriculum,
        )

        self.student_user = User.objects.create_user(
            username='21BCS032',
            first_name='Arpan',
            last_name='Karjee',
        )
        self.student_extra = ExtraInfo.objects.create(
            id='21BCS032',
            user=self.student_user,
            user_type='student',
            sex='M',
            user_status='PRESENT',
        )
        self.student = Student.objects.create(
            id=self.student_extra,
            programme='B.Tech',
            batch=2026,
            batch_id=self.batch,
            category='GEN',
            father_name='Mr. Narayan Karjee',
            curr_semester_no=6,
            cpi=7.3,
        )

        self.admin = User.objects.create_user(username='certificate-admin')
        designation = Designation.objects.create(name='acadadmin')
        HoldsDesignation.objects.create(
            user=self.admin, working=self.admin, designation=designation)
        self.token = Token.objects.create(user=self.admin)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_student_context(self):
        context = pcc.build_pointer_conversion_context(self.student)
        self.assertTrue(context['is_ready'])
        self.assertEqual(context['name'], 'Arpan Karjee')
        self.assertEqual(context['roll_number'], '21BCS032')
        self.assertEqual(context['salutation'], 'Mr.')
        self.assertEqual(context['cpi_display'], '7.3')
        self.assertEqual(context['min_cpi'], '5.0')
        self.assertEqual(context['programme'], 'Bachelor of Technology')
        self.assertEqual(context['programme_abbr'], 'B.Tech')

    def test_student_api(self):
        response = self.client.get(
            '/academic-procedures/api/acad/pointer-conversion/student/',
            {'roll_number': '21BCS032'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['student']['name'], 'Arpan Karjee')
        self.assertEqual(data['student']['cpi_display'], '7.3')
        self.assertIn('reference_preview', data['certificate'])

    def test_generate_pdf_api(self):
        response = self.client.post(
            '/academic-procedures/api/acad/pointer-conversion/pdf/',
            {
                'student_id': self.student.pk,
                'cpi_text': '7.3',
                'min_cpi': '5.0',
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('21BCS032_Pointer_Conversion_Certificate.pdf', response['Content-Disposition'])

        cert = BonafideCertificate.objects.filter(
            certificate_type='pointer_conv', student=self.student
        ).first()
        self.assertIsNotNone(cert)
        self.assertEqual(cert.fee_rows.get('cpi'), '7.3')

    def test_list_and_history_pdf_api(self):
        # Generate one first
        self.client.post(
            '/academic-procedures/api/acad/pointer-conversion/pdf/',
            {'student_id': self.student.pk}
        )
        # Check list
        response = self.client.get('/academic-procedures/api/acad/pointer-conversion/certificates/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        cert_id = data['results'][0]['id']

        # Check detail PDF
        detail_response = self.client.get(
            f'/academic-procedures/api/acad/pointer-conversion/certificates/{cert_id}/pdf/'
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response['Content-Type'], 'application/pdf')
