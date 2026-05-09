"""
test_workflows.py - End-to-end workflow tests for NAM.

Coverage per WF: 1 End-to-End + 1 Negative + 1 Exit = 3 tests.
Total: 3 WFs x 3 = 9 tests. Required = 3 x 2 = 6. Adequacy = 9/6 = 150%.
"""

from unittest.mock import patch

from applications.notifications_extension.models import (
    ModuleName, NotificationEventType, NotificationPreference,
)
from applications.notifications_extension.tests.conftest import BaseNAMTestCase


# ────────────────────────────────────────────────────────────────
# WF-NT-01 - Register Event -> Trigger -> Deliver
# ────────────────────────────────────────────────────────────────

class TestWF01_RegisterThenTrigger(BaseNAMTestCase):

    def setUp(self):
        super().setUp()
        from applications.notifications_extension import services
        services._recent_triggers.clear()

    def test_e2e_register_trigger_receive(self):
        """WF-NT-01-E2E-01: Full register -> trigger -> receive flow."""
        self.login_as_staff()

        # Step 1 - register event
        with patch("applications.notifications_extension.services.notify.send") as mock_notify:
            r_reg = self.client.post(
                "/api/notifications/event-types/register/",
                {
                    "event_name": "WF01 E2E",
                    "module": ModuleName.LEAVE_MODULE,
                    "default_priority": "medium",
                    "description": "E2E flow event",
                },
                format="json",
            )
            self.assertEqual(r_reg.status_code, 201)
            event_id = r_reg.data["event_type"]["event_id"]

            # Step 2 - trigger for student
            r_trig = self.client.post(
                "/api/notifications/trigger/",
                {
                    "event_id": event_id,
                    "recipient_username": self.student.username,
                    "message_content": "E2E message",
                    "deep_link": "/leave/status/",
                },
                format="json",
            )
            self.assertEqual(r_trig.status_code, 201)
            mock_notify.assert_called()

        # Step 3 - student fetches list
        self.login_as_student()
        r_list = self.client.get("/api/notifications/")
        self.assertEqual(r_list.status_code, 200)

        self._record_result(
            test_id="WF-NT-01-E2E-01", source_id="WF-NT-01",
            category="End-to-End",
            scenario="Register -> Trigger -> Student fetches list",
            preconditions="Clean dedup cache",
            input_action="register -> trigger -> GET /api/notifications/",
            expected_result="Event stored; notify.send called; list returns 200",
            actual_result="All three steps returned expected codes",
            status="Pass", evidence=f"event_id={event_id}",
        )

    def test_negative_student_cannot_trigger(self):
        """WF-NT-01-NEG-01: Student attempting to trigger is blocked."""
        # Pre-seed an event (staff registers)
        event = NotificationEventType.objects.create(
            event_name="WF01 Neg event",
            module=ModuleName.LEAVE_MODULE,
            default_priority="medium",
            registered_by=self.staff, is_active=True,
        )

        self.login_as_student()
        r = self.client.post(
            "/api/notifications/trigger/",
            {
                "event_id": str(event.event_id),
                "recipient_username": self.student.username,
                "message_content": "hack attempt",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 403)
        # Event still exists
        self.assertTrue(
            NotificationEventType.objects.filter(pk=event.pk).exists()
        )

        self._record_result(
            test_id="WF-NT-01-NEG-01", source_id="WF-NT-01",
            category="Negative",
            scenario="Student attempts to trigger event",
            preconditions="Event exists; logged in as student",
            input_action="POST /trigger/ as student",
            expected_result="403 Forbidden; event unchanged",
            actual_result="403 received; event still exists",
            status="Pass", evidence="BR-NT-03 RBAC enforced mid-workflow",
        )

    def test_exit_trigger_with_unknown_event(self):
        """WF-NT-01-EXIT-01: Trigger with unknown event_id exits cleanly."""
        self.login_as_staff()
        r = self.client.post(
            "/api/notifications/trigger/",
            {
                "event_id": "00000000-0000-0000-0000-000000000000",
                "recipient_username": self.student.username,
                "message_content": "x",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 404)

        self._record_result(
            test_id="WF-NT-01-EXIT-01", source_id="WF-NT-01",
            category="Exit",
            scenario="Trigger with unknown event_id exits with 404",
            preconditions="No event with that UUID",
            input_action="POST /trigger/ with bogus event_id",
            expected_result="404; workflow exits cleanly without side-effects",
            actual_result="404 received", status="Pass",
            evidence="Workflow gracefully exits",
        )


# ────────────────────────────────────────────────────────────────
# WF-NT-02 - Broadcast Fan-Out
# ────────────────────────────────────────────────────────────────

class TestWF02_BroadcastFanout(BaseNAMTestCase):

    def test_e2e_admin_broadcast_to_students(self):
        """WF-NT-02-E2E-01: Admin broadcasts to students; all receive."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        self.login_as_admin()
        with patch(
            "applications.notifications_extension.services._resolve_audience",
            return_value=User.objects.filter(pk=self.student.pk),
        ), patch("applications.notifications_extension.services.notify.send") as mock_notify:
            r = self.client.post(
                "/api/notifications/announcements/broadcast/",
                {
                    "title": "All Students",
                    "message": "Final exam schedule",
                    "audience_type": "students",
                    "expiry_date": "2026-06-30",
                    "priority": "medium",
                },
                format="json",
            )
        self.assertEqual(r.status_code, 201)
        mock_notify.assert_called()

        self._record_result(
            test_id="WF-NT-02-E2E-01", source_id="WF-NT-02",
            category="End-to-End",
            scenario="Admin broadcasts to students; fan-out happens",
            preconditions="Authenticated admin; audience resolves to 1 student",
            input_action="POST /announcements/broadcast/",
            expected_result="201; notify.send called for each recipient",
            actual_result=f"201; fan-out count={mock_notify.call_count}",
            status="Pass", evidence="WF-NT-02 E2E complete",
        )

    def test_negative_student_cannot_broadcast(self):
        """WF-NT-02-NEG-01: Student cannot call broadcast endpoint."""
        self.login_as_student()
        r = self.client.post(
            "/api/notifications/announcements/broadcast/",
            {
                "title": "rogue",
                "message": "should fail",
                "audience_type": "students",
                "expiry_date": "2026-06-30",
                "priority": "medium",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 403)

        self._record_result(
            test_id="WF-NT-02-NEG-01", source_id="WF-NT-02",
            category="Negative",
            scenario="Student attempts broadcast",
            preconditions="Authenticated student",
            input_action="POST /broadcast/ as student",
            expected_result="403 Forbidden",
            actual_result="403 received",
            status="Pass", evidence="RBAC blocks non-admins",
        )

    def test_exit_empty_audience(self):
        """WF-NT-02-EXIT-01: Broadcast with empty audience exits cleanly."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        self.login_as_admin()
        with patch(
            "applications.notifications_extension.services._resolve_audience",
            return_value=User.objects.none(),
        ), patch("applications.notifications_extension.services.notify.send") as mock_notify:
            r = self.client.post(
                "/api/notifications/announcements/broadcast/",
                {
                    "title": "Empty",
                    "message": "no audience",
                    "audience_type": "group",
                    "audience_value": "NobodyHere",
                    "expiry_date": "2026-06-30",
                    "priority": "medium",
                },
                format="json",
            )
        self.assertEqual(r.status_code, 201)
        mock_notify.assert_not_called()

        self._record_result(
            test_id="WF-NT-02-EXIT-01", source_id="WF-NT-02",
            category="Exit",
            scenario="Broadcast with empty audience exits cleanly",
            preconditions="Audience resolves to zero users",
            input_action="POST /broadcast/ with bad group",
            expected_result="201; zero fan-out",
            actual_result="201 received; no notify.send calls",
            status="Pass", evidence="Workflow exits without errors",
        )


# ────────────────────────────────────────────────────────────────
# WF-NT-03 - Preference Toggle + Filter
# ────────────────────────────────────────────────────────────────

class TestWF03_PreferenceFlow(BaseNAMTestCase):

    def test_e2e_toggle_off_filters_then_critical_delivers(self):
        """WF-NT-03-E2E-01: Toggle off -> medium skipped -> critical delivered."""
        # Step 1 - student toggles module off
        self.login_as_student()
        r1 = self.client.post(
            "/api/notifications/preferences/set/",
            {"module": ModuleName.LEAVE_MODULE, "is_enabled": False},
            format="json",
        )
        self.assertEqual(r1.status_code, 200)

        # Step 2 - staff sends medium (should be skipped)
        self.login_as_staff()
        with patch("applications.notifications_extension.services.notify.send") as mock_notify:
            self.client.post(
                "/api/notifications/send/",
                {
                    "recipient_username": self.student.username,
                    "module": ModuleName.LEAVE_MODULE,
                    "verb": "medium",
                    "priority": "medium",
                },
                format="json",
            )
            mock_notify.assert_not_called()

            # Step 3 - staff sends critical (should be delivered)
            self.client.post(
                "/api/notifications/send/",
                {
                    "recipient_username": self.student.username,
                    "module": ModuleName.LEAVE_MODULE,
                    "verb": "EMERGENCY",
                    "priority": "critical",
                },
                format="json",
            )
            mock_notify.assert_called()

        self._record_result(
            test_id="WF-NT-03-E2E-01", source_id="WF-NT-03",
            category="End-to-End",
            scenario="Toggle off -> medium skipped -> critical delivered",
            preconditions="Student authenticated; then staff sends twice",
            input_action="preferences/set -> send(medium) -> send(critical)",
            expected_result="medium skipped; critical delivered",
            actual_result="First assert_not_called then assert_called both pass",
            status="Pass",
            evidence="BR-NT-05 + BR-NT-06 interaction verified",
        )

    def test_negative_invalid_priority_rejected(self):
        """WF-NT-03-NEG-01: Invalid priority string rejected."""
        self.login_as_staff()
        r = self.client.post(
            "/api/notifications/send/",
            {
                "recipient_username": self.student.username,
                "module": ModuleName.LEAVE_MODULE,
                "verb": "bad prio",
                "priority": "ultra_mega",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 400)

        self._record_result(
            test_id="WF-NT-03-NEG-01", source_id="WF-NT-03",
            category="Negative",
            scenario="Invalid priority string rejected",
            preconditions="Authenticated staff",
            input_action="POST /send/ with priority='ultra_mega'",
            expected_result="400 Bad Request",
            actual_result=f"400 received; body={r.data}",
            status="Pass", evidence="Serializer enum validation works",
        )

    def test_exit_toggle_back_on_delivers(self):
        """WF-NT-03-EXIT-01: Toggle off then back on, delivery resumes."""
        self.login_as_student()
        self.client.post(
            "/api/notifications/preferences/set/",
            {"module": ModuleName.LEAVE_MODULE, "is_enabled": False},
            format="json",
        )
        # Toggle back on
        r = self.client.post(
            "/api/notifications/preferences/set/",
            {"module": ModuleName.LEAVE_MODULE, "is_enabled": True},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["preference"]["is_enabled"])

        self.login_as_staff()
        with patch("applications.notifications_extension.services.notify.send") as mock_notify:
            self.client.post(
                "/api/notifications/send/",
                {
                    "recipient_username": self.student.username,
                    "module": ModuleName.LEAVE_MODULE,
                    "verb": "resumed",
                    "priority": "medium",
                },
                format="json",
            )
            mock_notify.assert_called_once()

        self._record_result(
            test_id="WF-NT-03-EXIT-01", source_id="WF-NT-03",
            category="Exit",
            scenario="Re-enable module; delivery resumes",
            preconditions="Module toggled off then on",
            input_action="preferences/set twice -> send",
            expected_result="notify.send called once after re-enable",
            actual_result="assert_called_once passed",
            status="Pass", evidence="Preference lifecycle verified",
        )
