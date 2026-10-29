"""Django/database tests for the timetable REST API and solver integration.

These need the project's Django environment and a PostgreSQL test database
(the app uses ArrayField).  Run with the other module tests::

    python manage.py test applications.academic_procedures.test_timetable_api \
        --settings=Fusion.settings.test_settings

The solver integration tests are skipped when ortools is not installed.
"""

import threading
import unittest
import uuid

from django.contrib.auth.models import User
from django.db import connection, transaction
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from applications.academic_information.models import (
    Course, Curriculum, Curriculum_Instructor, Student,
)
from applications.academic_procedures.models import (
    Classroom, ElectiveBasket, ElectiveBasketCurriculum, FacultyPreference,
    TimetableSlot, TimetableVersion,
)
from applications.academic_procedures.solver import timetable_solver as ts
from applications.globals.models import (
    DepartmentInfo, Designation, ExtraInfo, Faculty, HoldsDesignation,
)

BASE = '/academic-procedures/api/timetable/'


class TimetableTestCase(TestCase):
    def setUp(self):
        self.cse = DepartmentInfo.objects.create(name='CSE')
        self.ece = DepartmentInfo.objects.create(name='ECE')
        self.design = DepartmentInfo.objects.create(name='Design')

        self.admin = self._user('tt-admin', designation='acadadmin')
        self.dean = self._user('tt-dean', designation='Dean Academic')
        self.prof1 = self._faculty('PROF1')
        self.prof2 = self._faculty('PROF2')
        self.student = self._student('24BCS001', self.cse, section='A')

        self.course = Course.objects.create(course_name='Course', course_details='-')
        self.cse1 = self._curriculum('CS101', 'CSE')
        self.cse2 = self._curriculum('CS102', 'CSE')
        self.common = self._curriculum('GS101', 'Common')
        self.ece1 = self._curriculum('EC101', 'ECE')
        self.ci_cse1 = self._teach(self.cse1, self.prof1)
        self.ci_ece1 = self._teach(self.ece1, self.prof1)
        self.ci_cse2 = self._teach(self.cse2, self.prof2)
        self.ci_common = self._teach(self.common, self.prof2)

        self.lh1 = Classroom.objects.create(room_id='LH1', building='A', capacity=120,
                                            room_type='Lecture Hall')
        self.lh2 = Classroom.objects.create(room_id='LH2', building='A', capacity=120,
                                            room_type='Lecture Hall')
        self.lab = Classroom.objects.create(room_id='LAB1', building='B', capacity=120,
                                            room_type='Computer Lab')
        self.tiny = Classroom.objects.create(room_id='TR1', building='B', capacity=1,
                                             room_type='Tutorial Room')

        self.draft = TimetableVersion.objects.create(
            academic_year=2026, semester_type='Odd Semester', version_number=1)
        self.client = APIClient()

    # ── fixtures ──────────────────────────────────────────────────────── #

    def _user(self, username, designation=None, user_type='staff', dept=None):
        user = User.objects.create_user(username=username)
        extra = ExtraInfo.objects.create(id=username.upper(), user=user, user_type=user_type,
                                         sex='M', user_status='PRESENT', department=dept)
        if designation:
            role, _ = Designation.objects.get_or_create(name=designation)
            HoldsDesignation.objects.create(user=user, working=user, designation=role)
        user.extra = extra
        return user

    def _faculty(self, username):
        user = self._user(username, user_type='faculty', dept=None)
        Faculty.objects.create(id=user.extra)
        return user

    def _student(self, roll, dept, section='', batch=2024, programme='B.Tech'):
        user = self._user(roll, user_type='student', dept=dept)
        Student.objects.create(id=user.extra, programme=programme, batch=batch,
                               category='GEN', section=section or None)
        return user

    def _curriculum(self, code, branch, batch=2024):
        return Curriculum.objects.create(
            course_code=code, course_id=self.course, credits=4,
            course_type='Professional Core', programme='B.Tech', branch=branch,
            batch=batch, sem=3, floated=True)

    def _teach(self, curriculum, user, chief=True):
        return Curriculum_Instructor.objects.create(
            curriculum_id=curriculum, instructor_id=user.extra, chief_inst=chief)

    def _slot(self, curriculum, ci, room, day, hour, version=None, branch=None,
              section='', slot_type='Lecture', block=None, locked=False):
        return TimetableSlot.objects.create(
            version=version or self.draft, curriculum=curriculum, curriculum_instructor=ci,
            classroom=room, batch=curriculum.batch, programme=curriculum.programme,
            branch=branch or curriculum.branch, section=section, day_of_week=day,
            start_hour=hour, slot_type=slot_type, lab_block_id=block, is_locked=locked)

    def as_user(self, user):
        self.client.force_authenticate(user=user)
        return self.client

    def override(self, slot, day, hour, room, **extra):
        payload = {'slot_id': slot.pk, 'new_day': day, 'new_start_hour': hour,
                   'new_room_id': room, **extra}
        return self.as_user(self.admin).post(BASE + 'slot/override/', payload, format='json')


