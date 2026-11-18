"""A thesis topic the Dean sends back reaches the HOD, who can act on it again."""
from django.contrib.auth.models import User
from django.test import TestCase
from notifications.models import Notification
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_procedures.models import ThesisTopic
from applications.globals.models import Designation, ExtraInfo, Faculty, HoldsDesignation
from applications.programme_curriculum.models import (
    Batch,
    Curriculum,
    Discipline,
    Programme,
)

BASE = '/academic-procedures/api'


class ThesisTopicSendBackTests(TestCase):
    def setUp(self):
        programme = Programme.objects.create(category='PG', name='M.Tech', programme_begin_year=2025)
        curriculum = Curriculum.objects.create(programme=programme, name='M.Tech 2025', no_of_semester=4)
        discipline = Discipline.objects.create(name='Computer Science and Engineering', acronym='CSE')
        batch = Batch.objects.create(name='M.Tech AI & ML', discipline=discipline, year=2025,
                                     curriculum=curriculum)
        self.student_user = self.person('25MCS001', 'student', 'student')
        self.student = Student.objects.create(
            id=self.student_user.extrainfo, programme='M.Tech', batch=2025, batch_id=batch,
            category='GEN', curr_semester_no=3)
        self.supervisor = self.faculty('sup1')
        self.co_supervisor = self.faculty('cosup1')
        self.hod = self.person('hodcse', 'faculty', 'HOD (CSE)')
        self.dean = self.person('deanacad', 'faculty', 'Dean Academic')
        self.topic = ThesisTopic.objects.create(
            student=self.student, supervisor=self.supervisor, co_supervisor=self.co_supervisor,
            supervisor_consented=True, co_supervisor_consented=True, category='Regular',
            broad_area='Machine learning', research_theme='Graph learning', status='hod_approved')

    def person(self, username, user_type, designation):
        user = User.objects.create_user(username=username)
        ExtraInfo.objects.create(id=username, user=user, user_type=user_type, user_status='PRESENT')
        held, _ = Designation.objects.get_or_create(name=designation)
        HoldsDesignation.objects.create(user=user, working=user, designation=held)
        return user

    def faculty(self, username):
        return Faculty.objects.create(id=self.person(username, 'faculty', 'faculty').extrainfo)

    def as_user(self, user):
        client = APIClient()
        token, _ = Token.objects.get_or_create(user=user)
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client

    def dean_sends_back(self, remarks='Narrow the scope.'):
        return self.as_user(self.dean).post(
            f'{BASE}/dean/thesis/{self.topic.id}/review/', {'approve': False, 'remarks': remarks},
            format='json')

    def test_the_dean_sends_a_topic_back_with_remarks_and_everyone_is_told(self):
        response = self.dean_sends_back()

        self.assertEqual(response.status_code, 200)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.status, 'dean_rejected')
        self.assertEqual(self.topic.dean_remarks, 'Narrow the scope.')
        for user in (self.hod, self.student_user, self.supervisor.id.user, self.co_supervisor.id.user):
            self.assertTrue(Notification.objects.filter(recipient=user).exists(), user.username)

    def test_a_topic_without_a_co_supervisor_is_sent_back_too(self):
        self.topic.co_supervisor = None
        self.topic.co_supervisor_consented = False
        self.topic.save()

        response = self.dean_sends_back()

        self.assertEqual(response.status_code, 200)
        for user in (self.hod, self.student_user, self.supervisor.id.user):
            self.assertTrue(Notification.objects.filter(recipient=user).exists(), user.username)
        self.assertFalse(Notification.objects.filter(recipient=self.co_supervisor.id.user).exists())

    def test_the_hods_send_back_tells_the_co_supervisor_who_must_consent_again(self):
        self.dean_sends_back()
        Notification.objects.all().delete()

        self.as_user(self.hod).post(f'{BASE}/hod/thesis/{self.topic.id}/review/',
                                    {'approve': False, 'remarks': 'Revise.'}, format='json')

        for user in (self.student_user, self.supervisor.id.user, self.co_supervisor.id.user):
            self.assertTrue(Notification.objects.filter(recipient=user).exists(), user.username)

    def test_the_deans_rejected_tab_lists_what_they_sent_back(self):
        self.dean_sends_back()

        data = self.as_user(self.dean).get(f'{BASE}/dean/dashboard/').json()

        self.assertEqual([t['id'] for t in data['rejected']], [self.topic.id])
        self.assertEqual(data['pending'], [])

    def test_the_hod_sees_it_pending_and_can_approve_it_back_to_the_dean(self):
        self.dean_sends_back()
        hod = self.as_user(self.hod)
        self.assertEqual([t['id'] for t in hod.get(f'{BASE}/hod/dashboard/').json()['pending']],
                         [self.topic.id])

        response = hod.post(f'{BASE}/hod/thesis/{self.topic.id}/review/', {'approve': True},
                            format='json')

        self.assertEqual(response.status_code, 200)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.status, 'hod_approved')
        pending = self.as_user(self.dean).get(f'{BASE}/dean/dashboard/').json()['pending']
        self.assertEqual([t['id'] for t in pending], [self.topic.id])

    def test_the_hod_can_send_it_on_to_the_supervisor(self):
        self.dean_sends_back()

        response = self.as_user(self.hod).post(
            f'{BASE}/hod/thesis/{self.topic.id}/review/',
            {'approve': False, 'remarks': 'Revise as the Dean asked.'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.status, 'hod_rejected')
        self.assertEqual(self.topic.hod_remarks, 'Revise as the Dean asked.')
        self.assertFalse(self.topic.supervisor_consented)
        self.assertFalse(self.topic.co_supervisor_consented)

    def test_the_hod_cannot_act_on_a_topic_back_with_the_supervisor(self):
        self.topic.status = 'hod_rejected'
        self.topic.supervisor_consented = False
        self.topic.save()

        response = self.as_user(self.hod).post(
            f'{BASE}/hod/thesis/{self.topic.id}/review/', {'approve': True}, format='json')

        self.assertEqual(response.status_code, 403)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.status, 'hod_rejected')

    def test_another_disciplines_hod_cannot_act_on_it(self):
        self.dean_sends_back()
        other_hod = self.person('hodece', 'faculty', 'HOD (ECE)')

        response = self.as_user(other_hod).post(
            f'{BASE}/hod/thesis/{self.topic.id}/review/', {'approve': True}, format='json')

        self.assertEqual(response.status_code, 403)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.status, 'dean_rejected')
