"""
Self-contained regression/contract tests for the placement_cell API module.

Goals (kept deliberately robust so they keep passing in the future):
  * Schema regressions  - guard the data-model fixes (e.g. Education.grade width).
  * URL wiring          - every placement API route resolves to a real view and
                          the urlconf stays API-only (no legacy template routes).
  * Authentication      - protected endpoints reject anonymous callers.
  * Authorization       - officer-only (TPO) endpoints reject students and admit
                          placement officers.

Run with the dedicated test settings (migrations disabled so the historical
migration chain cannot block test-DB creation)::

    python manage.py test applications.placement_cell.tests.test_placement_api \
        --settings=test_settings
"""

import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.globals.models import (
    DepartmentInfo,
    Designation,
    ExtraInfo,
    HoldsDesignation,
)
from applications.placement_cell.api import urls as placement_urls
from applications.placement_cell.models import (
    Education,
    NotifyStudent,
    OffCampusPlacement,
    PlacementAnnouncement,
    PlacementCalendarEvent,
    PlacementRestriction,
    PlacementSchedule,
)


class PlacementBaseTest(TestCase):
    """Builds a department, a student, a placement officer and a plain user."""

    def setUp(self):
        self.department = DepartmentInfo.objects.create(name="CSE")
        self.student_designation = Designation.objects.create(
            name="student", full_name="Student"
        )
        self.officer_designation = Designation.objects.create(
            name="placement officer", full_name="Placement Officer"
        )

        self.student_user = self._make_user("student1", "2023001", user_type="student")
        Student.objects.create(
            id=ExtraInfo.objects.get(user=self.student_user),
            programme="B.Tech",
            batch=2026,
            cpi=8.5,
            category="GEN",
        )
        self._hold(self.student_user, self.student_designation)

        self.officer_user = self._make_user("officer1", "OFF001", user_type="staff")
        self._hold(self.officer_user, self.officer_designation)

        # Authenticated but holds no placement designation.
        self.plain_user = self._make_user("plain1", "PLN001", user_type="staff")

    # -- fixture helpers -----------------------------------------------------
    def _make_user(self, username, info_id, *, user_type):
        user = User.objects.create_user(
            username=username,
            password="pw",
            email="{}@example.com".format(username),
            first_name=username,
        )
        extra, _ = ExtraInfo.objects.get_or_create(
            user=user,
            defaults={"id": info_id, "user_type": user_type, "department": self.department},
        )
        extra.user_type = user_type
        extra.department = self.department
        extra.save(update_fields=["user_type", "department"])
        return user

    def _hold(self, user, designation):
        HoldsDesignation.objects.create(
            user=user, working=user, designation=designation
        )

    def _client(self, user=None):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)
        return client


class SchemaRegressionTests(PlacementBaseTest):
    def test_grade_field_is_wide_enough_for_cgpa(self):
        # A previous migration shrank grade to 3 chars and truncated real CGPA
        # data (e.g. "8.39"). Keep it wide enough forever.
        self.assertGreaterEqual(Education._meta.get_field("grade").max_length, 4)

    def test_education_persists_cgpa_value(self):
        student = Student.objects.get(id__user=self.student_user)
        edu = Education.objects.create(
            unique_id=student, degree="B.Tech", grade="8.39", institute="IIITDMJ"
        )
        edu.refresh_from_db()
        self.assertEqual(edu.grade, "8.39")

    def test_core_models_are_creatable(self):
        notify = NotifyStudent.objects.create(
            placement_type="PLACEMENT",
            company_name="Acme Corp",
            ctc=Decimal("12.50"),
            description="Campus drive",
        )
        schedule = PlacementSchedule.objects.create(
            notify_id=notify,
            title="Acme Corp",
            placement_date=datetime.date.today(),
            location="Campus",
            time=datetime.time(10, 0),
        )
        self.assertIsNotNone(schedule.pk)


class UrlWiringTests(PlacementBaseTest):
    def test_every_route_resolves_to_a_callable_view(self):
        self.assertTrue(placement_urls.urlpatterns)
        for pattern in placement_urls.urlpatterns:
            self.assertTrue(
                callable(pattern.callback),
                "URL {!r} does not resolve to a view".format(pattern.name),
            )

    def test_urlconf_is_api_only_no_legacy_template_routes(self):
        # The legacy template-based routes were removed; guard against their
        # reintroduction by requiring every route to live under ^api/.
        for pattern in placement_urls.urlpatterns:
            regex = pattern.pattern.regex.pattern
            self.assertTrue(
                regex.startswith("^api/"),
                "Unexpected non-API route present: {}".format(regex),
            )

    def test_key_routes_reverse(self):
        for name in [
            "placement_api",
            "placement_statistics_api",
            "calendar_api",
            "debarred_students_api",
            "restrictions_api",
            "generate_cv_api",
        ]:
            self.assertTrue(reverse("placement:{}".format(name)))