class PermissionAndValidationTests(TimetableTestCase):

    def test_only_acadadmin_can_generate(self):
        response = self.as_user(self.student).post(
            BASE + 'generate/', {'academic_year': 2026}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_generate_rejects_bad_timeout(self):
        for timeout in (0, 601, 'abc'):
            response = self.as_user(self.admin).post(
                BASE + 'generate/', {'academic_year': 2026, 'timeout_seconds': timeout},
                format='json')
            self.assertEqual(response.status_code, 400, timeout)

    def test_drafts_are_hidden_from_non_admins(self):
        self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9)
        versions = self.as_user(self.student).get(BASE + 'versions/')
        self.assertEqual(versions.status_code, 200)
        self.assertEqual(versions.data, [])
        slots = self.as_user(self.student).get(BASE + 'slots/', {'version_id': self.draft.pk})
        self.assertEqual(slots.status_code, 403)
        slots = self.as_user(self.admin).get(BASE + 'slots/', {'version_id': self.draft.pk})
        self.assertEqual(slots.status_code, 200)
        self.assertEqual(len(slots.data), 1)

    def test_conflict_log_is_admin_only(self):
        response = self.as_user(self.student).get(BASE + 'conflict-log/',
                                                  {'version_id': self.draft.pk})
        self.assertEqual(response.status_code, 403)

    def test_malformed_query_numbers_are_400_not_500(self):
        response = self.as_user(self.admin).get(BASE + 'slots/', {'version_id': 'x'})
        self.assertEqual(response.status_code, 400)
        response = self.as_user(self.admin).get(BASE + 'versions/', {'academic_year': 'x'})
        self.assertEqual(response.status_code, 400)


class OverrideTests(TimetableTestCase):

    def test_same_person_on_another_course_blocks_the_move(self):
        moving = self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9)
        self._slot(self.ece1, self.ci_ece1, self.lh2, 1, 10)  # prof1, other cohort
        response = self.override(moving, 1, 10, 'LH1')
        self.assertEqual(response.status_code, 409)
        self.assertIn('FACULTY_CLASH', [c['type'] for c in response.data['conflicts']])

    def test_common_course_blocks_branch_course(self):
        moving = self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9)
        self._slot(self.common, self.ci_common, self.lh2, 2, 9)
        response = self.override(moving, 2, 9, 'LH1')
        self.assertEqual(response.status_code, 409)
        self.assertIn('COHORT_CLASH', [c['type'] for c in response.data['conflicts']])

    def test_room_clash_and_capacity(self):
        moving = self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9)
        self._slot(self.ece1, self.ci_cse2, self.lh2, 3, 9)
        response = self.override(moving, 3, 9, 'LH2')
        self.assertIn('ROOM_CLASH', [c['type'] for c in response.data['conflicts']])
        response = self.override(moving, 4, 9, 'TR1')
        self.assertIn('CAPACITY', [c['type'] for c in response.data['conflicts']])
        response = self.override(moving, 4, 9, 'LAB1')
        self.assertIn('ROOM_TYPE', [c['type'] for c in response.data['conflicts']])

    def test_lab_block_moves_as_a_whole_and_never_crosses_lunch(self):
        block = uuid.uuid4()
        first = self._slot(self.cse2, self.ci_cse2, self.lab, 3, 14, slot_type='Practical', block=block)
        second = self._slot(self.cse2, self.ci_cse2, self.lab, 3, 15, slot_type='Practical', block=block)
        response = self.override(second, 3, 12, 'LAB1')
        self.assertEqual(response.status_code, 400)
        response = self.override(second, 4, 9, 'LAB1')
        self.assertEqual(response.status_code, 200, response.data)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual([(first.day_of_week, first.start_hour), (second.day_of_week, second.start_hour)],
                         [(4, 9), (4, 10)])

    def test_lock_string_false_is_false(self):
        moving = self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9)
        response = self.override(moving, 5, 9, 'LH1', lock='false')
        self.assertEqual(response.status_code, 200, response.data)
        moving.refresh_from_db()
        self.assertFalse(moving.is_locked)

    def test_elective_basket_course_cannot_be_moved_alone(self):
        basket = ElectiveBasket.objects.create(basket_code='E1', name='E', semester=3,
                                               programme='B.Tech', academic_year=2026)
        ElectiveBasketCurriculum.objects.create(basket=basket, curriculum=self.cse1)
        moving = self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9)
        response = self.override(moving, 5, 9, 'LH1')
        self.assertEqual(response.status_code, 409)
        self.assertIn('ELECTIVE_BASKET', [c['type'] for c in response.data['conflicts']])

    def test_non_string_room_is_400(self):
        moving = self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9)
        response = self.override(moving, 5, 9, {'x': 1})
        self.assertEqual(response.status_code, 400)


