import datetime

from django.contrib.auth.models import User
from django.core.cache import cache
import yaml
from django.utils import timezone

from applications.globals.models import Designation, HoldsDesignation
from applications.placement_cell.models import (
    PlacementApplication,
    StudentPlacement,
)
from applications.placement_cell.tests.conftest import PlacementCellSpecBase


class TestUseCaseCatalogIntegrity(PlacementCellSpecBase):
    def test_all_documented_use_cases_define_three_scenarios(self):
        with (self.specs_dir / "use_cases.yaml").open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        use_cases = payload.get("use_cases", [])
        self.assertGreaterEqual(len(use_cases), 20)

        for use_case in use_cases:
            self.assertIn("source_id", use_case)
            self.assertIn("endpoint", use_case)
            self.assertIn("method", use_case)
            self.assertEqual(
                sorted(use_case.get("scenarios", {}).keys()),
                ["alternate_path", "exception_path", "happy_path"],
            )

    def test_use_case_test_ids_are_unique(self):
        with (self.specs_dir / "use_cases.yaml").open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        test_ids = []
        for use_case in payload.get("use_cases", []):
            for scenario in use_case.get("scenarios", {}).values():
                test_ids.append(scenario["_test_id"])

        self.assertEqual(len(test_ids), len(set(test_ids)))


class TestUC01_ProfileManagement(PlacementCellSpecBase):
    def test_happy_path_student_can_update_profile(self):
        metadata = self.load_spec("use_cases.yaml", "use_cases", "UC01")["scenarios"]["happy_path"]
        self._make_profile_complete(self.student_user)
        response = self.api_get("/placement/api/profile/", user=self.student_user)

        self.assertEqual(metadata["_scenario"], "Happy Path")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_complete"])
        self.assertEqual(response.data["profile"]["address"], "Hostel A")

    def test_alternate_path_student_can_view_profile_payload(self):
        metadata = self.load_spec("use_cases.yaml", "use_cases", "UC01")["scenarios"]["alternate_path"]
        self._create_schedule(company_name="Profile Linked Corp")
        response = self.api_get("/placement/api/profile/", user=self.student_user)

        self.assertEqual(metadata["_scenario"], "Alternate Path")
        self.assertEqual(response.status_code, 200)
        self.assertIn("profile", response.data)
        self.assertIn("eligibility_summary", response.data)
        self.assertEqual(response.data["eligibility_summary"]["eligible_count"], 1)
        self.assertIn("documents", response.data["field_errors"])

    def test_exception_path_invalid_profile_payload_is_rejected(self):
        metadata = self.load_spec("use_cases.yaml", "use_cases", "UC01")["scenarios"]["exception_path"]

        response = self.api_put(
            "/placement/api/profile/",
            user=self.student_user,
            data={
                "first_name": "",
                "last_name": "",
                "email": "invalid-email",
                "phone_no": "123",
                "address": "",
                "about_me": "",
            },
            format="multipart",
        )

        self.assertEqual(metadata["_scenario"], "Exception Path")
        self.assertEqual(response.status_code, 400)
        self.assertIn("field_errors", response.data)
        self.assertIn("email", response.data["field_errors"])


