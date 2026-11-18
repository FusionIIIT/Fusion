from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token

from applications.academic_information.models import Student
from applications.academic_procedures.models import ThesisEvaluation, ThesisRegistration
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.online_cms.models import Student_grades
from applications.programme_curriculum.models import (
    Batch,
    Course,
    Curriculum,
    Discipline,
    Programme,
    Semester,
    ThesisSlot,
)

URL = '/aims/api/database/spi-cpi/'


class DatabaseSpiCpiTests(TestCase):
    """SPI and CPI per student, for a chosen or the latest graded semester."""

    def setUp(self):
        admin = User.objects.create_user(username='spi_report_admin')
        HoldsDesignation.objects.create(
            user=admin, working=admin, held_at=timezone.now(),
            designation=Designation.objects.create(name='acadadmin'))
        self.client = Client(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=admin).key}')

        programme = Programme.objects.create(category='UG', name='B.Tech', programme_begin_year=2024)
        curriculum = Curriculum.objects.create(programme=programme, name='B.Tech 2024', no_of_semester=8)
        self.cse = Batch.objects.create(
            name='B.Tech', year=2024, curriculum=curriculum,
            discipline=Discipline.objects.create(name='Computer Science', acronym='CSE'))
        self.ece = Batch.objects.create(
            name='B.Tech', year=2024, curriculum=curriculum,
            discipline=Discipline.objects.create(name='Electronics', acronym='ECE'))
        self.older = Batch.objects.create(
            name='B.Tech', year=2023, curriculum=curriculum, discipline=self.cse.discipline)

        self.courses = {code: Course.objects.create(code=code, name=code, credit=credit,
                                                    syllabus='', ref_books='')
                        for code, credit in (('CS101', 4), ('CS201', 4), ('CS202', 2))}

        # Semester 1: 4 credits at A. Semester 2: 4 at B and 2 at O.
        self.student('24BCS001', self.cse, [(1, 'Odd Semester', 'CS101', 'A'),
                                            (2, 'Even Semester', 'CS201', 'B'),
                                            (2, 'Even Semester', 'CS202', 'O')])
        # Failed CS101 in semester 1 and cleared it later; the retake is filed
        # under semester 1 as an Even Semester grade.
        self.student('24BCS002', self.cse, [(1, 'Odd Semester', 'CS101', 'F'),
                                            (1, 'Even Semester', 'CS101', 'B')])
        self.student('24BEC001', self.ece, [])

    def student(self, roll, batch, grades):
        user = User.objects.create_user(username=roll, first_name='Student', last_name=roll)
        extra = ExtraInfo.objects.create(id=roll, user=user, user_type='student')
        Student.objects.create(id=extra, programme='B.Tech', batch=batch.year, batch_id=batch,
                               category='GEN', curr_semester_no=3)
        for semester, semester_type, code, grade in grades:
            Student_grades.objects.create(
                course_id=self.courses[code], semester=semester, semester_type=semester_type,
                roll_no=roll, grade=grade, batch=batch.year, year=2025, academic_year='2025-26')

    def report(self, **params):
        response = self.client.get(URL, params)
        self.assertEqual(response.status_code, 200, response.content)
        return {row['roll_no']: row for row in response.json()['rows']}

    def test_each_student_gets_their_latest_graded_semester(self):
        rows = self.report(batch=2024)
        self.assertEqual(set(rows), {'24BCS001', '24BCS002', '24BEC001'})
        self.assertEqual(rows['24BCS001'], {
            'roll_no': '24BCS001', 'student_name': 'Student 24BCS001',
            'discipline': 'B.Tech CSE', 'semester': 2, 'spi': 8.0, 'cpi': 8.4})

    def test_a_chosen_semester_gives_that_semesters_figures(self):
        rows = self.report(batch=2024, semester=1)
        self.assertEqual((rows['24BCS001']['spi'], rows['24BCS001']['cpi']), (9.0, 9.0))

    def test_a_retake_filed_under_the_other_type_keeps_the_semesters_own_term(self):
        row = self.report(batch=2024)['24BCS002']
        # SPI is the Odd term's F; CPI counts the cleared retake, as on the transcript.
        self.assertEqual((row['semester'], row['spi'], row['cpi']), (1, 2.0, 7.0))

    def test_a_summer_term_after_the_latest_semester_is_the_latest(self):
        # CS101 failed in semester 1 and cleared with an A in the summer after semester 2.
        self.student('24BCS003', self.cse, [(1, 'Odd Semester', 'CS101', 'F'),
                                            (2, 'Even Semester', 'CS201', 'B'),
                                            (2, 'Summer Semester', 'CS101', 'A')])
        row = self.report(batch=2024)['24BCS003']
        self.assertEqual((row['semester'], row['spi'], row['cpi']), ('Summer 1', 9.0, 8.0))
        # A chosen semester stops before its summer term.
        row = self.report(batch=2024, semester=2)['24BCS003']
        self.assertEqual((row['spi'], row['cpi']), (7.0, 4.5))

    def test_a_student_without_grades_is_listed_without_figures(self):
        row = self.report(batch=2024)['24BEC001']
        self.assertEqual((row['semester'], row['spi'], row['cpi']), (None, None, None))
        self.assertEqual(self.report(batch=2024, semester=5)['24BCS001']['spi'], None)

    def test_a_discipline_narrows_the_batch(self):
        self.assertEqual(set(self.report(batch=2024, batch_id=self.ece.id)), {'24BEC001'})

    def test_a_phd_semester_graded_only_by_its_thesis_counts(self):
        programme = Programme.objects.create(category='PHD', name='PhD', programme_begin_year=2024)
        curriculum = Curriculum.objects.create(programme=programme, name='PhD 2024', no_of_semester=8)
        phd = Batch.objects.create(name='PhD (Odd)', year=2024, curriculum=curriculum,
                                   discipline=self.cse.discipline)
        self.student('24PCS001', phd, [(1, 'Odd Semester', 'CS101', 'A')])
        Student.objects.filter(id_id='24PCS001').update(programme='PhD')
        semester = Semester.objects.create(curriculum=curriculum, semester_no=2)
        registration = ThesisRegistration.objects.create(
            student_id='24PCS001', semester=semester, credits=3,
            thesis_slot=ThesisSlot.objects.create(semester=semester, name='Thesis'))
        ThesisEvaluation.objects.create(registration=registration, block_number=1, grade='S')

        # As on the transcript: S carries no weight, so SPI 0.0 and the CPI so far.
        for params in ({'batch': 2024}, {'batch': 2024, 'semester': 2}):
            row = self.report(**params)['24PCS001']
            self.assertEqual((row['semester'], row['spi'], row['cpi']), (2, 0.0, 9.0), params)

    def test_bad_filters_are_refused(self):
        for params in ({}, {'batch': 'x'}, {'batch': 2024, 'semester': '0'},
                       {'batch': 2024, 'batch_id': self.older.id}):
            self.assertEqual(self.client.get(URL, params).status_code, 400, params)

    def test_the_filters_offer_every_discipline_batch(self):
        response = self.client.get('/aims/api/database/filters/')
        self.assertEqual(response.status_code, 200, response.content)
        labels = {(b['year'], b['label']) for b in response.json()['discipline_batches']}
        self.assertTrue({(2024, 'B.Tech CSE'), (2024, 'B.Tech ECE'), (2023, 'B.Tech CSE')} <= labels)