class PublishTests(TimetableTestCase):

    def test_only_dean_can_publish(self):
        self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9)
        response = self.as_user(self.prof1).patch(BASE + f'version/{self.draft.pk}/publish/')
        self.assertEqual(response.status_code, 403)

    def test_empty_version_cannot_be_published(self):
        response = self.as_user(self.dean).patch(BASE + f'version/{self.draft.pk}/publish/')
        self.assertEqual(response.status_code, 400)

    def test_publishing_archives_only_the_same_term(self):
        old = TimetableVersion.objects.create(academic_year=2026, semester_type='Odd Semester',
                                              version_number=2, status='Published')
        other_term = TimetableVersion.objects.create(academic_year=2026, semester_type='Even Semester',
                                                     version_number=1, status='Published')
        self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9)
        response = self.as_user(self.dean).patch(BASE + f'version/{self.draft.pk}/publish/')
        self.assertEqual(response.status_code, 200, response.data)
        statuses = dict(TimetableVersion.objects.values_list('pk', 'status'))
        self.assertEqual(statuses[self.draft.pk], 'Published')
        self.assertEqual(statuses[old.pk], 'Archived')
        self.assertEqual(statuses[other_term.pk], 'Published')


class ConcurrentPublishTests(TransactionTestCase):
    """Real row locks need real transactions, hence TransactionTestCase."""

    def setUp(self):
        user = User.objects.create_user(username='tt-dean2')
        ExtraInfo.objects.create(id='TTDEAN2', user=user, user_type='staff',
                                 sex='M', user_status='PRESENT')
        role = Designation.objects.create(name='Dean Academic')
        HoldsDesignation.objects.create(user=user, working=user, designation=role)
        self.dean = user
        course = Course.objects.create(course_name='C', course_details='-')
        curriculum = Curriculum.objects.create(
            course_code='CS101', course_id=course, credits=4, course_type='Professional Core',
            programme='B.Tech', branch='CSE', batch=2024, sem=3, floated=True)
        room = Classroom.objects.create(room_id='LH1', building='A', capacity=60,
                                        room_type='Lecture Hall')
        self.v1, self.v2 = [
            TimetableVersion.objects.create(academic_year=2026, semester_type='Odd Semester',
                                            version_number=n)
            for n in (1, 2)
        ]
        for version in (self.v1, self.v2):
            TimetableSlot.objects.create(
                version=version, curriculum=curriculum, classroom=room, batch=2024,
                programme='B.Tech', branch='CSE', day_of_week=1, start_hour=9,
                slot_type='Lecture')

    def _publish(self, version, results):
        try:
            client = APIClient()
            client.force_authenticate(user=self.dean)
            results[version.pk] = client.patch(
                BASE + f'version/{version.pk}/publish/').status_code
        finally:
            connection.close()

    def test_publish_waits_while_another_version_of_the_term_is_locked(self):
        # Regression: publish locked only its own row, so publishing v1 and v2
        # at the same time could leave both Published.  Here another
        # transaction holds v1's row (as an in-flight publish of v1 would);
        # publishing v2 must wait for it instead of running alongside.
        locked, release, results = threading.Event(), threading.Event(), {}

        def hold_v1():
            try:
                with transaction.atomic():
                    list(TimetableVersion.objects.select_for_update().filter(pk=self.v1.pk))
                    locked.set()
                    release.wait(15)
            finally:
                connection.close()

        holder = threading.Thread(target=hold_v1)
        holder.start()
        self.assertTrue(locked.wait(15))
        publisher = threading.Thread(target=self._publish, args=(self.v2, results))
        publisher.start()
        publisher.join(2)
        still_waiting = publisher.is_alive()
        release.set()
        holder.join(15)
        publisher.join(15)

        self.assertTrue(still_waiting, 'publish did not wait for the term lock')
        self.assertEqual(results[self.v2.pk], 200)

    def test_two_concurrent_publishes_leave_one_published_version(self):
        results = {}
        threads = [threading.Thread(target=self._publish, args=(v, results))
                   for v in (self.v1, self.v2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(30)
        self.assertEqual(sorted(results.values()), [200, 200])
        published = TimetableVersion.objects.filter(status='Published').count()
        self.assertEqual(published, 1)


class MyScheduleTests(TimetableTestCase):

    def setUp(self):
        super().setUp()
        self.draft.status = 'Published'
        self.draft.save()

    def test_student_sees_branch_common_and_own_section(self):
        mine = [
            self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9),
            self._slot(self.common, self.ci_common, self.lh1, 1, 10),
            self._slot(self.cse2, self.ci_cse2, self.lh1, 1, 11, section='A'),
        ]
        self._slot(self.cse2, self.ci_cse2, self.lh2, 1, 11, section='B')
        self._slot(self.ece1, self.ci_ece1, self.lh2, 1, 9)
        response = self.as_user(self.student).get(BASE + 'my-schedule/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(s['start_time'] for s in response.data['slots']),
                         sorted(s.start_time for s in mine))

    def test_branch_match_ignores_case(self):
        designer = self._student('24BDS001', self.design)
        design = self._curriculum('DS101', 'DESIGN')
        self._slot(design, None, self.lh1, 2, 9)
        response = self.as_user(designer).get(BASE + 'my-schedule/')
        self.assertEqual([s['course_code'] for s in response.data['slots']], ['DS101'])

    def test_bdes_student_sees_design_courses_filed_as_btech(self):
        # Regression: Design courses are B.Tech/DESIGN, Design students B.Des.
        designer = self._student('22BDS001', self.design, batch=2022, programme='B.Des')
        design = self._curriculum('DS201', 'DESIGN', batch=2022)
        cse = self._curriculum('CS201', 'CSE', batch=2022)
        self._slot(design, None, self.lh1, 2, 9)
        self._slot(cse, None, self.lh1, 2, 10)
        response = self.as_user(designer).get(BASE + 'my-schedule/')
        self.assertEqual([s['course_code'] for s in response.data['slots']], ['DS201'])

    def test_override_counts_bdes_students_in_design_room_size(self):
        for n in range(3):
            self._student(f'22BDS10{n}', self.design, batch=2022, programme='B.Des')
        design = self._curriculum('DS202', 'DESIGN', batch=2022)
        moving = self._slot(design, None, self.lh1, 2, 9)
        self.tiny.capacity = 3  # 3 students x 1.10 buffer needs 4 seats
        self.tiny.save()
        response = self.override(moving, 2, 9, 'TR1')
        self.assertIn('CAPACITY', [c['type'] for c in response.data['conflicts']])

    def test_co_instructor_sees_course_slots(self):
        self._teach(self.cse1, self.prof2, chief=False)
        self._slot(self.cse1, self.ci_cse1, self.lh1, 1, 9)  # stored with prof1
        response = self.as_user(self.prof2).get(BASE + 'my-schedule/')
        self.assertIn('CS101', [s['course_code'] for s in response.data['slots']])


class FacultyPreferenceTests(TimetableTestCase):

    def _post(self, user, **data):
        payload = {'day_of_week': 1, 'start_hour': 9, 'end_hour': 11,
                   'preference_type': 'Unavailable', **data}
        return self.as_user(user).post(BASE + 'faculty-preferences/', payload, format='json')

    def test_faculty_can_only_set_own_preferences(self):
        self.assertEqual(self._post(self.prof1).status_code, 201)
        response = self._post(self.prof1, faculty_id=self.prof2.extra.pk)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self._post(self.admin, faculty_id=self.prof2.extra.pk).status_code, 201)

    def test_invalid_windows_are_rejected(self):
        self.assertEqual(self._post(self.prof1, start_hour=13).status_code, 400)
        self.assertEqual(self._post(self.prof1, start_hour=11, end_hour=9).status_code, 400)
        self.assertEqual(self._post(self.prof1, preference_type='Maybe').status_code, 400)

    def test_students_cannot_read_preferences(self):
        FacultyPreference.objects.create(faculty_id=self.prof1.extra.pk, day_of_week=1,
                                         start_hour=9, end_hour=10,
                                         preference_type='Unavailable')
        response = self.as_user(self.student).get(BASE + 'faculty-preferences/')
        self.assertEqual(response.data, [])


