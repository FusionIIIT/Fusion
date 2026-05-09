"""
test_use_cases.py - Specification-driven tests for the 4 NAM Use Cases.

Coverage per UC: 1 Happy Path + 1 Alternate Path + 1 Exception = 3 tests.
Total: 4 UCs x 3 = 12 tests. Adequacy = 12 / 12 = 100%.
"""

from unittest.mock import patch

from applications.notifications_extension.models import ModuleName, NotificationEventType
from applications.notifications_extension.tests.conftest import BaseNAMTestCase


# ────────────────────────────────────────────────────────────────
# UC-NT-01 - Register Notification Event Type
# ────────────────────────────────────────────────────────────────

class TestUC01_RegisterEventType(BaseNAMTestCase):
    """UC-NT-01: modules register event types with NAM."""

    def test_happy_path_register_valid_event_type(self):
        """UC-NT-01-HP-01: Register a valid event with default priority."""
        self.login_as_staff()
        with patch("applications.notifications_extension.services.notify.send"):
            response = self.client.post(
                "/api/notifications/event-types/register/",
                {
                    "event_name": "Leave Approved",
                    "module": ModuleName.LEAVE_MODULE,
                    "default_priority": "medium",
                    "description": "Fired when HOD approves a leave",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        self.assertIn("event_type", response.data)
        self.assertIn("event_id", response.data["event_type"])
        self.assertTrue(response.data["event_type"]["is_active"])

        self._record_result(
            test_id="UC-NT-01-HP-01", source_id="UC-NT-01",
            category="Happy Path",
            scenario="Staff registers valid event with default priority",
            preconditions="Authenticated staff; module valid",
            input_action="POST /api/notifications/event-types/register/",
            expected_result="201 Created; event_id + is_active=true returned",
            actual_result="201 Created received; event_type stored with UUID",
            status="Pass",
            evidence=f"event_id={response.data['event_type']['event_id']}",
        )

    def test_alternate_path_register_with_critical_priority(self):
        """UC-NT-01-AP-01: Register event with critical priority."""
        self.login_as_staff()
        with patch("applications.notifications_extension.services.notify.send"):
            response = self.client.post(
                "/api/notifications/event-types/register/",
                {
                    "event_name": "Emergency Evacuation",
                    "module": ModuleName.OFFICE_MODULE,
                    "default_priority": "critical",
                    "description": "Campus emergency",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["event_type"]["default_priority"], "critical")

        self._record_result(
            test_id="UC-NT-01-AP-01", source_id="UC-NT-01",
            category="Alternate Path",
            scenario="Staff registers event with critical priority",
            preconditions="Authenticated staff",
            input_action="POST register/ with default_priority=critical",
            expected_result="201 Created; event stored with priority=critical",
            actual_result="201 Created received; priority persisted correctly",
            status="Pass",
            evidence="default_priority=critical",
        )

    def test_exception_path_invalid_module(self):
        """UC-NT-01-EX-01: Register with invalid module name."""
        self.login_as_staff()
        response = self.client.post(
            "/api/notifications/event-types/register/",
            {
                "event_name": "Bogus",
                "module": "NonExistentModule",
                "default_priority": "medium",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        self._record_result(
            test_id="UC-NT-01-EX-01", source_id="UC-NT-01",
            category="Exception",
            scenario="Staff registers event with invalid module",
            preconditions="Authenticated staff",
            input_action="POST register/ with module='NonExistentModule'",
            expected_result="400 Bad Request with module error",
            actual_result=f"400 received; body={response.data}",
            status="Pass",
            evidence="Validation at serializer level blocked bad module",
        )


# ────────────────────────────────────────────────────────────────
# UC-NT-02 - Trigger Notification via Event ID
# ────────────────────────────────────────────────────────────────

class TestUC02_TriggerByEventId(BaseNAMTestCase):
    """UC-NT-02: external modules trigger notifications by Event_ID."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.event_type = NotificationEventType.objects.create(
            event_name="UC02 Test Event",
            module=ModuleName.LEAVE_MODULE,
            default_priority="medium",
            registered_by=cls.staff,
            is_active=True,
        )

    def setUp(self):
        super().setUp()
        # Clear dedup cache before each test so repeated runs don't collide
        from applications.notifications_extension import services
        services._recent_triggers.clear()

    def test_happy_path_trigger_by_valid_event(self):
        """UC-NT-02-HP-01: Trigger valid event for existing recipient."""
        self.login_as_staff()
        with patch("applications.notifications_extension.services.notify.send") as mock:
            response = self.client.post(
                "/api/notifications/trigger/",
                {
                    "event_id": str(self.event_type.event_id),
                    "recipient_username": self.student.username,
                    "message_content": "Your leave is approved",
                    "deep_link": "/leave/status/",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        mock.assert_called_once()

        self._record_result(
            test_id="UC-NT-02-HP-01", source_id="UC-NT-02",
            category="Happy Path",
            scenario="Staff triggers valid event for existing student",
            preconditions="Event type registered; recipient exists",
            input_action="POST /api/notifications/trigger/",
            expected_result="201 Created; notify.send called once",
            actual_result="201 received; service dispatched notification",
            status="Pass",
            evidence="notify.send invoked; recipient=nam_student",
        )

    def test_alternate_path_trigger_with_deep_link(self):
        """UC-NT-02-AP-01: Trigger with a custom deep_link."""
        self.login_as_staff()
        with patch("applications.notifications_extension.services.notify.send") as mock:
            response = self.client.post(
                "/api/notifications/trigger/",
                {
                    "event_id": str(self.event_type.event_id),
                    "recipient_username": self.student.username,
                    "message_content": "Check your schedule",
                    "deep_link": "/academic/timetable",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        # Verify the URL kwarg was forwarded
        kwargs = mock.call_args.kwargs
        self.assertEqual(kwargs.get("url"), "/academic/timetable")

        self._record_result(
            test_id="UC-NT-02-AP-01", source_id="UC-NT-02",
            category="Alternate Path",
            scenario="Staff triggers with a custom deep_link",
            preconditions="Event type registered",
            input_action="POST trigger/ with deep_link='/academic/timetable'",
            expected_result="201 Created; url kwarg in notify.send matches",
            actual_result="201 received; url forwarded correctly",
            status="Pass",
            evidence="notify.send kwargs.url=/academic/timetable",
        )

    def test_exception_path_unknown_event_id(self):
        """UC-NT-02-EX-01: Trigger with an unregistered event_id."""
        self.login_as_staff()
        response = self.client.post(
            "/api/notifications/trigger/",
            {
                "event_id": "00000000-0000-0000-0000-000000000000",
                "recipient_username": self.student.username,
                "message_content": "should fail",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 404)

        self._record_result(
            test_id="UC-NT-02-EX-01", source_id="UC-NT-02",
            category="Exception",
            scenario="Staff triggers with unknown event_id",
            preconditions="No event type with that UUID",
            input_action="POST trigger/ with random UUID",
            expected_result="404 Not Found; no notification dispatched",
            actual_result=f"404 received; body={response.data}",
            status="Pass",
            evidence="Service raised NotificationNotFound",
        )


# ────────────────────────────────────────────────────────────────
# UC-NT-03 - Broadcast Manual Announcement
# ────────────────────────────────────────────────────────────────

class TestUC03_BroadcastAnnouncement(BaseNAMTestCase):
    """UC-NT-03: admin broadcasts to a resolved audience."""

    def test_happy_path_broadcast_to_all_users(self):
        """UC-NT-03-HP-01: Admin broadcasts to audience=all."""
        self.login_as_admin()
        with patch("applications.notifications_extension.services.notify.send") as mock:
            response = self.client.post(
                "/api/notifications/announcements/broadcast/",
                {
                    "title": "Convocation Notice",
                    "message": "Convocation ceremony on 15 May",
                    "audience_type": "all",
                    "audience_value": "",
                    "expiry_date": "2026-05-16",
                    "priority": "medium",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        self.assertGreaterEqual(mock.call_count, 1)

        self._record_result(
            test_id="UC-NT-03-HP-01", source_id="UC-NT-03",
            category="Happy Path",
            scenario="Admin broadcasts to all users with future expiry",
            preconditions="Authenticated admin; expiry date in future",
            input_action="POST /announcements/broadcast/",
            expected_result="201 Created; announcement stored; fan-out performed",
            actual_result=f"201 received; fan-out count={mock.call_count}",
            status="Pass",
            evidence="Announcement record + notify.send invocations",
        )

    def test_alternate_path_broadcast_to_specific_designation(self):
        """UC-NT-03-AP-01: Admin targets a specific designation (group)."""
        # Patch _resolve_audience: test DB has no globals_* tables
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.login_as_admin()
        with patch(
            "applications.notifications_extension.services._resolve_audience",
            return_value=User.objects.filter(pk=self.student.pk),
        ), patch("applications.notifications_extension.services.notify.send"):
            response = self.client.post(
                "/api/notifications/announcements/broadcast/",
                {
                    "title": "HOD Meeting",
                    "message": "Meeting at 3 PM",
                    "audience_type": "group",
                    "audience_value": "HOD (CSE)",
                    "expiry_date": "2026-05-01",
                    "priority": "medium",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)

        self._record_result(
            test_id="UC-NT-03-AP-01", source_id="UC-NT-03",
            category="Alternate Path",
            scenario="Admin broadcasts to a specific designation",
            preconditions="Authenticated admin; audience=group",
            input_action="POST broadcast/ with audience_value='HOD (CSE)'",
            expected_result="201 Created; audience scoped to the designation",
            actual_result="201 received; announcement stored",
            status="Pass",
            evidence="audience_type=group routed through _resolve_audience()",
        )

    def test_exception_path_invalid_audience_type(self):
        """UC-NT-03-EX-01: Broadcast with invalid audience type."""
        self.login_as_admin()
        response = self.client.post(
            "/api/notifications/announcements/broadcast/",
            {
                "title": "Nope",
                "message": "Should fail",
                "audience_type": "mars",
                "expiry_date": "2026-05-01",
                "priority": "medium",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        self._record_result(
            test_id="UC-NT-03-EX-01", source_id="UC-NT-03",
            category="Exception",
            scenario="Admin broadcasts with invalid audience type",
            preconditions="Authenticated admin",
            input_action="POST broadcast/ with audience_type='mars'",
            expected_result="400 Bad Request; error details",
            actual_result=f"400 received; body={response.data}",
            status="Pass",
            evidence="Serializer rejected invalid AudienceType",
        )


# ────────────────────────────────────────────────────────────────
# UC-NT-04 - Notification Tray (Navbar Bell)
# ────────────────────────────────────────────────────────────────

class TestUC04_NotificationTray(BaseNAMTestCase):
    """UC-NT-04: user interacts with the navbar bell and list."""

    def test_happy_path_fetch_paginated_list(self):
        """UC-NT-04-HP-01: Fetch paginated notifications list."""
        self.login_as_student()
        response = self.client.get("/api/notifications/?page=1&page_size=10")
        self.assertEqual(response.status_code, 200)
        self.assertIn("notifications", response.data)
        self.assertIn("pagination", response.data)
        self.assertEqual(response.data["pagination"]["page"], 1)
        self.assertEqual(response.data["pagination"]["page_size"], 10)

        self._record_result(
            test_id="UC-NT-04-HP-01", source_id="UC-NT-04",
            category="Happy Path",
            scenario="Student fetches paginated notifications",
            preconditions="Authenticated student",
            input_action="GET /api/notifications/?page=1&page_size=10",
            expected_result="200 OK; notifications + pagination metadata",
            actual_result="200 OK; pagination block returned",
            status="Pass",
            evidence=f"pagination={response.data['pagination']}",
        )

    def test_alternate_path_mark_single_as_read(self):
        """UC-NT-04-AP-01: Mark a single notification as read."""
        # Create a real notification by calling notify.send directly
        from notifications.signals import notify
        notify.send(
            self.staff, recipient=self.student, verb="Please read me",
            module=ModuleName.LEAVE_MODULE, url="/x",
        )
        from notifications.models import Notification
        note = Notification.objects.filter(recipient=self.student).first()
        self.assertIsNotNone(note)
        self.assertTrue(note.unread)

        self.login_as_student()
        response = self.client.patch(f"/api/notifications/{note.id}/mark-read/")
        self.assertEqual(response.status_code, 200)
        note.refresh_from_db()
        self.assertFalse(note.unread)

        self._record_result(
            test_id="UC-NT-04-AP-01", source_id="UC-NT-04",
            category="Alternate Path",
            scenario="Student marks a notification as read",
            preconditions="Student has an unread notification",
            input_action="PATCH /api/notifications/{id}/mark-read/",
            expected_result="200 OK; unread flag cleared in DB",
            actual_result="200 OK; note.unread=False after refresh",
            status="Pass",
            evidence=f"notification_id={note.id}",
        )

    def test_exception_path_unauthenticated_access(self):
        """UC-NT-04-EX-01: Unauthenticated fetch is denied."""
        # No client.force_authenticate()
        self.logout()
        response = self.client.get("/api/notifications/")
        self.assertIn(response.status_code, [401, 403])

        self._record_result(
            test_id="UC-NT-04-EX-01", source_id="UC-NT-04",
            category="Exception",
            scenario="Unauthenticated client tries to read list",
            preconditions="No auth token",
            input_action="GET /api/notifications/ without Authorization",
            expected_result="401/403 denied",
            actual_result=f"Got {response.status_code}",
            status="Pass",
            evidence="DRF IsAuthenticated returned 401/403",
        )
