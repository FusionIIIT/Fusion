import uuid
from datetime import date

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from applications.patent_system.models import Applicant, Application, CommunicationLog


def run():
    import uuid

    suffix = uuid.uuid4().hex[:8]
    created_users = []
    created_apps = []

    try:
        pcc = User.objects.create_user(
            username=f"pcc_{suffix}",
            email=f"pcc_{suffix}@example.com",
            password="pass1234",
        )
        director = User.objects.create_user(
            username=f"dir_{suffix}",
            email=f"dir_{suffix}@example.com",
            password="pass1234",
        )
        app_user = User.objects.create_user(
            username=f"app_{suffix}",
            email=f"app_{suffix}@example.com",
            password="pass1234",
        )
        created_users.extend([pcc, director, app_user])

        applicant = Applicant.objects.create(
            user=app_user,
            name="Smoke Applicant",
            email=f"app.personal_{suffix}@example.com",
            mobile="9999999999",
            address="Campus",
        )

        app1 = Application.objects.create(
            primary_applicant=applicant,
            title="Smoke Patent 1",
            status="Submitted",
            decision_status="Pending",
            submitted_date=date.today(),
        )
        created_apps.append(app1)

        client = APIClient()
        client.force_authenticate(user=pcc)

        review_response = client.post(
            f"/patentsystem/pccAdmin/applications/new/review/{app1.id}/",
            {"comments": "reviewed"},
            format="json",
        )
        assert review_response.status_code == 200, review_response.content

        invalid_transition = client.post(
            f"/patentsystem/pccAdmin/applications/ongoing/changeStatus/{app1.id}/",
            {"next_status": "Patent Filed"},
            format="json",
        )
        assert invalid_transition.status_code == 400, invalid_transition.content

        forward_response = client.post(
            f"/patentsystem/pccAdmin/applications/new/forward/{app1.id}/",
            {
                "attorney_name": "External Counsel",
                "attorney_email": "external@example.com",
                "comments": "forwarding",
            },
            format="json",
        )
        assert forward_response.status_code == 200, forward_response.content

        app1.refresh_from_db()
        assert app1.status == "Forwarded for Director's Review"
        assert CommunicationLog.objects.filter(application=app1).exists()

        comm_response = client.post(
            f"/patentsystem/pccAdmin/applications/{app1.id}/communication-logs/",
            {
                "external_attorney_name": "Counsel",
                "external_attorney_email": "c@example.com",
                "message_content": "shared draft",
                "status_or_notes": "awaiting",
            },
            format="json",
        )
        assert comm_response.status_code == 201, comm_response.content

        client.force_authenticate(user=director)
        reject_wrong_stage = client.post(
            "/patentsystem/director/application/reject",
            {"application_id": app1.id + 9999},
            format="json",
        )
        assert reject_wrong_stage.status_code in (400, 404), reject_wrong_stage.content

        approve_response = client.post(
            "/patentsystem/director/application/accept",
            {"application_id": app1.id, "comments": "approved"},
            format="json",
        )
        assert approve_response.status_code == 200, approve_response.content
        app1.refresh_from_db()
        assert app1.status == "Director's Approval Received"
        assert app1.decision_status == "Pending"

        app2 = Application.objects.create(
            primary_applicant=applicant,
            title="Smoke Patent 2",
            status="Forwarded for Director's Review",
            decision_status="Pending",
            submitted_date=date.today(),
        )
        created_apps.append(app2)

        reject_response = client.post(
            "/patentsystem/director/application/reject",
            {"application_id": app2.id},
            format="json",
        )
        assert reject_response.status_code == 200, reject_response.content
        app2.refresh_from_db()
        assert app2.status == "Patent Refused"

        print("PATENT_RUNTIME_SMOKE: PASS")
    finally:
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
