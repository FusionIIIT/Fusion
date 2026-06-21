import datetime

import yaml

from applications.academic_information.models import Student
from applications.placement_cell.models import (
    PlacementApplication,
    PlacementInterviewSchedule,
    PlacementRecord,
    PlacementStatus,
    StudentPlacement,
)
from applications.placement_cell.tests.conftest import PlacementCellSpecBase


class TestWorkflowCatalogIntegrity(PlacementCellSpecBase):
    def test_all_documented_workflows_define_two_scenarios(self):
        with (self.specs_dir / "workflows.yaml").open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        workflows = payload.get("workflows", [])
        self.assertGreaterEqual(len(workflows), 10)

        for workflow in workflows:
            self.assertIn("source_section", workflow)
            self.assertTrue(workflow.get("steps"))
            self.assertEqual(sorted(workflow.get("scenarios", {}).keys()), ["end_to_end", "negative"])

    def test_workflow_test_ids_are_unique(self):
        with (self.specs_dir / "workflows.yaml").open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        test_ids = []
        for workflow in payload.get("workflows", []):
            for scenario in workflow.get("scenarios", {}).values():
                test_ids.append(scenario["_test_id"])

        self.assertEqual(len(test_ids), len(set(test_ids)))


class TestGeneratedWorkflows(PlacementCellSpecBase):
    def _wf_metadata(self, wf_id, scenario_key):
        return self.load_spec("workflows.yaml", "workflows", wf_id)["scenarios"][scenario_key]

    def _assert_metadata(self, metadata, label):
        self.assertEqual(metadata["_scenario"], label)

    def _create_submitted_application(self, *, company_name):
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

    def _seed_statistics_record(self, *, user, company_name, ctc="18.00", year=2026):
        student = self._get_student(user)
        StudentPlacement.objects.get_or_create(unique_id=student)
        record = PlacementRecord.objects.create(
            placement_type="PLACEMENT",
            name=company_name,
            ctc=ctc,
            year=year,
        )
        student.studentrecord_set.create(record_id=record)
        return record

    def _wf01_end_to_end(self):
        metadata = self._wf_metadata("WF01", "end_to_end")
        self._create_officer_designation()
        student, schedule, application = self._create_submitted_application(company_name="WF01 Corp")

        update_response = self.api_put(
            f"/placement/api/application-detail/{application.id}/",
            user=self.officer,
            data={"status": "offer_released", "remarks": "Offer released"},
        )
        offers_response = self.api_get("/placement/api/my-offers/", user=self.student_user)

        self._assert_metadata(metadata, "End-to-End")
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(offers_response.status_code, 200)
        self.assertEqual(len(offers_response.data["offers"]), 1)
        self.assertEqual(offers_response.data["offers"][0]["company_name"], schedule.notify_id.company_name)
        self.assertEqual(application.student, student)

    def _wf01_negative(self):
        metadata = self._wf_metadata("WF01", "negative")
        schedule = self._create_schedule(company_name="WF01 Blocked Corp")
        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )

        self._assert_metadata(metadata, "Negative")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Placement profile is incomplete", response.data["detail"])

    def _wf02_end_to_end(self):
        metadata = self._wf_metadata("WF02", "end_to_end")
        schedule = self._create_schedule(company_name="WF02 Corp")

        self._make_profile_complete(self.student_user)
        profile_response = self.api_get("/placement/api/profile/", user=self.student_user)
        summary_response = self.api_get("/placement/api/profile/", user=self.student_user)
        apply_response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )

        self._assert_metadata(metadata, "End-to-End")
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(summary_response.status_code, 200)
        self.assertTrue(summary_response.data["is_complete"])
        self.assertEqual(apply_response.status_code, 200)
        self.assertEqual(apply_response.data["message"], "Application submitted successfully.")

    def _wf02_negative(self):
        metadata = self._wf_metadata("WF02", "negative")
        schedule = self._create_schedule(company_name="WF02 Blocked Corp")
        response = self.api_post(
            "/placement/api/apply-for-placement/",
            user=self.student_user,
            data={"jobId": schedule.id, "responses": []},
        )

        self._assert_metadata(metadata, "Negative")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Placement profile is incomplete", response.data["detail"])

    def _wf03_end_to_end(self):
        metadata = self._wf_metadata("WF03", "end_to_end")
        StudentPlacement.objects.create(unique_id=self._get_student(self.student_user), future_aspect="PLACEMENT")
        create_response = self.api_post(
            "/placement/api/placement/",
            user=self.officer,
            data={
                "company_name": "WF03 Corp",
                "title": "WF03 Corp",
                "placement_type": "PLACEMENT",
                "ctc": "15.00",
                "description": "Campus drive",
                "placement_date": (datetime.date.today() + datetime.timedelta(days=3)).isoformat(),
                "schedule_at": "2026-04-15 10:30",
                "location": "Auditorium",
            },
            format="multipart",
        )
        list_response = self.api_get("/placement/api/placement/", user=self.student_user)

        self._assert_metadata(metadata, "End-to-End")
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(list_response.status_code, 200)
        self.assertIn("WF03 Corp", [row["company_name"] for row in list_response.data])

    def _wf03_negative(self):
        metadata = self._wf_metadata("WF03", "negative")
        response = self.api_post(
            "/placement/api/placement/",
            user=self.officer,
            data={
                "company_name": "WF03 Past Corp",
                "placement_type": "PLACEMENT",
                "placement_date": (datetime.date.today() - datetime.timedelta(days=1)).isoformat(),
                "schedule_at": "2026-04-01 10:30",
            },
            format="multipart",
        )

        self._assert_metadata(metadata, "Negative")
        self.assertEqual(response.status_code, 400)
        self.assertIn("placement_date", response.data)

    def _wf04_end_to_end(self):
        metadata = self._wf_metadata("WF04", "end_to_end")
        self._create_officer_designation()
        _, _, application = self._create_submitted_application(company_name="WF04 Corp")

        schedule_response = self.api_post(
            f"/placement/api/application-detail/{application.id}/interview/",
            user=self.officer,
            data={
                "scheduled_at": (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
                "end_datetime": (datetime.datetime.now() + datetime.timedelta(days=1, hours=1)).strftime("%Y-%m-%d %H:%M"),
                "round_no": 1,
                "title": "Technical Interview",
                "remarks": "Interview scheduled",
            },
        )
        applications_response = self.api_get("/placement/api/my-applications/", user=self.student_user)

        self._assert_metadata(metadata, "End-to-End")
        self.assertEqual(schedule_response.status_code, 201)
        self.assertEqual(applications_response.status_code, 200)
        self.assertIsNotNone(applications_response.data["applications"][0]["next_interview"])
        self.assertEqual(applications_response.data["applications"][0]["next_interview"]["title"], "Technical Interview")

    def _wf04_negative(self):
        metadata = self._wf_metadata("WF04", "negative")
        self._create_officer_designation()
        _, _, application = self._create_submitted_application(company_name="WF04 Invalid Corp")
        response = self.api_post(
            f"/placement/api/application-detail/{application.id}/interview/",
            user=self.officer,
            data={"round_no": 1, "title": "Missing datetime"},
        )

        self._assert_metadata(metadata, "Negative")
        self.assertEqual(response.status_code, 400)
        self.assertIn("scheduled_at", response.data)

    def _wf05_end_to_end(self):
        metadata = self._wf_metadata("WF05", "end_to_end")
        self._create_officer_designation()
        student, schedule, application = self._create_submitted_application(company_name="WF05 Corp")
        apply_response = self.api_put(
            f"/placement/api/application-detail/{application.id}/",
            user=self.officer,
            data={"status": "offer_released", "remarks": "Offer issued"},
        )
        offers_response = self.api_get("/placement/api/my-offers/", user=self.student_user)

        self._assert_metadata(metadata, "End-to-End")
        self.assertEqual(apply_response.status_code, 200)
        self.assertEqual(offers_response.status_code, 200)
        self.assertEqual(len(offers_response.data["offers"]), 1)
        self.assertEqual(offers_response.data["offers"][0]["company_name"], "WF05 Corp")
        self.assertEqual(student.id.user, self.student_user)
        self.assertEqual(schedule.notify_id.company_name, "WF05 Corp")

    def _wf05_negative(self):
        metadata = self._wf_metadata("WF05", "negative")
        student, schedule, _ = self._create_submitted_application(company_name="WF05 Pending Corp")
        offers_response = self.api_get("/placement/api/my-offers/", user=self.student_user)

        self._assert_metadata(metadata, "Negative")
        self.assertEqual(offers_response.status_code, 200)
        self.assertEqual(offers_response.data["offers"], [])
        self.assertEqual(student.id.user, self.student_user)
        self.assertEqual(schedule.notify_id.company_name, "WF05 Pending Corp")

    def _wf06_end_to_end(self):
        metadata = self._wf_metadata("WF06", "end_to_end")
        create_response = self.api_post(
            "/placement/api/registration/",
            user=self.officer,
            data={
                "companyName": "WF06 Company",
                "description": "Placement partner",
                "address": "Hyderabad",
                "website": "https://wf06.example.com",
            },
        )
        list_response = self.api_get("/placement/api/registration/", user=self.officer)

        self._assert_metadata(metadata, "End-to-End")
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(list_response.status_code, 200)
        self.assertIn("WF06 Company", [row["companyName"] for row in list_response.data])

    def _wf06_negative(self):
        metadata = self._wf_metadata("WF06", "negative")
        response = self.api_post(
            "/placement/api/registration/",
            data={"companyName": "Blocked WF06 Company"},
        )

        self._assert_metadata(metadata, "Negative")
        self.assertIn(response.status_code, (401, 403))

    def _wf07_end_to_end(self):
        metadata = self._wf_metadata("WF07", "end_to_end")
        self._create_officer_designation()
        alumni_user = self._create_alumni_like_user(username="wf07alumni")

        create_response = self.api_post(
            "/placement/api/alumni/profile/",
            user=alumni_user,
            data={"graduation_year": 2020, "degree": "B.Tech", "current_company": "WF07 Corp"},
        )
        approve_response = self.api_put(
            f"/placement/api/alumni/verification/{create_response.data['id']}/",
            user=self.officer,
            data={"status": "approved", "verification_notes": "Verified"},
        )
        profile_response = self.api_get("/placement/api/alumni/profile/", user=alumni_user)

        self._assert_metadata(metadata, "End-to-End")
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(profile_response.status_code, 200)
        self.assertTrue(profile_response.data["can_access"])

    def _wf07_negative(self):
        metadata = self._wf_metadata("WF07", "negative")
        alumni_user = self._create_alumni_like_user(username="wf07pending")
        create_response = self.api_post(
            "/placement/api/alumni/profile/",
            user=alumni_user,
            data={"graduation_year": 2021, "degree": "B.Tech"},
        )
        update_response = self.api_put(
            "/placement/api/alumni/profile/",
            user=alumni_user,
            data={"degree": "M.Tech"},
        )

        self._assert_metadata(metadata, "Negative")
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(update_response.status_code, 403)
        self.assertIn("awaiting approval", update_response.data["detail"])

    def _wf08_end_to_end(self):
        metadata = self._wf_metadata("WF08", "end_to_end")
        response = self.api_post(
            "/placement/api/send-notification/",
            user=self.officer,
            data={"sendTo": "All", "description": "WF08 notification"},
        )

        self._assert_metadata(metadata, "End-to-End")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Notification sent successfully.")

    def _wf08_negative(self):
        metadata = self._wf_metadata("WF08", "negative")
        response = self.api_post(
            "/placement/api/send-notification/",
            user=self.officer,
            data={"sendTo": "Specific", "recipient": "missing-user", "description": "WF08 notification"},
        )

        self._assert_metadata(metadata, "Negative")
        self.assertEqual(response.status_code, 404)
        self.assertIn("recipient", response.data)

    def _wf09_end_to_end(self):
        metadata = self._wf_metadata("WF09", "end_to_end")
        StudentPlacement.objects.create(unique_id=self._get_student(self.student_user), future_aspect="PLACEMENT")
        self._create_schedule(company_name="WF09 Corp")
        response = self.api_get("/placement/api/placement/", user=self.student_user)

        self._assert_metadata(metadata, "End-to-End")
        self.assertEqual(response.status_code, 200)
        self.assertIn("WF09 Corp", [row["company_name"] for row in response.data])

    def _wf09_negative(self):
        metadata = self._wf_metadata("WF09", "negative")
        response = self.api_get("/placement/api/placement/")

        self._assert_metadata(metadata, "Negative")
        self.assertIn(response.status_code, (401, 403))

    def _wf10_end_to_end(self):
        metadata = self._wf_metadata("WF10", "end_to_end")
        self._create_officer_designation()
        self._seed_statistics_record(user=self.student_user, company_name="WF10 Corp")
        response = self.api_get(
            "/placement/api/reports/",
            user=self.officer,
            data={"report_type": "company"},
        )

        self._assert_metadata(metadata, "End-to-End")
        self.assertEqual(response.status_code, 200)
        self.assertIn("rows", response.data)
        self.assertEqual(response.data["rows"][0]["company"], "WF10 Corp")

    def _wf10_negative(self):
        metadata = self._wf_metadata("WF10", "negative")
        response = self.api_get("/placement/api/reports/", user=self.student_user)

        self._assert_metadata(metadata, "Negative")
        self.assertEqual(response.status_code, 403)
        self.assertIn("Only TPO and chairman users", response.data["detail"])


_WF_HELPERS = {
    "WF01": ("_wf01_end_to_end", "_wf01_negative"),
    "WF02": ("_wf02_end_to_end", "_wf02_negative"),
    "WF03": ("_wf03_end_to_end", "_wf03_negative"),
    "WF04": ("_wf04_end_to_end", "_wf04_negative"),
    "WF05": ("_wf05_end_to_end", "_wf05_negative"),
    "WF06": ("_wf06_end_to_end", "_wf06_negative"),
    "WF07": ("_wf07_end_to_end", "_wf07_negative"),
    "WF08": ("_wf08_end_to_end", "_wf08_negative"),
    "WF09": ("_wf09_end_to_end", "_wf09_negative"),
    "WF10": ("_wf10_end_to_end", "_wf10_negative"),
}


def _make_generated_workflow_test(helper_name):
    def _test(self):
        getattr(self, helper_name)()

    return _test


for _wf_id, (_e2e_helper, _negative_helper) in _WF_HELPERS.items():
    setattr(
        TestGeneratedWorkflows,
        f"test_{_wf_id.lower()}_end_to_end_workflow",
        _make_generated_workflow_test(_e2e_helper),
    )
    setattr(
        TestGeneratedWorkflows,
        f"test_{_wf_id.lower()}_negative_workflow_path",
        _make_generated_workflow_test(_negative_helper),
    )
