import datetime

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Calendar, Student
from applications.academic_procedures.api.views import (
    pg_registration_semester,
    pg_registration_term,
    registration_semester,
)
from applications.academic_procedures.models import PhDCourseRegistrationRequest
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.programme_curriculum.models import (
    Batch,
    Course,
    CourseSlot,
    Curriculum,
    Discipline,
    Programme,
    Semester,
    ThesisSlot,
)


class PgRegistrationTermTests(SimpleTestCase):
    """A PG semester registered on a date belongs to the term it runs in."""

    def test_an_even_semester_registered_in_november_is_the_coming_one(self):
        self.assertEqual(pg_registration_term(2, datetime.date(2026, 11, 17)),
                         ('2026-27', 'Even Semester', 2027))

    def test_an_even_semester_registered_in_january_is_the_running_one(self):
        self.assertEqual(pg_registration_term(2, datetime.date(2027, 1, 10)),
                         ('2026-27', 'Even Semester', 2027))

    def test_an_odd_semester_runs_in_the_session_starting_this_year(self):
        self.assertEqual(pg_registration_term(3, datetime.date(2026, 8, 13)),
                         ('2026-27', 'Odd Semester', 2026))
        self.assertEqual(pg_registration_term(3, datetime.date(2027, 4, 20)),
                         ('2027-28', 'Odd Semester', 2027))


