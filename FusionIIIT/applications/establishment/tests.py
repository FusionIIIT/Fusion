from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation, DepartmentInfo
from applications.establishment.models import (
    Establishment_variables,
    Cpda_application,
    Cpda_tracking,
    CpdaBalance,
    Cpda_bill,
    Ltc_application,
    Ltc_tracking,
    Ltc_eligible_user,
    Ltc_availed,
    Ltc_to_avail,
    Dependent,
    Appraisal,
    CoursesInstructed,
    NewCoursesOffered,
    NewCourseMaterial,
    ThesisResearchSupervision,
    SponsoredProjects,
    AppraisalRequest,
    Constants,
)
from applications.establishment.forms import Cpda_Form, Ltc_Eligible_Form


class EstablishmentModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testfaculty', password='password123')
        self.admin_user = User.objects.create_user(username='estadmin', password='password123')
        self.est_var = Establishment_variables.objects.create(est_admin=self.admin_user)

    def test_establishment_variables_creation(self):
        self.assertEqual(self.est_var.est_admin.username, 'estadmin')

    def test_cpda_application_and_balance(self):
        balance = CpdaBalance.objects.create(user=self.user, cpda_balance=300000)
        self.assertEqual(balance.cpda_balance, 300000)

        app = Cpda_application.objects.create(
            applicant=self.user,
            pf_number='PF1234',
            purpose='Attend IEEE Conference',
            requested_advance=50000,
            status='requested'
        )
        self.assertIn('cpda id', str(app))
        self.assertEqual(app.requested_advance, 50000)

        tracking = Cpda_tracking.objects.create(
            application=app,
            reviewer_id=self.admin_user,
            review_status='under_review'
        )
        self.assertEqual(tracking.review_status, 'under_review')
        self.assertIn('tracking', str(tracking))

    def test_ltc_eligible_user_calculations(self):
        eligible = Ltc_eligible_user.objects.create(
            user=self.user,
            date_of_joining=date.today() - timedelta(days=365 * 2),
            current_block_size=4,
            total_ltc_allowed=2,
            hometown_ltc_allowed=2,
            elsewhere_ltc_allowed=1,
            hometown_ltc_availed=1,
            elsewhere_ltc_availed=0
        )
        self.assertEqual(eligible.hometown_ltc_remaining(), 1)
        self.assertEqual(eligible.elsewhere_ltc_remaining(), 1)
        self.assertEqual(eligible.total_ltc_remaining(), 2)

        # When availed exceeds allowed, remaining should not be negative
        eligible.hometown_ltc_availed = 3
        self.assertEqual(eligible.hometown_ltc_remaining(), 0)

    def test_ltc_application_and_dependents(self):
        ltc_app = Ltc_application.objects.create(
            applicant=self.user,
            pf_number='PF1234',
            basic_pay=80000,
            leave_start=date.today(),
            leave_end=date.today() + timedelta(days=5),
            family_departure_date=date.today(),
            leave_nature='Earned Leave',
            purpose='Visiting Hometown',
            is_hometown_or_elsewhere='hometown',
            phone_number='9876543210',
            address_during_leave='123 Main St',
            travel_mode='rail',
            requested_advance=20000,
            status='requested'
        )
        self.assertIn('ltc id', str(ltc_app))

        dep = Dependent.objects.create(ltc=ltc_app, name='Dependent Child', age=10, depend='Child')
        self.assertEqual(dep.name, 'Dependent Child')
        self.assertEqual(dep.ltc, ltc_app)

    def test_appraisal_models(self):
        appraisal = Appraisal.objects.create(
            applicant=self.user,
            discipline='CSE',
            knowledge_field='Artificial Intelligence',
            research_interest='Machine Learning',
            status='pending',
            start_date=date.today() - timedelta(days=365),
            end_date=date.today()
        )
        self.assertIn('testfaculty', str(appraisal))

        course = CoursesInstructed.objects.create(
            appraisal=appraisal,
            semester=5,
            course_name='Software Engineering',
            course_num=301,
            lecture_hrs_wk=3.0,
            tutorial_hrs_wk=1.0,
            lab_hrs_wk=2.0,
            reg_students=120
        )
        self.assertEqual(course.course_name, 'Software Engineering')
        self.assertEqual(course.appraisal, appraisal)


class EstablishmentFormsTestCase(TestCase):
    def test_cpda_form_validation(self):
        # Invalid without required fields
        form = Cpda_Form(data={})
        self.assertFalse(form.is_valid())

        # Valid data
        form = Cpda_Form(data={
            'pf_number': '12345',
            'purpose': 'Conference travel',
            'declaration': True
        })
        self.assertTrue(form.is_valid())

    def test_ltc_eligible_form_validation(self):
        form = Ltc_Eligible_Form(data={
            'username': 'testfaculty',
            'joining_date': '2022-01-01',
            'current_block_size': 4,
            'total_ltc_allowed': 2,
            'hometown_ltc_allowed': 2,
            'elsewhere_ltc_allowed': 1,
            'hometown_ltc_availed': 0,
            'elsewhere_ltc_availed': 0
        })
        self.assertTrue(form.is_valid())


class EstablishmentViewsSecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_unauthenticated_user_redirects_to_login(self):
        urls = [
            reverse('establishment:establishment'),
            reverse('establishment:cpda'),
            reverse('establishment:ltc'),
            reverse('establishment:appraisal'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/accounts/login', response.url)


class EstablishmentRestApiTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='apifaculty', password='password123')
        self.client.force_login(self.user)

    def test_api_cpda_balance(self):
        CpdaBalance.objects.create(user=self.user, cpda_balance=250000)
        url = '/establishment/api/cpda/balance/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cpda_balance'], 250000)

    def test_api_cpda_submit_application(self):
        url = '/establishment/api/cpda/applications/'
        payload = {
            'purpose': 'Attend ACM SIGMOD Conference',
            'requested_advance': 45000,
            'pf_number': 'PF999'
        }
        response = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['purpose'], 'Attend ACM SIGMOD Conference')
        self.assertEqual(data['status'], 'requested')
        self.assertEqual(Cpda_application.objects.filter(applicant=self.user).count(), 1)

    def test_api_ltc_eligibility(self):
        Ltc_eligible_user.objects.create(
            user=self.user,
            date_of_joining='2020-01-01',
            current_block_size=4,
            total_ltc_allowed=2,
            hometown_ltc_allowed=2,
            elsewhere_ltc_allowed=1,
            hometown_ltc_availed=0,
            elsewhere_ltc_availed=0
        )
        url = '/establishment/api/ltc/eligibility/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['hometown_ltc_remaining'], 2)

    def test_api_appraisals_list(self):
        Appraisal.objects.create(
            applicant=self.user,
            discipline='CSE',
            knowledge_field='Database Systems',
            research_interest='Distributed Systems',
            status='pending'
        )
        url = '/establishment/api/appraisals/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

