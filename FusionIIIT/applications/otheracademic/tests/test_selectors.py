"""
Tests for otheracademic selectors.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from applications.otheracademic import selectors
from applications.otheracademic.models import (
    LeaveFormTable,
    LeavePG,
    BonafideFormTableUpdated,
    AssistantshipClaimFormStatusUpd,
    LeaveStatusChoices,
)


class UserSelectorsTestCase(TestCase):
    """Tests for user-related selectors."""

    def test_get_user_by_username_exists(self):
        """Test getting a user that exists."""
        user = User.objects.create_user(username='testuser', password='testpass')
        result = selectors.get_user_by_username('testuser')
        self.assertEqual(result, user)

    def test_get_user_by_username_not_exists(self):
        """Test getting a user that doesn't exist returns None."""
        result = selectors.get_user_by_username('nonexistent')
        self.assertIsNone(result)


class LeaveSelectorsTestCase(TestCase):
    """Tests for leave-related selectors."""

    def test_get_pending_ug_leaves_empty(self):
        """Test getting pending UG leaves when none exist."""
        result = selectors.get_pending_ug_leaves()
        self.assertEqual(list(result), [])

    def test_get_pending_pg_leaves_for_ta_empty(self):
        """Test getting pending PG leaves for TA when none exist."""
        result = selectors.get_pending_pg_leaves_for_ta()
        self.assertEqual(list(result), [])


class BonafideSelectorsTestCase(TestCase):
    """Tests for bonafide-related selectors."""

    def test_get_pending_bonafides_empty(self):
        """Test getting pending bonafides when none exist."""
        result = selectors.get_pending_bonafides()
        self.assertEqual(list(result), [])


class AssistantshipSelectorsTestCase(TestCase):
    """Tests for assistantship-related selectors."""

    def test_get_pending_assistantships_for_ta_empty(self):
        """Test getting pending assistantships for TA when none exist."""
        result = selectors.get_pending_assistantships_for_ta()
        self.assertEqual(list(result), [])

    def test_get_pending_assistantships_for_hod_empty(self):
        """Test getting pending assistantships for HOD when none exist."""
        result = selectors.get_pending_assistantships_for_hod()
        self.assertEqual(list(result), [])
