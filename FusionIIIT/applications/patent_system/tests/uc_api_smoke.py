from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from applications.globals.models import Designation, HoldsDesignation
from applications.patent_system.models import Applicant, Application, Attorney, BudgetApproval, Document


def assert_status(response, allowed, label):
    if response.status_code not in allowed:
        raise AssertionError(f"{label} failed ({response.status_code})")


def run():
    import uuid
    suffix = uuid.uuid4().hex[:8]
    created_users = []
    created_apps = []
    created_documents = []

    try:
        pcc = User.objects.create_user(
            username=f"pcc_{suffix}",
            email=f"pcc_{suffix}@example.com",
            password="pass1234",
        )
        director = User.objects.create_user(
            username=f"director_{suffix}",
            email=f"director_{suffix}@example.com",
            password="pass1234",
        )
        applicant_user = User.objects.create_user(
            username=f"applicant_{suffix}",
            email=f"applicant_{suffix}@example.com",
            password="pass1234",
        )
        created_users.extend([pcc, director, applicant_user])

        pcc_designation, _ = Designation.objects.get_or_create(
            name="pcc_admin",
            defaults={"full_name": "PCC Admin", "type": "administrative"},
        )
        director_designation, _ = Designation.objects.get_or_create(
            name="director",
            defaults={"full_name": "Director", "type": "administrative"},
        )

        HoldsDesignation.objects.get_or_create(user=pcc, working=pcc, designation=pcc_designation)
        HoldsDesignation.objects.get_or_create(user=director, working=director, designation=director_designation)

        applicant = Applicant.objects.create(
            user=applicant_user,
            name="UC Smoke Applicant",
            email=f"uc_{suffix}@example.com",
            mobile="9999999999",
            address="Campus",
        )

        application = Application.objects.create(
            primary_applicant=applicant,
            title=f"UC Smoke Patent {suffix}",
            status="Submitted",
            decision_status="Pending",
            submitted_date=date.today(),
        )
        created_apps.append(application)

        attorney = Attorney.objects.create(
            name=f"Counsel {suffix}",
            email=f"counsel_{suffix}@example.com",
            phone="9876543210",
            firm_name="External Legal LLP",
        )

        client = APIClient()
        client.raise_request_exception = False

        client.force_authenticate(user=pcc)
        assert_status(
            client.post(
                f"/patentsystem/pccAdmin/applications/new/review/{application.id}/",
                {"comments": "reviewed"},
                format="json",
            ),
            [200],
            "review application",
        )

        assert_status(
            client.post(
                f"/patentsystem/pccAdmin/applications/new/forward/{application.id}/",
                {
                    "attorney_name": "External Counsel",
                    "attorney_email": "external@example.com",
                    "comments": "forwarding to director",
                },
                format="json",
            ),
            [200],
            "forward application",
        )

        client.force_authenticate(user=director)
        assert_status(
            client.post(
                "/patentsystem/director/application/accept",
                {"application_id": application.id, "comments": "approved"},
                format="json",
            ),
            [200],
            "director accept",
        )

        client.force_authenticate(user=pcc)
        assert_status(
            client.post(
                f"/patentsystem/pccAdmin/applications/{application.id}/legal-assessment/",
                {
                    "attorney": attorney.id,
                    "opinion": "Positive",
                    "prior_art_summary": "No direct overlap",
                    "recommended_action": "Proceed",
                },
                format="json",
            ),
            [201],
            "legal assessment create",
        )
        assert_status(
            client.get(f"/patentsystem/pccAdmin/applications/{application.id}/legal-assessment/"),
            [200],
            "legal assessment list",
        )

        budget_response = client.post(
            f"/patentsystem/pccAdmin/applications/{application.id}/budget/",
            {"amount": "75000", "threshold": "50000", "comments": "budget required"},
            format="json",
        )
        assert_status(budget_response, [201], "budget create")

        budget_id = BudgetApproval.objects.filter(application=application).order_by("-id").values_list("id", flat=True).first()

        client.force_authenticate(user=director)
        assert_status(
            client.post(
                f"/patentsystem/pccAdmin/budget/{budget_id}/decision/",
                {"decision": "approve", "comments": "approved"},
                format="json",
            ),
            [200],
            "budget decide",
        )

        client.force_authenticate(user=pcc)
        assert_status(
            client.post(
                f"/patentsystem/pccAdmin/applications/{application.id}/external-filing/",
                {
                    "patent_office": "IPO",
                    "filing_reference": f"REF-{suffix}",
                    "communication_notes": "Filed successfully",
                    "filing_date": str(date.today()),
                },
                format="json",
            ),
            [201],
            "external filing create",
        )
        assert_status(
            client.get(f"/patentsystem/pccAdmin/applications/{application.id}/external-filing/"),
            [200],
            "external filing list",
        )

        office_action_resp = client.post(
            f"/patentsystem/pccAdmin/applications/{application.id}/office-actions/",
            {
                "office_name": "IPO",
                "action_reference": f"OA-{suffix}",
                "action_summary": "clarify claims",
                "due_date": str(date.today()),
            },
            format="json",
        )
        assert_status(office_action_resp, [201], "office action create")
        action_id = office_action_resp.json().get("id")
        assert_status(
            client.post(
                f"/patentsystem/pccAdmin/office-actions/{action_id}/respond/",
                {"response_text": "submitted revised claim set", "response_reference": f"R-{suffix}"},
                format="json",
            ),
            [201],
            "office action respond",
        )
        assert_status(
            client.get(f"/patentsystem/pccAdmin/applications/{application.id}/office-actions/"),
            [200],
            "office action list",
        )

        assert_status(
            client.post(
                f"/patentsystem/pccAdmin/applications/{application.id}/prior-art/",
                {"reference_type": "Patent", "citation": f"US-{suffix}", "notes": "related"},
                format="json",
            ),
            [201],
            "prior art create",
        )
        assert_status(
            client.get(f"/patentsystem/pccAdmin/applications/{application.id}/prior-art/?q=US-"),
            [200],
            "prior art list",
        )

        assert_status(
            client.post(
                f"/patentsystem/pccAdmin/applications/{application.id}/licensing/",
                {
                    "requester_name": "ACME",
                    "requester_org": "ACME Labs",
                    "request_details": "license request",
                },
                format="json",
            ),
            [201],
            "licensing create",
        )
        assert_status(
            client.get(f"/patentsystem/pccAdmin/applications/{application.id}/licensing/"),
            [200],
            "licensing list",
        )

        assert_status(
            client.post(
                f"/patentsystem/pccAdmin/applications/{application.id}/inventor-consents/",
                {"agreement_reference": f"AG-{suffix}"},
                format="json",
            ),
            [200],
            "inventor consents ensure",
        )
        assert_status(
            client.get(f"/patentsystem/pccAdmin/applications/{application.id}/inventor-consents/"),
            [200],
            "inventor consents list",
        )

        maintenance_response = client.post(
            f"/patentsystem/pccAdmin/applications/{application.id}/maintenance/",
            {"due_date": str(date.today()), "amount": "1000"},
            format="json",
        )
        assert_status(maintenance_response, [201], "maintenance setup")
        schedule_id = maintenance_response.json().get("id")
        assert_status(
            client.post(f"/patentsystem/pccAdmin/maintenance/{schedule_id}/mark-paid/", {}, format="json"),
            [200],
            "maintenance mark paid",
        )

        assert_status(client.get("/patentsystem/pccAdmin/queue/prioritized/"), [200], "queue")
        assert_status(client.get("/patentsystem/notifications/"), [200], "notifications")
        assert_status(client.get("/patentsystem/pccAdmin/audit-logs/"), [200], "audit logs")
        assert_status(client.get("/patentsystem/audit-logs/"), [200], "audit logs alias")
        assert_status(client.get("/patentsystem/pccAdmin/insights/"), [200], "pcc insights")

        document = Document.objects.create(title=f"Doc {suffix}", link="https://example.com/doc-v1", application=application)
        created_documents.append(document)

        assert_status(
            client.post(
                f"/patentsystem/documents/{document.id}/versions/upload/",
                {"link": "https://example.com/doc-v2"},
                format="json",
            ),
            [201],
            "document version upload",
        )
        assert_status(client.get(f"/patentsystem/documents/{document.id}/versions/"), [200], "document version list")
        assert_status(client.post(f"/patentsystem/documents/{document.id}/lock/", {}, format="json"), [200], "document lock")

        assert_status(
            client.post(
                f"/patentsystem/pccAdmin/applications/{application.id}/communication-logs/",
                {
                    "external_attorney_name": "Counsel",
                    "external_attorney_email": "c@example.com",
                    "message_content": "status update",
                    "status_or_notes": "pending",
                },
                format="json",
            ),
            [201],
            "communication log create",
        )
        assert_status(
            client.get(f"/patentsystem/pccAdmin/applications/{application.id}/communication-logs/"),
            [200],
            "communication log list",
        )

        client.force_authenticate(user=applicant_user)
        assert_status(
            client.post(
                f"/patentsystem/applicant/applications/{application.id}/appeals/",
                {"grounds": "request reconsideration"},
                format="json",
            ),
            [201],
            "appeal submit",
        )
        assert_status(client.get(f"/patentsystem/pccAdmin/applications/{application.id}/appeals/"), [200], "appeal list")
        assert_status(client.get("/patentsystem/applicant/insights/"), [200], "applicant insights")

        print("PATENT_UC_API_SMOKE: PASS")
    finally:
        for document in created_documents:
            try:
                document.delete()
            except Exception:
                pass

        for app in created_apps:
            try:
                app.delete()
            except Exception:
                pass

        for user in created_users:
            try:
                user.delete()
            except Exception:
                pass


run()