class TestUC02_BrowseAndSearchJobs(PlacementCellSpecBase):
    def test_happy_path_student_sees_upcoming_opportunities(self):
        metadata = self.load_spec("use_cases.yaml", "use_cases", "UC02")["scenarios"]["happy_path"]
        StudentPlacement.objects.create(unique_id=self._get_student(self.student_user), future_aspect="PLACEMENT")
        expected_schedule = self._create_schedule(company_name="Future Corp")
        past_schedule = self._create_schedule(
            company_name="Past Corp",
            placement_date=timezone.now().date() - datetime.timedelta(days=1),
        )

        response = self.api_get("/placement/api/placement/", user=self.student_user)

        self.assertEqual(metadata["_scenario"], "Happy Path")
        self.assertEqual(response.status_code, 200)
        returned_ids = {int(row["id"]) for row in response.data}
        self.assertIn(expected_schedule.id, returned_ids)
        self.assertIn(past_schedule.id, returned_ids)

    def test_alternate_path_filters_opportunities(self):
        metadata = self.load_spec("use_cases.yaml", "use_cases", "UC02")["scenarios"]["alternate_path"]
        self._create_schedule(company_name="Alpha Corp", location="Bangalore", ctc="22.00")
        self._create_schedule(company_name="Beta Labs", location="Delhi", ctc="12.00")

        response = self.api_get(
            "/placement/api/placement/",
            user=self.officer,
            data={"company": "Alpha", "location": "Bangalore", "min_package": "20"},
        )

        self.assertEqual(metadata["_scenario"], "Alternate Path")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["company_name"], "Alpha Corp")

    def test_tpo_can_see_jobs_posted_by_another_tpo(self):
        self._create_officer_designation("placement officer")
        other_tpo = User.objects.create_user(
            username="other_tpo",
            password="password",
            email="other_tpo@example.com",
        )
        self._create_officer_designation_for_user(other_tpo, "placement officer")
        shared_schedule = self._create_schedule(company_name="Shared TPO Job")

        response = self.api_get("/placement/api/placement/", user=other_tpo)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            shared_schedule.id,
            {int(row["id"]) for row in response.data},
        )

    def test_tpo_can_see_past_job_postings(self):
        self._create_officer_designation("placement officer")
        past_schedule = self._create_schedule(
            company_name="Past Admin Job",
            placement_date=timezone.now().date() - datetime.timedelta(days=2),
        )

        response = self.api_get("/placement/api/placement/", user=self.officer)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            past_schedule.id,
            {int(row["id"]) for row in response.data},
        )

    def test_tpo_designation_takes_precedence_over_student_designation(self):
        self._create_officer_designation("placement officer")
        self._make_profile_complete(self.student_user)
        HoldsDesignation.objects.create(
            user=self.student_user,
            working=self.student_user,
            designation=Designation.objects.get(name="placement officer"),
        )
        cache.set(f"last_selected_role_{self.student_user.id}", "placement officer", None)
        past_schedule = self._create_schedule(
            company_name="Mixed Role Admin Job",
            placement_date=timezone.now().date() - datetime.timedelta(days=2),
        )

        response = self.api_get("/placement/api/placement/", user=self.student_user)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            past_schedule.id,
            {int(row["id"]) for row in response.data},
        )

    def test_student_selected_role_keeps_applied_state_for_mixed_role_user(self):
        self._create_officer_designation("placement officer")
        student = self._make_profile_complete(self.student_user)
        HoldsDesignation.objects.create(
            user=self.student_user,
            working=self.student_user,
            designation=Designation.objects.get(name="placement officer"),
        )
        schedule = self._create_schedule(company_name="Applied State Job")
        PlacementApplication.objects.create(
            schedule=schedule,
            student=student,
            status="pending",
        )
        cache.set(f"last_selected_role_{self.student_user.id}", "student", None)

        response = self.api_get("/placement/api/placement/", user=self.student_user)

        self.assertEqual(response.status_code, 200)
        matched = next(item for item in response.data if int(item["id"]) == schedule.id)
        self.assertTrue(matched["check"])

    def test_exception_path_returns_empty_list_when_no_jobs_are_available(self):
        metadata = self.load_spec("use_cases.yaml", "use_cases", "UC02")["scenarios"]["exception_path"]
        response = self.api_get("/placement/api/placement/", user=self.student_user)

        self.assertEqual(metadata["_scenario"], "Exception Path")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])


class TestUC03_ApplyForPlacementOpportunity(PlacementCellSpecBase):
    def test_happy_path_student_can_submit_application(self):
        metadata = self.load_spec("use_cases.yaml", "use_cases", "UC03")["scenarios"]["happy_path"]
        student = self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(company_name="Apply Corp")

        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )

        self.assertEqual(metadata["_scenario"], "Happy Path")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Application submitted successfully.")
        self.assertTrue(PlacementApplication.objects.filter(schedule=schedule, student=student).exists())

    def test_alternate_path_ineligible_student_cannot_apply(self):
        metadata = self.load_spec("use_cases.yaml", "use_cases", "UC03")["scenarios"]["alternate_path"]
        self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(company_name="Eligibility Corp")
        schedule.branch = "ECE"
        schedule.save(update_fields=["branch"])

        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )

        self.assertEqual(metadata["_scenario"], "Alternate Path")
        self.assertEqual(response.status_code, 403)
        self.assertIn("You are not eligible for this job posting.", response.data["detail"])
        self.assertIn("Branch requirement not met.", response.data["errors"])

    def test_exception_path_duplicate_application_is_rejected(self):
        metadata = self.load_spec("use_cases.yaml", "use_cases", "UC03")["scenarios"]["exception_path"]
        self._make_profile_complete(self.student_user)
        schedule = self._create_schedule(company_name="Duplicate Corp")
        first_response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )

        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(metadata["_scenario"], "Exception Path")
        self.assertEqual(response.status_code, 409)
        self.assertIn("already applied", response.data["detail"])
