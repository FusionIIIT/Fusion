"""After a dropped semester the student registers for the one after it."""
import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from applications.academic_information.models import Calendar
from applications.academic_information.semester_drop import record_drop
from applications.academic_information.status_test_utils import (
    make_batch, make_staff, make_student, token_for,
)
from applications.academic_procedures.api.views import (
    pg_registration_semester, pre_registration_target_semester,
)
from applications.academic_procedures.models import (
    CourseReplacementRequest, course_registration,
)
from applications.programme_curriculum.models import (
    Batch, Course, CourseSlot, Curriculum, Discipline, Programme, Semester,
)


class MovingOnTests(TestCase):
    def setUp(self):
        self.batch = make_batch(2023, 'ECE')
        self.sems = {n: Semester.objects.create(curriculum=self.batch.curriculum, semester_no=n)
                     for n in (4, 5, 6, 7)}
        self.student = make_student('23BEC030', batch=self.batch, semester=4)
        self.office = make_staff()

    def test_pre_registration_targets_the_semester_after_the_dropped_one(self):
        record_drop(self.student, 5, '2025-26', 'Medical leave', self.office)
        self.assertEqual(pre_registration_target_semester(self.student), 6)
        record_drop(self.student, 6, '2025-26', 'Longer leave', self.office)
        self.assertEqual(pre_registration_target_semester(self.student), 7)

    def test_pg_registration_reaches_the_semester_after_the_dropped_one(self):
        programme = Programme.objects.create(category='PG', name='M.Tech',
                                             programme_begin_year=2025)
        curriculum = Curriculum.objects.create(programme=programme, name='M.Tech 2025',
                                               no_of_semester=4)
        batch = Batch.objects.create(name='M.Tech', year=2025, curriculum=curriculum,
                                     discipline=Discipline.objects.create(name='VLSI',
                                                                          acronym='VL'))
        for n in (2, 3, 4):
            Semester.objects.create(curriculum=curriculum, semester_no=n)
        student = make_student('25MVL001', batch=batch, semester=2)
        record_drop(student, 3, '2026-27', 'Medical leave', self.office)
        now = datetime.datetime.now()
        Calendar.objects.create(description=f'PG Registration 4 {now.year}',
                                from_date=now.date() - datetime.timedelta(days=1),
                                to_date=now.date() + datetime.timedelta(days=1))
        self.assertEqual(pg_registration_semester(student, now), (4, None))

    def test_a_replacement_keeps_the_type_of_the_registration_it_replaces(self):
        # An office-added Backlog in the dropped semester's elective slot,
        # replaced through the change requests: the replacement is Backlog too.
        self.student.curr_semester_no = 7
        self.student.save()
        record_drop(self.student, 5, '2025-26', 'Medical leave', self.office)
        old_course = Course.objects.create(code='OE5001', name='Old', credit=3, syllabus='',
                                           ref_books='', max_seats=10)
        new_course = Course.objects.create(code='OE5002', name='New', credit=3, syllabus='',
                                           ref_books='', max_seats=10)
        slot = CourseSlot.objects.create(semester=self.sems[5], name='OE5',
                                         type='Open Elective')
        slot.courses.add(old_course, new_course)
        course_registration.objects.create(
            student_id=self.student, semester_id=self.sems[5], course_id=old_course,
            course_slot_id=slot, registration_type='Backlog', session='2026-27',
            semester_type='Odd Semester')
        request = CourseReplacementRequest.objects.create(
            student=self.student, course_slot=slot, old_course=old_course,
            new_course=new_course, academic_year='2026-27', semester_type='Odd Semester')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token_for(self.office))
        response = client.post('/academic-procedures/api/acad/change-requests/allocate_all/', {
            'academic_year': '2026-27', 'semester_type': 'Odd Semester',
            'request_ids': [request.id]}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        reg = course_registration.objects.get(student_id=self.student)
        self.assertEqual((reg.course_id, reg.registration_type), (new_course, 'Backlog'))
