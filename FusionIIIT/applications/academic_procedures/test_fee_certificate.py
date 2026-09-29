from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_procedures.api import fee_certificate as fc
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


class FeeCertificateTestCase(TestCase):
    """A UG batch of 2026, with the published 2026-27 structure behind it."""

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
            notes=['*Note: fees may change.'],
        )

        self.student = self._student('26BCS1234', category='GEN', semester=3)

        self.admin = User.objects.create_user(username='fee-admin')
        designation = Designation.objects.create(name='acadadmin')
        HoldsDesignation.objects.create(
            user=self.admin, working=self.admin, designation=designation)
        self.client = APIClient()
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=self.admin).key}')

    def _student(self, roll, category='GEN', is_pwd=False, semester=3, batch=None):
        user = User.objects.create_user(username=roll, first_name='A',
                                        last_name='Student')
        extra = ExtraInfo.objects.create(id=roll, user=user, user_type='student',
                                         sex='F', user_status='PRESENT')
        return Student.objects.create(
            id=extra, programme='B.Tech', batch=(batch or self.batch).year,
            batch_id=batch or self.batch, category=category, is_pwd=is_pwd,
            father_name='Mr. A Parent', curr_semester_no=semester)


class PublishedFiguresTests(FeeCertificateTestCase):
    """The certificate must reproduce the circular, or it is worthless."""

    def test_the_general_figures_match_the_published_table(self):
        rows = fc.build_fee_rows(self.student, self.structure, 1)
        # Grand total plus mess, which the published table leaves out.
        self.assertEqual([row['amount'] for row in rows[:2]],
                         ['120750.00', '105250.00'])
        self.assertEqual(fc._total(rows), Decimal('857500.00'))

    def test_sc_st_and_pwd_pay_the_concession_figures(self):
        for roll, kwargs in (('26BCS2001', {'category': 'SC'}),
                             ('26BCS2002', {'category': 'ST'}),
                             ('26BCS2003', {'category': 'OBC', 'is_pwd': True})):
            student = self._student(roll, **kwargs)
            rows = fc.build_fee_rows(student, self.structure, 1)
            self.assertEqual([row['amount'] for row in rows[:2]],
                             ['49000.00', '33500.00'], roll)
            self.assertEqual(fc._total(rows), Decimal('283500.00'), roll)

    def test_only_the_first_semester_carries_the_one_time_heads(self):
        rows = fc.build_fee_rows(self.student, self.structure, 1)
        difference = Decimal(rows[0]['amount']) - Decimal(rows[1]['amount'])
        self.assertEqual(difference, Decimal('15500'))

    def test_a_head_that_varies_by_semester_is_read_per_semester(self):
        """PG tuition rises after the second semester."""
        self.structure.tuition_hostel_heads = [
            {'head': 'Tuition Fee',
             'general': [50000, 50000, 60000, 60000], 'concession': 'NIL'},
            {'head': 'Hostel Fees', 'general': 11000, 'concession': 11000},
        ]
        self.structure.semester_count = 4
        self.structure.mess_advance_per_semester = Decimal(20000)
        self.structure.one_time_heads = one_time(2000, 1000, 500, 1500, 500,
                                                 1000, 1000, 2500)
        self.structure.save()

        rows = fc.build_fee_rows(self.student, self.structure, 1)
        published = [int(Decimal(row['amount']) - Decimal(20000)) for row in rows]
        self.assertEqual(published, [78500, 68500, 78500, 78500])

    def test_nil_is_read_as_nothing_rather_than_refused(self):
        student = self._student('26BCS2100', category='SC')
        rows = fc.build_fee_rows(student, self.structure, 1)
        self.assertEqual(rows[1]['amount'], '33500.00')


