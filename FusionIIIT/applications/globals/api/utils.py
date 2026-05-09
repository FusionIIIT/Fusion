from django.contrib.auth import authenticate
from rest_framework import serializers


def parse_academic_year(year_value):
    """Normalize an academic year input into a (start_year, end_year) tuple."""
    if year_value is None:
        raise serializers.ValidationError("Academic year is required.")

    cleaned = str(year_value).strip()
    if '-' in cleaned:
        parts = cleaned.split('-')
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise serializers.ValidationError("Invalid academic year format.")
        start_year = int(parts[0])
        end_year = int(parts[1])
    else:
        if not cleaned.isdigit():
            raise serializers.ValidationError("Invalid academic year format.")
        start_year = int(cleaned)
        end_year = start_year + 1

    if end_year - start_year != 1:
        raise serializers.ValidationError("Academic year must span exactly one year.")

    return start_year, end_year


def get_and_authenticate_user(username, password):
    user = authenticate(username=username, password=password)
    if user is None:
        raise serializers.ValidationError("Invalid credentials.")
    return user
