import datetime

import yaml
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from applications.academic_information.models import Student
from applications.placement_cell.models import (
    PlacementAppeal,
    PlacementApplication,
    PlacementInterviewSchedule,
    PlacementPolicy,
    PlacementRecord,
    PlacementReportSchedule,
    PlacementStatus,
    StudentPlacement,
)
from applications.placement_cell.tests.conftest import PlacementCellSpecBase


class TestBusinessRuleCatalogIntegrity(PlacementCellSpecBase):
    def test_all_documented_business_rules_define_two_scenarios(self):
        with (self.specs_dir / "business_rules.yaml").open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        business_rules = payload.get("business_rules", [])
        self.assertGreaterEqual(len(business_rules), 20)

        for business_rule in business_rules:
            self.assertIn("source_id", business_rule)
            self.assertIn("endpoint", business_rule)
            self.assertIn("method", business_rule)
            self.assertEqual(sorted(business_rule.get("scenarios", {}).keys()), ["invalid", "valid"])

    def test_business_rule_test_ids_are_unique(self):
        with (self.specs_dir / "business_rules.yaml").open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        test_ids = []
        for business_rule in payload.get("business_rules", []):
            for scenario in business_rule.get("scenarios", {}).values():
                test_ids.append(scenario["_test_id"])

        self.assertEqual(len(test_ids), len(set(test_ids)))


class TestBR01_FuturePlacementDate(PlacementCellSpecBase):
    def test_valid_future_date_is_accepted(self):
        metadata = self.load_spec("business_rules.yaml", "business_rules", "BR01")["scenarios"]["valid"]

        response = self.api_post(
            "/placement/api/placement/",
            user=self.officer,
            data={
                "company_name": "Future Co",
                "title": "Future Co",
                "placement_type": "PLACEMENT",
                "ctc": "12.50",
                "description": "Campus drive",
                "placement_date": (timezone.now().date() + datetime.timedelta(days=3)).isoformat(),
                "schedule_at": "2026-04-15 10:30",
                "location": "Auditorium",
            },
            format="multipart",
        )

        self.assertEqual(metadata["_scenario"], "Valid")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["company_name"], "Future Co")

    def test_invalid_past_date_is_rejected(self):
        metadata = self.load_spec("business_rules.yaml", "business_rules", "BR01")["scenarios"]["invalid"]

        response = self.api_post(
            "/placement/api/placement/",
            user=self.officer,
            data={
                "company_name": "Past Co",
                "placement_type": "PLACEMENT",
                "placement_date": (timezone.now().date() - datetime.timedelta(days=1)).isoformat(),
                "schedule_at": "2026-04-01 10:30",
            },
            format="multipart",
        )

        self.assertEqual(metadata["_scenario"], "Invalid")
        self.assertEqual(response.status_code, 400)
        self.assertIn("placement_date", response.data)


class TestBR02_MandatoryProfileFields(PlacementCellSpecBase):
    def test_valid_profile_payload_is_accepted(self):
        metadata = self.load_spec("business_rules.yaml", "business_rules", "BR02")["scenarios"]["valid"]

        response = self.api_put(
            "/placement/api/profile/",
            user=self.student_user,
            data={
                "first_name": "Student",
                "last_name": "One",
                "email": "student1@example.com",
                "phone_no": "9876543210",
                "address": "Hostel A",
                "about_me": "Ready for placements",
            },
            format="multipart",
        )

        self.assertEqual(metadata["_scenario"], "Valid")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["address"], "Hostel A")
        self.assertNotIn("first_name", response.data["field_errors"])
        self.assertNotIn("email", response.data["field_errors"])

    def test_invalid_profile_payload_is_rejected(self):
        metadata = self.load_spec("business_rules.yaml", "business_rules", "BR02")["scenarios"]["invalid"]

        response = self.api_put(
            "/placement/api/profile/",
            user=self.student_user,
            data={
                "first_name": "",
                "last_name": "",
                "email": "not-an-email",
                "phone_no": "123",
                "address": "",
                "about_me": "",
            },
            format="multipart",
        )

        self.assertEqual(metadata["_scenario"], "Invalid")
        self.assertEqual(response.status_code, 400)
        self.assertIn("field_errors", response.data)
        self.assertIn("phone_no", response.data["field_errors"])


