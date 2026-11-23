from django.test import TestCase
from rest_framework.test import APIClient

from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, token_for)
from applications.academic_procedures.models import course_registration
from applications.examination.test_attendance_sheet import (
    make_course, make_pg_batch)
from applications.programme_curriculum.models import CourseSlot, Semester

BASE = '/examination/api/attendance-sheet/'
YEAR = '2026-27'
ODD = 'Odd Semester'


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(user))
    return client


def room(a, b, name='L201'):
    return {'from_sno': a, 'to_sno': b, 'room': name, 'date': '2026-11-30',
            'start_time': '09:00', 'end_time': '11:00',
            'instructor_text': ''}


class AttendanceSheetApiTests(TestCase):
    def setUp(self):
        self.course = make_course()
        self.ug_batch = make_batch(2023)
        self.pg_batch = make_pg_batch(2026, 'CSE', 'PG', 'M.Tech')
        self.semester = Semester.objects.create(
            curriculum=self.ug_batch.curriculum, semester_no=5)
        self.slot = CourseSlot.objects.create(
            semester=self.semester, name='EL', type='Core')
        self.admin = client_for(make_staff('admin1', 'acadadmin'))
        self.query = {'course': self.course.id, 'academic_year': YEAR,
                      'semester_type': ODD, 'exam': 'MID'}

    def enrol(self, roll, batch=None, programme='B.Tech'):
        student = make_student(roll, batch=batch or self.ug_batch)
        student.programme = programme
        student.save()
        course_registration.objects.create(
            student_id=student, semester_id=self.semester,
            course_id=self.course, course_slot_id=self.slot,
            registration_type='Regular', semester_type=ODD, session=YEAR)
        return student

    def enrol_ug(self, count=4):
        for n in range(1, count + 1):
            self.enrol('23BCS%03d' % n)

    def body(self, **extra):
        data = {'course': self.course.id, 'academic_year': YEAR,
                'semester_type': ODD, 'exam': 'MID', 'updated_at': None,
                'rooms': [room(1, 4)]}
        data.update(extra)
        return data

    def test_acadadmin_lists_courses_and_opens_one(self):
        self.enrol_ug()
        response = self.admin.get(
            BASE + 'courses/', {'academic_year': YEAR, 'semester_type': ODD})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual([c['code'] for c in response.json()], ['CS8004'])
        response = self.admin.get(BASE, self.query)
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(len(data['students']), 4)
        self.assertFalse(data['sectioned'])
        self.assertIsNone(data['plan'])
        self.assertEqual(data['course']['id'], self.course.id)
        self.assertEqual(data['exam'], 'MID')
        self.assertEqual(data['instructors'], {'by_section': {}, 'all': []})

    def test_save_copy_and_reopen(self):
        self.enrol_ug()
        response = self.admin.post(BASE + 'save/', self.body(), format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()['plan']['rooms']), 1)
        response = self.admin.post(BASE + 'copy/', {
            'course': self.course.id, 'academic_year': YEAR,
            'semester_type': ODD, 'from_exam': 'MID', 'to_exam': 'END',
            'replace': False}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['exam'], 'END')
        reopened = self.admin.get(BASE, dict(self.query, exam='END')).json()
        self.assertEqual(reopened['plan']['rooms'],
                         response.json()['plan']['rooms'])
        self.assertEqual(reopened['plan']['exam'], 'END')

    def test_save_errors_come_back_as_a_list(self):
        self.enrol_ug()
        response = self.admin.post(BASE + 'save/', self.body(
            rooms=[room(1, 3), room(3, 4, 'L202')]), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'detail': 'Fix these, then save.',
            'errors': ['Rooms 1 and 2 overlap.']})

    def test_too_long_room_name_and_instructor_text_are_400(self):
        self.enrol_ug()
        rooms = [dict(room(1, 2, 'L' * 31)),
                 dict(room(3, 4, 'L202'), instructor_text='P' * 501)]
        response = self.admin.post(BASE + 'save/', self.body(rooms=rooms),
                                   format='json')
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(response.json(), {
            'detail': 'Fix these, then save.',
            'errors': [
                'Room 1: room name must be at most 30 characters.',
                'Room 2: instructor text must be at most 500 characters.']})

    def test_stale_save_is_a_conflict_without_exists(self):
        self.enrol_ug()
        self.admin.post(BASE + 'save/', self.body(), format='json')
        response = self.admin.post(BASE + 'save/', self.body(), format='json')
        self.assertEqual(response.status_code, 409)
        self.assertNotIn('exists', response.json())
        self.assertIn('detail', response.json())

    def test_copy_over_an_existing_plan_needs_replace(self):
        self.enrol_ug()
        self.admin.post(BASE + 'save/', self.body(), format='json')
        self.admin.post(BASE + 'save/', self.body(exam='END'), format='json')
        payload = {'course': self.course.id, 'academic_year': YEAR,
                   'semester_type': ODD, 'from_exam': 'MID', 'to_exam': 'END',
                   'replace': False}
        response = self.admin.post(BASE + 'copy/', payload, format='json')
        self.assertEqual(response.status_code, 409)
        self.assertIs(response.json()['exists'], True)
        payload['replace'] = True
        response = self.admin.post(BASE + 'copy/', payload, format='json')
        self.assertEqual(response.status_code, 200, response.content)

    def test_malformed_inputs_are_400_and_unknown_course_is_404(self):
        self.enrol_ug()
        for change in ({'exam': 'FINAL'}, {'semester_type': 'Summer Semester'},
                       {'academic_year': '2026'}, {'course': 'abc'}):
            response = self.admin.get(BASE, dict(self.query, **change))
            self.assertEqual(response.status_code, 400, change)
            self.assertIn('detail', response.json())
        response = self.admin.post(BASE + 'save/', self.body(exam='X'),
                                   format='json')
        self.assertEqual(response.status_code, 400)
        response = self.admin.post(BASE + 'copy/', {
            'course': self.course.id, 'academic_year': YEAR,
            'semester_type': ODD, 'from_exam': 'MID', 'to_exam': 'X'},
            format='json')
        self.assertEqual(response.status_code, 400)
        response = self.admin.get(
            BASE + 'courses/', {'academic_year': YEAR, 'semester_type': 'Summer Semester'})
        self.assertEqual(response.status_code, 400)
        response = self.admin.get(BASE, dict(self.query, course=999999))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {
            'detail': 'No such course in your programmes for that term.'})

    def test_programme_admin_gets_404_for_a_mixed_course(self):
        self.enrol('23BCS001')
        self.enrol('26MCSA01', batch=self.pg_batch, programme='M.Tech')
        ug = client_for(make_staff('ug_admin', 'Acad UG'))
        missing = {'detail': 'No such course in your programmes for that term.'}
        response = ug.get(BASE, self.query)
        self.assertEqual((response.status_code, response.json()), (404, missing))
        response = ug.post(BASE + 'save/', self.body(), format='json')
        self.assertEqual((response.status_code, response.json()), (404, missing))
        response = ug.post(BASE + 'copy/', {
            'course': self.course.id, 'academic_year': YEAR,
            'semester_type': ODD, 'from_exam': 'MID', 'to_exam': 'END',
            'replace': False}, format='json')
        self.assertEqual((response.status_code, response.json()), (404, missing))
        listed = ug.get(BASE + 'courses/',
                        {'academic_year': YEAR, 'semester_type': ODD})
        self.assertEqual(listed.json(), [])

    def test_programme_admin_sees_a_course_of_their_own(self):
        self.enrol_ug(2)
        ug = client_for(make_staff('ug_admin', 'Acad UG'))
        pg = client_for(make_staff('pg_admin', 'Acad PG'))
        self.assertEqual(ug.get(BASE, self.query).status_code, 200)
        self.assertEqual(pg.get(BASE, self.query).status_code, 404)

    def test_other_roles_are_refused(self):
        student = make_student('23BCS099', batch=self.ug_batch)
        response = client_for(student.id.user).get(BASE, self.query)
        self.assertEqual(response.status_code, 403)
        faculty = client_for(make_staff('fac1', 'Associate Professor'))
        self.assertEqual(faculty.get(BASE + 'courses/', {
            'academic_year': YEAR, 'semester_type': ODD}).status_code, 403)
        self.assertEqual(faculty.post(
            BASE + 'save/', self.body(), format='json').status_code, 403)
