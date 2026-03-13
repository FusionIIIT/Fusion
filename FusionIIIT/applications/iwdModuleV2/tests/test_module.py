"""Baseline tests for service-layer validation and exceptions.

These tests are unit-level and do not require database fixtures.
"""

import pytest

from applications.iwdModuleV2.services import ServiceError
from applications.iwdModuleV2.services import ValidationError
from applications.iwdModuleV2.services import _to_non_negative_decimal


def test_service_error_is_exception():
    assert issubclass(ServiceError, Exception)


def test_non_negative_decimal_accepts_valid_value():
    value = _to_non_negative_decimal("12.50", "budget")
    assert str(value) == "12.50"


def test_non_negative_decimal_rejects_negative_value():
    with pytest.raises(ValidationError):
        _to_non_negative_decimal("-1", "budget")


def test_non_negative_decimal_rejects_invalid_value():
    with pytest.raises(ValidationError):
        _to_non_negative_decimal("abc", "budget")
