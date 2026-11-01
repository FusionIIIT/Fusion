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
        # No declared result yet, so no CPI; the stored cpi field is not used.
        self.assertEqual(context['cpi_display'], '')
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
        self.assertEqual(data['student']['cpi_display'], '')
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
        # Numbered as the bonafide certificate: the serial follows the roll.
        self.assertTrue(cert.reference_number.endswith(f'/21BCS032/{cert.pk:03d}'))
        self.assertEqual(response['X-Certificate-Reference'], cert.reference_number)

    def test_list_and_history_pdf_api(self):
        # Generate one first
        self.client.post(
            '/academic-procedures/api/acad/pointer-conversion/pdf/',
            {'student_id': self.student.pk, 'cpi_text': '7.3'}
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

    def test_cpi_from_the_last_declared_term(self):
        """A summer term after the last semester counts once its result is out."""
        from applications.examination.models import ResultAnnouncement
        from applications.online_cms.models import Student_grades
        from applications.programme_curriculum.models import Course

        regular = Course.objects.create(code='CS1001', name='Regular', credit=4)
        summer = Course.objects.create(code='CS1002', name='Summer', credit=4)
        for course, grade, semester_type in ((regular, 'B', 'Even Semester'),
                                             (summer, 'A+', 'Summer Semester')):
            Student_grades.objects.create(
                course_id=course, semester=2, year=2027, roll_no='21BCS032',
                grade=grade, batch=2026, academic_year='2026-27',
                semester_type=semester_type)

        ResultAnnouncement.objects.create(
            batch=self.batch, semester=2, semester_type='Even Semester',
            announced=True)
        self.assertEqual(pcc.resolve_student_cpi(self.student), (7.0, 2))

        ResultAnnouncement.objects.create(
            batch=self.batch, semester=2, semester_type='Summer Semester',
            announced=True)
        self.assertEqual(pcc.resolve_student_cpi(self.student), (8.5, 2))

    def test_cpi_must_be_a_number_up_to_ten(self):
        url = '/academic-procedures/api/acad/pointer-conversion/pdf/'
        for cpi_text, min_cpi in (('<b>10.0</b>', '5.0'), ('10.5', '5.0'),
                                  ('7.333', '5.0'), ('7.3', 'abc'), ('', '5.0')):
            response = self.client.post(url, {
                'student_id': self.student.pk,
                'cpi_text': cpi_text, 'min_cpi': min_cpi})
            self.assertEqual(response.status_code, 400, (cpi_text, min_cpi))
        self.assertFalse(BonafideCertificate.objects.filter(
            certificate_type='pointer_conv').exists())

    def test_only_current_students(self):
        self.student_user.is_active = False
        self.student_user.save(update_fields=['is_active'])
        response = self.client.get(
            '/academic-procedures/api/acad/pointer-conversion/student/',
            {'roll_number': '21BCS032'})
        self.assertEqual(response.status_code, 404)

    def test_certificate_list_tolerates_a_bad_page(self):
        response = self.client.get(
            '/academic-procedures/api/acad/pointer-conversion/certificates/',
            {'page': 'x', 'page_size': 'y'})
        self.assertEqual(response.status_code, 200)
