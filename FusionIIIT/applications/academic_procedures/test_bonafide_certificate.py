from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase
from PyPDF2 import PdfFileReader
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_procedures.api.bonafide_certificate import build_certificate_context
from applications.academic_procedures.models import BonafideCertificate
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.programme_curriculum.models import Batch, Curriculum, Discipline, Programme


class BonafideCertificateTests(TestCase):
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
            username='26BCS1234',
            first_name='Ananya Priyadarshini',
            last_name='Venkateshwarlu',
        )
        self.student_extra = ExtraInfo.objects.create(
            id='26BCS1234',
            user=self.student_user,
            user_type='student',
            sex='F',
            user_status='PRESENT',
        )
        self.student = Student.objects.create(
            id=self.student_extra,
            programme='B.Tech',
            batch=2026,
            batch_id=self.batch,
            category='GEN',
            father_name='Mr. Rajesh Venkateshwarlu',
            curr_semester_no=3,
        )

        self.admin = User.objects.create_user(username='certificate-admin')
        designation = Designation.objects.create(name='acadadmin')
        HoldsDesignation.objects.create(
            user=self.admin, working=self.admin, designation=designation)
        self.token = Token.objects.create(user=self.admin)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_student_context_uses_current_academic_records(self):
        response = self.client.get(
            '/academic-procedures/api/acad/bonafide/student/',
            {'roll_number': self.student.pk.lower()},
        )

        self.assertEqual(response.status_code, 200)
        student = response.data['student']
        self.assertEqual(student['name'], 'Ananya Priyadarshini Venkateshwarlu')
        self.assertEqual(student['salutation'], 'Ms.')
        self.assertEqual(student['relation'], 'D/o')
        self.assertEqual(student['father_name'], 'Rajesh Venkateshwarlu')
        self.assertEqual(student['year_ordinal'], '2nd')
        self.assertEqual(student['semester_ordinal'], '3rd')
        self.assertEqual(student['programme'], 'Bachelor of Technology')
        self.assertEqual(student['discipline'], 'Computer Science and Engineering')
        self.assertEqual(student['duration_years'], 4)
        self.assertEqual(student['start_year'], 2026)
        self.assertEqual(student['end_year'], 2030)
        self.assertTrue(student['is_ready'])
        self.assertRegex(
            response.data['certificate']['reference_preview'],
            r'/26BCS1234/\d{3,}$',
        )
        self.assertEqual(
            [option['value'] for option in response.data['purposes'][-2:]],
            ['VISA Purpose', 'Other'],
        )

    def test_roll_number_is_required(self):
        response = self.client.get(
            '/academic-procedures/api/acad/bonafide/student/'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'roll_number is required.')

    def test_unknown_roll_number_returns_not_found(self):
        response = self.client.get(
            '/academic-procedures/api/acad/bonafide/student/',
            {'roll_number': '26BCS9999'},
        )

        self.assertEqual(response.status_code, 404)

    def test_male_student_uses_male_salutation_and_relation(self):
        self.student.id.sex = 'M'
        context = build_certificate_context(self.student)

        self.assertEqual(context['salutation'], 'Mr.')
        self.assertEqual(context['relation'], 'S/o')
        self.assertEqual(context['pronoun'], 'his')

    def test_programme_category_controls_course_duration(self):
        cases = [
            ('PG', 'Master of Technology', 'M.Tech', 'M.Tech', 4, 2, 2027),
            ('PHD', 'Doctor of Philosophy', 'Ph.D.', 'PhD (Odd)', 18, 6, 2031),
        ]

        for category, name, student_programme, batch_name, semesters, years, end_year in cases:
            with self.subTest(category=category):
                programme = Programme.objects.create(
                    category=category,
                    name=name,
                    programme_begin_year=2025,
                )
                curriculum = Curriculum.objects.create(
                    programme=programme,
                    name=f'{name} 2025',
                    no_of_semester=semesters,
                )
                batch = Batch.objects.create(
                    name=batch_name,
                    discipline=self.discipline,
                    year=2025,
                    curriculum=curriculum,
                )
                self.student.programme = student_programme
                self.student.batch = 2025
                self.student.batch_id = batch

                context = build_certificate_context(self.student)

                self.assertEqual(context['duration_years'], years)
                self.assertEqual(context['start_year'], 2025)
                self.assertEqual(context['end_year'], end_year)

    def test_generation_creates_record_and_pdf(self):
        response = self.client.post(
            '/academic-procedures/api/acad/bonafide/pdf/',
            {'student_id': self.student.pk, 'purpose': 'Internship'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('.pdf', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))
        certificate = BonafideCertificate.objects.get()
        self.assertEqual(certificate.student, self.student)
        self.assertEqual(certificate.purpose, 'Internship')
        self.assertEqual(bytes(certificate.pdf_content), response.content)
        self.assertRegex(
            certificate.reference_number,
            rf'/26BCS1234/{certificate.pk:03d}$',
        )

        document = PdfFileReader(BytesIO(response.content))
        self.assertEqual(document.getNumPages(), 1)
        page = document.getPage(0)
        self.assertAlmostEqual(float(page.mediaBox.getWidth()), 595.28, places=1)
        self.assertAlmostEqual(float(page.mediaBox.getHeight()), 841.89, places=1)
        text = ' '.join(page.extractText().split())
        self.assertIn('Ananya Priyadarshini Venkateshwarlu', text)
        self.assertIn('D/o Mr. Rajesh Venkateshwarlu', text)
        self.assertIn('Bachelor of Technology in Computer Science and Engineering', text)
        self.assertIn('2026 to 2030', text)
        self.assertIn(
            'PDPM Indian Institute of Information Technology, Design and Manufacturing, Jabalpur',
            text,
        )
        self.assertIn(
            'Note: No objection certificate will be issued by the placement cell.', text)
        self.assertLess(
            text.index('request for Internship.'),
            text.index('Note: No objection certificate'),
        )
        self.assertLess(
            text.index('Note: No objection certificate'),
            text.index('(Priti Patel)'),
        )

    def test_certificate_serial_numbers_continue(self):
        references = []
        for purpose in ('Scholarship', 'Railway Pass'):
            response = self.client.post(
                '/academic-procedures/api/acad/bonafide/pdf/',
                {'student_id': self.student.pk, 'purpose': purpose},
                format='json',
            )
            self.assertEqual(response.status_code, 200)
            references.append(response['X-Certificate-Reference'])

        first = int(references[0].rsplit('/', 1)[1])
        second = int(references[1].rsplit('/', 1)[1])
        self.assertEqual(second, first + 1)
        self.assertGreaterEqual(len(references[0].rsplit('/', 1)[1]), 3)

    def test_incomplete_student_data_blocks_generation(self):
        self.student.father_name = ''
        self.student.save(update_fields=['father_name'])

        response = self.client.post(
            '/academic-procedures/api/acad/bonafide/pdf/',
            {'student_id': self.student.pk, 'purpose': 'Scholarship'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Father's name is unavailable.", response.data['details'])
        self.assertFalse(BonafideCertificate.objects.exists())

    def test_invalid_purpose_is_rejected(self):
        response = self.client.post(
            '/academic-procedures/api/acad/bonafide/pdf/',
            {'student_id': self.student.pk, 'purpose': 'Other'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(BonafideCertificate.objects.exists())

    def test_other_purpose_is_required_and_rendered(self):
        missing = self.client.post(
            '/academic-procedures/api/acad/bonafide/pdf/',
            {'student_id': self.student.pk, 'purpose': 'Other'},
            format='json',
        )
        self.assertEqual(missing.status_code, 400)

        response = self.client.post(
            '/academic-procedures/api/acad/bonafide/pdf/',
            {
                'student_id': self.student.pk,
                'purpose': 'Other',
                'custom_purpose': 'Conference Participation',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        certificate = BonafideCertificate.objects.get()
        self.assertEqual(certificate.purpose, 'Other')
        self.assertEqual(certificate.custom_purpose, 'Conference Participation')
        text = ' '.join(
            PdfFileReader(BytesIO(response.content)).getPage(0).extractText().split()
        )
        self.assertIn('request for Conference Participation.', text)
        self.assertNotIn('Note: No objection certificate', text)

    def test_certificate_history_supports_search_and_pagination(self):
        certificates = []
        for purpose, custom_purpose in (
                ('Scholarship', ''), ('Other', 'Conference Participation')):
            certificates.append(BonafideCertificate.objects.create(
                student=self.student,
                purpose=purpose,
                custom_purpose=custom_purpose,
                reference_number=(
                    f'IIITDMJ/AR/2026/08/{self.student.pk}/'
                    f'{BonafideCertificate.objects.count() + 1:03d}'
                ),
                issued_by=self.admin,
            ))

        response = self.client.get(
            '/academic-procedures/api/acad/bonafide/certificates/',
            {'page': 1, 'page_size': 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['purpose'],
            'Conference Participation',
        )

        serial_search = self.client.get(
            '/academic-procedures/api/acad/bonafide/certificates/',
            {'search': str(certificates[1].pk)},
        )
        self.assertEqual(serial_search.status_code, 200)
        self.assertEqual(serial_search.data['count'], 1)
        self.assertEqual(
            serial_search.data['results'][0]['id'], certificates[1].pk)

        for search in (
                '26BCS1234', 'Ananya Venkateshwarlu',
                'Conference Participation'):
            with self.subTest(search=search):
                result = self.client.get(
                    '/academic-procedures/api/acad/bonafide/certificates/',
                    {'search': search},
                )
                self.assertEqual(result.status_code, 200)
                self.assertGreaterEqual(result.data['count'], 1)

        date_search = self.client.get(
            '/academic-procedures/api/acad/bonafide/certificates/',
            {'search': BonafideCertificate.objects.first().issued_at.strftime('%d.%m.%Y')},
        )
        self.assertEqual(date_search.status_code, 200)
        self.assertEqual(date_search.data['count'], 2)

    def test_generated_certificate_can_be_previewed_and_downloaded(self):
        generated = self.client.post(
            '/academic-procedures/api/acad/bonafide/pdf/',
            {'student_id': self.student.pk, 'purpose': 'Scholarship'},
            format='json',
        )
        certificate = BonafideCertificate.objects.get()

        preview = self.client.get(
            f'/academic-procedures/api/acad/bonafide/certificates/{certificate.pk}/pdf/'
        )
        self.assertEqual(preview.status_code, 200)
        self.assertTrue(preview['Content-Disposition'].startswith('inline;'))
        self.assertEqual(preview.content, generated.content)

        download = self.client.get(
            f'/academic-procedures/api/acad/bonafide/certificates/{certificate.pk}/pdf/',
            {'download': '1'},
        )
        self.assertEqual(download.status_code, 200)
        self.assertTrue(download['Content-Disposition'].startswith('attachment;'))
        self.assertEqual(download.content, generated.content)

    def test_legacy_certificate_without_stored_pdf_can_be_previewed(self):
        certificate = BonafideCertificate.objects.create(
            student=self.student,
            purpose='Railway Pass',
            reference_number='IIITDMJ/AR/2026/08/26BCS1234/001',
            issued_by=self.admin,
        )

        response = self.client.get(
            f'/academic-procedures/api/acad/bonafide/certificates/{certificate.pk}/pdf/'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF-'))
        text = ' '.join(
            PdfFileReader(BytesIO(response.content)).getPage(0).extractText().split()
        )
        self.assertIn('request for Railway Pass.', text)

    def test_non_acadadmin_cannot_access_certificate_data(self):
        user = User.objects.create_user(username='student-role-user')
        designation = Designation.objects.create(name='student')
        HoldsDesignation.objects.create(user=user, working=user, designation=designation)
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.get(
            '/academic-procedures/api/acad/bonafide/student/',
            {'roll_number': self.student.pk},
        )

        self.assertEqual(response.status_code, 403)
        history = self.client.get(
            '/academic-procedures/api/acad/bonafide/certificates/'
        )
        self.assertEqual(history.status_code, 403)
