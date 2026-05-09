"""
tests/test_module.py — Unit tests for the notification module.

Coverage:
  - models     : NotificationPreference creation, __str__, defaults
  - selectors  : all query helpers
  - services   : all business logic, all module-specific notif senders, exceptions
  - api views  : HTTP status codes and response structure
"""

from unittest.mock import patch, call

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.notifications_extension.models import (
    ModuleName,
    LeaveNotifType,
    MessNotifType,
    VisitorHostelNotifType,
    HealthcareNotifType,
    ScholarshipNotifType,
    OfficeDeanPnDNotifType,
    OfficeDeanSNotifType,
    OfficeDeanRSPCNotifType,
    GymkhanaNotifType,
    ResearchProceduresNotifType,
    NotificationPreference,
)
from applications.notifications_extension import selectors, services
from applications.notifications_extension.services import (
    NotificationNotFound,
    InvalidModuleName,
    InvalidNotificationType,
)

User = get_user_model()


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def make_user(username="testuser", password="pass"):
    return User.objects.create_user(username=username, password=password)


# ─────────────────────────────────────────────
#  Model tests
# ─────────────────────────────────────────────

class NotificationPreferenceModelTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_preference_defaults_to_enabled(self):
        pref = NotificationPreference.objects.create(
            user=self.user, module=ModuleName.LEAVE_MODULE
        )
        self.assertTrue(pref.is_enabled)

    def test_preference_str_shows_on(self):
        pref = NotificationPreference.objects.create(
            user=self.user, module=ModuleName.LEAVE_MODULE, is_enabled=True
        )
        self.assertIn("ON", str(pref))

    def test_preference_str_shows_off(self):
        pref = NotificationPreference.objects.create(
            user=self.user, module=ModuleName.CENTRAL_MESS, is_enabled=False
        )
        self.assertIn("OFF", str(pref))

    def test_unique_together_constraint(self):
        from django.db import IntegrityError
        NotificationPreference.objects.create(
            user=self.user, module=ModuleName.LEAVE_MODULE
        )
        with self.assertRaises(Exception):
            NotificationPreference.objects.create(
                user=self.user, module=ModuleName.LEAVE_MODULE
            )

    def test_module_name_choices_exist(self):
        """All TextChoices values are valid."""
        choices = [c[0] for c in ModuleName.choices]
        self.assertIn(ModuleName.COMPLAINT_SYSTEM, choices)
        self.assertIn(ModuleName.RESEARCH_PROCEDURES, choices)
        self.assertIn(ModuleName.GYMKHANA_MODULE, choices)


# ─────────────────────────────────────────────
#  Selector tests
# ─────────────────────────────────────────────

class SelectorTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_is_module_enabled_defaults_true_no_record(self):
        self.assertTrue(
            selectors.is_module_enabled_for_user(self.user, ModuleName.LEAVE_MODULE)
        )

    def test_is_module_enabled_false_when_disabled(self):
        NotificationPreference.objects.create(
            user=self.user, module=ModuleName.LEAVE_MODULE, is_enabled=False
        )
        self.assertFalse(
            selectors.is_module_enabled_for_user(self.user, ModuleName.LEAVE_MODULE)
        )

    def test_get_unread_count_zero_initially(self):
        self.assertEqual(selectors.get_unread_count_for_user(self.user), 0)

    def test_get_all_preferences_empty_initially(self):
        self.assertEqual(selectors.get_all_preferences_for_user(self.user).count(), 0)

    def test_get_notification_by_id_returns_none_when_missing(self):
        result = selectors.get_notification_by_id(9999, self.user)
        self.assertIsNone(result)

    def test_get_notification_by_slug_returns_none_when_missing(self):
        # slug2id("1") → some id; we just check None is returned
        result = selectors.get_notification_by_slug("1", self.user)
        self.assertIsNone(result)


# ─────────────────────────────────────────────
#  Service tests — preferences & mark/delete
# ─────────────────────────────────────────────

class ServicePreferenceTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_set_preference_creates_record(self):
        pref = services.set_notification_preference(
            user=self.user, module=ModuleName.CENTRAL_MESS, is_enabled=False
        )
        self.assertFalse(pref.is_enabled)

    def test_set_preference_updates_existing(self):
        services.set_notification_preference(
            user=self.user, module=ModuleName.LEAVE_MODULE, is_enabled=True
        )
        pref = services.set_notification_preference(
            user=self.user, module=ModuleName.LEAVE_MODULE, is_enabled=False
        )
        self.assertFalse(pref.is_enabled)
        self.assertEqual(
            NotificationPreference.objects.filter(
                user=self.user, module=ModuleName.LEAVE_MODULE
            ).count(), 1
        )

    def test_set_preference_invalid_module_raises(self):
        with self.assertRaises(InvalidModuleName):
            services.set_notification_preference(
                user=self.user, module="fake_module", is_enabled=True
            )

    def test_mark_as_read_raises_when_not_found(self):
        with self.assertRaises(NotificationNotFound):
            services.mark_notification_as_read(notification_id=9999, user=self.user)

    def test_mark_as_unread_raises_when_not_found(self):
        with self.assertRaises(NotificationNotFound):
            services.mark_notification_as_unread(notification_id=9999, user=self.user)

    def test_delete_notification_raises_when_not_found(self):
        with self.assertRaises(NotificationNotFound):
            services.delete_notification(notification_id=9999, user=self.user)

    def test_mark_as_read_and_get_redirect_url_raises_when_not_found(self):
        with self.assertRaises(NotificationNotFound):
            services.mark_as_read_and_get_redirect_url(slug="9999", user=self.user)


# ─────────────────────────────────────────────
#  Service tests — module-specific notif senders
#  (all use mock to avoid real notify.send)
# ─────────────────────────────────────────────

