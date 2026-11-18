import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Calendar, Student
from applications.academic_procedures.models import (
    InitialRegistration,
    StudentRegistrationChecks,
    course_registration,
)
from applications.online_cms.models import Student_grades
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.programme_curriculum.models import (
    Batch,
    Course,
    CourseSlot,
    Curriculum,
    Discipline,
    Programme,
    Semester,
)

SUBMIT_URL = '/academic-procedures/api/stu/preregistration/submit/'
FORM_URL = '/academic-procedures/api/stu/preregistration/'


class PreRegistrationCase(TestCase):
    """A B.Des student pre-registering for semester 4, with the window open."""

    def setUp(self):
        programme = Programme.objects.create(category='UG', name='B.Des', programme_begin_year=2024)
        curriculum = Curriculum.objects.create(programme=programme, name='B.Des 2024', no_of_semester=8)
        discipline = Discipline.objects.create(name='Design', acronym='DS')
        batch = Batch.objects.create(name='B.Des', discipline=discipline, year=2024, curriculum=curriculum)
        self.past_semester = Semester.objects.create(curriculum=curriculum, semester_no=3)
        self.semester = Semester.objects.create(curriculum=curriculum, semester_no=4)

        def course(code):
            return Course.objects.create(code=code, name=code, credit=4, syllabus='', ref_books='')

        self.core, self.elective_a, self.elective_b = course('DS2001'), course('OE2001'), course('OE2002')
        self.core_slot = CourseSlot.objects.create(semester=self.semester, name='DS4', type='Design')
        self.core_slot.courses.add(self.core)
        self.elective_slot = CourseSlot.objects.create(semester=self.semester, name='OE1',
                                                       type='Open Elective')
        self.elective_slot.courses.add(self.elective_a, self.elective_b)
        self.backlog_slot = CourseSlot.objects.create(semester=self.semester, name='BL1', type='Backlog')
        self.backlog_slot_2 = CourseSlot.objects.create(semester=self.semester, name='BL2', type='Backlog')
        self.repeat_course = course('DS1001')
        self.backlog_slot.courses.add(self.repeat_course)
        self.backlog_slot_2.courses.add(self.repeat_course)

        user = User.objects.create_user(username='24BDS049')
        extra = ExtraInfo.objects.create(id='24BDS049', user=user, user_type='student',
                                         user_status='PRESENT')
        designation, _ = Designation.objects.get_or_create(name='student')
        HoldsDesignation.objects.create(user=user, working=user, designation=designation)
        self.student = Student.objects.create(id=extra, programme='B.Des', batch=2024, batch_id=batch,
                                              category='GEN', curr_semester_no=3)

        today = datetime.date.today()
        Calendar.objects.create(description=f'Pre Registration 4 {today.year}',
                                from_date=today - datetime.timedelta(days=1),
                                to_date=today + datetime.timedelta(days=1))

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}')

    def submit(self, registrations, backlog=()):
        return self.client.post(SUBMIT_URL, {'registrations': registrations,
                                             'backlog_registrations': list(backlog)}, format='json')

    def choice(self, slot, course, priority=1):
        return {'slot_id': slot.id, 'course_id': course.id, 'priority': priority}

    def saved_courses(self):
        return sorted(InitialRegistration.objects.filter(student_id=self.student)
                      .values_list('course_id__code', flat=True))

    def is_done(self):
        return StudentRegistrationChecks.objects.filter(
            student_id=self.student, semester_id=self.semester, pre_registration_flag=True).exists()



class PreRegistrationSubmitTests(PreRegistrationCase):
    """A pre-registration is saved whole, with its done mark, or not at all."""

    def test_a_submit_saves_every_choice_and_marks_pre_registration_done(self):
        response = self.submit([self.choice(self.core_slot, self.core),
                                self.choice(self.elective_slot, self.elective_a, 1),
                                self.choice(self.elective_slot, self.elective_b, 2)])
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(self.saved_courses(), ['DS2001', 'OE2001', 'OE2002'])
        self.assertTrue(self.is_done())

    def test_a_submit_refused_part_way_saves_nothing(self):
        response = self.submit([self.choice(self.core_slot, self.core)],
                               backlog=[{'slot_id': self.core_slot.id, 'course_id': self.core.id,
                                         'prev_registration_id': 999999, 'priority': 1}])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.saved_courses(), [])
        self.assertFalse(self.is_done())

    def test_a_submit_that_fails_to_save_keeps_nothing(self):
        with self.assertLogs('applications.academic_procedures.api.views', level='ERROR'):
            response = self.submit([self.choice(self.core_slot, self.core),
                                    self.choice(self.elective_slot, self.elective_a),
                                    self.choice(self.elective_slot, self.elective_a)])
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'could not be saved', response.content)
        self.assertEqual(self.saved_courses(), [])
        self.assertFalse(self.is_done())

    def test_choices_left_by_an_unfinished_submit_are_replaced(self):
        InitialRegistration.objects.create(student_id=self.student, semester_id=self.semester,
                                           course_slot_id=self.core_slot, course_id=self.core, priority=1)
        response = self.submit([self.choice(self.core_slot, self.core),
                                self.choice(self.elective_slot, self.elective_b)])
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(self.saved_courses(), ['DS2001', 'OE2002'])
        self.assertTrue(self.is_done())

    def test_a_completed_pre_registration_is_not_submitted_again(self):
        self.assertEqual(self.submit([self.choice(self.core_slot, self.core)]).status_code, 201)
        response = self.submit([self.choice(self.elective_slot, self.elective_a)])
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'already submitted', response.content)
        self.assertEqual(self.saved_courses(), ['DS2001'])


