from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token

from applications.academic_information.models import Student
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.programme_curriculum.models import (
    Batch,
    Curriculum,
    Discipline,
    Programme,
)

URL = '/aims/api/database/category-wise-student-count/'


class DatabaseCategoryCountTests(TestCase):
    """Students of a batch per category, one row per programme and discipline."""

    def setUp(self):
        admin = User.objects.create_user(username='category_report_admin')
        HoldsDesignation.objects.create(
            user=admin, working=admin, held_at=timezone.now(),
            designation=Designation.objects.create(name='acadadmin'))
        self.client = Client(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=admin).key}')

        ug = Programme.objects.create(category='UG', name='B.Tech', programme_begin_year=2024)
        btech = Curriculum.objects.create(programme=ug, name='B.Tech 2024', no_of_semester=8)
        pg = Programme.objects.create(category='PG', name='M.Tech', programme_begin_year=2024)
        mtech = Curriculum.objects.create(programme=pg, name='M.Tech 2024', no_of_semester=4)
        cse = Discipline.objects.create(name='Computer Science', acronym='CSE')
        self.cse = Batch.objects.create(name='B.Tech', year=2024, curriculum=btech, discipline=cse)
        self.ece = Batch.objects.create(
            name='B.Tech', year=2024, curriculum=btech,
            discipline=Discipline.objects.create(name='Electronics', acronym='ECE'))
        self.mtech = Batch.objects.create(name='M.Tech', year=2024, curriculum=mtech, discipline=cse)
        older = Batch.objects.create(name='B.Tech', year=2023, curriculum=btech, discipline=cse)
        self.older = older

        # CSE: 2 General (one a woman recorded as "F "), 1 EWS, 1 OBC with PwD,
        # 1 SC with no gender recorded, 1 ST woman.
        self.student('24BCS001', self.cse, 'GEN', 'M')
        self.student('24BCS002', self.cse, 'GEN', 'F ')
        self.student('24BCS003', self.cse, 'GEN', 'M', ews=True)
        self.student('24BCS004', self.cse, 'OBC', 'M', pwd=True)
        self.student('24BCS005', self.cse, 'SC', '')
        self.student('24BCS006', self.cse, 'ST', 'F')
        # ECE: 1 OBC, 1 other gender.
        self.student('24BEC001', self.ece, 'OBC', 'O')
        self.student('24MCS001', self.mtech, 'GEN', 'M', programme='M.Tech')
        # Another batch, never counted for 2024.
        self.student('23BCS001', older, 'GEN', 'M')

    def student(self, roll, batch, category, sex, ews=False, pwd=False, programme='B.Tech'):
        user = User.objects.create_user(username=roll)
        extra = ExtraInfo.objects.create(id=roll, user=user, user_type='student', sex=sex)
        Student.objects.create(id=extra, programme=programme, batch=batch.year, batch_id=batch,
                               category=category, is_ews=ews, is_pwd=pwd)

    def report(self, **params):
        response = self.client.get(URL, params)
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        return {row['discipline']: row for row in data['rows']}, data

    def test_each_discipline_counts_its_students_by_category(self):
        rows, data = self.report(batch=2024)
        self.assertEqual(list(rows), ['B.Tech CSE', 'B.Tech ECE', 'M.Tech CSE'])
        self.assertEqual(rows['B.Tech CSE'], {
            'discipline': 'B.Tech CSE', 'gen': 2, 'ews': 1, 'obc': 1, 'sc': 1, 'st': 1,
            'other': 0, 'total': 6, 'pwd': 1})
        self.assertEqual(rows['B.Tech ECE']['obc'], 1)
        self.assertEqual(rows['M.Tech CSE']['gen'], 1)
        self.assertEqual((data['students'], data['no_gender']), (8, 1))

    def test_the_categories_add_up_to_the_total(self):
        rows, _ = self.report(batch=2024)
        for row in rows.values():
            self.assertEqual(
                sum(row[k] for k in ('gen', 'ews', 'obc', 'sc', 'st', 'other')), row['total'])

    def test_gender_narrows_the_count_and_ignores_stray_spaces(self):
        rows, data = self.report(batch=2024, gender='F')
        self.assertEqual(list(rows), ['B.Tech CSE'])
        self.assertEqual((rows['B.Tech CSE']['gen'], rows['B.Tech CSE']['st'],
                          rows['B.Tech CSE']['total']), (1, 1, 2))
        # How many have no gender is told for the whole selection.
        self.assertEqual(data['no_gender'], 1)
        rows, _ = self.report(batch=2024, gender='o')
        self.assertEqual({k: r['total'] for k, r in rows.items()}, {'B.Tech ECE': 1})
        rows, _ = self.report(batch=2024, gender='M')
        self.assertEqual(rows['B.Tech CSE']['total'], 3)

    def test_programme_and_discipline_narrow_the_batch(self):
        rows, _ = self.report(batch=2024, programme_type='PG')
        self.assertEqual(list(rows), ['M.Tech CSE'])
        rows, _ = self.report(batch=2024, batch_id=self.ece.id)
        self.assertEqual(list(rows), ['B.Tech ECE'])
        rows, _ = self.report(batch=2023)
        self.assertEqual(rows['B.Tech CSE']['total'], 1)

    def test_an_unknown_stored_category_is_counted_as_other(self):
        Student.objects.filter(id_id='24BEC001').update(category='')
        rows, _ = self.report(batch=2024, batch_id=self.ece.id)
        self.assertEqual((rows['B.Tech ECE']['obc'], rows['B.Tech ECE']['other']), (0, 1))

    def test_bad_filters_are_refused(self):
        for params in ({}, {'batch': 'x'}, {'batch': 2024, 'gender': 'X'},
                       {'batch': 2024, 'batch_id': self.older.id},
                       {'batch': 2024, 'programme_type': 'MBA'}):
            self.assertEqual(self.client.get(URL, params).status_code, 400, params)

    def test_only_report_roles_may_see_it(self):
        user = User.objects.create_user(username='plain_user')
        client = Client(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}')
        self.assertEqual(client.get(URL, {'batch': 2024}).status_code, 403)
