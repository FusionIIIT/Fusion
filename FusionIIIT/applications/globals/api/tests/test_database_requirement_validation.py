from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from applications.globals.api import views


class DatabaseRequirementValidationTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(id=10, is_authenticated=True)

    @patch("applications.globals.api.views.get_object_or_404")
    def test_support_owner_blocked(self, mock_get_object):
        issue = Mock()
        issue.user_id = 10
        issue.support.count.return_value = 3
        mock_get_object.return_value = issue

        request = self.factory.post("/api/db/issues/1/support/")
        force_authenticate(request, user=self.user)

        response = views.db_issue_support_toggle(request, 1)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Issue owner cannot support their own issue")

    @patch("applications.globals.api.views.get_object_or_404")
    def test_closed_issue_update_blocked(self, mock_get_object):
        issue = Mock()
        issue.user_id = 10
        issue.closed = True
        mock_get_object.return_value = issue

        request = self.factory.put("/api/db/issues/1/", {"title": "Updated"}, format="json")
        force_authenticate(request, user=self.user)

        response = views.db_issue_update(request, 1)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Closed issues are read-only and cannot be edited.")

    def test_search_requires_minimum_three_characters(self):
        request = self.factory.get("/api/db/search/?q=ab")
        force_authenticate(request, user=self.user)

        response = views.db_user_search(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Search query must be at least 3 characters")

    def test_feedback_rejects_out_of_range_rating(self):
        request = self.factory.post("/api/db/feedback/", {"rating": 0, "feedback": "bad"}, format="json")
        force_authenticate(request, user=self.user)

        response = views.db_feedback(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("rating", response.data)