class PgRegistrationAheadTests(TestCase):
    """PG registers into its current or next semester, whichever the calendar opens."""

    def setUp(self):
        self.now = datetime.datetime.now()
        programme = Programme.objects.create(category='PG', name='M.Des', programme_begin_year=2026)
        self.curriculum = Curriculum.objects.create(programme=programme, name='M.Des 2026', no_of_semester=4)
        discipline = Discipline.objects.create(name='Design', acronym='DS')
        self.batch = Batch.objects.create(name='M.Des', discipline=discipline, year=2026,
                                          curriculum=self.curriculum)
        self.semesters = {n: Semester.objects.create(curriculum=self.curriculum, semester_no=n)
                          for n in (1, 2, 3, 4)}
        self.course = Course.objects.create(code='DS5001', name='Design Studio', credit=4,
                                            syllabus='', ref_books='')
        self.slot = CourseSlot.objects.create(semester=self.semesters[2], name='PC1',
                                              type='Professional Core')
        self.slot.courses.add(self.course)
        self.student = self.make_student('26MDS020', 'M.Des', self.batch, 1)

    def make_student(self, roll, programme, batch, semester):
        user = User.objects.create_user(username=roll)
        extra = ExtraInfo.objects.create(id=roll, user=user, user_type='student', user_status='PRESENT')
        designation, _ = Designation.objects.get_or_create(name='student')
        HoldsDesignation.objects.create(user=user, working=user, designation=designation)
        return Student.objects.create(id=extra, programme=programme, batch=batch.year, batch_id=batch,
                                      category='GEN', curr_semester_no=semester)

    def open_window(self, semester_no, days_from=-1, days_to=1):
        today = self.now.date()
        return Calendar.objects.create(
            description=f'PG Registration {semester_no} {self.now.year}',
            from_date=today + datetime.timedelta(days=days_from),
            to_date=today + datetime.timedelta(days=days_to))

    def client_for(self, student):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=student.id.user).key}')
        return client

    def test_a_first_semester_student_registers_into_the_open_second_semester(self):
        self.open_window(2)
        self.assertEqual(pg_registration_semester(self.student), (2, None))

    def test_a_promoted_student_registers_into_the_current_semester(self):
        self.open_window(3)
        promoted = self.make_student('25MDS001', 'M.Des', self.batch, 3)
        self.assertEqual(pg_registration_semester(promoted), (3, None))

    def test_a_window_two_semesters_ahead_is_another_batchs(self):
        self.open_window(3)
        semester_no, error = pg_registration_semester(self.student)
        self.assertEqual(semester_no, 1)
        self.assertEqual(error.status_code, 400)

    def test_each_batch_takes_its_own_window(self):
        self.open_window(2)
        self.open_window(4)
        senior = self.make_student('25MDS001', 'M.Des', self.batch, 3)
        self.assertEqual(pg_registration_semester(self.student), (2, None))
        self.assertEqual(pg_registration_semester(senior), (4, None))

    def test_a_window_for_a_semester_already_behind_does_not_open(self):
        self.open_window(2)
        senior = self.make_student('25MDS001', 'M.Des', self.batch, 3)
        semester_no, error = pg_registration_semester(senior)
        self.assertEqual(semester_no, 4)
        self.assertEqual(error.status_code, 400)

    def test_a_future_window_says_when_it_opens(self):
        self.open_window(2, days_from=2, days_to=4)
        semester_no, error = pg_registration_semester(self.student)
        self.assertEqual(semester_no, 2)
        self.assertIn(b'will start from', error.content)

    def test_after_the_window_closes_its_semester_is_still_the_one_shown(self):
        self.open_window(2, days_from=-4, days_to=-2)
        semester_no, error = pg_registration_semester(self.student)
        self.assertEqual(semester_no, 2)
        self.assertIn(b'period has ended', error.content)

    def test_without_any_window_the_missing_event_is_named(self):
        semester_no, error = pg_registration_semester(self.student)
        self.assertEqual(semester_no, 1)  # nothing registered yet in semester 1
        self.assertIn(f'PG Registration 1 {self.now.year}'.encode(), error.content)

    def test_phd_still_registers_into_its_current_semester(self):
        phd_programme = Programme.objects.create(category='PHD', name='PhD', programme_begin_year=2026)
        phd_curriculum = Curriculum.objects.create(programme=phd_programme, name='PhD 2026', no_of_semester=8)
        phd_batch = Batch.objects.create(name='PhD', discipline=self.batch.discipline, year=2026,
                                         curriculum=phd_curriculum)
        scholar = self.make_student('26PCS001', 'PhD', phd_batch, 1)
        self.open_window(2)
        semester_no, error = registration_semester(scholar)
        self.assertEqual(semester_no, 1)
        self.assertEqual(error.status_code, 400)

    def test_the_registration_page_offers_and_accepts_the_open_semester(self):
        self.open_window(2)
        client = self.client_for(self.student)

        slots = client.get('/academic-procedures/api/stu/phd/course-slots/')
        self.assertEqual(slots.status_code, 200, slots.content)
        body = slots.json()
        self.assertEqual(body['semester_no'], 2)
        self.assertTrue(body['registration_open'])
        self.assertEqual([s['name'] for s in body['slots']], ['PC1'])

        courses = client.get('/academic-procedures/api/stu/phd/course-slots/courses/',
                             {'slot_id': self.slot.id})
        self.assertEqual(courses.status_code, 200, courses.content)

        created = client.post('/academic-procedures/api/stu/phd/course-request/',
                              {'slot_id': self.slot.id, 'course_id': self.course.id}, format='json')
        self.assertEqual(created.status_code, 201, created.content)
        request = PhDCourseRegistrationRequest.objects.get()
        session, semester_type, _year = pg_registration_term(2)
        self.assertEqual((request.semester.semester_no, request.academic_year, request.semester_type),
                         (2, session, semester_type))

    def test_a_request_is_refused_when_no_window_is_open(self):
        response = self.client_for(self.student).post(
            '/academic-procedures/api/stu/phd/course-request/',
            {'slot_id': self.slot.id, 'course_id': self.course.id}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(PhDCourseRegistrationRequest.objects.exists())

    def test_thesis_shows_the_registration_semester_only_when_asked(self):
        ThesisSlot.objects.create(semester=self.semesters[1], name='Thesis S1')
        ThesisSlot.objects.create(semester=self.semesters[2], name='Thesis S2')
        self.open_window(2)
        client = self.client_for(self.student)
        url = '/academic-procedures/api/stu/thesis-enrollment/'

        current = client.get(url)
        self.assertEqual(current.status_code, 200, current.content)
        self.assertEqual(current.json()['thesis_slot']['name'], 'Thesis S1')

        for_registration = client.get(url, {'registration': 1})
        self.assertEqual(for_registration.json()['thesis_slot']['name'], 'Thesis S2')
