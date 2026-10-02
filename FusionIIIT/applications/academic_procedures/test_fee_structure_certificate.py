from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_procedures.api import fee_structure_certificate as fsc
from applications.academic_procedures.models import BonafideCertificate, FeeStructure
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.programme_curriculum.models import Batch, Curriculum, Discipline, Programme

ACADEMIC = [
    {'head': 'Gymkhana Fee', 'general': 3000, 'concession': 3000},
    {'head': 'Examination Fee', 'general': 1000, 'concession': 1000},
    {'head': 'Registration Fee', 'general': 1000, 'concession': 1000},
    {'head': 'Medical Insurance + PHC', 'general': 1500, 'concession': 1500},
    {'head': 'Internet and computer Charge', 'general': 1000, 'concession': 1000},
]


def one_time(*amounts):
    return [{'head': f'Head {index}', 'general': amount, 'concession': amount}
            for index, amount in enumerate(amounts, start=1)]


class FeeStructureCertificateTestCase(TestCase):
    def setUp(self):
        self.programme = Programme.objects.create(
            category='UG', name='Bachelor of Technology',
            programme_begin_year=2026)
        self.discipline = Discipline.objects.create(
            name='Computer Science and Engineering', acronym='CSE')
        self.curriculum = Curriculum.objects.create(
            programme=self.programme, name='B.Tech CSE 2026', no_of_semester=8)
        self.batch = Batch.objects.create(
            name='B.Tech', discipline=self.discipline, year=2026,
            curriculum=self.curriculum)

        self.structure = FeeStructure.objects.create(
            programme_category='UG', start_year=2026, semester_count=8,
            one_time_heads=one_time(2000, 2000, 500, 1500, 500, 2000, 2000, 5000),
            semester_heads=ACADEMIC,
            tuition_hostel_heads=[
                {'head': 'Tuition Fee', 'general': 71750, 'concession': 'NIL'},
                {'head': 'Hostel Fees', 'general': 11000, 'concession': 11000},
            ],
            mess_advance_per_semester=Decimal(15000),
        )

        self.student = self._student('26BCS1234', category='GEN', semester=1)

        self.admin = User.objects.create_user(username='fsc-admin')
        designation = Designation.objects.create(name='acadadmin')
        HoldsDesignation.objects.create(
            user=self.admin, working=self.admin, designation=designation)
        self.client = APIClient()
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=self.admin).key}')

    def _student(self, roll, category='GEN', is_pwd=False, semester=1, batch=None):
        user = User.objects.create_user(username=roll, first_name='A',
                                        last_name='Student')
        extra = ExtraInfo.objects.create(id=roll, user=user, user_type='student',
                                         sex='M', user_status='PRESENT')
        return Student.objects.create(
            id=extra, programme='B.Tech', batch=(batch or self.batch).year,
            batch_id=batch or self.batch, category=category, is_pwd=is_pwd,
            father_name='Mr. A Parent', curr_semester_no=semester)


class RowBuildingTests(FeeStructureCertificateTestCase):
    def test_session_semesters_pairs_the_odd_semester_first(self):
        self.assertEqual(fsc.session_semesters(1), (1, 2))
        self.assertEqual(fsc.session_semesters(2), (1, 2))
        self.assertEqual(fsc.session_semesters(3), (3, 4))
        self.assertEqual(fsc.session_semesters(4), (3, 4))

    def test_the_admission_semester_matches_the_published_circular(self):
        rows = fsc.build_structure_rows(self.student, self.structure, 1)
        self.assertEqual(fsc._column_total(rows, 'sem1'), Decimal('120750.00'))
        self.assertEqual(fsc._column_total(rows, 'sem2'), Decimal('105250.00'))
        self.assertEqual(fsc._column_total(rows, 'total'), Decimal('226000.00'))

    def test_a_later_session_carries_no_one_time_heads(self):
        rows = fsc.build_structure_rows(self.student, self.structure, 3)
        self.assertEqual(fsc._column_total(rows, 'sem1'),
                         fsc._column_total(rows, 'sem2'))
        one_time_row = next(r for r in rows if r['label'] == fsc.ONE_TIME_LABEL)
        self.assertEqual(one_time_row['total'], '0.00')

    def test_one_time_heads_are_combined_into_a_single_row(self):
        rows = fsc.build_structure_rows(self.student, self.structure, 1)
        one_time_row = next(r for r in rows if r['label'] == fsc.ONE_TIME_LABEL)
        self.assertEqual(one_time_row['sem1'], '15500.00')
        self.assertEqual(one_time_row['sem2'], '0.00')

    def test_concession_students_get_the_concession_figures(self):
        student = self._student('26BCS2001', category='SC')
        rows = fsc.build_structure_rows(student, self.structure, 1)
        tuition_row = next(r for r in rows if r['label'] == 'Tuition Fee')
        self.assertEqual(tuition_row['sem1'], '0.00')


class IssuedCertificateTests(FeeStructureCertificateTestCase):
    def _generate(self):
        return self.client.post(
            '/academic-procedures/api/acad/fee-structure-certificate/pdf/',
            {'student_id': self.student.pk}, format='json')

    def test_a_certificate_is_issued_as_a_pdf(self):
        response = self._generate()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response['X-Certificate-Reference'])

    def test_a_certificate_is_recorded_against_the_student(self):
        self._generate()
        certificate = BonafideCertificate.objects.get(
            certificate_type='fee_structure')
        self.assertEqual(certificate.student_id, self.student.pk)
        self.assertEqual(certificate.issued_by, self.admin)
        self.assertTrue(certificate.fee_rows)

    def test_a_student_without_a_structure_is_told_so(self):
        FeeStructure.objects.all().delete()
        response = self._generate()
        self.assertEqual(response.status_code, 400)
        self.assertIn('fee structure', response.json()['error'].lower())

    def test_only_fee_structure_certificates_are_listed(self):
        self._generate()
        BonafideCertificate.objects.create(
            student=self.student, purpose='Scholarship', issued_by=self.admin)
        listing = self.client.get(
            '/academic-procedures/api/acad/fee-structure-certificate/certificates/')
        self.assertEqual(listing.json()['count'], 1)

    def test_a_fee_structure_certificate_cannot_be_downloaded_as_a_bonafide_one(self):
        self._generate()
        certificate = BonafideCertificate.objects.get(
            certificate_type='fee_structure')
        response = self.client.get(
            '/academic-procedures/api/acad/bonafide/certificates/'
            f'{certificate.pk}/pdf/')
        self.assertEqual(response.status_code, 404)
