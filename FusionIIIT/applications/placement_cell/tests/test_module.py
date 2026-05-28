import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from notifications.models import Notification
from rest_framework.test import APIRequestFactory, force_authenticate

from applications.academic_information.models import Student
from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation
from applications.placement_cell import selectors, services
from applications.placement_cell.api.views import placement_api, placement_statistics_api
from applications.placement_cell.models import (
    AlumniConnection,
    AlumniMentorshipSession,
    AlumniProfile,
    AlumniReferral,
    CompanyDetails,
    Education,
    Has,
    NotifyStudent,
    PlacementApplication,
    PlacementField,
    PlacementApplicationTimeline,
    PlacementInterviewSchedule,
    PlacementNotificationPreference,
    PlacementProfileAuditLog,
    PlacementProfileDocument,
    PlacementRecord,
    PlacementSchedule,
    PlacementStatus,
    Project,
    Skill,
    StudentPlacement,
)


class PlacementCellSelectorTests(SimpleTestCase):
    @patch("applications.placement_cell.selectors.CompanyDetails.objects.filter")
    def test_get_company_names_by_prefix_returns_flat_list(self, mock_filter):
        mock_filter.return_value.values_list.return_value = ["A", "B"]

        company_names = selectors.get_company_names_by_prefix("A")

        self.assertEqual(company_names, ["A", "B"])


class PlacementCellServiceTests(SimpleTestCase):
    @patch("applications.placement_cell.services.PlacementRecord.objects.create")
    def test_create_placement_record_preserves_existing_fields(self, mock_create):
        record = Mock()
        mock_create.return_value = record

        result = services.create_placement_record(
            placement_type="PLACEMENT",
            student_name="Alice",
            ctc="10.5",
            year="2026",
            test_type="",
            test_score="",
        )

        mock_create.assert_called_once_with(
            placement_type="PLACEMENT",
            name="Alice",
            ctc="10.5",
            year="2026",
            test_type="",
            test_score="",
        )
        record.save.assert_called_once_with()
        self.assertIs(result, record)

    @patch("applications.placement_cell.services.PlacementSchedule.objects.create")
    @patch("applications.placement_cell.services.NotifyStudent.objects.create")
    @patch("applications.placement_cell.services.selectors.get_or_create_role")
    @patch("applications.placement_cell.services.selectors.get_or_create_company_detail")
    def test_create_schedule_and_notification_uses_selector_and_models(
        self,
        mock_company,
        mock_role,
        mock_notify_create,
        mock_schedule_create,
    ):
        notify = Mock()
        company = Mock()
        role = Mock()
        schedule = Mock()
        mock_company.return_value = company
        mock_role.return_value = role
        mock_notify_create.return_value = notify
        mock_schedule_create.return_value = schedule

        created_notify, created_schedule = services.create_schedule_and_notification(
            placement_type="PLACEMENT",
            company_name="Acme",
            ctc="12",
            description="desc",
            placement_date=timezone.now().date() + datetime.timedelta(days=1),
            location="Campus",
            time="10:00",
            role_name="SDE",
        )

        mock_company.assert_called_once_with("Acme")
        mock_role.assert_called_once_with("SDE")
        mock_schedule_create.assert_called_once_with(
            notify_id=notify,
            title="Acme",
            description="desc",
            placement_date=timezone.now().date() + datetime.timedelta(days=1),
            attached_file=None,
            role=role,
            location="Campus",
            time="10:00",
            company=company,
        )
        self.assertIs(created_notify, notify)
        self.assertIs(created_schedule, schedule)


class PlacementCellApiTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.department_cse = DepartmentInfo.objects.create(name="CSE")
        self.department_ece = DepartmentInfo.objects.create(name="ECE")
        self.student_designation = Designation.objects.create(name="student")
        self.officer = User.objects.create_user(
            username="officer",
            password="password",
            email="officer@example.com",
        )
        self.student_user = self._create_student_user(
            roll_no="2023001",
            username="student1",
            department=self.department_cse,
        )
        self.other_student_user = self._create_student_user(
            roll_no="2023002",
            username="student2",
            department=self.department_ece,
        )

    def _create_student_user(self, *, roll_no, username, department):
        user = User.objects.create_user(
            username=username,
            password="password",
            email=f"{username}@example.com",
            first_name=username,
        )
        extra = ExtraInfo.objects.get(user=user)
        extra.user_type = "student"
        extra.department = department
        extra.save(update_fields=["user_type", "department"])
        Student.objects.create(
            id=extra,
            programme="B.Tech",
            batch=2026,
            cpi=8.5,
            category="GEN",
        )
        HoldsDesignation.objects.create(
            user=user,
            working=user,
            designation=self.student_designation,
        )
        return user

    def _create_officer_designation(self, name):
        designation, _ = Designation.objects.get_or_create(name=name, full_name=name.title())
        HoldsDesignation.objects.get_or_create(
            user=self.officer,
            working=self.officer,
            designation=designation,
        )
        return designation

    def _get_student(self, user):
        return Student.objects.get(id__user=user)

    def _create_alumni_user(self, *, username="alumni1"):
        user = User.objects.create_user(
            username=username,
            password="password",
            email=f"{username}@example.com",
            first_name="Alumni",
            last_name="User",
        )
        extra = ExtraInfo.objects.get(user=user)
        extra.user_type = "faculty"
        extra.department = self.department_cse
        extra.save(update_fields=["user_type", "department"])
        return user

    def _create_schedule(self, *, company_name, placement_type, placement_date):
        notify = NotifyStudent.objects.create(
            placement_type=placement_type,
            company_name=company_name,
            ctc=Decimal("10.00"),
            description="desc",
        )
        return PlacementSchedule.objects.create(
            notify_id=notify,
            title=company_name,
            placement_date=placement_date,
            location="Campus",
            description="desc",
            time=datetime.time(10, 0),
            schedule_at=timezone.now(),
        )

    def _make_profile_complete(self, user):
        student = self._get_student(user)
        extra = student.id
        extra.about_me = "About me"
        extra.address = "Hostel"
        extra.phone_no = 9876543210
        extra.save(update_fields=["about_me", "address", "phone_no"])
        Education.objects.create(
            unique_id=student,
            degree="B.Tech",
            grade="90",
            institute="IIITDMJ",
            sdate=datetime.date(2020, 1, 1),
            edate=datetime.date(2021, 1, 1),
        )
        skill = Skill.objects.create(skill="Python")
        Has.objects.create(skill_id=skill, unique_id=student, skill_rating=80)
        Project.objects.create(
            unique_id=student,
            project_name="Capstone",
            project_status="COMPLETED",
            sdate=datetime.date(2020, 1, 1),
            edate=datetime.date(2020, 2, 1),
        )
        PlacementProfileDocument.objects.create(
            student=student,
            name="Resume",
            document=SimpleUploadedFile("resume.pdf", b"pdf-content", content_type="application/pdf"),
        )
        return student

    def test_update_invitation_status_is_immutable_after_first_response(self):
        status = PlacementStatus.objects.create(
            notify_id=NotifyStudent.objects.create(
                placement_type="PLACEMENT",
                company_name="Acme",
                ctc=Decimal("10.00"),
            ),
            unique_id=self._get_student(self.student_user),
            invitation="ACCEPTED",
        )

        updated = services.update_invitation_status(status.id, "REJECTED")

        status.refresh_from_db()
        self.assertEqual(updated, 0)
        self.assertEqual(status.invitation, "ACCEPTED")

    def test_education_clean_uses_model_dates_and_grade_limit(self):
        education = Education(
            unique_id=self._get_student(self.student_user),
            degree="B.Tech",
            grade="1234",
            institute="IIITDMJ",
            sdate=datetime.date(2024, 1, 1),
            edate=datetime.date(2024, 1, 1),
        )

        with self.assertRaises(ValidationError) as exc:
            education.full_clean()

        self.assertIn("grade", exc.exception.message_dict)
        self.assertIn("sdate", exc.exception.message_dict)

    def test_skill_rating_rejects_values_above_100(self):
        has_skill = Has(
            unique_id=self._get_student(self.student_user),
            skill_id_id=1,
            skill_rating=101,
        )

        with self.assertRaises(ValidationError) as exc:
            has_skill.full_clean(exclude=["skill_id"])

        self.assertIn("skill_rating", exc.exception.message_dict)

    def test_placement_api_get_filters_past_schedules_and_shows_recruitment_events_to_students(self):
        StudentPlacement.objects.create(
            unique_id=self._get_student(self.student_user),
            future_aspect="PLACEMENT",
        )
        today = timezone.now().date()
        expected_schedule = self._create_schedule(
            company_name="Future Placement",
            placement_type="PLACEMENT",
            placement_date=today + datetime.timedelta(days=1),
        )
        self._create_schedule(
            company_name="Past Placement",
            placement_type="PLACEMENT",
            placement_date=today - datetime.timedelta(days=1),
        )
        self._create_schedule(
            company_name="Future PBI",
            placement_type="PBI",
            placement_date=today + datetime.timedelta(days=2),
        )

        request = self.factory.get("/placement/api/placement/")
        force_authenticate(request, user=self.student_user)

        response = placement_api(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        returned_ids = {int(item["id"]) for item in response.data}
        self.assertIn(expected_schedule.id, returned_ids)
        self.assertIn(
            PlacementSchedule.objects.get(notify_id__company_name="Future PBI").id,
            returned_ids,
        )

    def test_placement_api_post_creates_company_when_missing(self):
        request = self.factory.post(
            "/placement/api/placement/",
            {
                "company_name": "New Co",
                "title": "New Co",
                "placement_type": "PLACEMENT",
                "ctc": "12.50",
                "description": "Campus drive",
                "placement_date": (timezone.now().date() + datetime.timedelta(days=3)).isoformat(),
                "schedule_at": "2026-04-15 10:30",
                "location": "Auditorium",
            },
            format="multipart",
        )
        force_authenticate(request, user=self.officer)

        response = placement_api(request)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(CompanyDetails.objects.filter(company_name="New Co").exists())
        schedule = PlacementSchedule.objects.get(pk=response.data["id"])
        self.assertEqual(schedule.company.company_name, "New Co")

    def test_placement_api_post_rejects_past_dates(self):
        request = self.factory.post(
            "/placement/api/placement/",
            {
                "company_name": "Past Co",
                "placement_type": "PLACEMENT",
                "placement_date": (timezone.now().date() - datetime.timedelta(days=1)).isoformat(),
                "schedule_at": "2026-04-01 10:30",
            },
            format="multipart",
        )
        force_authenticate(request, user=self.officer)

        response = placement_api(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("placement_date", response.data)

    def test_placement_api_get_supports_company_role_location_and_package_filters(self):
        self._create_officer_designation("placement officer")
        engineer_role = selectors.get_or_create_role("Software Engineer")
        analyst_role = selectors.get_or_create_role("Analyst")

        alpha_schedule = self._create_schedule(
            company_name="Alpha Corp",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=5),
        )
        alpha_schedule.location = "Bangalore"
        alpha_schedule.role = engineer_role
        alpha_schedule.notify_id.ctc = Decimal("22.00")
        alpha_schedule.notify_id.save(update_fields=["ctc"])
        alpha_schedule.save(update_fields=["location", "role"])

        beta_schedule = self._create_schedule(
            company_name="Beta Labs",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=6),
        )
        beta_schedule.location = "Delhi"
        beta_schedule.role = analyst_role
        beta_schedule.notify_id.ctc = Decimal("12.00")
        beta_schedule.notify_id.save(update_fields=["ctc"])
        beta_schedule.save(update_fields=["location", "role"])

        request = self.factory.get(
            "/placement/api/placement/",
            {
                "company": "Alpha",
                "role": "Engineer",
                "location": "Bangalore",
                "min_package": "20",
                "max_package": "25",
            },
        )
        force_authenticate(request, user=self.officer)

        response = placement_api(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["company_name"], "Alpha Corp")
        self.assertEqual(response.data[0]["role_st"], "Software Engineer")

    def test_placement_detail_api_get_returns_full_job_details(self):
        student = self._get_student(self.student_user)
        self._make_profile_complete(self.student_user)
        company = CompanyDetails.objects.create(
            company_name="Detail Corp",
            description="Product engineering company",
            address="Bangalore, India",
            website="https://detail.example.com",
        )
        role = selectors.get_or_create_role("Backend Engineer")
        field = PlacementField.objects.create(name="github_profile", type="text", required=True)
        schedule = self._create_schedule(
            company_name="Detail Corp",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=3),
        )
        schedule.company = company
        schedule.role = role
        schedule.location = "Bangalore"
        schedule.description = "Build backend systems"
        schedule.eligibility = "CPI >= 8"
        schedule.branch = "CSE"
        schedule.cpi = "8.0"
        schedule.end_datetime = timezone.now() + datetime.timedelta(days=2)
        schedule.save(
            update_fields=[
                "company",
                "role",
                "location",
                "description",
                "eligibility",
                "branch",
                "cpi",
                "end_datetime",
            ],
        )
        schedule.fields.add(field)

        request = self.factory.get(f"/placement/api/placement/{schedule.id}/")
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import placement_detail_api

        response = placement_detail_api(request, schedule.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["company_name"], "Detail Corp")
        self.assertEqual(response.data["role_st"], "Backend Engineer")
        self.assertEqual(response.data["location"], "Bangalore")
        self.assertEqual(response.data["company_details"]["website"], "https://detail.example.com")
        self.assertEqual(len(response.data["application_fields"]), 1)
        self.assertEqual(response.data["application_fields"][0]["name"], "github_profile")
        self.assertTrue(response.data["eligible"])

    def test_placement_statistics_api_supports_filters_and_department_aggregation(self):
        student_one = self._get_student(self.student_user)
        student_two = self._get_student(self.other_student_user)
        acme_record = PlacementRecord.objects.create(
            placement_type="PLACEMENT",
            name="Acme",
            ctc=Decimal("18.00"),
            year=2026,
        )
        beta_record = PlacementRecord.objects.create(
            placement_type="PLACEMENT",
            name="Beta",
            ctc=Decimal("8.00"),
            year=2025,
        )
        StudentPlacement.objects.get_or_create(unique_id=student_one)
        StudentPlacement.objects.get_or_create(unique_id=student_two)
        student_one.studentrecord_set.create(record_id=acme_record)
        student_two.studentrecord_set.create(record_id=beta_record)

        filtered_request = self.factory.get(
            "/placement/api/statistics/",
            {"company": "Acme", "ctc_min": "15", "year": "2026"},
        )
        force_authenticate(filtered_request, user=self.officer)
        filtered_response = placement_statistics_api(filtered_request)

        self.assertEqual(filtered_response.status_code, 200)
        self.assertEqual(len(filtered_response.data), 1)
        self.assertEqual(filtered_response.data[0]["placement_name"], "Acme")

        aggregate_request = self.factory.get(
            "/placement/api/statistics/",
            {"aggregate_by": "department"},
        )
        force_authenticate(aggregate_request, user=self.officer)
        aggregate_response = placement_statistics_api(aggregate_request)

        self.assertEqual(aggregate_response.status_code, 200)
        self.assertEqual(
            aggregate_response.data,
            [
                {"department": "CSE", "count": 1},
                {"department": "ECE", "count": 1},
            ],
        )

    def test_apply_for_placement_rejects_incomplete_profile(self):
        student = self._get_student(self.student_user)
        schedule = self._create_schedule(
            company_name="Acme",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=1),
        )
        request = self.factory.post(
            "/placement/api/apply-for-placement/",
            {"jobId": schedule.id, "responses": []},
            format="json",
        )
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import apply_for_placement_api

        response = apply_for_placement_api(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.data)
        self.assertFalse(PlacementApplication.objects.filter(student=student).exists())

    @override_settings(PLACEMENT_MAX_ACTIVE_APPLICATIONS=3)
    def test_apply_for_placement_enforces_active_application_limit(self):
        student = self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(
            company_name="Limit Co",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=1),
        )
        for index in range(3):
            prior_schedule = self._create_schedule(
                company_name=f"Company {index}",
                placement_type="PLACEMENT",
                placement_date=timezone.now().date() + datetime.timedelta(days=2 + index),
            )
            PlacementApplication.objects.create(schedule=prior_schedule, student=student)

        request = self.factory.post(
            "/placement/api/apply-for-placement/",
            {"jobId": schedule.id, "responses": []},
            format="json",
        )
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import apply_for_placement_api

        response = apply_for_placement_api(request)

        self.assertEqual(response.status_code, 403)
        self.assertIn("3 active applications", response.data["detail"])

    @override_settings(PLACEMENT_MAX_ACTIVE_APPLICATIONS=3)
    def test_apply_for_placement_warns_when_student_is_near_limit(self):
        student = self._make_profile_complete(self.student_user)
        existing_schedule = self._create_schedule(
            company_name="Existing Co",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=1),
        )
        next_schedule = self._create_schedule(
            company_name="Warning Co",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=2),
        )
        PlacementApplication.objects.create(
            schedule=existing_schedule,
            student=student,
        )

        request = self.factory.post(
            "/placement/api/apply-for-placement/",
            {"jobId": next_schedule.id, "responses": []},
            format="json",
        )
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import apply_for_placement_api

        response = apply_for_placement_api(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["warning"],
            "You have 1 active applications. The limit is 3.",
        )

    def test_withdraw_application_marks_state_and_notifies_student(self):
        self._create_officer_designation("placement officer")
        student = self._get_student(self.student_user)
        schedule = self._create_schedule(
            company_name="Withdraw Co",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=1),
        )
        application = PlacementApplication.objects.create(schedule=schedule, student=student)
        PlacementStatus.objects.create(
            notify_id=schedule.notify_id,
            unique_id=student,
            invitation="ACCEPTED",
        )
        request = self.factory.delete(f"/placement/api/apply-for-placement/{schedule.id}/")
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import withdraw_application_api

        response = withdraw_application_api(request, schedule.id)

        self.assertEqual(response.status_code, 200)
        application.refresh_from_db()
        self.assertEqual(application.status, "withdrawn")
        self.assertIsNotNone(application.withdrawn_at)
        self.assertTrue(
            PlacementProfileAuditLog.objects.filter(
                student=student,
                action="application_withdrawn",
            ).exists(),
        )

    def test_application_detail_api_returns_timeline_and_interviews_for_tpo(self):
        self._create_officer_designation("placement officer")
        student = self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(
            company_name="Detail Co",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=1),
        )
        application = PlacementApplication.objects.create(
            schedule=schedule,
            student=student,
            status="shortlisted",
            remarks="Strong profile",
        )
        PlacementApplicationTimeline.objects.create(
            application=application,
            stage="Shortlisted",
            remarks="Moved to shortlist",
            actor=self.officer,
        )
        PlacementInterviewSchedule.objects.create(
            application=application,
            round_no=1,
            title="Technical Interview",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            mode="ONLINE",
            meeting_link="https://meet.test/room",
            remarks="Prepare DSA",
            created_by=self.officer,
        )
        request = self.factory.get(f"/placement/api/application-detail/{application.id}/")
        force_authenticate(request, user=self.officer)

        from applications.placement_cell.api.views import application_detail_api

        response = application_detail_api(request, application.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], application.id)
        self.assertEqual(response.data["timeline"][1]["stage"], "Shortlisted")
        self.assertEqual(response.data["interviews"][0]["title"], "Technical Interview")
        self.assertEqual(response.data["student"]["branch"], "CSE")
        self.assertEqual(response.data["student"]["passout_year"], 2026)
        self.assertEqual(len(response.data["documents"]), 1)
        self.assertEqual(response.data["resume"]["name"], "Resume")

    def test_application_interview_schedule_api_creates_interview_and_notifies_student(self):
        self._create_officer_designation("placement officer")
        student = self._get_student(self.student_user)
        schedule = self._create_schedule(
            company_name="Interview Co",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=1),
        )
        application = PlacementApplication.objects.create(schedule=schedule, student=student)
        request = self.factory.post(
            f"/placement/api/application-detail/{application.id}/interview/",
            {
                "round_no": 1,
                "title": "Technical Interview",
                "scheduled_at": (timezone.now() + datetime.timedelta(days=2)).isoformat(),
                "mode": "ONLINE",
                "meeting_link": "https://meet.test/interview",
                "remarks": "Join 10 minutes early",
            },
            format="json",
        )
        force_authenticate(request, user=self.officer)

        from applications.placement_cell.api.views import application_interview_schedule_api

        response = application_interview_schedule_api(request, application.id)

        self.assertEqual(response.status_code, 201)
        application.refresh_from_db()
        self.assertEqual(application.status, "interview_scheduled")
        self.assertTrue(
            PlacementInterviewSchedule.objects.filter(application=application, title="Technical Interview").exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.student_user,
                verb__icontains="Interview scheduled",
                module="Placement Cell",
            ).exists()
        )

    def test_application_detail_api_selected_status_adds_record_to_placement_stats(self):
        self._create_officer_designation("placement officer")
        student = self._get_student(self.student_user)
        schedule = self._create_schedule(
            company_name="Selected Co",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=1),
        )
        application = PlacementApplication.objects.create(schedule=schedule, student=student, status="offer_released")
        request = self.factory.put(
            f"/placement/api/application-detail/{application.id}/",
            {
                "status": "accept",
                "remarks": "Final selected",
            },
            format="json",
        )
        force_authenticate(request, user=self.officer)

        from applications.placement_cell.api.views import application_detail_api

        response = application_detail_api(request, application.id)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            StudentRecord.objects.filter(
                unique_id=student,
                record_id__name="Selected Co",
            ).exists()
        )
        self.assertTrue(
            PlacementApplicationTimeline.objects.filter(
                application=application,
                stage="Selected",
            ).exists()
        )

    def test_my_offers_api_includes_offer_released_applications(self):
        student = self._get_student(self.student_user)
        schedule = self._create_schedule(
            company_name="Offer Co",
            placement_type="PLACEMENT",
            placement_date=timezone.now().date() + datetime.timedelta(days=5),
        )
        PlacementApplication.objects.create(
            schedule=schedule,
            student=student,
            status="offer_released",
        )
        offer = PlacementStatus.objects.create(
            notify_id=schedule.notify_id,
            unique_id=student,
            invitation="PENDING",
            timestamp=timezone.now(),
            no_of_days=2,
        )
        request = self.factory.get("/placement/api/my-offers/")
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import my_offers_api

        response = my_offers_api(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["offers"]), 1)
        self.assertEqual(response.data["offers"][0]["id"], offer.id)
        self.assertEqual(response.data["offers"][0]["company_name"], "Offer Co")
        self.assertEqual(response.data["offers"][0]["status"], "PENDING")

    def test_profile_api_returns_documents_audit_logs_and_preferences(self):
        student = self._get_student(self.student_user)
        preference = PlacementNotificationPreference.objects.create(
            student=student,
            enable_portal=True,
            enable_email=False,
            enable_sms=True,
        )
        PlacementProfileDocument.objects.create(
            student=student,
            name="Resume",
            document=SimpleUploadedFile("resume.pdf", b"pdf-content", content_type="application/pdf"),
        )
        PlacementProfileAuditLog.objects.create(
            student=student,
            actor=self.student_user,
            action="profile_updated",
            details={"about_me": "Updated"},
        )
        request = self.factory.get("/placement/api/profile/")
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import placement_profile_api

        response = placement_profile_api(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["preferences"]["email"], preference.enable_email)
        self.assertEqual(len(response.data["documents"]), 1)
        self.assertEqual(len(response.data["audit_logs"]), 1)
        self.assertEqual(response.data["profile"]["branch"], "CSE")
        self.assertEqual(response.data["profile"]["passout_year"], 2026)
        self.assertEqual(response.data["profile"]["cpi"], 8.5)
        self.assertIn("eligibility_summary", response.data)

    def test_profile_payload_includes_skill_id_for_editing(self):
        student = self._get_student(self.student_user)
        skill = Skill.objects.create(skill="React")
        has = Has.objects.create(skill_id=skill, unique_id=student, skill_rating=1)
        request = self.factory.get("/api/profile/")
        force_authenticate(request, user=self.student_user)

        from applications.globals.api.views import profile

        response = profile(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["skills"][0]["id"], has.id)

    def test_profile_api_returns_fallback_payload_when_extrainfo_is_missing(self):
        user_without_profile = User.objects.create_user(
            username="nologinprofile",
            password="testpass123",
            email="nologinprofile@example.com",
        )
        request = self.factory.get("/api/profile/")
        force_authenticate(request, user=user_without_profile)

        from applications.globals.api.views import profile

        response = profile(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["username"], "nologinprofile")
        self.assertIsNone(response.data["profile"])
        self.assertEqual(response.data["current"], [])

    def test_profile_api_put_enforces_mandatory_fields(self):
        request = self.factory.put(
            "/placement/api/profile/",
            {
                "first_name": "",
                "last_name": "",
                "email": "invalid-email",
                "phone_no": "123",
                "address": "",
                "about_me": "",
            },
            format="multipart",
        )
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import placement_profile_api

        response = placement_profile_api(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("field_errors", response.data)
        self.assertIn("first_name", response.data["field_errors"])
        self.assertIn("email", response.data["field_errors"])
        self.assertIn("phone_no", response.data["field_errors"])

    def test_profile_api_put_updates_profile_and_creates_audit_log(self):
        student = self._get_student(self.student_user)
        request = self.factory.put(
            "/placement/api/profile/",
            {
                "first_name": "Student",
                "last_name": "One",
                "email": "student1@example.com",
                "phone_no": "9876543210",
                "address": "Hostel A",
                "about_me": "Ready for placements",
            },
            format="multipart",
        )
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import placement_profile_api

        response = placement_profile_api(request)

        self.assertEqual(response.status_code, 200)
        student.refresh_from_db()
        student.id.user.refresh_from_db()
        self.assertEqual(student.id.user.first_name, "Student")
        self.assertEqual(student.id.user.last_name, "One")
        self.assertEqual(student.id.user.email, "student1@example.com")
        self.assertEqual(student.id.address, "Hostel A")
        self.assertEqual(student.id.about_me, "Ready for placements")
        self.assertTrue(
            PlacementProfileAuditLog.objects.filter(
                student=student,
                action="profile_updated",
            ).exists(),
        )

    def test_profile_api_put_notifies_student_when_profile_is_updated(self):
        request = self.factory.put(
            "/placement/api/profile/",
            {
                "first_name": "Student",
                "last_name": "One",
                "email": "student1@example.com",
                "phone_no": "9876543210",
                "address": "Hostel A",
                "about_me": "Ready for placements",
            },
            format="multipart",
        )
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import placement_profile_api

        response = placement_profile_api(request)

        self.assertEqual(response.status_code, 200)
        notification = Notification.objects.filter(
            recipient=self.student_user,
            module="Placement Cell",
        ).latest("timestamp")
        self.assertEqual(notification.verb, "Your placement profile has been updated.")

    def test_profile_update_put_updates_existing_skill_without_duplicate_error(self):
        student = self._get_student(self.student_user)
        skill = Skill.objects.create(skill="Python")
        has = Has.objects.create(skill_id=skill, unique_id=student, skill_rating=80)
        request = self.factory.put(
            "/api/profile_update/",
            {
                "skillsubmit": {
                    "id": has.id,
                    "skill_id": {"skill": "Python"},
                    "skill_rating": 90,
                },
            },
            format="json",
        )
        force_authenticate(request, user=self.student_user)

        from applications.globals.api.views import profile_update

        response = profile_update(request)

        self.assertEqual(response.status_code, 200)
        has.refresh_from_db()
        self.assertEqual(has.skill_id.skill, "Python")
        self.assertEqual(has.skill_rating, 90)
        self.assertEqual(Has.objects.filter(unique_id=student, skill_id=skill).count(), 1)

    def test_profile_update_put_updates_existing_education_record(self):
        student = self._get_student(self.student_user)
        education = Education.objects.create(
            unique_id=student,
            degree="B.Tech",
            stream="CSE",
            institute="IIITDMJ",
            grade="9.1",
            sdate=datetime.date(2020, 1, 1),
            edate=datetime.date(2024, 1, 1),
        )
        request = self.factory.put(
            "/api/profile_update/",
            {
                "education": {
                    "id": education.id,
                    "degree": "M.Tech",
                    "stream": "AI",
                    "institute": "IIITDMJ",
                    "grade": "9.5",
                    "sdate": "2021-01-01",
                    "edate": "2025-01-01",
                },
            },
            format="json",
        )
        force_authenticate(request, user=self.student_user)

        from applications.globals.api.views import profile_update

        response = profile_update(request)

        self.assertEqual(response.status_code, 200)
        education.refresh_from_db()
        self.assertEqual(education.degree, "M.Tech")
        self.assertEqual(education.stream, "AI")
        self.assertEqual(education.grade, "9.5")
        self.assertEqual(education.unique_id, student)

    def test_profile_update_rejects_phone_number_that_is_not_10_digits(self):
        request = self.factory.put(
            "/api/profile_update/",
            {
                "profilesubmit": {
                    "about_me": "Ready for placements",
                    "date_of_birth": "2004-01-01",
                    "address": "Hostel A",
                    "phone_no": "12345",
                },
            },
            format="json",
        )
        force_authenticate(request, user=self.student_user)

        from applications.globals.api.views import profile_update

        response = profile_update(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("phone_no", response.data)
        self.assertIn("10 digits", response.data["phone_no"][0])

    def test_profile_update_notification_is_returned_in_dashboard_feed(self):
        request = self.factory.put(
            "/api/profile_update/",
            {
                "profilesubmit": {
                    "about_me": "Ready for placements",
                    "date_of_birth": "2004-01-01",
                    "address": "Hostel A",
                    "phone_no": "9876543210",
                },
            },
            format="json",
        )
        force_authenticate(request, user=self.student_user)

        from applications.globals.api.views import NotificationList, profile_update

        update_response = profile_update(request)
        self.assertEqual(update_response.status_code, 200)

        list_request = self.factory.get("/api/notification/")
        force_authenticate(list_request, user=self.student_user)
        list_response = NotificationList(list_request)

        self.assertEqual(list_response.status_code, 200)
        self.assertTrue(len(list_response.data["notifications"]) > 0)
        self.assertEqual(
            list_response.data["notifications"][0]["verb"],
            "Your profile has been updated.",
        )

    def test_profile_update_creates_dashboard_notification_with_expected_metadata(self):
        request = self.factory.put(
            "/api/profile_update/",
            {
                "profilesubmit": {
                    "about_me": "Updated bio",
                    "date_of_birth": "2004-01-01",
                    "address": "Hostel B",
                    "phone_no": "9876543210",
                },
            },
            format="json",
        )
        force_authenticate(request, user=self.student_user)

        from applications.globals.api.views import profile_update

        response = profile_update(request)

        self.assertEqual(response.status_code, 200)
        notification = Notification.objects.filter(recipient=self.student_user).latest("timestamp")
        self.assertEqual(notification.verb, "Your profile has been updated.")
        self.assertEqual(notification.data.get("module"), "Placement Cell")
        self.assertEqual(notification.data.get("url"), "/profile")

    def test_profile_update_notification_is_unread_by_default_and_can_be_marked_read(self):
        update_request = self.factory.put(
            "/api/profile_update/",
            {
                "profilesubmit": {
                    "about_me": "Updated bio",
                    "date_of_birth": "2004-01-01",
                    "address": "Hostel C",
                    "phone_no": "9876543210",
                },
            },
            format="json",
        )
        force_authenticate(update_request, user=self.student_user)

        from applications.globals.api.views import NotificationRead, profile_update

        update_response = profile_update(update_request)
        self.assertEqual(update_response.status_code, 200)

        notification = Notification.objects.filter(recipient=self.student_user).latest("timestamp")
        self.assertTrue(notification.unread)

        read_request = self.factory.post(
            "/api/notificationread",
            {"id": notification.id},
            format="json",
        )
        force_authenticate(read_request, user=self.student_user)
        read_response = NotificationRead(read_request)

        self.assertEqual(read_response.status_code, 200)
        notification.refresh_from_db()
        self.assertFalse(notification.unread)

    def test_profile_update_notification_list_is_scoped_to_current_user(self):
        own_update_request = self.factory.put(
            "/api/profile_update/",
            {
                "profilesubmit": {
                    "about_me": "Own update",
                    "date_of_birth": "2004-01-01",
                    "address": "Hostel D",
                    "phone_no": "9876543210",
                },
            },
            format="json",
        )
        force_authenticate(own_update_request, user=self.student_user)

        other_update_request = self.factory.put(
            "/api/profile_update/",
            {
                "profilesubmit": {
                    "about_me": "Other update",
                    "date_of_birth": "2004-01-01",
                    "address": "Hostel E",
                    "phone_no": "9123456789",
                },
            },
            format="json",
        )
        force_authenticate(other_update_request, user=self.other_student_user)

        from applications.globals.api.views import NotificationList, profile_update

        own_update_response = profile_update(own_update_request)
        other_update_response = profile_update(other_update_request)
        self.assertEqual(own_update_response.status_code, 200)
        self.assertEqual(other_update_response.status_code, 200)

        list_request = self.factory.get("/api/notification/")
        force_authenticate(list_request, user=self.student_user)
        list_response = NotificationList(list_request)

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data["notifications"]), 1)
        self.assertEqual(
            list_response.data["notifications"][0]["verb"],
            "Your profile has been updated.",
        )

    def test_profile_api_post_accepts_png_document_upload(self):
        student = self._get_student(self.student_user)
        request = self.factory.post(
            "/placement/api/profile/",
            {
                "name": "Offer Letter",
                "document": SimpleUploadedFile(
                    "offer-letter.png",
                    b"png-content",
                    content_type="image/png",
                ),
            },
            format="multipart",
        )
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import placement_profile_api

        response = placement_profile_api(request)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            PlacementProfileDocument.objects.filter(
                student=student,
                name="Offer Letter",
            ).exists(),
        )

    @patch("applications.placement_cell.api.views.render_to_pdf")
    def test_generate_cv_api_creates_audit_log_on_download(self, mock_render_to_pdf):
        student = self._get_student(self.student_user)
        mock_render_to_pdf.return_value = HttpResponse(
            b"%PDF-1.4",
            content_type="application/pdf",
        )
        request = self.factory.post(
            "/placement/api/generate-cv/",
            {
                "achievements": True,
                "education": True,
                "skills": False,
                "projects": True,
            },
            format="json",
        )
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import generate_cv_api

        response = generate_cv_api(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            PlacementProfileAuditLog.objects.filter(
                student=student,
                actor=self.student_user,
                action="resume_downloaded",
            ).exists()
        )
        audit_log = PlacementProfileAuditLog.objects.filter(
            student=student,
            action="resume_downloaded",
        ).latest("id")
        self.assertEqual(audit_log.details["filename"], "student_cv.pdf")
        self.assertEqual(
            audit_log.details["selected_sections"],
            ["achievements", "education", "projects"],
        )

    def test_profile_api_post_rejects_documents_larger_than_5mb(self):
        request = self.factory.post(
            "/placement/api/profile/",
            {
                "document": SimpleUploadedFile(
                    "resume.pdf",
                    b"a" * (5 * 1024 * 1024 + 1),
                    content_type="application/pdf",
                ),
            },
            format="multipart",
        )
        force_authenticate(request, user=self.student_user)

        from applications.placement_cell.api.views import placement_profile_api

        response = placement_profile_api(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("document", response.data)

    def test_alumni_profile_submission_creates_pending_request(self):
        alumni_user = self._create_alumni_user()
        request = self.factory.post(
            "/placement/api/alumni/profile/",
            {
                "graduation_year": 2020,
                "degree": "B.Tech",
                "current_company": "Acme",
                "topics": "Mentoring, Placements",
                "availability": "Weekends",
                "bio": "Happy to help",
                "mentorship_enabled": True,
            },
            format="multipart",
        )
        force_authenticate(request, user=alumni_user)

        from applications.placement_cell.api.views import alumni_profile_api

        response = alumni_profile_api(request)

        self.assertEqual(response.status_code, 201)
        profile = AlumniProfile.objects.get(user=alumni_user)
        self.assertEqual(profile.status, "pending")
        self.assertTrue(profile.mentorship_enabled)

    def test_tpo_can_approve_alumni_and_assign_designation(self):
        self._create_officer_designation("placement officer")
        alumni_user = self._create_alumni_user(username="alumni2")
        profile = AlumniProfile.objects.create(
            user=alumni_user,
            graduation_year=2021,
            degree="B.Tech",
            status="pending",
        )
        request = self.factory.put(
            f"/placement/api/alumni/verification/{profile.id}/",
            {"status": "approved", "verification_notes": "Verified"},
            format="json",
        )
        force_authenticate(request, user=self.officer)

        from applications.placement_cell.api.views import alumni_verification_detail_api

        response = alumni_verification_detail_api(request, profile.id)

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.status, "approved")
        self.assertTrue(
            HoldsDesignation.objects.filter(
                working=alumni_user,
                designation__name="alumni",
            ).exists()
        )

    def test_approved_alumni_can_post_referral_and_student_can_connect_and_request_session(self):
        alumni_user = self._create_alumni_user(username="alumni3")
        alumni_profile = AlumniProfile.objects.create(
            user=alumni_user,
            graduation_year=2019,
            degree="B.Tech",
            status="approved",
            mentorship_enabled=True,
            topics="Career",
            availability="Weekend",
        )
        referral_request = self.factory.post(
            "/placement/api/alumni/referrals/",
            {
                "title": "SDE Referral",
                "company": "Acme",
                "description": "Referral opportunity",
            },
            format="json",
        )
        force_authenticate(referral_request, user=alumni_user)

        from applications.placement_cell.api.views import (
            alumni_connections_api,
            alumni_referrals_api,
            alumni_sessions_api,
        )

        referral_response = alumni_referrals_api(referral_request)
        self.assertEqual(referral_response.status_code, 201)
        self.assertEqual(AlumniReferral.objects.count(), 1)

        student_user = self.student_user
        connection_request = self.factory.post(
            "/placement/api/alumni/connections/",
            {"alumni_id": alumni_profile.id, "message": "Would love to connect"},
            format="json",
        )
        force_authenticate(connection_request, user=student_user)
        connection_response = alumni_connections_api(connection_request)
        self.assertEqual(connection_response.status_code, 201)
        self.assertEqual(AlumniConnection.objects.count(), 1)

        session_request = self.factory.post(
            "/placement/api/alumni/sessions/",
            {
                "alumni_id": alumni_profile.id,
                "topic": "Resume Review",
                "agenda": "Need help with interviews",
                "scheduled_at": timezone.now().isoformat(),
                "mode": "online",
            },
            format="json",
        )
        force_authenticate(session_request, user=student_user)
        session_response = alumni_sessions_api(session_request)
        self.assertEqual(session_response.status_code, 201)
        self.assertEqual(AlumniMentorshipSession.objects.count(), 1)
