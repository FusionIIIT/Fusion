from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_procedures.api import demand_letter as dl
from applications.academic_procedures.models import (
    BonafideCertificate, DemandLetterBankAccounts, FeeStructure)
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


class DemandLetterTestCase(TestCase):
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
            general_label='Gen/OBC/EWS', concession_label='PWD/SC/ST',
            one_time_heads=one_time(2000, 2000, 500, 1500, 500, 2000, 2000, 5000),
            semester_heads=ACADEMIC,
            tuition_hostel_heads=[
                {'head': 'Tuition Fee', 'general': 71750, 'concession': 'NIL'},
                {'head': 'Hostel Fees', 'general': 11000, 'concession': 11000},
            ],
            mess_advance_per_semester=Decimal(15000),
            notes=['*Note: fees may change.'],
        )

        DemandLetterBankAccounts.objects.create(
            pk=1,
            academic_fee_account={
                'name': 'PDPM IIITDM STUDENT FEE ACCOUNT', 'number': '50030581281',
                'ifsc': 'IDIB000M694', 'bank_branch': 'INDIAN BANK, Meghawan IIITDM Jabalpur',
                'account_type': 'Current Account',
            },
            mess_fee_account={
                'name': 'IIITDMJ MESS ACCOUNT', 'number': '50035242857',
                'ifsc': 'IDIB000M694', 'bank_branch': 'INDIAN BANK, Meghawan IIITDM Jabalpur',
                'account_type': 'Saving Account',
            },
        )

        self.student = self._student('26BCS1234', category='GEN', semester=3)

        self.admin = User.objects.create_user(username='demand-admin')
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


class FigureTests(DemandLetterTestCase):
    def test_the_academic_and_mess_fee_are_split_apart(self):
        row = dl.build_demand_row(self.student, self.structure, 3)
        self.assertEqual(row['academic_fee'], '90250.00')
        self.assertEqual(row['mess_fee'], '15000.00')

    def test_concession_students_get_the_concession_figures(self):
        student = self._student('26BCS2001', category='SC')
        row = dl.build_demand_row(student, self.structure, 3)
        self.assertEqual(row['academic_fee'], '18500.00')
        self.assertEqual(row['category_label'], 'PWD/SC/ST')

    def test_general_students_get_the_general_label(self):
        row = dl.build_demand_row(self.student, self.structure, 3)
        self.assertEqual(row['category_label'], 'Gen/OBC/EWS')

    def test_the_admission_semester_folds_in_the_one_time_heads(self):
        sem1 = dl.build_demand_row(self.student, self.structure, 1)
        sem2 = dl.build_demand_row(self.student, self.structure, 2)
        self.assertEqual(sem1['academic_fee'], '105750.00')
        self.assertEqual(sem2['academic_fee'], '90250.00')

    def test_programme_short_matches_the_circular(self):
        self.assertEqual(dl._programme_short(self.student), 'B-TECH')

    def test_the_bank_details_come_from_the_shared_record_not_a_constant(self):
        bank = dl._bank_details()
        self.assertEqual(bank['academic']['number'], '50030581281')
        self.assertEqual(bank['mess']['number'], '50035242857')

        accounts = DemandLetterBankAccounts.load()
        accounts.academic_fee_account = {
            **accounts.academic_fee_account, 'number': '99999999999'}
        accounts.save()
        self.assertEqual(dl._bank_details()['academic']['number'], '99999999999')

    def test_a_blank_bank_account_is_detected_as_missing(self):
        accounts = DemandLetterBankAccounts.load()
        self.assertFalse(dl._bank_account_missing(accounts.academic_fee_account))
        self.assertTrue(dl._bank_account_missing({}))
        self.assertTrue(dl._bank_account_missing({'name': 'X'}))

    def test_financial_year_pairs_odd_and_even_semesters(self):
        self.assertEqual(dl.financial_year_for(self.student, 1)[1], '2026-27')
        self.assertEqual(dl.financial_year_for(self.student, 2)[1], '2026-27')
        self.assertEqual(dl.financial_year_for(self.student, 3)[1], '2027-28')
        self.assertEqual(dl.financial_year_for(self.student, 4)[1], '2027-28')


