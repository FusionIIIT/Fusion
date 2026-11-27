"""An HOD role may name its discipline by short name or full name.

"HOD (Design)" and "HOD (Des.)" are both the HOD of the Design discipline (short
name "Des."), and "HOD (Liberal Arts)" and "HOD (LA)" both of Liberal Arts.
Every academic HOD check has to accept either spelling.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.academic_procedures.api.views import (
    _hod_users_for_discipline,
    _is_hod_of_student,
    get_hod_disciplines,
    is_hod_of_discipline,
)
from applications.academic_procedures.models import ThesisTopic
from applications.globals.models import (
    DepartmentInfo,
    Designation,
    ExtraInfo,
    Faculty,
    HoldsDesignation,
)
from applications.programme_curriculum.hod import hod_designation_names
from applications.programme_curriculum.models import (
    Batch,
    Curriculum,
    Discipline,
    Programme,
)

BASE = '/academic-procedures/api'


class HodFixtures:
    """Design, Liberal Arts, CSE and Mechatronics disciplines, a Design and a
    Liberal Arts student, a supervisor, and helpers to add people and call the
    API as them."""

    def setUp(self):
        programme = Programme.objects.create(category='PG', name='M.Des', programme_begin_year=2025)
        self.curriculum = Curriculum.objects.create(programme=programme, name='M.Des 2025', no_of_semester=4)
        self.design = Discipline.objects.create(name='Design', acronym='Des.')
        self.liberal_arts = Discipline.objects.create(name='Liberal Arts', acronym='LA')
        self.cse = Discipline.objects.create(name='Computer Science and Engineering', acronym='CSE')
        self.mechatronics = Discipline.objects.create(name='Mechatronics', acronym='MT')

        self.design_student = self.student('25MDS001', self.design)
        self.la_student = self.student('25PLA001', self.liberal_arts)
        self.supervisor = Faculty.objects.create(id=self.person('sup1', 'faculty', 'Professor').extrainfo)

    # -- fixtures --------------------------------------------------------

    def person(self, username, user_type, *designations, department=None):
        user = User.objects.create_user(username=username)
        ExtraInfo.objects.create(id=username, user=user, user_type=user_type,
                                 user_status='PRESENT', department=department)
        for name in designations:
            held, _ = Designation.objects.get_or_create(name=name)
            HoldsDesignation.objects.create(user=user, working=user, designation=held)
        return user

    def student(self, roll, discipline):
        batch = Batch.objects.create(name=f'{discipline.acronym} 2025', discipline=discipline,
                                     year=2025, curriculum=self.curriculum)
        user = self.person(roll, 'student', 'student')
        return Student.objects.create(id=user.extrainfo, programme='M.Des', batch=2025,
                                      batch_id=batch, category='GEN', curr_semester_no=3)

    def topic(self, student, status='hod_pending'):
        return ThesisTopic.objects.create(
            student=student, supervisor=self.supervisor, supervisor_consented=True,
            category='Regular', broad_area='Interaction design', research_theme='Assistive devices',
            status=status)

    def as_user(self, user):
        client = APIClient()
        token, _ = Token.objects.get_or_create(user=user)
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client

    def pending_ids(self, user):
        response = self.as_user(user).get(f'{BASE}/hod/dashboard/')
        self.assertEqual(response.status_code, 200)
        return [row['id'] for row in response.json()['pending']]


class HodDisciplineNameTests(HodFixtures, TestCase):
    # -- which disciplines an HOD role covers ------------------------------

    def test_full_name_and_short_name_both_mean_the_same_discipline(self):
        for designation, acronym in [('HOD (Design)', 'Des.'), ('HOD (Des.)', 'Des.'),
                                     ('HOD (Liberal Arts)', 'LA'), ('HOD (LA)', 'LA'),
                                     ('HOD (CSE)', 'CSE'), ('HOD (MT)', 'MT')]:
            with self.subTest(designation=designation):
                user = self.person(f'u{Designation.objects.count()}', 'faculty', designation)
                self.assertEqual(get_hod_disciplines(user), [acronym])

    def test_spelling_and_spaces_in_the_role_name_do_not_matter(self):
        user = self.person('hodx', 'faculty', 'hod(des)')
        self.assertEqual(get_hod_disciplines(user), ['Des.'])

    def test_holding_both_spellings_lists_the_discipline_once(self):
        user = self.person('hodboth', 'faculty', 'HOD (Design)', 'HOD (Des.)')
        self.assertEqual(get_hod_disciplines(user), ['Des.'])

    def test_a_role_that_is_not_an_hod_role_gives_no_discipline(self):
        user = self.person('prof', 'faculty', 'Professor', 'Dean Academic')
        self.assertEqual(get_hod_disciplines(user), [])

    def test_an_hod_role_for_an_unknown_discipline_is_kept_as_written(self):
        user = self.person('hodnew', 'faculty', 'HOD (Robotics)')
        self.assertEqual(get_hod_disciplines(user), ['Robotics'])

    def test_every_spelling_of_a_disciplines_hod_role_is_found(self):
        for name in ('HOD (Design)', 'HOD (Des.)', 'HOD (CSE)'):
            Designation.objects.get_or_create(name=name)
        self.assertEqual(sorted(hod_designation_names('Des.')), ['HOD (Des.)', 'HOD (Design)'])
        self.assertEqual(hod_designation_names('CSE'), ['HOD (CSE)'])

    def test_is_hod_of_discipline_and_of_student_accept_the_full_name(self):
        design_hod = self.person('hoddes', 'faculty', 'HOD (Design)')
        cse_hod = self.person('hodcse', 'faculty', 'HOD (CSE)')
        self.assertTrue(is_hod_of_discipline(design_hod, 'Des.'))
        self.assertTrue(_is_hod_of_student(design_hod, self.design_student))
        self.assertFalse(is_hod_of_discipline(cse_hod, 'Des.'))
        self.assertFalse(_is_hod_of_student(cse_hod, self.design_student))
        self.assertFalse(is_hod_of_discipline(design_hod, ''))

    def test_hods_to_notify_include_holders_of_either_spelling(self):
        full = self.person('hoddes', 'faculty', 'HOD (Design)')
        short = self.person('hoddes2', 'faculty', 'HOD (Des.)')
        self.person('hodcse', 'faculty', 'HOD (CSE)')
        self.assertEqual(sorted(u.username for u in _hod_users_for_discipline('Des.')),
                         ['hoddes', 'hoddes2'])
        self.assertFalse(_hod_users_for_discipline(None).exists())
        self.assertIn(full, _hod_users_for_discipline('Des.'))
        self.assertIn(short, _hod_users_for_discipline('Des.'))

    # -- thesis topic approval end to end ----------------------------------

    def test_hod_design_sees_and_approves_a_design_students_topic(self):
        hod = self.person('hoddes', 'faculty', 'HOD (Design)')
        topic = self.topic(self.design_student)

        self.assertEqual(self.pending_ids(hod), [topic.id])
        response = self.as_user(hod).post(f'{BASE}/hod/thesis/{topic.id}/review/',
                                          {'approve': True}, format='json')
        self.assertEqual(response.status_code, 200)
        topic.refresh_from_db()
        self.assertEqual(topic.status, 'hod_approved')

    def test_hod_liberal_arts_sees_a_liberal_arts_students_topic(self):
        hod = self.person('hodla', 'faculty', 'HOD (Liberal Arts)')
        topic = self.topic(self.la_student)
        self.assertEqual(self.pending_ids(hod), [topic.id])

    def test_another_disciplines_hod_still_cannot_see_or_act(self):
        hod = self.person('hodcse', 'faculty', 'HOD (CSE)')
        topic = self.topic(self.design_student)

        self.assertEqual(self.pending_ids(hod), [])
        response = self.as_user(hod).post(f'{BASE}/hod/thesis/{topic.id}/review/',
                                          {'approve': True}, format='json')
        self.assertEqual(response.status_code, 403)
        topic.refresh_from_db()
        self.assertEqual(topic.status, 'hod_pending')

    # -- course proposals: a professor's HOD ---------------------------------

    def superior(self, professor):
        response = self.as_user(professor).get(
            '/programme_curriculum/api/get_superior_data/',
            {'uploaderId': professor.username, 'uploaderDes': 'Professor'})
        self.assertEqual(response.status_code, 200)
        return response.json()['superior_data']

    def test_a_mechatronics_professors_hod_is_found_under_hod_mt(self):
        department = DepartmentInfo.objects.create(name='Mechatronics')
        self.person('hodmt', 'faculty', 'HOD (MT)')
        professor = self.person('profmt', 'faculty', 'Professor', department=department)

        superior = self.superior(professor)
        self.assertEqual(superior['username'], 'hodmt')
        self.assertEqual(superior['designation'], 'HOD (MT)')

    def test_a_design_professors_hod_is_still_found_under_hod_design(self):
        department = DepartmentInfo.objects.create(name='Design')
        self.person('hoddes', 'faculty', 'HOD (Design)')
        professor = self.person('profdes', 'faculty', 'Professor', department=department)

        superior = self.superior(professor)
        self.assertEqual(superior['username'], 'hoddes')
        self.assertEqual(superior['designation'], 'HOD (Design)')

    def test_a_department_without_an_hod_role_has_no_superior(self):
        department = DepartmentInfo.objects.create(name='Library')
        professor = self.person('proflib', 'faculty', 'Professor', department=department)
        self.assertIsNone(self.superior(professor))
