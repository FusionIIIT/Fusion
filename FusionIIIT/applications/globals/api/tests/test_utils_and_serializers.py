from django.test import SimpleTestCase

from applications.globals.api.serializers import ProfileDeleteRequestSerializer
from applications.globals.api.utils import parse_academic_year


class UtilsAndSerializersTests(SimpleTestCase):
    def test_parse_academic_year_from_single_year(self):
        start, end = parse_academic_year('2025')
        self.assertEqual((start, end), (2025, 2026))

    def test_parse_academic_year_from_range(self):
        start, end = parse_academic_year('2024-2025')
        self.assertEqual((start, end), (2024, 2025))

    def test_profile_delete_request_requires_exactly_one_key(self):
        serializer = ProfileDeleteRequestSerializer(data={'deleteedu': '1', 'deletepub': '2'})
        self.assertFalse(serializer.is_valid())

    def test_profile_delete_request_accepts_single_key(self):
        serializer = ProfileDeleteRequestSerializer(data={'deleteedu': '1'})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['delete_key'], 'deleteedu')
