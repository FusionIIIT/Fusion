import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Calendar, Student
from applications.academic_procedures.models import (
    InitialRegistration,
    StudentRegistrationChecks,
)
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


class PreRegistrationSubmitTests(TestCase):
    """A pre-registration is saved whole, with its done mark, or not at all."""

    def setUp(self):
        programme = Programme.objects.create(category='UG', name='B.Des', programme_begin_year=2024)
        curriculum = Curriculum.objects.create(programme=programme, name='B.Des 2024', no_of_semester=8)
        discipline = Discipline.objects.create(name='Design', acronym='DS')
        batch = Batch.objects.create(name='B.Des', discipline=discipline, year=2024, curriculum=curriculum)
        Semester.objects.create(curriculum=curriculum, semester_no=3)
        self.semester = Semester.objects.create(curriculum=curriculum, semester_no=4)

        def course(code):
            return Course.objects.create(code=code, name=code, credit=4, syllabus='', ref_books='')

        self.core, self.elective_a, self.elective_b = course('DS2001'), course('OE2001'), course('OE2002')
        self.core_slot = CourseSlot.objects.create(semester=self.semester, name='DS4', type='Design')
        self.core_slot.courses.add(self.core)
        self.elective_slot = CourseSlot.objects.create(semester=self.semester, name='OE1',
                                                       type='Open Elective')
        self.elective_slot.courses.add(self.elective_a, self.elective_b)

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