class ServiceNotifSendersTest(TestCase):

    def setUp(self):
        self.sender    = make_user("sender")
        self.recipient = make_user("recipient")

    def _patch(self):
        return patch("applications.notifications_extension.services.notify.send")

    # Leave
    def test_leave_module_notif_leave_applied(self):
        with self._patch() as mock_send:
            services.leave_module_notif(
                sender=self.sender, recipient=self.recipient,
                type=LeaveNotifType.LEAVE_APPLIED
            )
            mock_send.assert_called_once()
            _, kwargs = mock_send.call_args
            self.assertIn("successfully submitted", kwargs["verb"])

    def test_leave_module_notif_withdrawn_with_date(self):
        with self._patch() as mock_send:
            services.leave_module_notif(
                sender=self.sender, recipient=self.recipient,
                type=LeaveNotifType.LEAVE_WITHDRAWN, date="2025-01-01"
            )
            mock_send.assert_called_once()
            _, kwargs = mock_send.call_args
            self.assertIn("2025-01-01", kwargs["verb"])

    def test_leave_module_notif_invalid_type_raises(self):
        with self.assertRaises(InvalidNotificationType):
            services.leave_module_notif(
                sender=self.sender, recipient=self.recipient, type="bad_type"
            )

    # Mess
    def test_central_mess_notif_feedback(self):
        with self._patch() as mock_send:
            services.central_mess_notif(
                sender=self.sender, recipient=self.recipient,
                type=MessNotifType.FEEDBACK_SUBMITTED
            )
            mock_send.assert_called_once()

    def test_central_mess_notif_invalid_type_raises(self):
        with self.assertRaises(InvalidNotificationType):
            services.central_mess_notif(
                sender=self.sender, recipient=self.recipient, type="bad"
            )

    # Visitor hostel
    def test_visitors_hostel_notif_confirmed(self):
        with self._patch() as mock_send:
            services.visitors_hostel_notif(
                sender=self.sender, recipient=self.recipient,
                type=VisitorHostelNotifType.BOOKING_CONFIRMATION
            )
            mock_send.assert_called_once()

    # Healthcare
    def test_healthcare_center_notif_appointment(self):
        with self._patch() as mock_send:
            services.healthcare_center_notif(
                sender=self.sender, recipient=self.recipient,
                type=HealthcareNotifType.APPOINTMENT_BOOKED
            )
            mock_send.assert_called_once()

    # File tracking
    def test_file_tracking_notif(self):
        with self._patch() as mock_send:
            services.file_tracking_notif(
                sender=self.sender, recipient=self.recipient, title="Budget File"
            )
            _, kwargs = mock_send.call_args
            self.assertEqual(kwargs["verb"], "Budget File")

    # Scholarship
    def test_scholarship_portal_notif_accept_mcm(self):
        with self._patch() as mock_send:
            services.scholarship_portal_notif(
                sender=self.sender, recipient=self.recipient,
                type=ScholarshipNotifType.ACCEPT_MCM
            )
            mock_send.assert_called_once()

    def test_scholarship_portal_notif_award(self):
        with self._patch() as mock_send:
            services.scholarship_portal_notif(
                sender=self.sender, recipient=self.recipient,
                type="award_Merit"
            )
            _, kwargs = mock_send.call_args
            self.assertIn("Merit", kwargs["verb"])

    # Complaint system
    def test_complaint_system_notif_student(self):
        with self._patch() as mock_send:
            services.complaint_system_notif(
                sender=self.sender, recipient=self.recipient,
                type="new_complaint", complaint_id=42,
                is_student=True, message="New complaint raised"
            )
            _, kwargs = mock_send.call_args
            self.assertEqual(kwargs["url"], "complaint:detail2")

    def test_complaint_system_notif_non_student(self):
        with self._patch() as mock_send:
            services.complaint_system_notif(
                sender=self.sender, recipient=self.recipient,
                type="new_complaint", complaint_id=42,
                is_student=False, message="New complaint raised"
            )
            _, kwargs = mock_send.call_args
            self.assertEqual(kwargs["url"], "complaint:detail")

    # Gymkhana
    def test_gymkhana_voting_notif(self):
        with self._patch() as mock_send:
            services.gymkhana_voting_notif(
                sender=self.sender, recipient=self.recipient,
                type=GymkhanaNotifType.VOTING_OPEN,
                title="President Election", desc="Vote now"
            )
            _, kwargs = mock_send.call_args
            self.assertIn("President Election", kwargs["verb"])

    # Assistantship
    def test_assistantship_claim_notify(self):
        with self._patch() as mock_send:
            services.assistantship_claim_notify(
                sender=self.sender, recipient=self.recipient,
                month="January", year="2025"
            )
            _, kwargs = mock_send.call_args
            self.assertIn("January", kwargs["verb"])
            self.assertIn("2025", kwargs["verb"])

    # Research
    def test_research_procedures_notif_approved(self):
        with self._patch() as mock_send:
            services.research_procedures_notif(
                sender=self.sender, recipient=self.recipient,
                type=ResearchProceduresNotifType.APPROVED
            )
            mock_send.assert_called_once()

    def test_research_procedures_notif_invalid_raises(self):
        with self.assertRaises(InvalidNotificationType):
            services.research_procedures_notif(
                sender=self.sender, recipient=self.recipient, type="bad_type"
            )

    # Opt-out respected
    def test_send_respects_user_opt_out(self):
        NotificationPreference.objects.create(
            user=self.recipient, module=ModuleName.LEAVE_MODULE, is_enabled=False
        )
        with self._patch() as mock_send:
            services.leave_module_notif(
                sender=self.sender, recipient=self.recipient,
                type=LeaveNotifType.LEAVE_APPLIED
            )
            mock_send.assert_not_called()


# ─────────────────────────────────────────────
#  API endpoint tests
# ─────────────────────────────────────────────

class NotificationAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user   = make_user("apiuser")
        self.client.force_authenticate(user=self.user)

    def test_list_returns_200(self):
        r = self.client.get("/api/notifications/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("notifications", r.data)

    def test_unread_returns_200(self):
        r = self.client.get("/api/notifications/unread/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("unread_count", r.data)

    def test_unread_count_returns_200(self):
        r = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("unread_count", r.data)

    def test_mark_all_read_returns_200(self):
        r = self.client.patch("/api/notifications/mark-all-read/")
        self.assertEqual(r.status_code, 200)

    def test_delete_all_returns_200(self):
        r = self.client.delete("/api/notifications/delete-all/")
        self.assertEqual(r.status_code, 200)

    def test_mark_read_nonexistent_returns_404(self):
        r = self.client.patch("/api/notifications/9999/mark-read/")
        self.assertEqual(r.status_code, 404)

    def test_mark_unread_nonexistent_returns_404(self):
        r = self.client.patch("/api/notifications/9999/mark-unread/")
        self.assertEqual(r.status_code, 404)

    def test_delete_nonexistent_returns_404(self):
        r = self.client.delete("/api/notifications/9999/delete/")
        self.assertEqual(r.status_code, 404)

    def test_get_preferences_returns_200(self):
        r = self.client.get("/api/notifications/preferences/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("preferences", r.data)

    def test_set_preference_returns_200(self):
        r = self.client.post(
            "/api/notifications/preferences/set/",
            {"module": ModuleName.LEAVE_MODULE, "is_enabled": False},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["preference"]["is_enabled"])

    def test_set_preference_invalid_module_returns_400(self):
        r = self.client.post(
            "/api/notifications/preferences/set/",
            {"module": "bad_module", "is_enabled": True},
            format="json",
        )
        self.assertEqual(r.status_code, 400)

    def test_mark_as_read_and_redirect_nonexistent_returns_404(self):
        r = self.client.get("/api/notifications/mark-as-read-and-redirect/9999/")
        self.assertEqual(r.status_code, 404)

    def test_unauthenticated_returns_401_or_403(self):
        unauth = APIClient()
        r = unauth.get("/api/notifications/")
        self.assertIn(r.status_code, [401, 403])

    # ─────────────────────────────────────────────
    #  API Performance — Pagination
    # ─────────────────────────────────────────────
    def test_pagination_default(self):
        r = self.client.get("/api/notifications/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("pagination", r.data)
        self.assertEqual(r.data["pagination"]["page"], 1)
        self.assertEqual(r.data["pagination"]["page_size"], 50)

    def test_pagination_custom(self):
        r = self.client.get("/api/notifications/?page=1&page_size=10")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["pagination"]["page_size"], 10)

    def test_pagination_invalid_returns_400(self):
        r = self.client.get("/api/notifications/?page=abc")
        self.assertEqual(r.status_code, 400)


# ─────────────────────────────────────────────
#  BR-NT-03 — Staff-only enforcement (RBAC)
# ─────────────────────────────────────────────

class StaffOnlyEndpointTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user(
            username="student", password="pw", is_staff=False
        )
        self.staff = User.objects.create_user(
            username="staff", password="pw", is_staff=True
        )
        self.client = APIClient()

    def test_student_cannot_send(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.post(
            "/api/notifications/send/",
            {
                "recipient_username": "student",
                "module": ModuleName.LEAVE_MODULE,
                "verb": "test",
                "priority": "medium",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_staff_can_send(self):
        self.client.force_authenticate(user=self.staff)
        r = self.client.post(
            "/api/notifications/send/",
            {
                "recipient_username": "student",
                "module": ModuleName.LEAVE_MODULE,
                "verb": "Your leave approved",
                "priority": "medium",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 201)

    def test_student_cannot_register_event_type(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.post(
            "/api/notifications/event-types/register/",
            {
                "event_name": "Test",
                "module": ModuleName.LEAVE_MODULE,
                "default_priority": "medium",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_student_cannot_trigger(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.post(
            "/api/notifications/trigger/",
            {
                "event_id": "00000000-0000-0000-0000-000000000000",
                "recipient_username": "student",
                "message_content": "test",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_student_cannot_send_group(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.post(
            "/api/notifications/send-group/",
            {"audience": "students", "module": ModuleName.LEAVE_MODULE, "verb": "test"},
            format="json",
        )
        self.assertEqual(r.status_code, 403)


# ─────────────────────────────────────────────
#  BR-NT-05 — Critical Priority Bypass
# ─────────────────────────────────────────────

class CriticalPriorityTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.sender = User.objects.create_user(username="s", password="p", is_staff=True)
        self.recipient = User.objects.create_user(username="r", password="p")

    def test_critical_bypasses_disabled_preference(self):
        """BR-NT-05: critical notification should be sent even when module is disabled."""
        from applications.notifications_extension import services
        NotificationPreference.objects.create(
            user=self.recipient, module=ModuleName.LEAVE_MODULE, is_enabled=False
        )
        with patch("applications.notifications_extension.services.notify.send") as mock_send:
            services._send(
                sender=self.sender, recipient=self.recipient,
                url="#", module=ModuleName.LEAVE_MODULE, verb="Critical!",
                priority="critical",
            )
            mock_send.assert_called_once()

    def test_non_critical_respects_disabled_preference(self):
        """BR-NT-06: normal notification should be skipped when module is disabled."""
        from applications.notifications_extension import services
        NotificationPreference.objects.create(
            user=self.recipient, module=ModuleName.LEAVE_MODULE, is_enabled=False
        )
        with patch("applications.notifications_extension.services.notify.send") as mock_send:
            services._send(
                sender=self.sender, recipient=self.recipient,
                url="#", module=ModuleName.LEAVE_MODULE, verb="Normal",
                priority="medium",
            )
            mock_send.assert_not_called()


# ─────────────────────────────────────────────
#  BR-NT-04 — Duplicate Suppression
# ─────────────────────────────────────────────

class DedupTest(TestCase):
    def test_duplicate_trigger_raises(self):
        """BR-NT-04: triggering the same event for the same user within 60s is blocked."""
        from applications.notifications_extension import services
        from applications.notifications_extension.models import NotificationEventType
        from applications.notifications_extension.services import DuplicateNotification, NotificationNotFound

        User = get_user_model()
        staff = User.objects.create_user(username="staff", password="p", is_staff=True)
        recipient = User.objects.create_user(username="recipient", password="p")

        event = NotificationEventType.objects.create(
            event_name="Test Event", module=ModuleName.LEAVE_MODULE,
            default_priority="medium", registered_by=staff, is_active=True,
        )
        services._recent_triggers.clear()

        with patch("applications.notifications_extension.services.notify.send"):
            services.trigger_notification_by_event_id(
                event_id=str(event.event_id), sender=staff, recipient=recipient,
                message_content="first",
            )
            with self.assertRaises(DuplicateNotification):
                services.trigger_notification_by_event_id(
                    event_id=str(event.event_id), sender=staff, recipient=recipient,
                    message_content="dup",
                )


# ─────────────────────────────────────────────
#  Group Send — Audience Resolution
# ─────────────────────────────────────────────

class GroupSendTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username="st", password="p", is_staff=True)
        # Create some fake students
        for roll in ["23BCS101", "23BCS102", "22BCS050"]:
            User.objects.create_user(username=roll, password="p")
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff)

    def test_batch_audience_matches_prefix(self):
        with patch("applications.notifications_extension.services.notify.send"):
            r = self.client.post(
                "/api/notifications/send-group/",
                {"audience": "batch", "audience_value": "23BCS",
                 "module": ModuleName.LEAVE_MODULE, "verb": "test"},
                format="json",
            )
            self.assertEqual(r.status_code, 201)
            # Should match 23BCS101 and 23BCS102 (not 22BCS050)
            self.assertGreaterEqual(r.data["delivered"], 2)

    def test_group_send_rejects_unknown_audience(self):
        r = self.client.post(
            "/api/notifications/send-group/",
            {"audience": "martians", "module": ModuleName.LEAVE_MODULE, "verb": "t"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)

    def test_group_send_rejects_bad_module(self):
        r = self.client.post(
            "/api/notifications/send-group/",
            {"audience": "students", "module": "FakeModule", "verb": "t"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)
