"""A published result for the student's current semester waits for that
semester's course feedback. Older terms, unpublished results and a form with
nothing to fill are never held back."""
import json

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from applications.academic_information.models import Student
from applications.academic_procedures.models import (
    FeedbackFilled, FeedbackQuestion, course_registration,
)
from applications.examination.api import views
from applications.examination.models import ResultAnnouncement
from applications.globals.models import ExtraInfo, Faculty
from applications.online_cms.models import Student_grades
from applications.programme_curriculum.models import (
    Batch, Course, CourseInstructor, Curriculum, Discipline, Programme,
    Semester,
)


class FeedbackGateTests(TestCase):
    def setUp(self):
        programme = Programme.objects.create(
            category='UG', name='Test B.Tech', programme_begin_year=2026)
        discipline = Discipline.objects.create(
            name='Test Computer Science', acronym='TCSE')
        curriculum = Curriculum.objects.create(
            programme=programme, name='Test Curriculum', no_of_semester=8)
        self.batch = Batch.objects.create(
            name='B.Tech', discipline=discipline, year=2026,
            curriculum=curriculum)
        semesters = {n: Semester.objects.create(curriculum=curriculum, semester_no=n)
                     for n in (1, 2)}

        user = User.objects.create_user(username='26TCS001')
        extra = ExtraInfo.objects.create(
            id='26TCS001', user=user, user_type='student')
        self.student = Student.objects.create(
            id=extra, programme='B.Tech', batch=2026, batch_id=self.batch,
            category='GEN', curr_semester_no=2)
        self.user = user

        faculty_user = User.objects.create_user(
            username='TFAC001', first_name='Test', last_name='Faculty')
        faculty = Faculty.objects.create(id=ExtraInfo.objects.create(
            id='TFAC001', user=faculty_user, user_type='faculty'))

        for semester_no, semester_type, year, code in (
                (1, 'Odd Semester', 2026, 'TT1001'),
                (2, 'Even Semester', 2027, 'TT2001')):
            course = Course.objects.create(
                code=code, name=code, credit=4, syllabus='', ref_books='',
                max_seats=60)
            CourseInstructor.objects.create(
                course_id=course, instructor_id=faculty, year=year,
                semester_type=semester_type)
            course_registration.objects.create(
                student_id=self.student, semester_id=semesters[semester_no],
                course_id=course, session='2026-27',
                semester_type=semester_type, working_year=year)
            Student_grades.objects.create(
                course_id=course, semester=semester_no, year=year,
                roll_no='26TCS001', grade='A', batch=2026,
                academic_year='2026-27', semester_type=semester_type)
            ResultAnnouncement.objects.create(
                batch=self.batch, semester=semester_no,
                semester_type=semester_type, announced=True)

        FeedbackQuestion.objects.create(
            section='contents', text='Was it clear?', order=1)
        self.factory = APIRequestFactory()

    def check_result(self, semester_no, semester_type):
        request = self.factory.post('/x/', {
            'semester_no': semester_no, 'semester_type': semester_type},
            format='json')
        force_authenticate(request, user=self.user)
        return json.loads(views.CheckResultView.as_view()(request).content)

    def credit_summary_semesters(self):
        request = self.factory.get('/x/')
        force_authenticate(request, user=self.user)
        data = views.StudentCreditSummaryView.as_view()(request).data
        return [sem['semester_no'] for sem in data['semesters']]

    def test_an_older_semester_is_never_held_back(self):
        self.assertTrue(self.check_result(1, 'Odd Semester')['success'])

    def test_the_current_semester_waits_for_feedback(self):
        result = self.check_result(2, 'Even Semester')
        self.assertFalse(result['success'])
        self.assertTrue(result['require_feedback'])

        FeedbackFilled.objects.create(student=self.student, semester_no=2)
        self.assertTrue(self.check_result(2, 'Even Semester')['success'])

    def test_an_unpublished_result_says_so_before_asking_for_feedback(self):
        ResultAnnouncement.objects.filter(semester=2).update(announced=False)
        result = self.check_result(2, 'Even Semester')
        self.assertEqual(result['message'], 'Results not announced yet.')
        self.assertNotIn('require_feedback', result)

    def test_a_form_with_nothing_to_fill_does_not_block(self):
        FeedbackQuestion.objects.all().delete()
        self.assertTrue(self.check_result(2, 'Even Semester')['success'])

        FeedbackQuestion.objects.create(
            section='contents', text='Was it clear?', order=1)
        CourseInstructor.objects.filter(semester_type='Even Semester').delete()
        self.assertTrue(self.check_result(2, 'Even Semester')['success'])

    def test_the_result_sheet_follows_the_same_rule(self):
        def sheet(payload):
            request = self.factory.post('/x/', payload, format='json')
            force_authenticate(request, user=self.user)
            return views.GenerateStudentResultPDFAPI.as_view()(request)

        held = sheet({'semester_no': 2, 'semester_type': 'Even Semester'})
        self.assertTrue(json.loads(held.content)['require_feedback'])
        self.assertEqual(sheet({'semester_type': 'Even Semester'}).status_code, 400)

        FeedbackFilled.objects.create(student=self.student, semester_no=2)
        released = sheet({'semester_no': 2, 'semester_type': 'Even Semester'})
        self.assertEqual(released['Content-Type'], 'application/pdf')

    def test_the_credit_summary_holds_back_the_same_semester(self):
        self.assertEqual(self.credit_summary_semesters(), [1])
        FeedbackFilled.objects.create(student=self.student, semester_no=2)
        self.assertEqual(self.credit_summary_semesters(), [1, 2])
