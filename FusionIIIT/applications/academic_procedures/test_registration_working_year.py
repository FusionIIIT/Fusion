from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from applications.academic_information.models import Student
from applications.academic_procedures.models import course_registration, session_working_year
from applications.globals.models import ExtraInfo
from applications.programme_curriculum.models import (
    Batch,
    Course,
    Curriculum,
    Discipline,
    Programme,
    Semester,
)


class SessionWorkingYearTests(SimpleTestCase):
    """The working year is the calendar year the term runs in."""

    def test_an_odd_semester_runs_in_the_first_year_of_the_session(self):
        self.assertEqual(session_working_year('2026-27', 'Odd Semester'), 2026)

    def test_even_and_summer_semesters_run_in_the_second_year(self):
        self.assertEqual(session_working_year('2026-27', 'Even Semester'), 2027)
        self.assertEqual(session_working_year('2025-2026', 'Summer Semester'), 2026)

    def test_an_unreadable_session_gives_no_year(self):
        for session in (None, '', '1999', 'Even 2026'):
            self.assertIsNone(session_working_year(session, 'Even Semester'), session)

    def test_a_missing_semester_type_gives_no_year(self):
        for semester_type in (None, '', '  '):
            self.assertIsNone(session_working_year('2026-27', semester_type), semester_type)


class RegistrationWorkingYearTests(TestCase):
    """No way of creating a registration leaves out the year its term runs in."""

    def setUp(self):
        programme = Programme.objects.create(category='UG', name='B.Tech', programme_begin_year=2024)
        curriculum = Curriculum.objects.create(programme=programme, name='B.Tech 2024', no_of_semester=8)
        discipline = Discipline.objects.create(name='Computer Science', acronym='CSE')
        batch = Batch.objects.create(name='B.Tech', discipline=discipline, year=2024, curriculum=curriculum)
        self.semester = Semester.objects.create(curriculum=curriculum, semester_no=6)
        self.courses = [
            Course.objects.create(code=code, name=code, credit=3, syllabus='', ref_books='')
            for code in ('CS3001', 'CS3002')
        ]
        user = User.objects.create_user(username='24BCS001')
        extra = ExtraInfo.objects.create(id='24BCS001', user=user, user_type='student', user_status='PRESENT')
        self.student = Student.objects.create(id=extra, programme='B.Tech', batch=2024, batch_id=batch,
                                              category='GEN', curr_semester_no=6)

    def registration(self, course=None, **fields):
        return course_registration(student_id=self.student, semester_id=self.semester,
                                   course_id=course or self.courses[0], **fields)

    def stored_year(self, registration):
        return course_registration.objects.values_list('working_year', flat=True).get(pk=registration.pk)

    def test_create_fills_the_year_from_the_session(self):
        created = course_registration.objects.create(
            student_id=self.student, semester_id=self.semester, course_id=self.courses[0],
            session='2026-27', semester_type='Even Semester')
        self.assertEqual(self.stored_year(created), 2027)

    def test_bulk_create_fills_the_year_of_every_row(self):
        course_registration.objects.bulk_create([
            self.registration(course, session='2026-27', semester_type='Odd Semester')
            for course in self.courses
        ])
        self.assertEqual(
            list(course_registration.objects.values_list('working_year', flat=True)), [2026, 2026])

    def test_a_year_given_by_the_caller_is_kept(self):
        registration = self.registration(session='2026-27', semester_type='Even Semester', working_year=2030)
        registration.save()
        self.assertEqual(self.stored_year(registration), 2030)

    def test_saving_only_some_fields_still_stores_the_filled_year(self):
        registration = self.registration(semester_type='Even Semester')
        registration.save()
        self.assertIsNone(self.stored_year(registration))

        registration.session = '2026-27'
        registration.save(update_fields=['session'])
        self.assertEqual(self.stored_year(registration), 2027)

    def test_an_unreadable_session_is_saved_without_a_year(self):
        registration = self.registration(session='1999', semester_type='Even Semester')
        registration.save()
        self.assertIsNone(self.stored_year(registration))