class AuthenticationTests(PlacementBaseTest):
    PROTECTED = [
        "placement_api",
        "placement_statistics_api",
        "calendar_api",
        "debarred_students_api",
        "restrictions_api",
        "my_applications_api",
    ]

    def test_protected_endpoints_reject_anonymous(self):
        client = APIClient()
        for name in self.PROTECTED:
            response = client.get(reverse("placement:{}".format(name)))
            self.assertIn(
                response.status_code,
                (401, 403),
                "{} should require authentication (got {})".format(
                    name, response.status_code
                ),
            )


class AuthorizationTests(PlacementBaseTest):
    OFFICER_ONLY = ["debarred_students_api", "restrictions_api"]

    def test_students_are_denied_officer_endpoints(self):
        client = self._client(self.student_user)
        for name in self.OFFICER_ONLY:
            response = client.get(reverse("placement:{}".format(name)))
            self.assertEqual(
                response.status_code,
                403,
                "{} should be forbidden for students".format(name),
            )

    def test_plain_authenticated_user_denied_officer_endpoints(self):
        client = self._client(self.plain_user)
        for name in self.OFFICER_ONLY:
            response = client.get(reverse("placement:{}".format(name)))
            self.assertEqual(response.status_code, 403)

    def test_officer_can_read_officer_endpoints(self):
        client = self._client(self.officer_user)
        for name in self.OFFICER_ONLY:
            response = client.get(reverse("placement:{}".format(name)))
            self.assertEqual(
                response.status_code,
                200,
                "{} should be allowed for officers".format(name),
            )

    def test_officer_can_list_placements(self):
        response = self._client(self.officer_user).get(
            reverse("placement:placement_api")
        )
        self.assertEqual(response.status_code, 200)

    def test_officer_can_create_and_list_restriction(self):
        client = self._client(self.officer_user)
        create = client.post(
            reverse("placement:restrictions_api"),
            data={
                "criteria": "CPI",
                "condition": "lt",
                "value": "6.0",
                "description": "Low CPI",
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        self.assertEqual(PlacementRestriction.objects.count(), 1)

        listed = client.get(reverse("placement:restrictions_api"))
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data), 1)


