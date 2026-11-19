import os
from unittest import mock

from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.core import mail
from django.test import TestCase, override_settings

from applications.academic_information.models import Student
from applications.academic_procedures.models import ReviewInvitation, ThesisSubmission, ThesisTopic
from applications.academic_procedures.utils import send_invitation_email, send_review_form_email
from applications.globals.models import Designation, ExtraInfo, Faculty, HoldsDesignation
from applications.programme_curriculum.models import Batch, Curriculum, Discipline, Programme

FRONTEND = 'https://fusion.example.org'


@mock.patch.dict(os.environ, {'FRONTEND_URL': FRONTEND})
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ReviewInvitationAdminTests(TestCase):
    """The admin shows the same examiner links that the invitation emails send."""

    def setUp(self):
        programme = Programme.objects.create(category='PhD', name='PhD', programme_begin_year=2024)
        curriculum = Curriculum.objects.create(programme=programme, name='PhD 2024', no_of_semester=8)
        discipline = Discipline.objects.create(name='Computer Science and Engineering', acronym='CSE')
        batch = Batch.objects.create(name='PhD', discipline=discipline, year=2024, curriculum=curriculum)
        student = Student.objects.create(id=self.person('24PCS001', 'student'), programme='PhD',
                                         batch=2024, batch_id=batch, category='GEN', curr_semester_no=3)
        supervisor = Faculty.objects.create(id=self.person('sup1', 'faculty'))
        topic = ThesisTopic.objects.create(
            student=student, supervisor=supervisor, supervisor_consented=True, category='Regular',
            broad_area='Machine learning', research_theme='Graph learning', status='hod_approved')
        submission = ThesisSubmission.objects.create(thesis=topic, synopsis='s.pdf', thesis_report='r.pdf')
        self.invitation = ReviewInvitation.objects.create(
            submission=submission, prof_name='Prof. X', prof_position='Professor', prof_address='-',
            prof_phone='0', prof_email='x@example.org')
        admin_user = User.objects.create_superuser(username='root', email='root@example.org', password='pw')
        # Fusion's login handler (signal and middleware) sets up the session's designations; a
        # superuser with no Fusion profile needs none of it, so mark it done as a login would.
        with mock.patch.object(user_logged_in, 'send', return_value=[]):
            self.client.force_login(admin_user)
        session = self.client.session
        session['function_executed'] = True
        session.save()

    def person(self, username, user_type):
        user = User.objects.create_user(username=username)
        held, _ = Designation.objects.get_or_create(name=user_type)
        HoldsDesignation.objects.create(user=user, working=user, designation=held)
        return ExtraInfo.objects.create(id=username, user=user, user_type=user_type, user_status='PRESENT')

    def test_change_page_shows_the_emailed_links(self):
        token = self.invitation.token
        response = self.client.get(f'/admin/academic_procedures/reviewinvitation/{self.invitation.id}/change/')
        self.assertEqual(response.status_code, 200)
        for path in (f'/thesis-invitation/{token}/accept', f'/thesis-invitation/{token}/reject',
                     f'/thesis-evaluation/{token}'):
            self.assertContains(response, f'href="{FRONTEND}{path}"')

    def test_emails_send_the_same_links(self):
        token = self.invitation.token
        send_invitation_email(self.invitation)
        send_review_form_email(self.invitation)
        bodies = ' '.join(m.body for m in mail.outbox)
        self.assertEqual(len(mail.outbox), 2)
        for path in (f'/thesis-invitation/{token}/accept', f'/thesis-invitation/{token}/reject',
                     f'/thesis-evaluation/{token}'):
            self.assertIn(f'{FRONTEND}{path}', bodies)
