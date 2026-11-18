import json
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token

from applications.academic_information.models import Student
from applications.academic_information.utils import (
    allocate, allocation_progress, publish_allocations,
)
from applications.academic_procedures.models import (
    FinalRegistration, InitialRegistration, course_registration,
)
from applications.globals.models import (
    Designation, ExtraInfo, Faculty, HoldsDesignation,
)
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

    def test_choice_whose_slot_was_deleted_is_reported_and_the_rest_allotted(self):
        # A slot deleted after students pre-registered leaves their choice with
        # no slot (on_delete=SET_NULL). Allocation stopped on it with
        # "CourseSlot matching query does not exist." and allotted nothing.
        dropped_course = Course.objects.create(
            code='TT1002', name='Dropped Course', credit=1, syllabus='',
            ref_books='', max_seats=60)
        dropped_slot = CourseSlot.objects.create(
            semester=self.semester, name='Dropped Slot',
            type='Professional Core')
        dropped_slot.courses.add(dropped_course)
        InitialRegistration.objects.create(
            student_id=self.student, semester_id=self.semester,
            course_id=dropped_course, course_slot_id=dropped_slot, priority=1,
            registration_type='Regular')
        dropped_slot.delete()

        response = allocate(SimpleNamespace(POST={
            'batch': 2026,
            'sem': 1,
            'year': 2026,
            'programme_type': 'UG',
            'skip_course_ids': [],
        }))
        payload = json.loads(response.content)

        self.assertEqual(payload['status'], 1, payload)
        self.assertEqual(payload['progress']['remaining_allocations'], 0)
        self.assertEqual(
            list(FinalRegistration.objects.values_list('course_id__code', flat=True)),
            ['TT1001'])
        self.assertEqual(payload['unslotted_choices'], [{
            'course_id': dropped_course.id,
            'course_code': 'TT1002',
            'course_name': 'Dropped Course',
            'students': 1,
        }])
        self.assertIn('TT1002', payload['message'])
        self.assertIn('no longer exists', payload['message'])

    def new_course(self, code):
        return Course.objects.create(
            code=code, name=f'Course {code}', credit=4, syllabus='',
            ref_books='', max_seats=60)

    def choose(self, student, semester, slot, courses_by_priority):
        for priority, course in courses_by_priority:
            InitialRegistration.objects.create(
                student_id=student, semester_id=semester, course_id=course,
                course_slot_id=slot, priority=priority,
                registration_type='Regular')

    def run_allocation(self):
        return json.loads(allocate(SimpleNamespace(POST={
            'batch': 2026, 'sem': 1, 'year': 2026, 'programme_type': 'UG',
            'skip_course_ids': [],
        })).content)

    def allotted(self):
        return set(FinalRegistration.objects.values_list(
            'student_id_id', 'course_id__code'))

    def student_in_another_curriculum(self, roll_no):
        curriculum = Curriculum.objects.create(
            programme=Programme.objects.get(category='UG'),
            name=f'Test Curriculum {roll_no}', no_of_semester=8)
        semester = Semester.objects.create(curriculum=curriculum, semester_no=1)
        batch = Batch.objects.create(
            name='B.Tech', discipline=Discipline.objects.create(
                name=f'Test Discipline {roll_no}', acronym=roll_no[2:5]),
            year=2026, curriculum=curriculum)
        user = User.objects.create_user(username=roll_no)
        student = Student.objects.create(
            id=ExtraInfo.objects.create(id=roll_no, user=user, user_type='student'),
            programme='B.Tech', batch=2026, batch_id=batch, category='GEN',
            curr_semester_no=1, section='E1')
        return student, semester

    def project_courses(self, prefix):
        return [self.new_course(f'{prefix}{n}') for n in (1, 2, 3)]

    def test_slot_named_like_an_open_elective_elsewhere_allots_one_course(self):
        # Batch 2023 semester 8: CSE's "Project" slot was an Open Elective,
        # ECE typed its copy "Project" and ME named it "PROJECT"; their
        # students were allotted all three ranked courses.
        courses = self.project_courses('TP40')
        elective = CourseSlot.objects.create(
            semester=self.semester, name='Project', type='Open Elective')
        elective.courses.add(*courses)
        self.choose(self.student, self.semester, elective,
                    [(1, courses[0]), (2, courses[1]), (3, courses[2])])
        other, other_semester = self.student_in_another_curriculum('26TME001')
        typed_project = CourseSlot.objects.create(
            semester=other_semester, name='PROJECT ', type='Project')
        typed_project.courses.add(*courses)
        self.choose(other, other_semester, typed_project,
                    [(1, courses[1]), (2, courses[0]), (3, courses[2])])

        payload = self.run_allocation()

        self.assertEqual(payload['status'], 1, payload)
        self.assertEqual(payload['progress']['remaining_allocations'], 0, payload)
        self.assertEqual(self.allotted(), {
            ('26TCS001', 'TT1001'), ('26TCS001', 'TP401'), ('26TME001', 'TP402')})

    def test_courses_of_a_slot_that_is_not_an_elective_are_all_allotted_even_when_ranked(self):
        # The form makes students rank every slot, PC4 included, so the
        # ranking must not decide how a slot is allotted; the curriculum does.
        slot = CourseSlot.objects.create(
            semester=self.semester, name='PC4', type='Others')
        first, second = self.new_course('TP4101'), self.new_course('TP4102')
        slot.courses.add(first, second)
        self.choose(self.student, self.semester, slot, [(1, first), (2, second)])
        other, other_semester = self.student_in_another_curriculum('26TME002')
        other_slot = CourseSlot.objects.create(
            semester=other_semester, name='PC4', type='Others')
        other_slot.courses.add(first, second)
        self.choose(other, other_semester, other_slot, [(1, first), (1, second)])

        payload = self.run_allocation()

        self.assertEqual(payload['status'], 1, payload)
        self.assertEqual(self.allotted(), {
            ('26TCS001', 'TT1001'), ('26TCS001', 'TP4101'), ('26TCS001', 'TP4102'),
            ('26TME002', 'TP4101'), ('26TME002', 'TP4102')})

    def test_open_elective_slot_sharing_a_name_with_another_slot_is_allotted(self):
        # Batch 2023 semester 8: ECE's "Project" slot (type Project) was handled
        # first and its name marked done, so CSE's "Project" Open Elective slot
        # was skipped and its 282 students got no project.
        thesis = self.new_course('TP4201')
        typed_project = CourseSlot.objects.create(
            semester=self.semester, name='Project', type='Project')
        typed_project.courses.add(thesis)
        self.choose(self.student, self.semester, typed_project, [(1, thesis)])
        other, other_semester = self.student_in_another_curriculum('26TEC001')
        btp, internship = self.new_course('TP4202'), self.new_course('TP4203')
        elective = CourseSlot.objects.create(
            semester=other_semester, name='Project', type='Open Elective')
        elective.courses.add(btp, internship)
        self.choose(other, other_semester, elective, [(1, btp), (2, internship)])

        payload = self.run_allocation()

        self.assertEqual(payload['status'], 1, payload)
        self.assertEqual(payload['progress']['remaining_allocations'], 0, payload)
        self.assertEqual(self.allotted(), {
            ('26TCS001', 'TT1001'), ('26TCS001', 'TP4201'), ('26TEC001', 'TP4202')})

    def test_several_first_choices_in_an_elective_slot_are_all_allotted(self):
        # PhD coursework: 26PCSO02 chose two OE3 courses, both priority 1, and
        # takes both. Grouping slots by name must not change that.
        courses = self.project_courses('TP43')
        elective = CourseSlot.objects.create(
            semester=self.semester, name='OE3', type='Open Elective')
        elective.courses.add(*courses)
        self.choose(self.student, self.semester, elective,
                    [(1, courses[0]), (1, courses[1])])

        payload = self.run_allocation()

        self.assertEqual(payload['status'], 1, payload)
        self.assertEqual(self.allotted(), {
            ('26TCS001', 'TT1001'), ('26TCS001', 'TP431'), ('26TCS001', 'TP432')})


