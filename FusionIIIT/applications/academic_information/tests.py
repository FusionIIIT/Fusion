import json
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import TestCase

from applications.academic_information.models import Student
from applications.academic_information.utils import (
    allocate, allocation_progress, publish_allocations,
)
from applications.academic_procedures.models import (
    FinalRegistration, InitialRegistration, course_registration,
)
from applications.globals.models import ExtraInfo, Faculty
from applications.programme_curriculum.models import (
    Batch, Course, CourseInstructor, CourseSlot, Curriculum, Discipline,
    Programme, Semester,
)


class AllocationPublicationTests(TestCase):
    def setUp(self):
        programme = Programme.objects.create(
            category='UG', name='Test B.Tech', programme_begin_year=2026)
        discipline = Discipline.objects.create(
            name='Test Computer Science', acronym='TCSE')
        curriculum = Curriculum.objects.create(
            programme=programme, name='Test B.Tech Curriculum',
            no_of_semester=8)
        self.semester = Semester.objects.create(
            curriculum=curriculum, semester_no=1)
        self.batch = Batch.objects.create(
            name='B.Tech', discipline=discipline, year=2026,
            curriculum=curriculum)
        self.course = Course.objects.create(
            code='TT1001', name='Test Course', credit=4, syllabus='',
            ref_books='', max_seats=60)
        self.slot = CourseSlot.objects.create(
            semester=self.semester, name='Test Core Slot',
            type='Professional Core')
        self.slot.courses.add(self.course)

        student_user = User.objects.create_user(username='26TCS001')
        student_extra = ExtraInfo.objects.create(
            id='26TCS001', user=student_user, user_type='student')
        self.student = Student.objects.create(
            id=student_extra, programme='B.Tech', batch=2026,
            batch_id=self.batch, category='GEN', curr_semester_no=1,
            section='E1')

        faculty_user = User.objects.create_user(
            username='TFAC001', first_name='Test', last_name='Faculty')
        faculty_extra = ExtraInfo.objects.create(
            id='TFAC001', user=faculty_user, user_type='faculty')
        faculty = Faculty.objects.create(id=faculty_extra)
        self.offering = CourseInstructor.objects.create(
            course_id=self.course, instructor_id=faculty, year=2026,
            semester_type='Odd Semester', section_label='E1')

        InitialRegistration.objects.create(
            student_id=self.student, semester_id=self.semester,
            course_id=self.course, course_slot_id=self.slot, priority=1,
            registration_type='Regular')

    def create_second_student(self):
        user = User.objects.create_user(username='26TCS002')
        extra = ExtraInfo.objects.create(
            id='26TCS002', user=user, user_type='student')
        student = Student.objects.create(
            id=extra, programme='B.Tech', batch=2026,
            batch_id=self.batch, category='GEN', curr_semester_no=1,
            section='E1')
        InitialRegistration.objects.create(
            student_id=student, semester_id=self.semester,
            course_id=self.course, course_slot_id=self.slot, priority=1,
            registration_type='Regular')
        return student

    def test_allocate_immediately_publishes_courses(self):
        response = allocate(SimpleNamespace(POST={
            'batch': 2026,
            'sem': 1,
            'year': 2026,
            'programme_type': 'UG',
            'skip_course_ids': [],
        }))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['status'], 1)

        allocation = FinalRegistration.objects.get()
        self.assertTrue(allocation.verified)
        self.assertEqual(allocation.course_instructor, self.offering)

        registration = course_registration.objects.get()
        self.assertEqual(registration.student_id, self.student)
        self.assertEqual(registration.course_id, self.course)
        self.assertEqual(registration.semester_id, self.semester)
        self.assertEqual(registration.course_instructor, self.offering)
        self.assertEqual(registration.working_year, 2026)
        self.assertEqual(registration.session, '2026-27')
        self.assertEqual(registration.semester_type, 'Odd Semester')

    def test_publish_repairs_old_allocations_without_duplicates(self):
        FinalRegistration.objects.create(
            student_id=self.student, semester_id=self.semester,
            course_id=self.course, course_slot_id=self.slot,
            registration_type='Regular', verified=True)

        first = publish_allocations(2026, 1, 2026, 'UG')
        second = publish_allocations(2026, 1, 2026, 'UG')

        self.assertEqual(first['registrations_created'], 1)
        self.assertEqual(second['registrations_created'], 0)
        self.assertEqual(second['registrations_updated'], 1)
        self.assertEqual(course_registration.objects.count(), 1)
        self.assertEqual(
            course_registration.objects.get().course_instructor,
            self.offering,
        )

    def test_allocate_preserves_existing_and_allocates_only_remaining_students(self):
        second_student = self.create_second_student()
        existing = FinalRegistration.objects.create(
            student_id=self.student, semester_id=self.semester,
            course_id=self.course, course_slot_id=self.slot,
            registration_type='Regular', verified=True,
            course_instructor=self.offering)
        publish_allocations(2026, 1, 2026, 'UG')

        before = allocation_progress(2026, 1, 'UG')
        self.assertEqual(before['allocated_allocations'], 1)
        self.assertEqual(before['remaining_students'], 1)

        response = allocate(SimpleNamespace(POST={
            'batch': 2026,
            'sem': 1,
            'year': 2026,
            'programme_type': 'UG',
            'skip_course_ids': [],
        }))

        self.assertEqual(json.loads(response.content)['status'], 1)
        self.assertTrue(FinalRegistration.objects.filter(pk=existing.pk).exists())
        self.assertEqual(FinalRegistration.objects.count(), 2)
        self.assertTrue(FinalRegistration.objects.filter(
            student_id=second_student, verified=True).exists())
        self.assertEqual(course_registration.objects.count(), 2)
        after = allocation_progress(2026, 1, 'UG')
        self.assertEqual(after['remaining_allocations'], 0)

    def test_partial_allocation_response_reports_remaining_students(self):
        self.create_second_student()
        existing = FinalRegistration.objects.create(
            student_id=self.student, semester_id=self.semester,
            course_id=self.course, course_slot_id=self.slot,
            registration_type='Regular', verified=True,
            course_instructor=self.offering)

        response = allocate(SimpleNamespace(POST={
            'batch': 2026,
            'sem': 1,
            'year': 2026,
            'programme_type': 'UG',
            'skip_course_ids': [self.course.id],
        }))
        payload = json.loads(response.content)

        self.assertEqual(payload['status'], 1)
        self.assertEqual(payload['progress']['remaining_students'], 1)
        self.assertTrue(FinalRegistration.objects.filter(pk=existing.pk).exists())
        self.assertEqual(FinalRegistration.objects.count(), 1)

    def test_open_elective_resume_skips_already_allocated_student(self):
        self.slot.type = 'Open Elective'
        self.slot.save(update_fields=['type'])
        second_student = self.create_second_student()
        existing = FinalRegistration.objects.create(
            student_id=self.student, semester_id=self.semester,
            course_id=self.course, course_slot_id=self.slot,
            registration_type='Regular', verified=True,
            course_instructor=self.offering)

        response = allocate(SimpleNamespace(POST={
            'batch': 2026,
            'sem': 1,
            'year': 2026,
            'programme_type': 'UG',
            'skip_course_ids': [],
        }))
        payload = json.loads(response.content)

        self.assertEqual(payload['status'], 1)
        self.assertEqual(payload['progress']['remaining_allocations'], 0)
        self.assertTrue(FinalRegistration.objects.filter(pk=existing.pk).exists())
        self.assertTrue(FinalRegistration.objects.filter(
            student_id=second_student).exists())
        self.assertEqual(FinalRegistration.objects.count(), 2)
