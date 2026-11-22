from django.test import TestCase

from applications.academic_information.models import Student
from applications.academic_information.status_test_utils import make_student
from applications.academic_information.student_status import (
    LOCKED_STATUSES,
    StudentLocked,
    assert_unlocked,
    exclude_locked,
    is_locked_status,
    locked_roll_nos,
    unlocked_q,
)


class LockHelperTests(TestCase):
    def test_locked_statuses(self):
        self.assertEqual(LOCKED_STATUSES, frozenset({'ALUMNI', 'WITHDRAWN', 'ARCHIVED', 'LEFT'}))

    def test_normalise_and_lock(self):
        self.assertTrue(is_locked_status(' alumni '))
        self.assertTrue(is_locked_status('Withdrawn'))
        self.assertFalse(is_locked_status('PRESENT'))
        self.assertFalse(is_locked_status('NEW'))
        self.assertFalse(is_locked_status(None))
        self.assertFalse(is_locked_status(''))

    def test_locked_roll_nos_one_query(self):
        make_student('21BCS001', status='ALUMNI')
        make_student('21BCS002', status='PRESENT')
        make_student('21BCS003', status=' alumni ')
        with self.assertNumQueries(1):
            found = locked_roll_nos(['21BCS001', '21BCS002', '21BCS003', 'NOPE'])
        self.assertEqual(found, {'21BCS001': 'ALUMNI', '21BCS003': 'ALUMNI'})

    def test_locked_roll_nos_empty_makes_no_query(self):
        with self.assertNumQueries(0):
            self.assertEqual(locked_roll_nos([]), {})

    def test_exclude_locked(self):
        make_student('21BCS001', status='ALUMNI')
        make_student('21BCS002', status='PRESENT')
        make_student('21BCS003', status='Left ')
        rolls = list(exclude_locked(Student.objects.all()).values_list('id_id', flat=True))
        self.assertEqual(rolls, ['21BCS002'])

    def test_assert_unlocked_message(self):
        make_student('21BCS001', status='ALUMNI')
        with self.assertRaises(StudentLocked) as caught:
            assert_unlocked(['21BCS001'])
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(
            str(caught.exception.detail),
            '21BCS001 is Alumni; their records cannot be changed. '
            'Restore them in System Administrator first.')

    def test_assert_unlocked_names_at_most_three(self):
        for n in range(1, 6):
            make_student('21BCS00%d' % n, status='ALUMNI')
        with self.assertRaises(StudentLocked) as caught:
            assert_unlocked(['21BCS00%d' % n for n in range(1, 6)])
        self.assertEqual(
            str(caught.exception.detail),
            '21BCS001 (Alumni), 21BCS002 (Alumni), 21BCS003 (Alumni) and 2 more are '
            'stopped; their records cannot be changed. Restore them in System Administrator first.')

    def test_assert_unlocked_passes_for_present(self):
        make_student('21BCS001', status='PRESENT')
        assert_unlocked(['21BCS001'])
        assert_unlocked([])

    def test_unlocked_q_across_a_relation(self):
        make_student('21BCS001', status=' Alumni')
        make_student('21BCS002', status='PRESENT')
        rolls = list(Student.objects.filter(unlocked_q('id__')).values_list('id_id', flat=True))
        self.assertEqual(rolls, ['21BCS002'])
