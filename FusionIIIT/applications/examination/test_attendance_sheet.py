from django.db import IntegrityError, transaction
from django.test import TestCase

from applications.programme_curriculum.models import Course
from applications.examination.models import ExamAttendancePlan, ExamAttendanceRoom
import datetime


def make_course():
    return Course.objects.create(
        code='CS8004', name='Deep Learning and Applications',
        credit=3, syllabus='', ref_books='')


class PlanModelTests(TestCase):
    def test_one_plan_per_course_term_and_exam(self):
        course = make_course()
        kw = dict(course=course, academic_year='2026-27',
                  semester_type='Odd Semester', roll_count=40)
        ExamAttendancePlan.objects.create(exam='MID', **kw)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExamAttendancePlan.objects.create(exam='MID', **kw)
        ExamAttendancePlan.objects.create(exam='END', **kw)

    def test_rooms_come_back_in_position_order(self):
        plan = ExamAttendancePlan.objects.create(
            course=make_course(), academic_year='2026-27',
            semester_type='Odd Semester', exam='MID', roll_count=40)
        for room, pos in (('L104', 2), ('L201', 1)):
            ExamAttendanceRoom.objects.create(
                plan=plan, position=pos, from_sno=1, to_sno=20, room=room,
                date=datetime.date(2026, 11, 30),
                start_time=datetime.time(9, 0), end_time=datetime.time(11, 0))
        self.assertEqual([r.room for r in plan.rooms.all()], ['L201', 'L104'])
