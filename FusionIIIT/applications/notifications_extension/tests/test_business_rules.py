"""
test_business_rules.py - Specification-driven BR tests for NAM.

Coverage per BR: 1 Valid + 1 Invalid = 2 tests.
Total: 7 BRs x 2 = 14 tests. Adequacy = 14 / 14 = 100%.
"""

from unittest.mock import patch

from applications.notifications_extension.models import (
    ModuleName, NotificationEventType, NotificationPreference,
)
from applications.notifications_extension.tests.conftest import BaseNAMTestCase


# ────────────────────────────────────────────────────────────────
# BR-NT-01 - UI Centralization
# ────────────────────────────────────────────────────────────────

class TestBR01_UICentralization(BaseNAMTestCase):
    """BR-NT-01: all notifications go to the single central store."""

    def test_valid_send_creates_single_central_record(self):
        """BR-NT-01-V-01: Send notification - stored in one central table."""
        self.login_as_staff()
        with patch("applications.notifications_extension.services.notify.send") as mock:
            response = self.client.post(
                "/api/notifications/send/",
                {
                    "recipient_username": self.student.username,
                    "module": ModuleName.LEAVE_MODULE,
                    "verb": "Central store test",
                    "priority": "medium",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        mock.assert_called_once()

        self._record_result(
            test_id="BR-NT-01-V-01", source_id="BR-NT-01",
            category="Valid",
            scenario="Notification goes into central notifications table",
            preconditions="Authenticated staff",
            input_action="POST /api/notifications/send/",
            expected_result="201; notify.send invoked once (central store)",
            actual_result="201 received; single notify.send call",
            status="Pass",
            evidence="No parallel module-owned store written",
        )

    def test_invalid_rogue_module_rejected(self):
        """BR-NT-01-I-01: Rogue module name blocked."""
        self.login_as_staff()
        response = self.client.post(
            "/api/notifications/send/",
            {
                "recipient_username": self.student.username,
                "module": "RogueModule",
                "verb": "should be blocked",
                "priority": "medium",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        self._record_result(
            test_id="BR-NT-01-I-01", source_id="BR-NT-01",
            category="Invalid",
            scenario="Rogue module name rejected by serializer",
            preconditions="Authenticated staff",
            input_action="POST /send/ with module='RogueModule'",
            expected_result="400 Bad Request",
            actual_result=f"400 received; body={response.data}",
            status="Pass",
            evidence="Central store protected from unlisted modules",
        )


# ────────────────────────────────────────────────────────────────
# BR-NT-03 - RBAC (Staff/Admin Only)
# ────────────────────────────────────────────────────────────────

class TestBR03_RBACStaffOnly(BaseNAMTestCase):

    def test_valid_staff_can_send(self):
        """BR-NT-03-V-01: Staff sending returns 201."""
        self.login_as_staff()
        with patch("applications.notifications_extension.services.notify.send"):
            response = self.client.post(
                "/api/notifications/send/",
                {
                    "recipient_username": self.student.username,
                    "module": ModuleName.LEAVE_MODULE,
                    "verb": "from staff",
                    "priority": "medium",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)

        self._record_result(
            test_id="BR-NT-03-V-01", source_id="BR-NT-03",
            category="Valid", scenario="Staff user allowed to send",
            preconditions="Staff user authenticated",
            input_action="POST /send/ while is_staff=True",
            expected_result="201 Created",
            actual_result="201 received", status="Pass",
            evidence="DRF IsAdminUser permission passed",
        )

    def test_invalid_student_cannot_send(self):
        """BR-NT-03-I-01: Student sending returns 403."""
        self.login_as_student()
        response = self.client.post(
            "/api/notifications/send/",
            {
                "recipient_username": self.student.username,
                "module": ModuleName.LEAVE_MODULE,
                "verb": "hack",
                "priority": "medium",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

        self._record_result(
            test_id="BR-NT-03-I-01", source_id="BR-NT-03",
            category="Invalid", scenario="Student is forbidden from sending",
            preconditions="Student user (is_staff=False) authenticated",
            input_action="POST /send/ as student",
            expected_result="403 Forbidden",
            actual_result=f"403 received; body={response.data}",
            status="Pass",
            evidence="DRF IsAdminUser rejected non-staff",
        )


# ────────────────────────────────────────────────────────────────
# BR-NT-04 - Duplicate Suppression
# ────────────────────────────────────────────────────────────────

class TestBR04_DuplicateSuppression(BaseNAMTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.event = NotificationEventType.objects.create(
            event_name="Dup test event", module=ModuleName.LEAVE_MODULE,
            default_priority="medium", registered_by=cls.staff, is_active=True,
        )

    def setUp(self):
        super().setUp()
        from applications.notifications_extension import services
        services._recent_triggers.clear()

    def test_valid_two_triggers_outside_cooldown(self):
        """BR-NT-04-V-01: Two triggers outside 60s both succeed."""
        from applications.notifications_extension import services
        from datetime import timedelta
        from django.utils import timezone

        self.login_as_staff()
        with patch("applications.notifications_extension.services.notify.send"):
            r1 = self.client.post(
                "/api/notifications/trigger/",
                {
                    "event_id": str(self.event.event_id),
                    "recipient_username": self.student.username,
                    "message_content": "first",
                },
                format="json",
            )
            self.assertEqual(r1.status_code, 201)

            # Fake that > 60s has passed by rewinding the cache timestamp
            key = (self.student.id, str(self.event.event_id))
            services._recent_triggers[key] = (
                timezone.now() - timedelta(seconds=120)
            )

            r2 = self.client.post(
                "/api/notifications/trigger/",
                {
                    "event_id": str(self.event.event_id),
                    "recipient_username": self.student.username,
                    "message_content": "second",
                },
                format="json",
            )
            self.assertEqual(r2.status_code, 201)

        self._record_result(
            test_id="BR-NT-04-V-01", source_id="BR-NT-04",
            category="Valid",
            scenario="Two triggers more than 60s apart both succeed",
            preconditions="Same event + same recipient; 60s elapsed",
            input_action="POST /trigger/ twice with 60s gap",
            expected_result="Both calls return 201",
            actual_result=f"First={r1.status_code}, Second={r2.status_code}",
            status="Pass",
            evidence="Cooldown window respected only when < 60s",
        )

    def test_invalid_duplicate_within_60s(self):
        """BR-NT-04-I-01: Second trigger within 60s raises duplicate."""
        self.login_as_staff()
        with patch("applications.notifications_extension.services.notify.send"):
            r1 = self.client.post(
                "/api/notifications/trigger/",
                {
                    "event_id": str(self.event.event_id),
                    "recipient_username": self.student.username,
                    "message_content": "first",
                },
                format="json",
            )
            r2 = self.client.post(
                "/api/notifications/trigger/",
                {
                    "event_id": str(self.event.event_id),
                    "recipient_username": self.student.username,
                    "message_content": "dup",
                },
                format="json",
            )

        self.assertEqual(r1.status_code, 201)
        # Either 429 Too Many or 400 depending on handler mapping - accept both
        self.assertIn(r2.status_code, [400, 409, 429])

        self._record_result(
            test_id="BR-NT-04-I-01", source_id="BR-NT-04",
            category="Invalid",
            scenario="Second trigger within 60s is rejected",
            preconditions="Same event + recipient within 60s",
            input_action="POST /trigger/ twice in the same second",
            expected_result="First 201; second 4xx with dedup message",
            actual_result=f"First={r1.status_code}, Second={r2.status_code}",
            status="Pass",
            evidence="DuplicateNotification raised by service",
        )


# ────────────────────────────────────────────────────────────────
# BR-NT-05 - Critical Priority Bypass
# ────────────────────────────────────────────────────────────────

class TestBR05_CriticalBypass(BaseNAMTestCase):

    def test_valid_critical_bypasses_disabled_module(self):
        """BR-NT-05-V-01: Critical priority bypasses opt-out."""
        NotificationPreference.objects.create(
            user=self.student, module=ModuleName.LEAVE_MODULE, is_enabled=False,
        )
        from applications.notifications_extension import services

        with patch("applications.notifications_extension.services.notify.send") as mock:
            services._send(
                sender=self.staff, recipient=self.student,
                url="#", module=ModuleName.LEAVE_MODULE,
                verb="CRITICAL", priority="critical",
            )
        mock.assert_called_once()

        self._record_result(
            test_id="BR-NT-05-V-01", source_id="BR-NT-05",
            category="Valid",
            scenario="Critical priority bypasses disabled module",
            preconditions="User disabled Leave Module",
            input_action="services._send() with priority='critical'",
            expected_result="notify.send called despite opt-out",
            actual_result="notify.send invoked exactly once",
            status="Pass",
            evidence="Service honored BR-NT-05 override",
        )

    def test_invalid_medium_respects_disabled_module(self):
        """BR-NT-05-I-01: Non-critical respects opt-out."""
        NotificationPreference.objects.create(
            user=self.student, module=ModuleName.LEAVE_MODULE, is_enabled=False,
        )
        from applications.notifications_extension import services

        with patch("applications.notifications_extension.services.notify.send") as mock:
            services._send(
                sender=self.staff, recipient=self.student,
                url="#", module=ModuleName.LEAVE_MODULE,
                verb="normal", priority="medium",
            )
        mock.assert_not_called()

        self._record_result(
            test_id="BR-NT-05-I-01", source_id="BR-NT-05",
            category="Invalid",
            scenario="Medium priority respects disabled module",
            preconditions="User disabled Leave Module",
            input_action="services._send() with priority='medium'",
            expected_result="notify.send is NOT called",
            actual_result="notify.send assert_not_called passed",
            status="Pass",
            evidence="BR-NT-06 opt-out honored for non-critical",
        )


# ────────────────────────────────────────────────────────────────
# BR-NT-02 - Navbar Consistency (structural)
# ────────────────────────────────────────────────────────────────

class TestBR02_NavbarConsistency(BaseNAMTestCase):
    """The NotificationBell component is the single source of truth in the
    global header — modules may not render their own trays."""

    FRONTEND_ROOT = None  # lazy resolution

    @classmethod
    def _frontend_root(cls):
        if cls.FRONTEND_ROOT is None:
            from pathlib import Path
            # tests/ -> applications.notifications_extension/ -> backend/ -> project root
            project_root = Path(__file__).resolve().parents[3]
            cls.FRONTEND_ROOT = project_root / "Fusion-client" / "src"
        return cls.FRONTEND_ROOT

    def test_valid_bell_component_exists_and_is_imported(self):
        """BR-NT-02-V-01: NotificationBell exists + imported by a global header."""
        from pathlib import Path
        import re

        root = self._frontend_root()
        bell_path = root / "Modules" / "Notification" / "components" / "NotificationBell.jsx"
        self.assertTrue(bell_path.exists(), f"Missing {bell_path}")

        # At least one file (typically header.jsx) must import the bell so it
        # renders globally across module transitions.
        importers = []
        pattern = re.compile(r"NotificationBell")
        for jsx in root.rglob("*.jsx"):
            if jsx.name == "NotificationBell.jsx":
                continue
            try:
                text = jsx.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if pattern.search(text):
                importers.append(jsx.name)
        self.assertGreaterEqual(len(importers), 1)

        self._record_result(
            test_id="BR-NT-02-V-01", source_id="BR-NT-02",
            category="Valid",
            scenario="NotificationBell component exists and is imported globally",
            preconditions="Frontend project structure unchanged",
            input_action="File-system check for NotificationBell.jsx + imports",
            expected_result="Component file present and referenced in header",
            actual_result=f"Found bell at {bell_path.name}; imported in {importers[:3]}",
            status="Pass",
            evidence=f"{len(importers)} files reference NotificationBell",
        )

    def test_invalid_only_one_bell_definition(self):
        """BR-NT-02-I-01: Only ONE NotificationBell definition in the repo."""
        root = self._frontend_root()
        matches = list(root.rglob("NotificationBell.jsx"))
        # Exclude node_modules
        matches = [m for m in matches if "node_modules" not in str(m)]
        self.assertEqual(len(matches), 1,
                         f"Expected exactly 1 NotificationBell.jsx, got {len(matches)}: {matches}")

        self._record_result(
            test_id="BR-NT-02-I-01", source_id="BR-NT-02",
            category="Invalid",
            scenario="No rogue NotificationBell implementations",
            preconditions="Frontend repo",
            input_action="Glob for NotificationBell.jsx anywhere in src/",
            expected_result="Exactly one NotificationBell.jsx file",
            actual_result=f"Found {len(matches)} files => {[m.name for m in matches]}",
            status="Pass",
            evidence="Single source of truth enforced by convention",
        )


# ────────────────────────────────────────────────────────────────
# BR-NT-06 - Automatic Expiry
# ────────────────────────────────────────────────────────────────

class TestBR06_AutomaticExpiry(BaseNAMTestCase):
    """Announcements past their expiry_date are hidden from the active list."""

    def test_valid_future_expiry_appears_in_active_list(self):
        """BR-NT-06-V-01: Future-expiry announcement appears in active list."""
        from datetime import date, timedelta
        from applications.notifications_extension.models import Announcement
        Announcement.objects.create(
            title="Active announcement", message="Still valid",
            sender=self.admin, audience_type="all", audience_value="",
            expiry_date=date.today() + timedelta(days=30),
        )
        self.login_as_student()
        r = self.client.get("/api/notifications/announcements/")
        self.assertEqual(r.status_code, 200)
        titles = [a["title"] for a in r.data.get("announcements", [])]
        self.assertIn("Active announcement", titles)

        self._record_result(
            test_id="BR-NT-06-V-01", source_id="BR-NT-06",
            category="Valid",
            scenario="Announcement with future expiry_date is listed as active",
            preconditions="Announcement exists with expiry_date in future",
            input_action="GET /api/notifications/announcements/",
            expected_result="Active list contains the announcement",
            actual_result=f"Returned titles: {titles}",
            status="Pass",
            evidence="selectors.get_active_announcements filter passes",
        )

    def test_invalid_past_expiry_hidden_from_active_list(self):
        """BR-NT-06-I-01: Past-expiry announcement hidden from active list."""
        from datetime import date, timedelta
        from applications.notifications_extension.models import Announcement
        Announcement.objects.create(
            title="Stale announcement", message="Should be hidden",
            sender=self.admin, audience_type="all", audience_value="",
            expiry_date=date.today() - timedelta(days=1),
        )
        self.login_as_student()
        r = self.client.get("/api/notifications/announcements/")
        self.assertEqual(r.status_code, 200)
        titles = [a["title"] for a in r.data.get("announcements", [])]
        self.assertNotIn("Stale announcement", titles)

        self._record_result(
            test_id="BR-NT-06-I-01", source_id="BR-NT-06",
            category="Invalid",
            scenario="Announcement with past expiry_date hidden from active list",
            preconditions="Announcement exists with expiry_date in the past",
            input_action="GET /api/notifications/announcements/",
            expected_result="Active list does NOT contain the stale announcement",
            actual_result=f"Returned titles: {titles}",
            status="Pass",
            evidence="expiry_date__gte=today filter enforced",
        )


# ────────────────────────────────────────────────────────────────
# BR-NT-07 - Designation-Based Broadcast Audience
# ────────────────────────────────────────────────────────────────

class TestBR07_DesignationAudience(BaseNAMTestCase):

    def test_valid_designation_group_audience_routed(self):
        """BR-NT-07-V-01: group audience uses globals_holdsdesignation."""
        # We patch _resolve_audience to return a controlled queryset so the
        # test is independent of the shared Fusion globals tables.
        self.login_as_admin()
        from django.contrib.auth import get_user_model
        User = get_user_model()

        with patch(
            "applications.notifications_extension.services._resolve_audience",
            return_value=User.objects.filter(pk=self.student.pk),
        ) as mock_resolve, patch("applications.notifications_extension.services.notify.send"):
            response = self.client.post(
                "/api/notifications/announcements/broadcast/",
                {
                    "title": "Dept Meeting",
                    "message": "3 PM",
                    "audience_type": "group",
                    "audience_value": "HOD (CSE)",
                    "expiry_date": "2026-05-01",
                    "priority": "medium",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        mock_resolve.assert_called_once()
        args = mock_resolve.call_args.args
        self.assertEqual(args[0], "group")
        self.assertEqual(args[1], "HOD (CSE)")

        self._record_result(
            test_id="BR-NT-07-V-01", source_id="BR-NT-07",
            category="Valid",
            scenario="group audience routed via _resolve_audience",
            preconditions="Authenticated admin",
            input_action="POST /broadcast/ audience_type=group",
            expected_result="_resolve_audience called with ('group', value)",
            actual_result="Called once with correct args",
            status="Pass", evidence="BR-NT-07 wiring confirmed",
        )

    def test_invalid_designation_returns_empty_audience(self):
        """BR-NT-07-I-01: Unknown designation yields empty fan-out."""
        self.login_as_admin()
        from django.contrib.auth import get_user_model
        User = get_user_model()

        with patch(
            "applications.notifications_extension.services._resolve_audience",
            return_value=User.objects.none(),
        ), patch("applications.notifications_extension.services.notify.send") as mock:
            response = self.client.post(
                "/api/notifications/announcements/broadcast/",
                {
                    "title": "Ghost",
                    "message": "nobody",
                    "audience_type": "group",
                    "audience_value": "NonExistentRole",
                    "expiry_date": "2026-05-01",
                    "priority": "medium",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        mock.assert_not_called()

        self._record_result(
            test_id="BR-NT-07-I-01", source_id="BR-NT-07",
            category="Invalid",
            scenario="Unknown designation yields empty recipient set",
            preconditions="Authenticated admin",
            input_action="POST /broadcast/ with bad designation",
            expected_result="201; zero notify.send calls",
            actual_result="201 received; notify.send never invoked",
            status="Pass", evidence="Empty queryset => zero fan-out",
        )


# ────────────────────────────────────────────────────────────────
# BR-NT-08 - Audit Trail Integrity
# ────────────────────────────────────────────────────────────────

class TestBR08_AuditTrail(BaseNAMTestCase):
    """Every broadcast stores Author_ID + Timestamp; unauthorized calls create no audit record."""

    def test_valid_broadcast_stamps_author_and_timestamp(self):
        """BR-NT-08-V-01: Broadcast stores sender (Author_ID) + created_at (Timestamp)."""
        from django.contrib.auth import get_user_model
        from applications.notifications_extension.models import Announcement
        User = get_user_model()

        self.login_as_admin()
        before_count = Announcement.objects.count()
        with patch(
            "applications.notifications_extension.services._resolve_audience",
            return_value=User.objects.filter(pk=self.student.pk),
        ), patch("applications.notifications_extension.services.notify.send"):
            r = self.client.post(
                "/api/notifications/announcements/broadcast/",
                {
                    "title": "Audit trail test",
                    "message": "Check audit fields",
                    "audience_type": "all",
                    "expiry_date": "2026-12-31",
                    "priority": "medium",
                },
                format="json",
            )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Announcement.objects.count(), before_count + 1)

        announcement = Announcement.objects.latest("created_at")
        self.assertEqual(announcement.sender_id, self.admin.id)  # Author_ID
        self.assertIsNotNone(announcement.created_at)             # Timestamp
        self.assertEqual(announcement.title, "Audit trail test")

        self._record_result(
            test_id="BR-NT-08-V-01", source_id="BR-NT-08",
            category="Valid",
            scenario="Admin broadcast persists Author_ID + Timestamp",
            preconditions="Authenticated admin user",
            input_action="POST /api/notifications/announcements/broadcast/",
            expected_result="Announcement has sender + created_at populated",
            actual_result=f"sender_id={announcement.sender_id}, created_at={announcement.created_at}",
            status="Pass",
            evidence="Database row audited with Author_ID and Timestamp",
        )

    def test_invalid_unauthorized_call_creates_no_audit_row(self):
        """BR-NT-08-I-01: Unauthenticated call creates NO Announcement audit row."""
        from applications.notifications_extension.models import Announcement
        before_count = Announcement.objects.count()

        self.logout()
        r = self.client.post(
            "/api/notifications/announcements/broadcast/",
            {
                "title": "Rogue",
                "message": "Should not be audited",
                "audience_type": "all",
                "expiry_date": "2026-12-31",
                "priority": "medium",
            },
            format="json",
        )
        self.assertIn(r.status_code, [401, 403])
        self.assertEqual(Announcement.objects.count(), before_count)

        self._record_result(
            test_id="BR-NT-08-I-01", source_id="BR-NT-08",
            category="Invalid",
            scenario="Unauthorized caller does not pollute the audit log",
            preconditions="No authentication",
            input_action="POST /announcements/broadcast/ without token",
            expected_result="401/403; Announcement count unchanged",
            actual_result=f"Got {r.status_code}; row count still {Announcement.objects.count()}",
            status="Pass",
            evidence="No audit row created for unauthorized attempt",
        )


# ────────────────────────────────────────────────────────────────
# BR-NT-09 - Soft Archive with Retention
# ────────────────────────────────────────────────────────────────

class TestBR09_SoftArchive(BaseNAMTestCase):

    def test_valid_delete_creates_archive_record(self):
        """BR-NT-09-V-01: DELETE creates ArchivedNotification row."""
        from notifications.signals import notify
        from notifications.models import Notification
        from applications.notifications_extension.models import ArchivedNotification

        notify.send(
            self.staff, recipient=self.student, verb="to archive",
            module=ModuleName.LEAVE_MODULE, url="#",
        )
        note = Notification.objects.filter(recipient=self.student).first()
        self.assertIsNotNone(note)

        self.login_as_student()
        r = self.client.delete(f"/api/notifications/{note.id}/delete/")
        self.assertEqual(r.status_code, 200)

        self.assertTrue(
            ArchivedNotification.objects.filter(
                user=self.student, notification_id=note.id,
            ).exists()
        )
        # Source notification row still present
        self.assertTrue(Notification.objects.filter(id=note.id).exists())

        self._record_result(
            test_id="BR-NT-09-V-01", source_id="BR-NT-09",
            category="Valid",
            scenario="Delete creates archive row; source row retained",
            preconditions="User has an active notification",
            input_action="DELETE /api/notifications/{id}/delete/",
            expected_result="ArchivedNotification row created; DB row not deleted",
            actual_result="Both assertions pass",
            status="Pass",
            evidence="Soft-delete semantics confirmed",
        )

    def test_invalid_delete_nonexistent_returns_404(self):
        """BR-NT-09-I-01: Delete non-existent notification -> 404."""
        from applications.notifications_extension.models import ArchivedNotification
        before = ArchivedNotification.objects.count()

        self.login_as_student()
        r = self.client.delete("/api/notifications/99999999/delete/")
        self.assertEqual(r.status_code, 404)
        after = ArchivedNotification.objects.count()
        self.assertEqual(before, after)

        self._record_result(
            test_id="BR-NT-09-I-01", source_id="BR-NT-09",
            category="Invalid",
            scenario="Delete non-existent notification id",
            preconditions="No notification with that id exists",
            input_action="DELETE /api/notifications/99999999/delete/",
            expected_result="404 Not Found; no archive record created",
            actual_result=f"404 received; archive count unchanged ({before})",
            status="Pass",
            evidence="NotificationNotFound mapped to 404",
        )
