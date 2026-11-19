from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from applications.academic_information.models import Student
from applications.academic_procedures.api.views import _teaching_credits_completed
from applications.academic_procedures.models import (
    TeachingCreditAllocation,
    TeachingCreditRegistration,
)
from applications.examination.api.views import _phd_extra_records
from applications.globals.models import ExtraInfo
from applications.programme_curriculum.models import (
    Batch,
    Course,
    Curriculum,
    Discipline,
    Programme,
    Semester,
    TeachingCredit,
    TeachingCreditSlot,
)


class TeachingCreditVersionTests(TestCase):
    """Teaching credits are versioned like courses, and a semester's results
    can name the catalogue entry they are for (Teaching Work I and II together)."""

    def setUp(self):
        programme = Programme.objects.create(category='PHD', name='Doctor of Philosophy',
                                             programme_begin_year=2020)
        self.discipline = Discipline.objects.create(name='Mechanical Engineering', acronym='ME')
        curriculum = Curriculum.objects.create(programme=programme, name='PhD ME 2020',
                                               no_of_semester=10)
        self.semester = Semester.objects.create(curriculum=curriculum, semester_no=5)
        batch = Batch.objects.create(name='Ph.D', discipline=self.discipline, year=2020,
                                     curriculum=curriculum)
        user = User.objects.create_user(username='20PMEO12')
        extra = ExtraInfo.objects.create(id='20PMEO12', user=user, user_type='student',
                                         user_status='PRESENT')
        self.student = Student.objects.create(id=extra, programme='PhD', batch=2020,
                                              batch_id=batch, category='GEN', curr_semester_no=5)
        self.slot = TeachingCreditSlot.objects.create(semester=self.semester, name='TW')

    def _entry(self, code, credit, version='1.0', latest=True, name='Teaching Work II'):
        return TeachingCredit.objects.create(code=code, name=name, credit=credit,
                                             version=Decimal(version), latest_version=latest,
                                             discipline=self.discipline, programme_type='PHD')

    def _result(self, entry, result='satisfactory'):
        TeachingCreditRegistration.objects.create(
            student=self.student, teaching_credit_slot=self.slot, teaching_credit=entry,
            semester=self.semester, status='verified')
        return TeachingCreditAllocation.objects.create(
            student=self.student, semester=self.semester, teaching_credit=entry,
            status='completed', result=result)

    def _teaching_rows(self):
        return [(r['code'], r['name'], r['display_credit'], r['display_grade'])
                for r in _phd_extra_records(self.student, 5)
                if r['key'].startswith('teaching_credit_')]

    def test_a_code_can_have_two_versions_with_different_credits(self):
        self._entry('ME795', 1)
        self._entry('ME795', 2, version='1.1', latest=False)
        self.assertEqual(
            sorted(TeachingCredit.objects.filter(code='ME795').values_list('credit', flat=True)),
            [1, 2])

    def test_the_same_code_and_version_cannot_be_added_twice(self):
        self._entry('ME795', 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._entry('ME795', 2)

    def test_a_result_shows_its_own_entry_and_credit(self):
        self._entry('ME795', 1)
        self._result(self._entry('ME795', 2, version='1.1', latest=False))
        self.assertEqual(self._teaching_rows(), [('ME795', 'Teaching Work II', 2, 'S')])
        self.assertEqual(_teaching_credits_completed(self.student), 2)

    def test_one_semester_can_hold_teaching_work_i_and_ii(self):
        self._result(self._entry('ME794', 1, name='Teaching Work I'))
        self._result(self._entry('ME795', 1))
        self.assertEqual(sorted(self._teaching_rows()), [
            ('ME794', 'Teaching Work I', 1, 'S'), ('ME795', 'Teaching Work II', 1, 'S')])
        self.assertEqual(_teaching_credits_completed(self.student), 2)

    def test_an_unsatisfactory_result_shows_x_and_earns_nothing(self):
        self._result(self._entry('ME795', 1), result='not_satisfactory')
        self.assertEqual(self._teaching_rows(), [('ME795', 'Teaching Work II', 1, 'X')])
        self.assertEqual(_teaching_credits_completed(self.student), 0)

    def test_the_same_entry_cannot_be_recorded_twice_in_a_semester(self):
        entry = self._entry('ME795', 1)
        self._result(entry)
        with self.assertRaises(IntegrityError), transaction.atomic():
            TeachingCreditAllocation.objects.create(
                student=self.student, semester=self.semester, teaching_credit=entry)

    def test_a_live_allocation_is_still_one_per_semester(self):
        course = Course.objects.create(code='ME101', name='Engineering Mechanics', credit=4,
                                       syllabus='', ref_books='')
        TeachingCreditAllocation.objects.create(student=self.student, semester=self.semester,
                                                choice_1=course)
        with self.assertRaises(IntegrityError), transaction.atomic():
            TeachingCreditAllocation.objects.create(student=self.student, semester=self.semester,
                                                    choice_1=course)

    def test_a_live_result_takes_its_entry_from_the_semester_registration(self):
        course = Course.objects.create(code='ME101', name='Engineering Mechanics', credit=4,
                                       syllabus='', ref_books='')
        self.slot.teaching_credits.add(self._entry('ME795', 1))
        TeachingCreditRegistration.objects.create(student=self.student, teaching_credit_slot=self.slot,
                                                  semester=self.semester, status='verified')
        TeachingCreditAllocation.objects.create(
            student=self.student, semester=self.semester, choice_1=course, allocated_course=course,
            status='completed', result='satisfactory')
        self.assertEqual(self._teaching_rows(), [('ME795', 'Teaching Work II', 1, 'S')])
        self.assertEqual(_teaching_credits_completed(self.student), 1)

    def test_the_latest_version_wins_when_the_registration_names_none(self):
        self.slot.teaching_credits.add(self._entry('ME795', 2, version='1.1', latest=False),
                                       self._entry('ME795', 1))
        TeachingCreditRegistration.objects.create(student=self.student, teaching_credit_slot=self.slot,
                                                  semester=self.semester, status='verified')
        TeachingCreditAllocation.objects.create(student=self.student, semester=self.semester,
                                                status='completed', result='satisfactory')
        self.assertEqual(_teaching_credits_completed(self.student), 1)