class TestBR03_NoDuplicateApplication(PlacementCellSpecBase):
    def test_valid_first_application_succeeds(self):
        metadata = self.load_spec("business_rules.yaml", "business_rules", "BR03")["scenarios"]["valid"]
        student = self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(company_name="Rule Corp")

        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )

        self.assertEqual(metadata["_scenario"], "Valid")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PlacementApplication.objects.filter(schedule=schedule, student=student).exists())

    def test_invalid_duplicate_application_is_rejected(self):
        metadata = self.load_spec("business_rules.yaml", "business_rules", "BR03")["scenarios"]["invalid"]
        self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(company_name="Rule Duplicate Corp")
        self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )

        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )

        self.assertEqual(metadata["_scenario"], "Invalid")
        self.assertEqual(response.status_code, 409)
        self.assertIn("already applied", response.data["detail"])


class TestPlacementPolicyManagement(PlacementCellSpecBase):
    def test_chairman_can_view_and_add_policies(self):
        self._create_officer_designation(name="placement chairman")

        create_response = self.api_post(
            "/placement/api/policies/",
            user=self.officer,
            data={
                "title": "Dream Offer Rule",
                "description": "Students with an accepted dream offer cannot continue in regular drives.",
            },
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["title"], "Dream Offer Rule")
        self.assertTrue(PlacementPolicy.objects.filter(title="Dream Offer Rule").exists())

        list_response = self.api_get("/placement/api/policies/", user=self.officer)

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data[0]["title"], "Dream Offer Rule")

    def test_chairman_can_edit_policies(self):
        self._create_officer_designation(name="placement chairman")
        policy = PlacementPolicy.objects.create(
            title="Original Rule",
            description="Original description",
            created_by=self.officer,
        )

        response = self.api_put(
            f"/placement/api/policies/{policy.id}/",
            user=self.officer,
            data={
                "title": "Updated Rule",
                "description": "Updated description",
            },
        )

        self.assertEqual(response.status_code, 200)
        policy.refresh_from_db()
        self.assertEqual(policy.title, "Updated Rule")
        self.assertEqual(policy.description, "Updated description")

    def test_non_chairman_cannot_manage_policies(self):
        response = self.api_get("/placement/api/policies/", user=self.student_user)

        self.assertEqual(response.status_code, 403)
        self.assertIn("Only placement chairman users", response.data["detail"])