class IssuedCertificateTests(DemandLetterTestCase):
    def _generate(self, semester=3, due_date='2027-01-03', **extra):
        return self.client.post(
            '/academic-procedures/api/acad/demand-letter/pdf/',
            {'student_id': self.student.pk, 'semester': semester,
             'due_date': due_date, **extra},
            format='json')

    def test_a_certificate_is_issued_as_a_pdf(self):
        response = self._generate()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response['X-Certificate-Reference'])

    def test_a_certificate_is_recorded_against_the_student(self):
        self._generate()
        certificate = BonafideCertificate.objects.get(certificate_type='demand')
        self.assertEqual(certificate.student_id, self.student.pk)
        self.assertEqual(certificate.issued_by, self.admin)
        self.assertEqual(certificate.fee_rows[0]['semester'], 3)
        self.assertEqual(certificate.fee_rows[0]['due_date'], '2027-01-03')

    def test_a_missing_due_date_is_refused(self):
        self.assertEqual(self._generate(due_date='').status_code, 400)

    def test_a_malformed_due_date_is_refused(self):
        self.assertEqual(self._generate(due_date='03-01-2027').status_code, 400)

    def test_a_semester_outside_the_structure_is_refused(self):
        self.assertEqual(self._generate(semester=99).status_code, 400)

    def test_a_student_without_a_structure_is_told_so(self):
        FeeStructure.objects.all().delete()
        response = self._generate()
        self.assertEqual(response.status_code, 400)
        self.assertIn('fee structure', response.json()['error'].lower())

    def test_the_same_bank_accounts_apply_to_every_programme_and_year(self):
        pg_programme = Programme.objects.create(
            category='PG', name='Master of Technology', programme_begin_year=2026)
        pg_curriculum = Curriculum.objects.create(
            programme=pg_programme, name='M.Tech CSE 2026', no_of_semester=4)
        pg_batch = Batch.objects.create(
            name='M.Tech', discipline=self.discipline, year=2027,
            curriculum=pg_curriculum)
        FeeStructure.objects.create(
            programme_category='PG', start_year=2027, semester_count=4,
            semester_heads=ACADEMIC, mess_advance_per_semester=Decimal(15000))
        pg_student = self._student('27MCS0001', batch=pg_batch, semester=1)

        response = self.client.post(
            '/academic-procedures/api/acad/demand-letter/pdf/',
            {'student_id': pg_student.pk, 'semester': 1, 'due_date': '2027-01-03'},
            format='json')
        self.assertEqual(response.status_code, 200)

    def test_missing_bank_accounts_are_refused(self):
        accounts = DemandLetterBankAccounts.load()
        accounts.academic_fee_account = {}
        accounts.save()
        response = self._generate()
        self.assertEqual(response.status_code, 400)
        self.assertIn('bank account', response.json()['error'].lower())

    def test_only_demand_letters_are_listed(self):
        self._generate()
        BonafideCertificate.objects.create(
            student=self.student, purpose='Scholarship', issued_by=self.admin)
        listing = self.client.get(
            '/academic-procedures/api/acad/demand-letter/certificates/')
        self.assertEqual(listing.json()['count'], 1)

    def test_a_demand_letter_cannot_be_downloaded_as_a_bonafide_one(self):
        self._generate()
        demand = BonafideCertificate.objects.get(certificate_type='demand')
        response = self.client.get(
            f'/academic-procedures/api/acad/bonafide/certificates/{demand.pk}/pdf/')
        self.assertEqual(response.status_code, 404)


class BankAccountsEndpointTests(DemandLetterTestCase):
    def test_the_accounts_can_be_fetched(self):
        response = self.client.get(
            '/academic-procedures/api/acad/demand-letter-bank-accounts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['academic_fee_account']['number'], '50030581281')

    def test_the_accounts_can_be_edited_and_stay_a_single_row(self):
        response = self.client.put(
            '/academic-procedures/api/acad/demand-letter-bank-accounts/',
            {
                'academic_fee_account': {
                    'name': 'New Account', 'number': '111', 'ifsc': 'ABCD0001234',
                    'bank_branch': 'Somewhere', 'account_type': 'Current Account',
                },
                'mess_fee_account': {
                    'name': 'Mess', 'number': '222', 'ifsc': 'ABCD0001234',
                    'bank_branch': 'Somewhere', 'account_type': 'Saving Account',
                },
            },
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['academic_fee_account']['number'], '111')
        self.assertEqual(DemandLetterBankAccounts.objects.count(), 1)
