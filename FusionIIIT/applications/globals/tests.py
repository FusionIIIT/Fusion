from django.test import SimpleTestCase

from applications.globals.programme_scope import (
    canonical_programme_name,
    programme_display_name,
)


class ProgrammeNameTests(SimpleTestCase):
    def test_phd_spellings_share_one_internal_value(self):
        for value in ('PhD', 'Ph.D', 'Ph.D.', 'PHD', 'phd'):
            self.assertEqual(canonical_programme_name(value), 'PhD')

    def test_phd_display_name_is_stable_for_legacy_values(self):
        for value in ('PhD', 'Ph.D', 'Ph.D.'):
            self.assertEqual(
                programme_display_name(value),
                'Doctor of Philosophy',
            )
