"""Database-free tests for timetable API validation and model/migration sync.

Run from the FusionIIIT directory::

    python -m unittest applications.academic_procedures.test_timetable_validation

Model and migration files are read as source (``ast``), so these tests do not
need Django settings, a database, or ortools.
"""

import ast
import os
import unittest

from applications.academic_procedures.api import timetable_validation as v
from applications.academic_procedures.api.timetable_workflow import plan_publication
from applications.academic_procedures.solver import timetable_solver as ts

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def _parse(relative_path):
    with open(os.path.join(APP_DIR, relative_path), encoding='utf-8') as source:
        return ast.parse(source.read())


def _model_class(name):
    for node in _parse('models.py').body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f'model {name} not found')


def _choice_values(model, attribute):
    for statement in _model_class(model).body:
        if (isinstance(statement, ast.Assign)
                and getattr(statement.targets[0], 'id', None) == attribute):
            return [ast.literal_eval(pair)[0] for pair in statement.value.elts]
    raise AssertionError(f'{model}.{attribute} not found')


class ParseIntTests(unittest.TestCase):

    def test_accepts_ints_digit_strings_and_integral_floats(self):
        self.assertEqual(v.parse_int(5, 'x'), 5)
        self.assertEqual(v.parse_int('5', 'x'), 5)
        self.assertEqual(v.parse_int(' 5 ', 'x'), 5)
        self.assertEqual(v.parse_int(9.0, 'x'), 9)

    def test_rejects_fractions_instead_of_truncating(self):
        # Regression: 9.7 used to become 9 (an hour the client never asked for).
        for value in (9.7, '9.7', 0.5):
            with self.assertRaises(ValueError, msg=value):
                v.parse_int(value, 'new_start_hour')

    def test_rejects_non_numbers(self):
        for value in (None, 'abc', '', True, False, [], {}):
            with self.assertRaises(ValueError, msg=repr(value)):
                v.parse_int(value, 'x')

    def test_bounds_and_choices(self):
        with self.assertRaisesRegex(ValueError, '>= 1'):
            v.parse_int(0, 'timeout_seconds', minimum=1)
        with self.assertRaisesRegex(ValueError, '<= 600'):
            v.parse_int(601, 'timeout_seconds', maximum=600)
        self.assertEqual(v.parse_int(600, 'timeout_seconds', minimum=1, maximum=600), 600)
        with self.assertRaises(ValueError):
            v.parse_int(13, 'hour', choices=ts.HOURS)  # lunch
        self.assertEqual(v.parse_int('12', 'hour', choices=ts.HOURS), 12)


class ParseBoolTests(unittest.TestCase):

    def test_true_values(self):
        for value in (True, 'true', 'TRUE ', '1', 'yes', 1, 1.0):
            self.assertIs(v.parse_bool(value, 'lock'), True, repr(value))

    def test_false_values(self):
        # bool('false') is True; that bug made "lock": "false" lock the slot.
        for value in (False, 'false', 'False', '0', 'no', '', 0):
            self.assertIs(v.parse_bool(value, 'lock'), False, repr(value))

    def test_rejects_anything_else(self):
        for value in ('maybe', None, 2, [], {}):
            with self.assertRaises(ValueError, msg=repr(value)):
                v.parse_bool(value, 'lock')


