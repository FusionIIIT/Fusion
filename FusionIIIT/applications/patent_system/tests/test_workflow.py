from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from applications.patent_system.models import Applicant, Application, Attorney, CommunicationLog, AssociatedWith


class PatentWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.pcc_admin = User.objects.create_user(
            username="pccadmin", email="pcc@example.com", password="pass1234"
        )
        self.director = User.objects.create_user(
            username="director", email="director@example.com", password="pass1234"
        )
        self.attorney_user = User.objects.create_user(
            username="attorney", email="attorney@example.com", password="pass1234"
        )
        self.applicant_user = User.objects.create_user(
            username="applicant", email="applicant@example.com", password="pass1234"
        )

        self.applicant = Applicant.objects.create(
            user=self.applicant_user,
            name="Applicant One",
            email="applicant.personal@example.com",
            mobile="9999999999",
            address="Campus",
        )

        self.attorney = Attorney.objects.create(
            name="External Counsel",
            email="attorney@example.com",
            phone="9998887777",
            firm_name="Counsel LLP",
        )

        self.application = Application.objects.create(
            primary_applicant=self.applicant,
            title="Smart Patent",
            status="Submitted",
            decision_status="Pending",
            submitted_date=date.today(),
        )

    def test_pcc_review_updates_status_and_owner(self):
        self.client.force_authenticate(user=self.pcc_admin)

        response = self.client.post(
            f"/patentsystem/pccAdmin/applications/new/review/{self.application.id}/",
            {"comments": "Reviewed and ready"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "Reviewed by PCC Admin")
        self.assertEqual(self.application.assigned_pcc_admin, self.pcc_admin)
        self.assertEqual(self.application.comments, "Reviewed and ready")

    def test_pcc_forward_creates_communication_log(self):
        self.application.status = "Reviewed by PCC Admin"
        self.application.assigned_pcc_admin = self.pcc_admin
        self.application.save()

        self.client.force_authenticate(user=self.pcc_admin)

        response = self.client.post(
            f"/patentsystem/pccAdmin/applications/new/forward/{self.application.id}/",
            {
                "attorney_name": "External Counsel",
                "attorney_email": "external@example.com",
                "comments": "Forwarding for director approval",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "Forwarded for Director's Review")
        self.assertEqual(self.application.assigned_pcc_admin, self.pcc_admin)

        self.assertEqual(CommunicationLog.objects.filter(application=self.application).count(), 1)
        log = CommunicationLog.objects.get(application=self.application)
        self.assertEqual(log.external_attorney_name, "External Counsel")
        self.assertEqual(log.external_attorney_email, "external@example.com")

    def test_change_status_rejects_invalid_transition_target(self):
        self.client.force_authenticate(user=self.pcc_admin)

        response = self.client.post(
            f"/patentsystem/pccAdmin/applications/ongoing/changeStatus/{self.application.id}/",
            {"next_status": "Not A Valid Status"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid next_status", response.json().get("error", ""))

    def test_director_accept_sets_director_approval_received(self):
        self.application.status = "Forwarded for Director's Review"
        self.application.assigned_pcc_admin = self.pcc_admin
        self.application.attorney = self.attorney
        self.application.save()

        self.client.force_authenticate(user=self.director)
        response = self.client.post(
            "/patentsystem/director/application/accept",
            {"application_id": self.application.id, "comments": "Approved"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "Attorney Assigned")
        self.assertEqual(self.application.decision_status, "Pending")
        self.assertTrue(bool(self.application.token_no))
        self.assertEqual(self.application.attorney, self.attorney)

    def test_pcc_forward_requires_reviewed_status(self):
        self.client.force_authenticate(user=self.pcc_admin)

        response = self.client.post(
            f"/patentsystem/pccAdmin/applications/new/forward/{self.application.id}/",
            {
                "attorney_name": "External Counsel",
                "attorney_email": "external@example.com",
                "comments": "Forwarding for director approval",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Reviewed by PCC Admin", response.json().get("error", ""))

    def test_change_status_requires_sequential_transition(self):
        self.application.status = "Forwarded for Director's Review"
        self.application.assigned_pcc_admin = self.pcc_admin
        self.application.save()
        self.client.force_authenticate(user=self.pcc_admin)

        response = self.client.post(
            f"/patentsystem/pccAdmin/applications/ongoing/changeStatus/{self.application.id}/",
            {"next_status": "Patent Filed"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid status transition", response.json().get("error", ""))

    def test_director_reject_requires_forwarded_status(self):
        self.application.status = "Submitted"
        self.application.save()
        self.client.force_authenticate(user=self.director)

        response = self.client.post(
            "/patentsystem/director/application/reject",
            {"application_id": self.application.id},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Forwarded for Director's Review", response.json().get("error", ""))

    def test_director_reject_maps_to_patent_refused(self):
        self.application.status = "Forwarded for Director's Review"
        self.application.save()

        self.client.force_authenticate(user=self.director)
        response = self.client.post(
            "/patentsystem/director/application/reject",
            {"application_id": self.application.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "Needs Revision")
        self.assertEqual(self.application.decision_status, "Needs Revision")

    def test_attorney_forward_returns_to_director(self):
        self.application.status = "Attorney Assigned"
        self.application.attorney = self.attorney
        self.application.save()

        self.client.force_authenticate(user=self.attorney_user)
        response = self.client.post(
            f"/patentsystem/attorney/applications/{self.application.id}/forward/",
            {"comments": "Patentability assessment completed"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "Returned to Director")
        self.assertEqual(self.application.attorney_review_notes, "Patentability assessment completed")

    def test_attorney_forward_requires_comments(self):
        self.application.status = "Attorney Assigned"
        self.application.attorney = self.attorney
        self.application.save()

        self.client.force_authenticate(user=self.attorney_user)
        response = self.client.post(
            f"/patentsystem/attorney/applications/{self.application.id}/forward/",
            {"comments": ""},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Comments are required", response.json().get("error", ""))

    def test_communication_log_post_and_get(self):
        self.client.force_authenticate(user=self.pcc_admin)

        create_response = self.client.post(
            f"/patentsystem/pccAdmin/applications/{self.application.id}/communication-logs/",
            {
                "external_attorney_name": "Counsel One",
                "external_attorney_email": "counsel@example.com",
                "message_content": "Shared claim draft",
                "status_or_notes": "Awaiting feedback",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)

        list_response = self.client.get(
            f"/patentsystem/pccAdmin/applications/{self.application.id}/communication-logs/"
        )
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(list_response.json()[0]["message_content"], "Shared claim draft")

    def test_same_applicant_can_file_multiple_patents(self):
        second_application = Application.objects.create(
            primary_applicant=self.applicant,
            title="Second Patent Filing",
            status="Submitted",
            decision_status="Pending",
            submitted_date=date.today(),
        )

        AssociatedWith.objects.create(
            application=self.application,
            applicant=self.applicant,
            percentage_share=50,
        )
        AssociatedWith.objects.create(
            application=second_application,
            applicant=self.applicant,
            percentage_share=50,
        )

        self.assertEqual(
            Application.objects.filter(primary_applicant=self.applicant).count(),
            2,
        )
        self.assertEqual(AssociatedWith.objects.filter(applicant=self.applicant).count(), 2)
