import datetime

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Calendar
from applications.academic_information.utils import (
    allocation_year_problem,
    check_for_registration_complete,
    expected_allocation_year,
    pre_registration_window,
)
from applications.academic_procedures.api.views import working_year_for_session
from applications.globals.models import Designation, HoldsDesignation


class ExpectedAllocationYearTests(SimpleTestCase):
    """UG and PG batches start in August: semester n of batch B runs in B + n // 2."""

    def test_odd_semesters_run_in_the_year_they_start(self):
        self.assertEqual(expected_allocation_year(2024, 1, 'UG'), 2024)
        self.assertEqual(expected_allocation_year(2024, 5, 'UG'), 2026)

    def test_even_semesters_run_in_the_next_calendar_year(self):
        self.assertEqual(expected_allocation_year(2024, 2, 'UG'), 2025)
        self.assertEqual(expected_allocation_year(2024, 6, 'UG'), 2027)
        self.assertEqual(expected_allocation_year(2025, 2, 'PG'), 2026)

    def test_phd_is_not_checked(self):
        self.assertIsNone(expected_allocation_year(2024, 6, 'PHD'))
        self.assertIsNone(allocation_year_problem(2024, 6, 2026, 'PHD'))

    def test_the_right_year_passes(self):
        self.assertIsNone(allocation_year_problem(2024, 6, 2027, 'UG'))
        self.assertIsNone(allocation_year_problem('2024', '6', '2027', 'ug'))

    def test_the_wrong_year_names_the_right_one(self):
        self.assertEqual(
            allocation_year_problem(2024, 6, 2026, 'UG'),
            'Semester 6 of Batch 2024 is the Even Semester of 2026-27, '
            'which runs in 2027. Choose Year 2027.')


class WorkingYearForSessionTests(SimpleTestCase):

    def test_odd_semester_is_the_first_year_of_the_session(self):
        self.assertEqual(working_year_for_session('2026-27', 'Odd Semester'), 2026)

    def test_even_and_summer_are_the_second_year(self):
        self.assertEqual(working_year_for_session('2026-27', 'Even Semester'), 2027)
        self.assertEqual(working_year_for_session('2025-2026', 'Summer Semester'), 2026)

    def test_an_unreadable_session_falls_back_to_the_current_year(self):
        import datetime
        self.assertEqual(working_year_for_session('', 'Even Semester'), datetime.datetime.now().year)


class AllocationRefusesTheWrongYearTests(TestCase):

    def setUp(self):
        admin = User.objects.create_user(username='academic-admin')
        HoldsDesignation.objects.create(user=admin, working=admin,
                                        designation=Designation.objects.create(name='acadadmin'))
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=admin).key}')

    def test_check_allocation_refuses_a_year_the_semester_does_not_run_in(self):
        response = self.client.post('/aims/api/check-allocation', {
            'batch': 2024, 'sem': 6, 'year': 2026, 'programme_type': 'UG'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Choose Year 2027', response.data['message'])

    def test_start_allocation_refuses_a_year_the_semester_does_not_run_in(self):
        response = self.client.post('/aims/api/start-allocation', {
            'batch': 2024, 'semester': 6, 'year': 2026, 'programme_type': 'UG'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Choose Year 2027', response.json()['error'])

    def test_check_allocation_accepts_the_right_year(self):
        response = self.client.post('/aims/api/check-allocation', {
            'batch': 2024, 'sem': 6, 'year': 2027, 'programme_type': 'UG'}, format='json')
        self.assertNotEqual(response.status_code, 400)


class PreRegistrationWindowTests(TestCase):
    """Calendar entries are named after the year the window was set up, not the term's."""

    def make(self, description, start):
        return Calendar.objects.create(description=description, from_date=start,
                                       to_date=start + datetime.timedelta(days=3))

    def test_a_january_semester_uses_the_window_set_up_the_november_before(self):
        november = self.make('Pre Registration 6 2026', datetime.date(2026, 11, 13))
        self.assertEqual(pre_registration_window(6, 2027), november)

    def test_next_years_round_is_not_taken_for_this_term(self):
        this_round = self.make('Pre Registration 6 2026', datetime.date(2026, 11, 13))
        self.make('Pre Registration 6 2027', datetime.date(2027, 11, 12))
        self.assertEqual(pre_registration_window(6, 2027), this_round)

    def test_an_august_semester_uses_the_window_of_the_same_year(self):
        june = self.make('Pre Registration 5 2026', datetime.date(2026, 6, 20))
        self.make('Pre Registration 5 2025', datetime.date(2025, 6, 18))
        self.assertEqual(pre_registration_window(5, 2026), june)

    def test_no_window_for_the_term_is_reported_as_not_found(self):
        self.make('Pre Registration 6 2025', datetime.date(2025, 11, 14))
        self.assertEqual(check_for_registration_complete(2024, 6, 2027, 'UG')['status'], -3)