class PaidUnpaidTests(FeeCertificateTestCase):
    def test_earlier_semesters_default_to_paid_and_later_to_unpaid(self):
        rows = fc.build_fee_rows(self.student, self.structure, 3)
        self.assertEqual([row['status'] for row in rows],
                         ['Paid', 'Paid', '', 'Unpaid', 'Unpaid', 'Unpaid',
                          'Unpaid', 'Unpaid'])

    def test_the_current_semester_has_no_default_and_must_be_chosen(self):
        """Defaulting it would silently assert a payment nobody confirmed."""
        rows = fc.build_fee_rows(self.student, self.structure, 3)
        _, errors = fc._clean_rows(
            [{'semester': row['semester'], 'status': row['status']}
             for row in rows], rows)
        self.assertEqual(len(errors), 1)
        self.assertIn('3rd Semester', errors[0])

    def test_every_semester_marked_is_accepted(self):
        rows = fc.build_fee_rows(self.student, self.structure, 3)
        submitted = [{'semester': row['semester'], 'status': row['status'] or 'Paid'}
                     for row in rows]
        cleaned, errors = fc._clean_rows(submitted, rows)
        self.assertEqual(errors, [])
        self.assertEqual(len(cleaned), 8)

    def test_a_status_that_is_neither_paid_nor_unpaid_is_refused(self):
        rows = fc.build_fee_rows(self.student, self.structure, 3)
        submitted = [{'semester': row['semester'], 'status': 'Maybe'}
                     for row in rows]
        _, errors = fc._clean_rows(submitted, rows)
        self.assertEqual(len(errors), 8)


class StructureBindingTests(FeeCertificateTestCase):
    """A batch keeps the fees published for its own session."""

    def test_a_later_session_does_not_change_an_earlier_batch(self):
        FeeStructure.objects.create(
            programme_category='UG', start_year=2027, semester_count=8,
            one_time_heads=one_time(9999),
            semester_heads=ACADEMIC,
            tuition_hostel_heads=[
                {'head': 'Tuition Fee', 'general': 99999, 'concession': 'NIL'}],
            mess_advance_per_semester=Decimal(15000))

        chosen = fc.fee_structure_for(self.student)
        self.assertEqual(chosen.start_year, 2026)

    def test_a_newer_batch_gets_the_newer_session(self):
        newer = Batch.objects.create(name='B.Tech', discipline=self.discipline,
                                     year=2027, curriculum=self.curriculum)
        FeeStructure.objects.create(
            programme_category='UG', start_year=2027, semester_count=8,
            one_time_heads=one_time(1000), semester_heads=ACADEMIC,
            tuition_hostel_heads=[
                {'head': 'Tuition Fee', 'general': 80000, 'concession': 'NIL'}],
            mess_advance_per_semester=Decimal(15000))

        student = self._student('27BCS0001', batch=newer)
        self.assertEqual(fc.fee_structure_for(student).start_year, 2027)

    def test_a_batch_before_any_published_session_falls_back(self):
        older = Batch.objects.create(name='B.Tech', discipline=self.discipline,
                                     year=2020, curriculum=self.curriculum)
        student = self._student('20BCS0001', batch=older)
        self.assertEqual(fc.fee_structure_for(student).start_year, 2026)

    def test_every_specialisation_shares_its_category(self):
        """One PG structure covers M.Tech AI & ML and the rest."""
        pg_programme = Programme.objects.create(
            category='PG', name='Master of Technology', programme_begin_year=2026)
        pg_curriculum = Curriculum.objects.create(
            programme=pg_programme, name='M.Tech AI 2026', no_of_semester=4)
        pg_batch = Batch.objects.create(name='M.Tech AI & ML',
                                        discipline=self.discipline, year=2026,
                                        curriculum=pg_curriculum)
        pg_structure = FeeStructure.objects.create(
            programme_category='PG', start_year=2026, semester_count=4,
            one_time_heads=one_time(10000), semester_heads=ACADEMIC,
            tuition_hostel_heads=[
                {'head': 'Tuition Fee', 'general': 50000, 'concession': 'NIL'}],
            mess_advance_per_semester=Decimal(20000))

        student = self._student('26MCS0001', batch=pg_batch)
        self.assertEqual(fc.fee_structure_for(student), pg_structure)