@unittest.skipUnless(ts._ORTOOLS_AVAILABLE, 'ortools is not installed')
class GenerationIntegrationTests(TimetableTestCase):
    """Runs the real solver against the test database through the API."""

    def generate(self):
        return self.as_user(self.admin).post(
            BASE + 'generate/', {'academic_year': 2026, 'timeout_seconds': 30}, format='json')

    def assertNoClashes(self, version_id):
        slots = list(TimetableSlot.objects.filter(version_id=version_id))
        rooms = [(s.day_of_week, s.start_hour, s.classroom_id) for s in slots]
        self.assertEqual(len(rooms), len(set(rooms)), 'room double-booked')
        teaching = [
            (ci.instructor_id_id, s.day_of_week, s.start_hour)
            for s in slots
            for ci in Curriculum_Instructor.objects.filter(curriculum_id=s.curriculum_id)
        ]
        self.assertEqual(len(teaching), len(set(teaching)), 'person double-booked')
        branches = {s.branch for s in slots if s.branch != 'Common'}
        cohort = []
        for s in slots:
            for branch in (branches if s.branch == 'Common' else {s.branch}):
                cohort.append((s.batch, s.programme, branch, s.day_of_week, s.start_hour))
        self.assertEqual(len(cohort), len(set(cohort)), 'cohort double-booked')

    def test_generation_creates_a_clash_free_draft(self):
        response = self.generate()
        self.assertEqual(response.status_code, 200, response.data)
        version = TimetableVersion.objects.get(pk=response.data['version_id'])
        self.assertEqual(version.status, 'Draft')
        self.assertEqual(version.created_by, self.admin)
        # 4 floated curricula x default 3 lectures + 1 tutorial
        self.assertEqual(version.slots.count(), 16)
        self.assertNoClashes(version.pk)

    def test_locks_carry_forward_and_removed_locks_stay_removed(self):
        first = self.generate().data['version_id']
        pinned = TimetableSlot.objects.filter(version_id=first, curriculum=self.cse1).first()
        pinned.is_locked = True
        pinned.save()

        second = self.generate().data['version_id']
        carried = TimetableSlot.objects.filter(version_id=second, is_locked=True)
        self.assertEqual(
            [(s.curriculum_id, s.day_of_week, s.start_hour, s.classroom_id) for s in carried],
            [(pinned.curriculum_id, pinned.day_of_week, pinned.start_hour, pinned.classroom_id)])

        carried.update(is_locked=False)  # admin unlocks it in the newer version
        third = self.generate().data['version_id']
        self.assertFalse(TimetableSlot.objects.filter(version_id=third, is_locked=True).exists())

    def test_no_room_large_enough_is_infeasible(self):
        Classroom.objects.update(capacity=1)
        response = self.generate()
        self.assertEqual(response.status_code, 422)
        version = TimetableVersion.objects.get(pk=response.data['version_id'])
        self.assertEqual(version.status, 'Infeasible')
        self.assertTrue(version.conflict_logs.filter(error_code='NO_ELIGIBLE_ROOM').exists())
