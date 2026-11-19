import json

from django.contrib.auth.models import User
from django.test import TestCase
from notifications.models import Notification
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.globals.models import Designation, HoldsDesignation
from applications.programme_curriculum.models import Discipline, NewProposalFile, Proposal_Tracking

INWARD_FILES = '/programme_curriculum/faculty_inward_files'
COURSE_PROPOSALS = '/programme_curriculum/faculty_view_course_proposal'


class ProposalNotificationLinkTests(TestCase):
    """A course proposal's notifications open the React page where the recipient acts on it."""

    def setUp(self):
        professor = Designation.objects.create(name='Professor', full_name='Professor', type='academic')
        hod = Designation.objects.create(name='HOD (CSE)', full_name='HOD (CSE)', type='administrative')
        dean = Designation.objects.create(name='Dean Academic', full_name='Dean Academic', type='administrative')

        def user(username, *designations):
            u = User.objects.create_user(username=username)
            for d in designations:
                HoldsDesignation.objects.create(user=u, working=u, designation=d)
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=u).key}')
            return u, client

        self.uploader, self.uploader_client = user('prof1', professor)
        self.hod, self.hod_client = user('hod1', professor, hod)
        self.dean, _ = user('dean1', dean)
        self.discipline = Discipline.objects.create(name='Computer Science', acronym='CSE')
        self.proposal = NewProposalFile.objects.create(
            uploader='prof1', designation='Professor', code='CS999', name='Test Course',
            syllabus='-', ref_books='-')

    def send_to_hod(self):
        response = self.uploader_client.post(
            f'/programme_curriculum/api/filetracking/{self.proposal.id}/',
            json.dumps({'uploader': 'prof1', 'designation': 'Professor', 'receiverId': 'hod1',
                        'receiverDesignation': 'HOD (CSE)', 'discipline': self.discipline.id,
                        'remarks': ''}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201, response.content)
        return Proposal_Tracking.objects.get(file_id=str(self.proposal.id))

    def test_received_proposal_opens_inward_files_as_the_receiving_designation(self):
        self.send_to_hod()
        notification = Notification.objects.get(recipient=self.hod)
        self.assertEqual(notification.data['url'], INWARD_FILES)
        self.assertEqual(notification.data['role'], 'HOD (CSE)')
        self.assertEqual(notification.data['module'], 'Programme and Curriculum')

    def test_proposal_forwarded_by_the_hod_opens_inward_files_as_dean(self):
        tracking = self.send_to_hod()
        response = self.hod_client.post(
            f'/programme_curriculum/api/forward_course_forms/{tracking.id}/?username=hod1&des=HOD (CSE)',
            json.dumps({'uploader': 'hod1', 'designation': 'HOD (CSE)', 'receiverId': 'dean1',
                        'receiverDesignation': 'Dean Academic', 'discipline': self.discipline.id,
                        'fileId': self.proposal.id, 'remarks': ''}),
            content_type='application/json')
        self.assertLess(response.status_code, 400, response.content)
        notification = Notification.objects.get(recipient=self.dean)
        self.assertEqual(notification.data['url'], INWARD_FILES)
        self.assertEqual(notification.data['role'], 'Dean Academic')

    def test_rejected_proposal_opens_the_proposers_course_proposals(self):
        tracking = self.send_to_hod()
        response = self.hod_client.post(f'/programme_curriculum/api/reject_form/{tracking.id}/?des=HOD (CSE)')
        self.assertEqual(response.status_code, 200, response.content)
        notification = Notification.objects.get(recipient=self.uploader)
        self.assertEqual(notification.data['url'], COURSE_PROPOSALS)
        self.assertIn('Rejected', notification.verb)