class StringAndClassroomTests(unittest.TestCase):

    def test_clean_str(self):
        self.assertEqual(v.clean_str('  CSE ', 'programme', 15), 'CSE')
        with self.assertRaises(ValueError):
            v.clean_str('   ', 'name', 10)
        with self.assertRaises(ValueError):
            v.clean_str('x' * 16, 'programme', 15)
        for value in (None, ['a'], {'a': 1}, True):
            with self.assertRaises(ValueError, msg=repr(value)):
                v.clean_str(value, 'name', 10)

    def test_room_id_must_be_addressable_by_the_detail_url(self):
        for good in ('L101', 'CS-LAB_2', 'x' * 20):
            self.assertEqual(v.clean_room_id(good), good)
        for bad in ('', 'L 101', 'L/101', 'x' * 21, 101, None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                v.clean_room_id(bad)

    def test_classroom_fields(self):
        fields = v.clean_classroom_fields({'building': ' A ', 'capacity': '60',
                                           'room_type': 'Lecture Hall', 'is_active': 'false'})
        self.assertEqual(fields, {'building': 'A', 'capacity': 60,
                                  'room_type': 'Lecture Hall', 'is_active': False})
        self.assertEqual(v.clean_classroom_fields({}), {})  # PATCH with nothing

    def test_classroom_fields_reject_bad_values(self):
        for data in ({'capacity': 0}, {'capacity': v.POSITIVE_INT_MAX + 1},
                     {'room_type': 'Kitchen'}, {'building': 'x' * 101},
                     {'building': ''}, {'is_active': 'maybe'}):
            with self.assertRaises(ValueError, msg=data):
                v.clean_classroom_fields(data)
        with self.assertRaisesRegex(ValueError, 'capacity is required'):
            v.clean_classroom_fields({'building': 'A'}, required_fields=('building', 'capacity'))


class PublicationPlanTests(unittest.TestCase):

    def test_archives_every_other_published_version_of_the_term(self):
        # Even if bad earlier data left two Published versions, publishing
        # leaves exactly one.
        error, archive = plan_publication(
            3, {1: 'Published', 2: 'Published', 3: 'Draft', 4: 'Archived'}, True)
        self.assertIsNone(error)
        self.assertEqual(archive, [1, 2])

    def test_first_publication_archives_nothing(self):
        self.assertEqual(plan_publication(1, {1: 'Approved'}, True), (None, []))

    def test_only_publishable_statuses(self):
        for status in ('Draft', 'UnderReview', 'Approved'):
            self.assertIsNone(plan_publication(1, {1: status}, True)[0], status)
        for status in ('Published', 'Archived', 'Infeasible'):
            error, archive = plan_publication(1, {1: status, 2: 'Published'}, True)
            self.assertIn(status, error)
            self.assertEqual(archive, [], 'a refused publish must archive nothing')

    def test_empty_version_cannot_be_published(self):
        error, archive = plan_publication(1, {1: 'Draft', 2: 'Published'}, False)
        self.assertIn('no scheduled slots', error)
        self.assertEqual(archive, [])


class ChoicesMatchModelsTests(unittest.TestCase):
    """The API validates against copies of model choices; keep them equal."""

    def test_room_types(self):
        self.assertEqual(list(v.ROOM_TYPES), _choice_values('Classroom', 'ROOM_TYPE_CHOICES'))

    def test_preferred_room_types(self):
        # Regression: 'Seminar Room' was accepted though the model has no such choice.
        self.assertEqual(list(v.PREFERRED_ROOM_TYPES),
                         _choice_values('CourseWeeklyRequirement', 'PREFERRED_ROOM_TYPE_CHOICES'))

    def test_semester_types(self):
        self.assertEqual(list(v.SEMESTER_TYPES),
                         _choice_values('TimetableVersion', 'SEMESTER_TYPE_CHOICES'))

    def test_solver_days_and_hours(self):
        self.assertEqual(ts.DAYS, _choice_values('TimetableSlot', 'DAY_CHOICES'))
        self.assertEqual(ts.HOURS, _choice_values('TimetableSlot', 'HOUR_CHOICES'))

    def test_solver_room_affinity_uses_real_room_types(self):
        for room_types in ts.SLOT_ROOM_AFFINITY.values():
            self.assertTrue(set(room_types) <= set(v.ROOM_TYPES), room_types)


class ModelsMatchMigrationTests(unittest.TestCase):
    """Meta options must match migration 0061, or makemigrations adds a migration."""

    def _migration_names(self, operation):
        names = set()
        for node in ast.walk(_parse('migrations/0061_timetable_models.py')):
            if isinstance(node, ast.Call) and ast.unparse(node.func) == f'migrations.{operation}':
                for inner in ast.walk(node):
                    if isinstance(inner, ast.keyword) and inner.arg == 'name' and \
                            isinstance(inner.value, ast.Constant) and inner.value.value.startswith(('tt_', 'unique_')):
                        names.add(inner.value.value)
        return names

    def _meta_names(self, model, kind):
        names = set()
        for statement in _model_class(model).body:
            if isinstance(statement, ast.ClassDef) and statement.name == 'Meta':
                for node in ast.walk(statement):
                    if isinstance(node, ast.Call) and ast.unparse(node.func).endswith(kind):
                        for keyword in node.keywords:
                            if keyword.arg == 'name':
                                names.add(ast.literal_eval(keyword.value))
        return names

    def test_unique_constraint_name(self):
        self.assertEqual(self._meta_names('TimetableVersion', 'UniqueConstraint'),
                         self._migration_names('AddConstraint'))

    def test_index_names(self):
        self.assertEqual(self._meta_names('TimetableSlot', 'Index'),
                         self._migration_names('AddIndex'))

    def test_no_unique_together_on_version(self):
        source = ast.unparse(_model_class('TimetableVersion'))
        self.assertNotIn('unique_together', source)


if __name__ == '__main__':
    unittest.main()