class AnnouncementApiTests(PlacementBaseTest):
    """Announcements: readable by any authenticated role, writable by the TPO only."""

    def test_announcements_require_authentication(self):
        response = APIClient().get(reverse("placement:placement_announcements_api"))
        self.assertIn(response.status_code, (401, 403))

    def test_any_authenticated_role_can_list_announcements(self):
        PlacementAnnouncement.objects.create(title="Drive", body="Acme on campus")
        response = self._client(self.student_user).get(
            reverse("placement:placement_announcements_api")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_student_cannot_post_announcement(self):
        response = self._client(self.student_user).post(
            reverse("placement:placement_announcements_api"),
            data={"title": "X", "body": "Y"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(PlacementAnnouncement.objects.count(), 0)

    def test_officer_can_post_and_delete_announcement(self):
        client = self._client(self.officer_user)
        created = client.post(
            reverse("placement:placement_announcements_api"),
            data={"title": "Drive", "body": "Acme on campus", "is_pinned": True},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(PlacementAnnouncement.objects.count(), 1)
        announcement = PlacementAnnouncement.objects.get()
        self.assertEqual(announcement.posted_by, self.officer_user)

        deleted = client.delete(
            reverse(
                "placement:placement_announcement_detail_api",
                args=[announcement.pk],
            )
        )
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(PlacementAnnouncement.objects.count(), 0)


class OffCampusPlacementApiTests(PlacementBaseTest):
    """Off-campus placements are managed entirely by the TPO."""

    def test_students_are_denied(self):
        response = self._client(self.student_user).get(
            reverse("placement:offcampus_placements_api")
        )
        self.assertEqual(response.status_code, 403)

    def test_officer_can_record_offcampus_against_roll_number(self):
        client = self._client(self.officer_user)
        created = client.post(
            reverse("placement:offcampus_placements_api"),
            data={
                "roll_no": self.student_user.username,
                "company_name": "Acme Corp",
                "role": "SDE",
                "offer_type": "placement",
                "ctc": "18.00",
                "offer_date": "2026-06-01",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(OffCampusPlacement.objects.count(), 1)
        record = OffCampusPlacement.objects.get()
        self.assertEqual(record.added_by, self.officer_user)
        self.assertEqual(created.data["roll_no"], self.student_user.username)

        listed = client.get(reverse("placement:offcampus_placements_api"))
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data), 1)

    def test_unknown_roll_number_is_rejected(self):
        response = self._client(self.officer_user).post(
            reverse("placement:offcampus_placements_api"),
            data={
                "roll_no": "DOES_NOT_EXIST",
                "company_name": "Acme",
                "role": "SDE",
                "offer_date": "2026-06-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OffCampusPlacement.objects.count(), 0)

    def test_officer_can_delete_offcampus_record(self):
        student_extra = ExtraInfo.objects.get(user=self.student_user)
        record = OffCampusPlacement.objects.create(
            student=student_extra,
            company_name="Acme",
            role="SDE",
            offer_date=datetime.date(2026, 6, 1),
            added_by=self.officer_user,
        )
        response = self._client(self.officer_user).delete(
            reverse(
                "placement:offcampus_placement_detail_api", args=[record.pk]
            )
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(OffCampusPlacement.objects.count(), 0)


class PublishedCpiApiTests(PlacementBaseTest):
    """Published-CPI batch list, student list and Excel export are TPO-only."""

    CPI_ROUTES = ["placement_cpi_batches_api", "placement_cpi_students_api"]

    def test_cpi_routes_require_authentication(self):
        client = APIClient()
        for name in self.CPI_ROUTES:
            response = client.get(reverse("placement:{}".format(name)))
            self.assertIn(response.status_code, (401, 403))

    def test_students_are_denied_cpi_routes(self):
        client = self._client(self.student_user)
        for name in self.CPI_ROUTES:
            response = client.get(reverse("placement:{}".format(name)))
            self.assertEqual(response.status_code, 403)

    def test_officer_can_read_cpi_batches(self):
        response = self._client(self.officer_user).get(
            reverse("placement:placement_cpi_batches_api")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_cpi_students_without_batch_returns_empty_list(self):
        response = self._client(self.officer_user).get(
            reverse("placement:placement_cpi_students_api")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_cpi_students_excel_export_returns_workbook(self):
        response = self._client(self.officer_user).get(
            reverse("placement:placement_cpi_students_api"),
            {"batch_id": 1, "export": "excel"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/ms-excel")
        self.assertIn("attachment", response["Content-Disposition"])


class CalendarEventApiTests(PlacementBaseTest):
    """Calendar events: readable by any role, writable only by the TPO."""

    def test_listing_requires_authentication(self):
        response = APIClient().get(
            reverse("placement:placement_calendar_events_api")
        )
        self.assertIn(response.status_code, (401, 403))

    def test_any_authenticated_role_can_list(self):
        PlacementCalendarEvent.objects.create(
            title="Info session", start=datetime.datetime(2026, 6, 25, 10, 0)
        )
        response = self._client(self.student_user).get(
            reverse("placement:placement_calendar_events_api")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_student_cannot_create(self):
        response = self._client(self.student_user).post(
            reverse("placement:placement_calendar_events_api"),
            data={"title": "X", "start": "2026-06-25T10:00"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(PlacementCalendarEvent.objects.count(), 0)

    def test_officer_can_create_update_and_delete(self):
        client = self._client(self.officer_user)
        created = client.post(
            reverse("placement:placement_calendar_events_api"),
            data={
                "title": "Pre-placement talk",
                "start": "2026-06-25T10:00",
                "category": "event",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        event_id = created.data["id"]
        self.assertEqual(
            PlacementCalendarEvent.objects.get().created_by, self.officer_user
        )

        updated = client.patch(
            reverse(
                "placement:placement_calendar_event_detail_api", args=[event_id]
            ),
            data={"title": "Renamed talk"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["title"], "Renamed talk")

        deleted = client.delete(
            reverse(
                "placement:placement_calendar_event_detail_api", args=[event_id]
            )
        )
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(PlacementCalendarEvent.objects.count(), 0)
