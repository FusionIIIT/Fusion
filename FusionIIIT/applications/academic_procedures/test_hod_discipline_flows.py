"""Every HOD screen works for an HOD role named by the discipline's full name.

For each approval an HOD gives (thesis topic change, committee change,
comprehensive exam, open seminar, teaching credit, examiner panel, TA
assignment) the HOD of a student's discipline must see the request on their
dashboard and be able to act on it whether the role reads "HOD (Design)" or
"HOD (Des.)", while the HOD of another discipline must neither see it nor act.
"""
from decimal import Decimal

from django.test import TestCase
from notifications.models import Notification

from applications.academic_information.models import Student
from applications.academic_procedures.models import (
    CommitteeMember,
    ComprehensiveExam,
    ComprehensiveExamAttempt,
    OpenSeminar,
    OpenSeminarAttempt,
    TeachingCreditAllocation,
    TeachingCreditEvaluationResponse,
    ThesisCommitteeChangeRequest,
    ThesisEvaluation,
    ThesisEvaluationScore,
    ThesisExaminerPanel,
    ThesisRegistration,
    ThesisTopicChangeRequest,
)
from applications.globals.models import Faculty
from applications.programme_curriculum.models import (
    Batch,
    Course,
    Discipline,
    Semester,
    ThesisSlot,
)

from .test_hod_discipline_names import BASE, HodFixtures


