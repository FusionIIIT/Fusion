import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo
from applications.globals.models_profile import (Achievement, Course, Education, Experience, Has, Patent,
                                                 Project, Publication, Skill)
from applications.programme_curriculum.models import Batch, Curriculum, Discipline, Programme


def delete_url(record_id):
    return f'/api/profile_delete/{record_id}/'


class ProfileDeleteTests(TestCase):
    """A student removes entries from their own profile, and only their own."""

    def setUp(self):
        programme = Programme.objects.create(category='UG', name='B.Tech', programme_begin_year=2024)
        curriculum = Curriculum.objects.create(programme=programme, name='B.Tech 2024', no_of_semester=8)
        discipline = Discipline.objects.create(name='Computer Science', acronym='CSE')
        batch = Batch.objects.create(name='B.Tech', discipline=discipline, year=2024, curriculum=curriculum)

        def student(roll):
            user = User.objects.create_user(username=roll)
            extra = ExtraInfo.objects.create(id=roll, user=user, user_type='student', user_status='PRESENT')
            Student.objects.create(id=extra, programme='B.Tech', batch=2024, batch_id=batch,
                                   category='GEN', curr_semester_no=3)
            return user, Student.objects.get(id=extra)

        user, self.student = student('24BCS001')
        _, self.other = student('24BCS002')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}')

        today = datetime.date(2024, 1, 1)
        self.records = {
            'deleteskill': Has.objects.create(skill_id=Skill.objects.create(skill='Python'),
                                              unique_id=self.student, skill_rating=80),
            'deleteedu': Education.objects.create(unique_id=self.student, degree='B.Tech', grade='9',
                                                  institute='IIITDMJ', sdate=today),
            'deletecourse': Course.objects.create(unique_id=self.student, course_name='ML', sdate=today),
            'deleteexp': Experience.objects.create(unique_id=self.student, title='Intern', company='X',
                                                   location='Y', sdate=today),
            'deletepro': Project.objects.create(unique_id=self.student, project_name='Fusion', sdate=today),
            'deleteach': Achievement.objects.create(unique_id=self.student, achievement='Award',
                                                    issuer='Z', date_earned=today),
            'deletepub': Publication.objects.create(unique_id=self.student, publication_title='Paper',
                                                    publisher='P', publication_date=today),
            'deletepat': Patent.objects.create(unique_id=self.student, patent_name='Patent',
                                               patent_office='IPO', patent_date=today),
        }

    def test_each_kind_of_entry_is_deleted_by_its_owner(self):
        for key, record in self.records.items():
            with self.subTest(key=key):
                response = self.client.delete(delete_url(record.id), {key: True}, format='json')
                self.assertEqual(response.status_code, 200, response.content)
                self.assertFalse(type(record).objects.filter(id=record.id).exists())

    def test_another_students_entry_is_not_found_and_kept(self):
        theirs = Education.objects.create(unique_id=self.other, degree='B.Tech', grade='8',
                                          institute='IIITDMJ', sdate=datetime.date(2024, 1, 1))
        response = self.client.delete(delete_url(theirs.id), {'deleteedu': True}, format='json')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Education.objects.filter(id=theirs.id).exists())

    def test_an_unknown_kind_of_entry_is_refused(self):
        record = self.records['deleteedu']
        response = self.client.delete(delete_url(record.id), {'deletesomething': True}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Education.objects.filter(id=record.id).exists())