class BacklogEligibilityTests(PreRegistrationCase):
    """A backlog or improvement repeats the latest attempt at a course with a
    backlog grade (F, X, CD) or an improvement grade (C, D+, D), once."""

    def attempt(self, grade, session='2025-26', semester_type='Odd Semester', registration_type='Regular'):
        registration = course_registration.objects.create(
            student_id=self.student, working_year=int(session[:4]), semester_id=self.past_semester,
            course_id=self.repeat_course, session=session, semester_type=semester_type,
            registration_type=registration_type)
        if grade:
            Student_grades.objects.create(
                course_id=self.repeat_course, roll_no='24BDS049', grade=grade, batch=2024,
                semester=3, year=int(session[:4]), academic_year=session, semester_type=semester_type)
        return registration

    def repeat(self, registration, slot=None):
        return {'slot_id': (slot or self.backlog_slot).id, 'course_id': self.repeat_course.id,
                'prev_registration_id': registration.id if registration else None, 'priority': 1}

    def submit_repeats(self, *repeats):
        return self.submit([self.choice(self.core_slot, self.core)], backlog=repeats)

    def saved_repeat(self):
        return list(InitialRegistration.objects.filter(student_id=self.student, course_slot_id=self.backlog_slot)
                    .values_list('registration_type', 'old_course_registration_id'))

    def test_a_failed_course_is_repeated_as_a_backlog(self):
        failed = self.attempt('F')
        response = self.submit_repeats(self.repeat(failed))
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(self.saved_repeat(), [('Backlog', failed.id)])

    def test_a_d_plus_is_repeated_as_an_improvement(self):
        low = self.attempt('D+')
        response = self.submit_repeats(self.repeat(low))
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(self.saved_repeat(), [('Improvement', low.id)])

    def test_a_course_passed_with_c_plus_cannot_be_repeated(self):
        passed = self.attempt('C+')
        response = self.submit_repeats(self.repeat(passed))
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'DS1001 cannot be repeated with grade C+', response.content)
        self.assertEqual(self.saved_courses(), [])
        self.assertFalse(self.is_done())

    def test_a_course_still_in_progress_cannot_be_repeated(self):
        # 23BSM022 named an Extra Credits course they were still taking.
        current = self.attempt(None, session='2026-27')
        response = self.submit_repeats(self.repeat(current))
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'no result yet', response.content)
        self.assertEqual(self.saved_courses(), [])

    def test_only_the_latest_attempt_at_a_course_can_be_repeated(self):
        first_try = self.attempt('F', session='2024-25')
        self.attempt('B', session='2025-26', registration_type='Backlog')
        response = self.submit_repeats(self.repeat(first_try))
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'taken again later', response.content)
        self.assertEqual(self.saved_courses(), [])

    def test_one_registration_cannot_be_repeated_in_two_backlog_slots(self):
        failed = self.attempt('F')
        response = self.submit_repeats(self.repeat(failed), self.repeat(failed, self.backlog_slot_2))
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'more than one backlog slot', response.content)
        self.assertEqual(self.saved_courses(), [])

    def test_a_backlog_must_name_the_registration_it_repeats(self):
        response = self.submit_repeats(self.repeat(None))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.saved_courses(), [])

    def test_the_form_offers_only_registrations_that_can_be_repeated(self):
        failed = self.attempt('F', session='2024-25')
        other = Course.objects.create(code='DS1002', name='DS1002', credit=4, syllabus='', ref_books='')
        low = course_registration.objects.create(
            student_id=self.student, working_year=2025, semester_id=self.past_semester, course_id=other,
            session='2025-26', semester_type='Odd Semester')
        Student_grades.objects.create(course_id=other, roll_no='24BDS049', grade='D', batch=2024, semester=3,
                                      year=2025, academic_year='2025-26', semester_type='Odd Semester')
        passed = course_registration.objects.create(
            student_id=self.student, working_year=2025, semester_id=self.past_semester, course_id=self.core,
            session='2025-26', semester_type='Odd Semester')
        Student_grades.objects.create(course_id=self.core, roll_no='24BDS049', grade='B', batch=2024, semester=3,
                                      year=2025, academic_year='2025-26', semester_type='Odd Semester')

        response = self.client.get(FORM_URL)

        self.assertEqual(response.status_code, 200, response.content)
        backlog = next(slot for slot in response.json() if slot['slot_name'] == 'BL1')
        offered = {(row['id'], row['grade'], row['repeat_as']) for row in backlog['prev_registrations']}
        self.assertEqual(offered, {(failed.id, 'F', 'Backlog'), (low.id, 'D', 'Improvement')})
        self.assertNotIn(passed.id, {row['id'] for row in backlog['prev_registrations']})