class IssuedCertificateTests(FeeCertificateTestCase):
    def _generate(self, purpose='Education Loan', **extra):
        rows = fc.build_fee_rows(self.student, self.structure, 3)
        return self.client.post('/academic-procedures/api/acad/fee-certificate/pdf/',
                                {'student_id': self.student.pk,
                                 'purpose': purpose,
                                 'rows': [{'semester': row['semester'],
                                           'status': row['status'] or 'Paid'}
                                          for row in rows],
                                 **extra},
                                format='json')

    def test_a_certificate_is_issued_as_a_pdf(self):
        response = self._generate()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response['X-Certificate-Reference'])

    def test_an_issued_certificate_keeps_the_rows_it_printed(self):
        """A later fee revision must not rewrite a document already handed over."""
        self._generate()
        certificate = BonafideCertificate.objects.get(certificate_type='fee')
        printed = [row['amount'] for row in certificate.fee_rows]

        self.structure.tuition_hostel_heads = [
            {'head': 'Tuition Fee', 'general': 999999, 'concession': 'NIL'}]
        self.structure.save()

        certificate.refresh_from_db()
        self.assertEqual([row['amount'] for row in certificate.fee_rows], printed)
        self.assertTrue(certificate.pdf_content)

    def test_a_certificate_is_recorded_against_the_student(self):
        self._generate()
        certificate = BonafideCertificate.objects.get(certificate_type='fee')
        self.assertEqual(certificate.student_id, self.student.pk)
        self.assertEqual(certificate.certificate_type, 'fee')
        self.assertEqual(certificate.issued_by, self.admin)

    def test_an_unmarked_semester_is_refused(self):
        response = self.client.post(
            '/academic-procedures/api/acad/fee-certificate/pdf/',
            {'student_id': self.student.pk, 'purpose': 'Scholarship',
             'rows': [{'semester': 1, 'status': 'Paid'}]},
            format='json')
        self.assertEqual(response.status_code, 400)

    def test_other_needs_its_own_wording(self):
        self.assertEqual(self._generate(purpose='Other').status_code, 400)
        self.assertEqual(
            self._generate(purpose='Other',
                           custom_purpose='Passport application').status_code, 200)

    def test_a_purpose_outside_the_list_is_refused(self):
        self.assertEqual(self._generate(purpose='Railway Pass').status_code, 400)

    def test_a_student_without_a_structure_is_told_so(self):
        FeeStructure.objects.all().delete()
        response = self._generate()
        self.assertEqual(response.status_code, 400)
        self.assertIn('fee structure', response.json()['error'].lower())

    def test_only_fee_certificates_are_listed(self):
        self._generate()
        BonafideCertificate.objects.create(
            student=self.student, purpose='Scholarship', issued_by=self.admin)
        listing = self.client.get(
            '/academic-procedures/api/acad/fee-certificate/certificates/')
        self.assertEqual(listing.json()['count'], 1)

    def test_only_bonafide_certificates_are_listed_on_the_other_screen(self):
        self._generate()
        BonafideCertificate.objects.create(
            student=self.student, purpose='Scholarship', issued_by=self.admin)
        listing = self.client.get(
            '/academic-procedures/api/acad/bonafide/certificates/')
        self.assertEqual(listing.json()['count'], 1)
        self.assertEqual(listing.json()['results'][0]['purpose'], 'Scholarship')
        self.assertNotIn('fee',
                         [row['purpose'].lower()
                          for row in listing.json()['results']])

    def test_a_fee_certificate_cannot_be_downloaded_as_a_bonafide_one(self):
        self._generate()
        fee = BonafideCertificate.objects.get(certificate_type='fee')
        response = self.client.get(
            f'/academic-procedures/api/acad/bonafide/certificates/{fee.pk}/pdf/')
        self.assertEqual(response.status_code, 404)

    def test_a_bonafide_certificate_cannot_be_downloaded_as_a_fee_one(self):
        bonafide = BonafideCertificate.objects.create(
            student=self.student, purpose='Scholarship', issued_by=self.admin)
        response = self.client.get(
            '/academic-procedures/api/acad/fee-certificate/certificates/'
            f'{bonafide.pk}/pdf/')
        self.assertEqual(response.status_code, 404)