class HodFlowTests(HodFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.hod_design = self.person('hoddes', 'faculty', 'HOD (Design)')
        self.hod_des = self.person('hoddes2', 'faculty', 'HOD (Des.)')
        self.hod_liberal_arts = self.person('hodla', 'faculty', 'HOD (Liberal Arts)')
        self.hod_la = self.person('hodla2', 'faculty', 'HOD (LA)')
        self.hod_cse = self.person('hodcse', 'faculty', 'HOD (CSE)')
        self.semester = Semester.objects.create(curriculum=self.curriculum, semester_no=3)

    # -- helpers -------------------------------------------------------------

    def listed_ids(self, user, dashboard, key='pending'):
        response = self.as_user(user).get(f'{BASE}/{dashboard}')
        self.assertEqual(response.status_code, 200, response.content)
        return [row['id'] for row in response.json()[key]]

    def check_flow(self, make, dashboard, action, body, done_status, key='pending', shown_id=None):
        """`make(student)` adds a request waiting for the HOD of the student's
        discipline; `action` is the URL that decides it."""
        shown_id = shown_id or (lambda item: item.id)
        design_item = make(self.design_student)
        la_item = make(self.la_student)
        before = design_item.status

        for hod in (self.hod_design, self.hod_des):
            with self.subTest(sees=hod.username):
                listed = self.listed_ids(hod, dashboard, key)
                self.assertIn(shown_id(design_item), listed)
                self.assertNotIn(shown_id(la_item), listed)
        for hod in (self.hod_liberal_arts, self.hod_la):
            with self.subTest(sees=hod.username):
                listed = self.listed_ids(hod, dashboard, key)
                self.assertIn(shown_id(la_item), listed)
                self.assertNotIn(shown_id(design_item), listed)

        with self.subTest('another discipline\'s HOD'):
            self.assertNotIn(shown_id(design_item), self.listed_ids(self.hod_cse, dashboard, key))
            response = self.as_user(self.hod_cse).post(
                f'{BASE}/{action(design_item)}', body, format='json')
            self.assertEqual(response.status_code, 403)
            design_item.refresh_from_db()
            self.assertEqual(design_item.status, before)

        with self.subTest('HOD (Des.) decides'):
            response = self.as_user(self.hod_des).post(
                f'{BASE}/{action(design_item)}', body, format='json')
            self.assertEqual(response.status_code, 200, response.content)
            design_item.refresh_from_db()
            self.assertEqual(design_item.status, done_status)

        with self.subTest('HOD (Liberal Arts) decides'):
            response = self.as_user(self.hod_liberal_arts).post(
                f'{BASE}/{action(la_item)}', body, format='json')
            self.assertEqual(response.status_code, 200, response.content)
            la_item.refresh_from_db()
            self.assertEqual(la_item.status, done_status)

    def approved_topic(self, student):
        return self.topic(student, status='dean_approved')

    # -- thesis topic and committee changes ------------------------------------

    def test_thesis_topic_change_request(self):
        self.check_flow(
            make=lambda s: ThesisTopicChangeRequest.objects.create(
                thesis=self.approved_topic(s), status='hod_pending'),
            dashboard='hod/thesis/change-requests/',
            action=lambda cr: f'hod/thesis/change-request/{cr.id}/review/',
            body={'approve': True}, done_status='dean_pending')

    def test_thesis_committee_change_request(self):
        self.check_flow(
            make=lambda s: ThesisCommitteeChangeRequest.objects.create(
                thesis=self.approved_topic(s), status='hod_pending'),
            dashboard='hod/thesis/committee-change-requests/',
            action=lambda cr: f'hod/thesis/committee-change/{cr.id}/review/',
            body={'approve': True}, done_status='dean_pending')

    # -- comprehensive exam ---------------------------------------------------

    def exam(self, student, status='dpgc_pending'):
        self.approved_topic(student)
        return ComprehensiveExam.objects.create(
            student=student, supervisor=self.supervisor, entry_qualification='masters', status=status)

    def test_comprehensive_exam_convener_dpgc_approval(self):
        self.check_flow(
            make=self.exam,
            dashboard='hod/comprehensive-exam/dpgc-dashboard/',
            action=lambda exam: f'hod/comprehensive-exam/{exam.id}/dpgc-approve/',
            body={'approve': True}, done_status='in_progress')

    def test_comprehensive_exam_convener_pgcs_review(self):
        self.check_flow(
            make=lambda s: ComprehensiveExamAttempt.objects.create(
                exam=self.exam(s, status='in_progress'), attempt_number=1, status='pgcs_pending'),
            dashboard='hod/comprehensive-exam/pgcs-dashboard/',
            action=lambda attempt: f'hod/comprehensive-exam/attempt/{attempt.id}/pgcs-review/',
            body={'approve': True}, done_status='dean_pending',
            shown_id=lambda attempt: attempt.exam_id)

    # -- open seminar -----------------------------------------------------------

    def seminar(self, student, status='hod_pending'):
        self.approved_topic(student)
        return OpenSeminar.objects.create(student=student, supervisor=self.supervisor, status=status)

    def test_open_seminar_convener_dpgc_review(self):
        self.check_flow(
            make=self.seminar,
            dashboard='hod/open-seminar/dpgc-dashboard/',
            action=lambda seminar: f'hod/open-seminar/{seminar.id}/dpgc-review/',
            body={'approve': True}, done_status='dean_pending')

    def test_open_seminar_review_after_the_rpc(self):
        self.check_flow(
            make=lambda s: OpenSeminarAttempt.objects.create(
                open_seminar=self.seminar(s, status='in_progress'), attempt_number=1,
                status='hod_review_pending'),
            dashboard='hod/open-seminar/review-dashboard/',
            action=lambda attempt: f'hod/open-seminar/attempt/{attempt.id}/review/',
            body={'approve': True}, done_status='dean_pending',
            shown_id=lambda attempt: attempt.open_seminar_id)

    # -- teaching credit ----------------------------------------------------------

    def course(self, code):
        return Course.objects.create(code=code, name=f'Course {code}', syllabus='-', ref_books='-')

    def test_teaching_credit_allocation(self):
        course = self.course('DS101')
        self.check_flow(
            make=lambda s: TeachingCreditAllocation.objects.create(
                student=s, semester=self.semester, choice_1=course, status='pending'),
            dashboard='hod/teaching-credit/dashboard/',
            action=lambda reg: f'hod/teaching-credit/{reg.id}/decide/',
            body={'allocate': True, 'allocated_course': course.id}, done_status='allocated')

    def test_teaching_credit_completion(self):
        course = self.course('DS102')

        def allocated(student):
            reg = TeachingCreditAllocation.objects.create(
                student=student, semester=self.semester, choice_1=course,
                allocated_course=course, status='allocated')
            TeachingCreditEvaluationResponse.objects.create(registration=reg, respondent=self.la_student)
            return reg

        self.check_flow(
            make=allocated,
            dashboard='hod/teaching-credit/dashboard/', key='awaiting_completion',
            action=lambda reg: f'hod/teaching-credit/{reg.id}/complete/',
            body={'result': 'satisfactory'}, done_status='completed')

    # -- thesis examiner panel ----------------------------------------------------

    def candidates(self):
        return [{'name': f'Examiner {n}', 'position': 'Professor', 'address': 'IIT',
                 'phone': '0', 'fax': '', 'email': f'e{n}@example.org'} for n in range(1, 5)]

    def test_thesis_examiner_panel(self):
        slot = ThesisSlot.objects.create(semester=self.semester, name='Thesis', evaluation_type='decimal')
        registration = ThesisRegistration.objects.create(
            student=self.design_student, thesis_slot=slot, semester=self.semester, status='verified',
            thesis_topic=self.approved_topic(self.design_student))
        evaluation = ThesisEvaluation.objects.create(registration=registration, block_number=1)
        ThesisEvaluationScore.objects.create(evaluation=evaluation, supervisor_score=Decimal('8.0'))
        batch = self.design_student.batch_id
        for hod in (self.hod_design, self.hod_des, self.hod_cse):
            Faculty.objects.create(id=hod.extrainfo)

        for hod in (self.hod_design, self.hod_des):
            with self.subTest(sees=hod.username):
                response = self.as_user(hod).get(f'{BASE}/hod/thesis-examiner-panels/')
                self.assertEqual(response.status_code, 200)
                groups = response.json()['groups']
                self.assertEqual(
                    [(g['discipline_acronym'], [(b['batch_id'], b['ready_for_panel']) for b in g['batches']])
                     for g in groups],
                    [('Des.', [(batch.id, True)])])

        body = {'discipline_id': self.design.id, 'year': batch.year,
                'batches': [{'batch_id': batch.id, 'candidates': self.candidates()}]}
        with self.subTest('another discipline\'s HOD'):
            response = self.as_user(self.hod_cse).get(f'{BASE}/hod/thesis-examiner-panels/')
            self.assertEqual(response.json()['groups'], [])
            response = self.as_user(self.hod_cse).post(
                f'{BASE}/hod/thesis-examiner-panels/submit/', body, format='json')
            self.assertEqual(response.status_code, 403)
            self.assertFalse(ThesisExaminerPanel.objects.exists())

        with self.subTest('HOD (Design) submits'):
            response = self.as_user(self.hod_design).post(
                f'{BASE}/hod/thesis-examiner-panels/submit/', body, format='json')
            self.assertEqual(response.status_code, 200, response.content)
            panel = ThesisExaminerPanel.objects.get(batch=batch)
            self.assertEqual(panel.status, 'dean_pending')
            self.assertEqual(panel.candidates.count(), 4)

    # -- teaching assistant assignment -------------------------------------------

    def test_ta_assignment_students_by_full_discipline_name(self):
        ece = Discipline.objects.create(name='Electronics and Communication Engineering', acronym='ECE')
        batch = Batch.objects.create(name='ECE 2025', discipline=ece, year=2025, curriculum=self.curriculum)
        user = self.person('25MEC001', 'student', 'student')
        Student.objects.create(id=user.extrainfo, programme='M.Tech', batch=2025, batch_id=batch,
                               category='GEN', curr_semester_no=1, specialization='PNC')

        for n, role in enumerate(('HOD (ECE)', 'HOD (Electronics and Communication Engineering)')):
            with self.subTest(role=role):
                hod = self.person(f'hodece{n}', 'faculty', role)
                response = self.as_user(hod).get(f'{BASE}/hod/students/')
                self.assertEqual(response.status_code, 200, response.content)
                self.assertEqual([s['username'] for s in response.json()['students']], ['25MEC001'])

        with self.subTest('an HOD with no TA mapping'):
            response = self.as_user(self.hod_design).get(f'{BASE}/hod/students/')
            self.assertEqual(response.status_code, 403)

    # -- notifications to the HOD --------------------------------------------------

    def test_a_forwarded_topic_notifies_every_holder_of_either_spelling(self):
        topic = self.topic(self.design_student, status='supervisor_pending')
        topic.supervisor_consented = False
        topic.save()
        members = [Faculty.objects.create(id=self.person(f'rpc{n}', 'faculty', 'Professor').extrainfo)
                   for n in (1, 2)]

        response = self.as_user(self.supervisor.id.user).post(
            f'{BASE}/supervisor/thesis/{topic.id}/review/',
            {'supervisor_consented': True, 'committee': [m.id_id for m in members]}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        topic.refresh_from_db()
        self.assertEqual(topic.status, 'hod_pending')
        self.assertEqual(CommitteeMember.objects.filter(thesis=topic).count(), 3)

        notified = set(Notification.objects.filter(verb='Thesis topic pending your review')
                       .values_list('recipient__username', flat=True))
        self.assertEqual(notified, {'hoddes', 'hoddes2'})