class TestGeneratedBusinessRules(PlacementCellSpecBase):
    def _get_br_metadata(self, br_id, scenario_key):
        return self.load_spec("business_rules.yaml", "business_rules", br_id)["scenarios"][scenario_key]

    def _create_submitted_application(self, *, company_name="Rule Workflow Corp"):
        student = self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(company_name=company_name)
        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )
        self.assertEqual(response.status_code, 200)
        application = PlacementApplication.objects.get(schedule=schedule, student=student)
        return student, schedule, application

    def _create_rejected_appeal_context(self):
        student, schedule, application = self._create_submitted_application(company_name="Appeal Corp")
        application.status = "reject"
        application.remarks = "Rejected for rule validation"
        application.save(update_fields=["status", "remarks", "updated_at"])
        placement_status, _ = PlacementStatus.objects.get_or_create(
            notify_id=schedule.notify_id,
            unique_id=student,
            defaults={
                "invitation": "REJECTED",
                "no_of_days": 2,
            },
        )
        placement_status.invitation = "REJECTED"
        placement_status.no_of_days = 2
        placement_status.save(update_fields=["invitation", "no_of_days", "timestamp"])
        return student, schedule, application, placement_status

    def _assert_metadata_and_status(self, metadata, expected_label, response, expected_statuses):
        self.assertEqual(metadata["_scenario"], expected_label)
        self.assertIn(response.status_code, expected_statuses)

    def _run_profile_update_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        response = self.api_put(
            "/placement/api/profile/",
            user=self.student_user,
            data={
                "first_name": "Student",
                "last_name": "One",
                "email": "student1@example.com",
                "phone_no": "9876543210",
                "address": "Hostel A",
                "about_me": "Ready for placements",
            },
            format="multipart",
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        self.assertEqual(response.data["profile"]["address"], "Hostel A")

    def _run_profile_update_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_put(
            "/placement/api/profile/",
            user=self.student_user,
            data={
                "first_name": "",
                "last_name": "",
                "email": "bad-email",
                "phone_no": "123",
                "address": "",
                "about_me": "",
            },
            format="multipart",
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {400})
        self.assertIn("field_errors", response.data)

    def _run_profile_completeness_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        self._make_profile_complete(self.student_user)
        response = self.api_get("/placement/api/profile/", user=self.student_user)
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        self.assertTrue(response.data["is_complete"])

    def _run_profile_completeness_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_get("/placement/api/profile/", user=self.student_user)
        self._assert_metadata_and_status(metadata, "Invalid", response, {200})
        self.assertFalse(response.data["is_complete"])
        self.assertIn("skills", response.data["field_errors"])

    def _run_document_upload_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        response = self.api_post(
            "/placement/api/profile/",
            user=self.student_user,
            data={
                "name": "Resume",
                "document": SimpleUploadedFile("resume.pdf", b"pdf-content", content_type="application/pdf"),
            },
            format="multipart",
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {201})
        self.assertEqual(response.data["name"], "Resume")

    def _run_document_upload_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_post(
            "/placement/api/profile/",
            user=self.student_user,
            data={
                "name": "Resume",
                "document": SimpleUploadedFile("resume.exe", b"binary", content_type="application/octet-stream"),
            },
            format="multipart",
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {400})
        self.assertIn("document", response.data)

    def _run_schedule_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        response = self.api_post(
            "/placement/api/placement/",
            user=self.officer,
            data={
                "company_name": "Schedule Corp",
                "title": "Schedule Corp",
                "placement_type": "PLACEMENT",
                "ctc": "12.50",
                "description": "Campus drive",
                "placement_date": (timezone.now().date() + datetime.timedelta(days=3)).isoformat(),
                "schedule_at": "2026-04-15 10:30",
                "location": "Auditorium",
            },
            format="multipart",
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {201})
        self.assertEqual(response.data["company_name"], "Schedule Corp")

    def _run_schedule_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_post(
            "/placement/api/placement/",
            user=self.officer,
            data={
                "company_name": "Past Schedule Corp",
                "placement_type": "PLACEMENT",
                "placement_date": (timezone.now().date() - datetime.timedelta(days=1)).isoformat(),
                "schedule_at": "2026-04-01 10:30",
            },
            format="multipart",
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {400})
        self.assertIn("placement_date", response.data)

    def _run_apply_eligible_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        student = self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(company_name="Eligibility Rule Corp")
        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        self.assertTrue(PlacementApplication.objects.filter(schedule=schedule, student=student).exists())

    def _run_apply_eligible_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(company_name="Blocked Eligibility Corp")
        schedule.branch = "ECE"
        schedule.save(update_fields=["branch"])
        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {403})
        self.assertIn("not eligible", response.data["detail"])

    def _run_offer_deadline_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        student = self._get_student(self.student_user)
        schedule = self._create_schedule(company_name="Offer Deadline Corp")
        offer = PlacementStatus.objects.create(
            notify_id=schedule.notify_id,
            unique_id=student,
            invitation="PENDING",
            timestamp=timezone.now(),
            no_of_days=2,
        )
        response = self.api_post(
            f"/placement/api/offer/{offer.id}/respond/",
            user=self.student_user,
            data={"action": "ACCEPTED"},
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        offer.refresh_from_db()
        self.assertEqual(offer.invitation, "ACCEPTED")

    def _run_offer_deadline_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        student = self._get_student(self.student_user)
        schedule = self._create_schedule(company_name="Expired Offer Corp")
        offer = PlacementStatus.objects.create(
            notify_id=schedule.notify_id,
            unique_id=student,
            invitation="PENDING",
            no_of_days=1,
        )
        PlacementStatus.objects.filter(pk=offer.pk).update(timestamp=timezone.now() - datetime.timedelta(days=3))
        response = self.api_post(
            f"/placement/api/offer/{offer.id}/respond/",
            user=self.student_user,
            data={"action": "ACCEPTED"},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {403})
        self.assertIn("expired", response.data["detail"])

    def _run_duplicate_valid(self, br_id):
        self._run_apply_eligible_valid(br_id)

    def _run_duplicate_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(company_name="Duplicate Rule Corp")
        self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )
        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {409})
        self.assertIn("already applied", response.data["detail"])

    def _run_application_update_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        self._create_officer_designation()
        _, _, application = self._create_submitted_application(company_name="Status Update Corp")
        response = self.api_put(
            f"/placement/api/application-detail/{application.id}/",
            user=self.officer,
            data={"status": "shortlisted", "remarks": "Shortlisted"},
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        application.refresh_from_db()
        self.assertEqual(application.status, "shortlisted")

    def _run_application_update_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        _, _, application = self._create_submitted_application(company_name="Blocked Update Corp")
        response = self.api_put(
            f"/placement/api/application-detail/{application.id}/",
            user=self.student_user,
            data={"status": "shortlisted", "remarks": "Student cannot update"},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {403})

    @override_settings(PLACEMENT_MAX_ACTIVE_APPLICATIONS=1)
    def _run_application_limit_valid(self, br_id):
        self._run_apply_eligible_valid(br_id)

    @override_settings(PLACEMENT_MAX_ACTIVE_APPLICATIONS=1)
    def _run_application_limit_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        self._make_profile_complete(self.student_user)
        first_schedule = self._create_schedule(company_name="Limit One Corp")
        second_schedule = self._create_schedule(company_name="Limit Two Corp")
        first_response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": first_schedule.id, "responses": []},
        )
        self.assertEqual(first_response.status_code, 200)
        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": second_schedule.id, "responses": []},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {403})
        self.assertIn("active applications", response.data["detail"])

    def _run_interview_schedule_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        self._create_officer_designation()
        _, _, application = self._create_submitted_application(company_name="Interview Rule Corp")
        scheduled_at = (timezone.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
        end_datetime = (timezone.now() + datetime.timedelta(days=1, hours=1)).strftime("%Y-%m-%d %H:%M")
        response = self.api_post(
            f"/placement/api/application-detail/{application.id}/interview/",
            user=self.officer,
            data={
                "scheduled_at": scheduled_at,
                "end_datetime": end_datetime,
                "round_no": 1,
                "title": "Technical Round",
                "remarks": "Interview scheduled",
            },
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {201})
        self.assertEqual(response.data["round_no"], 1)

    def _run_interview_schedule_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        self._create_officer_designation()
        _, _, application = self._create_submitted_application(company_name="Interview Error Corp")
        response = self.api_post(
            f"/placement/api/application-detail/{application.id}/interview/",
            user=self.officer,
            data={"round_no": 1, "title": "Missing time"},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {400})
        self.assertIn("scheduled_at", response.data)

    def _run_application_tracking_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        student, _, application = self._create_submitted_application(company_name="Tracking Corp")
        PlacementInterviewSchedule.objects.create(
            application=application,
            round_no=1,
            title="Round 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            end_datetime=timezone.now() + datetime.timedelta(days=1, hours=1),
            remarks="Scheduled round",
        )
        response = self.api_get("/placement/api/my-applications/", user=self.student_user)
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        self.assertEqual(response.data["applications"][0]["company_name"], "Tracking Corp")
        self.assertIsNotNone(response.data["applications"][0]["next_interview"])
        self.assertEqual(student.id.user, self.student_user)

    def _run_application_tracking_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_get("/placement/api/my-applications/", user=self.student_user)
        self._assert_metadata_and_status(metadata, "Invalid", response, {200})
        self.assertEqual(response.data["applications"], [])

    def _run_offer_management_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        student = self._get_student(self.student_user)
        first_schedule = self._create_schedule(company_name="Offer Accept Corp")
        offer = PlacementStatus.objects.create(
            notify_id=first_schedule.notify_id,
            unique_id=student,
            invitation="PENDING",
            timestamp=timezone.now(),
            no_of_days=2,
        )
        response = self.api_post(
            f"/placement/api/offer/{offer.id}/respond/",
            user=self.student_user,
            data={"action": "ACCEPTED"},
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        offer.refresh_from_db()
        self.assertEqual(offer.invitation, "ACCEPTED")

    def _run_offer_management_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        student = self._get_student(self.student_user)
        existing_schedule = self._create_schedule(company_name="Accepted Offer Corp")
        PlacementStatus.objects.create(
            notify_id=existing_schedule.notify_id,
            unique_id=student,
            invitation="ACCEPTED",
            timestamp=timezone.now(),
            no_of_days=2,
        )
        pending_schedule = self._create_schedule(company_name="Blocked Offer Corp")
        pending_offer = PlacementStatus.objects.create(
            notify_id=pending_schedule.notify_id,
            unique_id=student,
            invitation="PENDING",
            timestamp=timezone.now(),
            no_of_days=2,
        )
        response = self.api_post(
            f"/placement/api/offer/{pending_offer.id}/respond/",
            user=self.student_user,
            data={"action": "ACCEPTED"},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {409})
        self.assertIn("accepted offer", response.data["detail"])

    def _run_notification_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        response = self.api_post(
            "/placement/api/send-notification/",
            user=self.officer,
            data={"sendTo": "All", "description": "Placement update"},
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        self.assertEqual(response.data["message"], "Notification sent successfully.")

    def _run_notification_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_post(
            "/placement/api/send-notification/",
            user=self.officer,
            data={"sendTo": "Specific", "recipient": "unknown-user", "description": "Placement update"},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {404})
        self.assertIn("recipient", response.data)

    def _run_reports_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        self._create_officer_designation()
        response = self.api_get("/placement/api/reports/", user=self.officer)
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        self.assertIn("templates", response.data)

    def _run_reports_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_get("/placement/api/reports/", user=self.student_user)
        self._assert_metadata_and_status(metadata, "Invalid", response, {403})
        self.assertIn("Only TPO and chairman users", response.data["detail"])

    def _run_auth_required_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        response = self.api_get("/placement/api/profile/", user=self.student_user)
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        self.assertIn("profile", response.data)

    def _run_auth_required_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_get("/placement/api/profile/")
        self._assert_metadata_and_status(metadata, "Invalid", response, {401, 403})

    def _run_statistics_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        student_one = self._get_student(self.student_user)
        student_two = self._get_student(self.other_student_user)
        record_one = PlacementRecord.objects.create(placement_type="PLACEMENT", name="Acme", ctc="18.00", year=2026)
        record_two = PlacementRecord.objects.create(placement_type="PLACEMENT", name="Beta", ctc="8.00", year=2025)
        StudentPlacement.objects.get_or_create(unique_id=student_one)
        StudentPlacement.objects.get_or_create(unique_id=student_two)
        student_one.studentrecord_set.create(record_id=record_one)
        student_two.studentrecord_set.create(record_id=record_two)
        response = self.api_get("/placement/api/statistics/", user=self.officer, data={"aggregate_by": "department"})
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        self.assertTrue(len(response.data) >= 1)

    def _run_statistics_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_get("/placement/api/statistics/")
        self._assert_metadata_and_status(metadata, "Invalid", response, {401, 403})

    def _run_report_schedule_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        self._create_officer_designation()
        response = self.api_post(
            "/placement/api/report-schedules/",
            user=self.officer,
            data={
                "name": "Weekly Report",
                "report_type": "custom",
                "frequency": "weekly",
                "export_format": "excel",
                "recipients": ["officer@example.com"],
            },
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {201})
        self.assertEqual(response.data["name"], "Weekly Report")

    def _run_report_schedule_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_post(
            "/placement/api/report-schedules/",
            user=self.student_user,
            data={"name": "Blocked Report"},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {403})
        self.assertIn("Only TPO and chairman users", response.data["detail"])

    def _run_registration_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        response = self.api_post(
            "/placement/api/registration/",
            user=self.officer,
            data={
                "companyName": "New Company",
                "description": "Placement partner",
                "address": "Hyderabad",
                "website": "https://company.example.com",
            },
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        self.assertEqual(response.data["companyName"], "New Company")

    def _run_registration_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_post(
            "/placement/api/registration/",
            data={"companyName": "No Auth Company"},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {401, 403})

    def _run_policy_management_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        self._create_officer_designation(name="placement chairman")
        response = self.api_post(
            "/placement/api/policies/",
            user=self.officer,
            data={
                "title": "One Offer Rule",
                "description": "Students may hold only one accepted placement offer at a time.",
            },
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {201})
        self.assertEqual(response.data["title"], "One Offer Rule")
        self.assertTrue(PlacementPolicy.objects.filter(title="One Offer Rule").exists())

    def _run_policy_management_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        response = self.api_get("/placement/api/policies/", user=self.student_user)
        self._assert_metadata_and_status(metadata, "Invalid", response, {403})
        self.assertIn("Only placement chairman users", response.data["detail"])

    def _run_alumni_profile_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        alumni_user = self._create_alumni_like_user(username="alumni_valid")
        response = self.api_post(
            "/placement/api/alumni/profile/",
            user=alumni_user,
            data={"graduation_year": 2020, "degree": "B.Tech", "current_company": "Alumni Corp"},
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {201})
        self.assertEqual(response.data["graduation_year"], 2020)

    def _run_alumni_profile_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        alumni_user = self._create_alumni_like_user(username="alumni_pending")
        create_response = self.api_post(
            "/placement/api/alumni/profile/",
            user=alumni_user,
            data={"graduation_year": 2021, "degree": "B.Tech"},
        )
        self.assertEqual(create_response.status_code, 201)
        response = self.api_put(
            "/placement/api/alumni/profile/",
            user=alumni_user,
            data={"degree": "M.Tech"},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {403})
        self.assertIn("awaiting approval", response.data["detail"])

    def _create_alumni_like_user(self, *, username):
        user = self._create_student_user(
            roll_no=f"AL{username[:6]}",
            username=username,
            department=self.department_cse,
        )
        extra = user.extrainfo
        extra.user_type = "faculty"
        extra.save(update_fields=["user_type"])
        Student.objects.filter(id=extra).delete()
        return user

    def _run_appeal_create_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        _, _, _, placement_status = self._create_rejected_appeal_context()
        response = self.api_post(
            "/placement/api/placement-appeals/",
            user=self.student_user,
            data={"placement_status": placement_status.id, "reason": "Please review the rejection"},
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {201})
        self.assertEqual(response.data["status"], "pending")

    def _run_appeal_create_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        _, _, _, placement_status = self._create_rejected_appeal_context()
        response = self.api_post(
            "/placement/api/placement-appeals/",
            user=self.student_user,
            data={"placement_status": placement_status.id, "reason": ""},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {400})
        self.assertIn("reason", response.data)

    def _run_appeal_review_valid(self, br_id):
        metadata = self._get_br_metadata(br_id, "valid")
        self._create_officer_designation()
        _, _, _, placement_status = self._create_rejected_appeal_context()
        create_response = self.api_post(
            "/placement/api/placement-appeals/",
            user=self.student_user,
            data={"placement_status": placement_status.id, "reason": "Please review"},
        )
        self.assertEqual(create_response.status_code, 201)
        appeal = PlacementAppeal.objects.get(pk=create_response.data["id"])
        response = self.api_put(
            f"/placement/api/placement-appeals/{appeal.id}/",
            user=self.officer,
            data={"status": "reviewed", "response": "Reviewed by TPO"},
        )
        self._assert_metadata_and_status(metadata, "Valid", response, {200})
        self.assertEqual(response.data["status"], "reviewed")

    def _run_appeal_review_invalid(self, br_id):
        metadata = self._get_br_metadata(br_id, "invalid")
        self._create_officer_designation()
        _, _, _, placement_status = self._create_rejected_appeal_context()
        create_response = self.api_post(
            "/placement/api/placement-appeals/",
            user=self.student_user,
            data={"placement_status": placement_status.id, "reason": "Please review"},
        )
        self.assertEqual(create_response.status_code, 201)
        appeal = PlacementAppeal.objects.get(pk=create_response.data["id"])
        response = self.api_put(
            f"/placement/api/placement-appeals/{appeal.id}/",
            user=self.student_user,
            data={"status": "reviewed", "response": "Student cannot review"},
        )
        self._assert_metadata_and_status(metadata, "Invalid", response, {403, 404})


_BR_HELPERS = {
    "BR04": ("_run_profile_update_valid", "_run_profile_update_invalid"),
    "BR05": ("_run_profile_completeness_valid", "_run_profile_completeness_invalid"),
    "BR06": ("_run_schedule_valid", "_run_schedule_invalid"),
    "BR07": ("_run_apply_eligible_valid", "_run_apply_eligible_invalid"),
    "BR08": ("_run_offer_deadline_valid", "_run_offer_deadline_invalid"),
    "BR09": ("_run_duplicate_valid", "_run_duplicate_invalid"),
    "BR10": ("_run_application_update_valid", "_run_application_update_invalid"),
    "BR11": ("_run_application_limit_valid", "_run_application_limit_invalid"),
    "BR12": ("_run_schedule_valid", "_run_schedule_invalid"),
    "BR13": ("_run_interview_schedule_valid", "_run_interview_schedule_invalid"),
    "BR14": ("_run_application_update_valid", "_run_application_update_invalid"),
    "BR15": ("_run_application_tracking_valid", "_run_application_tracking_invalid"),
    "BR16": ("_run_offer_management_valid", "_run_offer_management_invalid"),
    "BR17": ("_run_appeal_create_valid", "_run_appeal_create_invalid"),
    "BR18": ("_run_notification_valid", "_run_notification_invalid"),
    "BR19": ("_run_notification_valid", "_run_notification_invalid"),
    "BR20": ("_run_notification_valid", "_run_auth_required_invalid"),
    "BR21": ("_run_notification_valid", "_run_notification_invalid"),
    "BR22": ("_run_reports_valid", "_run_reports_invalid"),
    "BR23": ("_run_reports_valid", "_run_reports_invalid"),
    "BR24": ("_run_auth_required_valid", "_run_auth_required_invalid"),
    "BR25": ("_run_statistics_valid", "_run_statistics_invalid"),
    "BR26": ("_run_report_schedule_valid", "_run_report_schedule_invalid"),
    "BR27": ("_run_registration_valid", "_run_registration_invalid"),
    "BR28": ("_run_profile_update_valid", "_run_profile_update_invalid"),
    "BR29": ("_run_reports_valid", "_run_reports_invalid"),
    "BR30": ("_run_reports_valid", "_run_reports_invalid"),
    "BR31": ("_run_alumni_profile_valid", "_run_alumni_profile_invalid"),
    "BR32": ("_run_statistics_valid", "_run_statistics_invalid"),
    "BR33": ("_run_profile_completeness_valid", "_run_profile_completeness_invalid"),
    "BR34": ("_run_notification_valid", "_run_notification_invalid"),
    "BR35": ("_run_registration_valid", "_run_registration_invalid"),
    "BR36": ("_run_application_update_valid", "_run_application_update_invalid"),
    "BR37": ("_run_statistics_valid", "_run_statistics_invalid"),
    "BR38": ("_run_appeal_review_valid", "_run_appeal_review_invalid"),
    "BR39": ("_run_notification_valid", "_run_notification_invalid"),
    "BR40": ("_run_appeal_review_valid", "_run_appeal_review_invalid"),
}


def _make_generated_br_test(br_id, helper_name):
    def _test(self):
        getattr(self, helper_name)(br_id)

    return _test


for _br_id, (_valid_helper, _invalid_helper) in _BR_HELPERS.items():
    setattr(
        TestGeneratedBusinessRules,
        f"test_{_br_id.lower()}_valid_rule_is_enforced",
        _make_generated_br_test(_br_id, _valid_helper),
    )
    setattr(
        TestGeneratedBusinessRules,
        f"test_{_br_id.lower()}_invalid_rule_is_rejected",
        _make_generated_br_test(_br_id, _invalid_helper),
    )
