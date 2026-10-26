import json

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token

from applications.globals.models import Designation, HoldsDesignation
from applications.programme_curriculum.api.views_student_management import (
    resolve_discipline_reference,
    resolve_requested_batch,
)
from applications.programme_curriculum.models import Batch, Discipline


class DisciplineResolutionTests(TestCase):
    def test_resolves_master_name_and_acronym(self):
        discipline = Discipline.objects.create(
            name='Quantum Systems', acronym='QS'
        )

        by_name, name_error = resolve_discipline_reference(' Quantum  Systems ')
        by_acronym, acronym_error = resolve_discipline_reference('qs')

        self.assertIsNone(name_error)
        self.assertIsNone(acronym_error)
        self.assertEqual(by_name, discipline)
        self.assertEqual(by_acronym, discipline)

    def test_unknown_reference_does_not_create_a_discipline(self):
        discipline, error = resolve_discipline_reference('Unknown Field')

        self.assertIsNone(discipline)
        self.assertIn('does not exist', error)
        self.assertFalse(Discipline.objects.exists())

    def test_rejects_an_ambiguous_acronym(self):
        Discipline.objects.create(name='Natural Sciences', acronym='NS')
        Discipline.objects.create(name='Network Systems', acronym='NS')

        discipline, error = resolve_discipline_reference('NS')

        self.assertIsNone(discipline)
        self.assertIn('ambiguous', error)


class BatchResolutionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='batch_admin', password='pw')
        self.token = Token.objects.create(user=self.user)
        designation = Designation.objects.create(name='acadadmin')
        HoldsDesignation.objects.create(
            user=self.user,
            working=self.user,
            designation=designation,
            held_at=timezone.now(),
        )
        self.liberal_arts = Discipline.objects.create(
            name='Liberal Arts', acronym='LA'
        )
        self.natural_sciences = Discipline.objects.create(
            name='Natural Sciences', acronym='NS'
        )
        self.la_odd = Batch.objects.create(
            name='PhD (Odd)',
            discipline=self.liberal_arts,
            year=2026,
            total_seats=20,
        )
        self.ns_odd = Batch.objects.create(
            name='PhD (Odd)',
            discipline=self.natural_sciences,
            year=2026,
            total_seats=20,
        )
        self.ns_even = Batch.objects.create(
            name='PhD (Even)',
            discipline=self.natural_sciences,
            year=2026,
            total_seats=20,
        )

    def post_prerequisites(self, payload):
        return self.client.post(
            '/programme_curriculum/api/batches/validate_prerequisites/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key),
        )

    def test_prerequisites_resolve_names_and_acronyms_to_odd_batches(self):
        response = self.post_prerequisites({
            'academic_year': 2026,
            'programme_type': 'phd',
            'phd_semester': 'odd',
            'disciplines': ['Liberal Arts', 'NS'],
        })

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['can_upload_students'])
        self.assertEqual(
            {item['batch_id'] for item in body['existing_batches']},
            {self.la_odd.id, self.ns_odd.id},
        )

    def test_prerequisites_do_not_accept_another_intake(self):
        self.la_odd.delete()
        Batch.objects.create(
            name='PhD (Even)',
            discipline=self.liberal_arts,
            year=2026,
            total_seats=20,
        )

        response = self.post_prerequisites({
            'academic_year': 2026,
            'programme_type': 'phd',
            'phd_semester': 'odd',
            'disciplines': ['Liberal Arts'],
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['can_upload_students'])

    def test_requested_batch_is_verified_against_canonical_discipline(self):
        batch, error = resolve_requested_batch(
            self.la_odd.id,
            'LA',
            2026,
            'phd',
            'odd',
            None,
        )

        self.assertIsNone(error)
        self.assertEqual(batch, self.la_odd)

    def test_requested_batch_rejects_wrong_discipline_or_semester(self):
        wrong_discipline, discipline_error = resolve_requested_batch(
            self.la_odd.id,
            'Natural Sciences',
            2026,
            'phd',
            'odd',
            None,
        )
        wrong_semester, semester_error = resolve_requested_batch(
            self.ns_even.id,
            'Natural Sciences',
            2026,
            'phd',
            'odd',
            None,
        )

        self.assertIsNone(wrong_discipline)
        self.assertIn('not Natural Sciences', discipline_error)
        self.assertIsNone(wrong_semester)
        self.assertIn('admission semester', semester_error)