class PhdStudentListTests(TestCase):
    def setUp(self):
        self.client = Client()
        admin = User.objects.create_user(username='roll_list_admin')
        token = Token.objects.create(user=admin)
        designation = Designation.objects.create(name='acadadmin')
        HoldsDesignation.objects.create(
            user=admin,
            working=admin,
            designation=designation,
            held_at=timezone.now(),
        )
        self.auth = 'Token {}'.format(token.key)

        programme = Programme.objects.create(
            category='PHD', name='Test Ph.D.', programme_begin_year=2026)
        discipline = Discipline.objects.create(
            name='Test Doctoral Discipline', acronym='TDD')
        curriculum = Curriculum.objects.create(
            programme=programme, name='Test Ph.D. Curriculum',
            no_of_semester=8)
        semester = Semester.objects.create(
            curriculum=curriculum, semester_no=1)
        canonical_batch = Batch.objects.create(
            name='PhD (Odd)', discipline=discipline, year=2026,
            curriculum=curriculum)
        legacy_batch = Batch.objects.create(
            name='PhD (Even)', discipline=discipline, year=2026)
        self.course = Course.objects.create(
            code='TD8001', name='Doctoral Test Course', credit=4,
            syllabus='', ref_books='')

        self._register_student(
            '26TDD001', 'Other', canonical_batch, semester)
        self._register_student(
            '26TDD002', 'Ph.D', legacy_batch, semester)

    def _register_student(self, roll_no, programme, batch, semester):
        user = User.objects.create_user(username=roll_no)
        extra = ExtraInfo.objects.create(
            id=roll_no, user=user, user_type='student')
        student = Student.objects.create(
            id=extra, programme=programme, batch=2026, batch_id=batch,
            category='GEN', curr_semester_no=1)
        course_registration.objects.create(
            student_id=student,
            working_year=2026,
            semester_id=semester,
            course_id=self.course,
            registration_type='Regular',
            session='2026-27',
            semester_type='Odd Semester',
        )

    def test_phd_preview_accepts_category_and_legacy_programme_value(self):
        response = self.client.post(
            '/aims/api/generatexlsheet',
            data=json.dumps({
                'academic_year': '2026-27',
                'semester_type': 'Odd Semester',
                'course': self.course.id,
                'programme_type': 'PHD',
                'preview_only': True,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {student['roll_no'] for student in response.json()['students']},
            {'26TDD001', '26TDD002'},
        )
