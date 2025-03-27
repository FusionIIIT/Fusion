from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.utils.timezone import now
from django.contrib.auth.models import User

# auth_user import


import json
from .models import (
    Application,
    ApplicationSectionI,
    ApplicationSectionII,
    ApplicationSectionIII,
    AssociatedWith,
    Applicant,
    Attorney
)
# to be delete
# -----------------------------------------
# 🔹 Applicant Views
# -----------------------------------------

import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.utils.timezone import now
from .models import Application, ApplicationSectionI, ApplicationSectionII, ApplicationSectionIII, Applicant, AssociatedWith

def generate_file_path(folder, filename):
    """Helper function to generate a unique file path."""
    base, extension = os.path.splitext(filename)
    timestamp = now().strftime("%Y%m%d%H%M%S")
    return os.path.join(f"patent/{folder}", f"{base}_{timestamp}{extension}")

@csrf_exempt
def submit_application(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        json_data = request.POST.get("json_data")
        if not json_data:
            return JsonResponse({"error": "Missing JSON data"}, status=400)
        
        data = json.loads(json_data)

        # Required file fields
        poc_file = request.FILES.get("poc_details")
        mou_file = request.FILES.get("mou_file")
        form_iii_file = request.FILES.get("form_iii")

        required_fields = [
            "title", "inventors", "area_of_invention", "problem_statement", "objective",
            "novelty", "advantages", "tested_experimentally", "applications",
            "funding_details", "funding_source", "publication_details", "mou_details",
            "research_details", "company_name", "contact_person", "contact_no",
            "development_stage", "user_id", "inventor_contributions"
        ]
        
        for field in required_fields:
            if field not in data:
                return JsonResponse({"error": f"Missing required field: {field}"}, status=400)

        # Create application entry with submitted date
        application = Application.objects.create(
            title=data["title"],
            status="Submitted",
            decision_status="Pending",
            submitted_date=now(),
        )

        # Save file uploads and store paths
        poc_file_path = None
        mou_file_path = None
        form_iii_file_path = None

        if poc_file:
            poc_file_path = default_storage.save(
                generate_file_path("Section-I/poc_details", poc_file.name), poc_file
            )
        if mou_file:
            mou_file_path = default_storage.save(
                generate_file_path("Section-II/mou_details", mou_file.name), mou_file
            )
        if form_iii_file:
            form_iii_file_path = default_storage.save(
                generate_file_path("Section-III/form_iii", form_iii_file.name), form_iii_file
            )

        ApplicationSectionI.objects.create(
            application=application,
            area=data["area_of_invention"],
            problem=data["problem_statement"],
            objective=data["objective"],
            novelty=data["novelty"],
            advantages=data["advantages"],
            is_tested=data["tested_experimentally"],
            applications=data["applications"],
            poc_details=poc_file_path
        )

        ApplicationSectionII.objects.create(
            application=application,
            funding_details=data["funding_details"],
            funding_source=data["funding_source"],
            publication_details=data["publication_details"],
            mou_details=data["mou_details"],
            mou_file=mou_file_path,
            research_details=data["research_details"]
        )

        ApplicationSectionIII.objects.create(
            application=application,
            company_name=data["company_name"],
            contact_person=data["contact_person"],
            contact_no=data["contact_no"],
            development_stage=data["development_stage"],
            form_iii=form_iii_file_path
        )

        for inventor in json.loads(data["inventor_contributions"]):
            email = inventor["institute_mail"]
            percentage = inventor["percentage"]
            name = inventor.get("name", "")
            personal_mail = inventor.get("personal_mail", "")
            mobile = inventor.get("mobile", "")
            address = inventor.get("address", "")

            try:
                user = User.objects.get(email=email)
                applicant, created = Applicant.objects.get_or_create(
                    user_id=user.id,
                    defaults={
                        "email": personal_mail,
                        "name": name,
                        "mobile": mobile,
                        "address": address,
                    }
                )

                AssociatedWith.objects.create(
                    application=application,
                    applicant=applicant,
                    percentage_share=percentage
                )
            except User.DoesNotExist:
                return JsonResponse({"error": f"Inventor {email} not found in auth_user"}, status=404)

        # Generate token
        application_id = application.id
        token = f"IIITDMJ/AGR/{application_id:06d}/AAS/104"
        application.token_no = token
        application.save()

        return JsonResponse({
            "message": "Application submitted successfully",
            "application_id": application_id,
            "token": token
        })
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# End of the submit application

def applicant_dashboard(request):
    return JsonResponse({"message": "Load applicant dashboard"})

def applicant_main_dashboard(request):
    return JsonResponse({"message": "Load applicant main dashboard"})

def view_applications(request):
    return JsonResponse({"message": "view_applications"})

def saved_drafts(request):
    return JsonResponse({"message": "save drafts"})

def applicant_notifications(request):
    return JsonResponse({"notifications": ["Patent approved", "Review required"]})


def application_form(request):
    return JsonResponse({"message": "Load application form"})


def ip_filing_form(request):
    return JsonResponse({"message": "Load IP filing form"})


def status_view(request):
    return JsonResponse({"message": "View application status"})


# -----------------------------------------
# 🔹 Director Views
# -----------------------------------------

def director_main_dashboard(request):
    return JsonResponse({"message": "Director Main Dashboard"})


def director_dashboard(request):
    return JsonResponse({"message": "Director Dashboard"})


@csrf_exempt
def director_accept_reject(request):
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            application = Application.objects.get(id=data["app_id"])
            application.status = data["status"]
            application.save()
            return JsonResponse({"message": f"Application {data['status']} by Director"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Application not found"}, status=404)
    return JsonResponse({"error": "Invalid request method"}, status=405)


def recents_view(request):
    recents = list(Application.objects.order_by("-updated_at").values("id", "title", "status")[:5])
    return JsonResponse({"recent_applications": recents})


def pending_reviews(request):
    pending = list(Application.objects.filter(status="Pending").values("id", "title"))
    return JsonResponse({"pending_reviews": pending})


def reviewed_applications(request):
    reviewed = list(Application.objects.filter(status="Reviewed").values("id", "title"))
    return JsonResponse({"reviewed_applications": reviewed})


def active_applications(request):
    active = list(Application.objects.filter(status="Active").values("id", "title"))
    return JsonResponse({"active_applications": active})


def director_status_view(request):
    return JsonResponse({"message": "Director Status View"})


def director_notifications(request):
    return JsonResponse({"notifications": ["New submission", "Pending review"]})


def submitted_applications(request):
    submitted = list(Application.objects.filter(status="Submitted").values("id", "title"))
    return JsonResponse({"submitted_applications": submitted})


# -----------------------------------------
# 🔹 PCC Admin Views
# -----------------------------------------

def pcc_admin_main_dashboard(request):
    return JsonResponse({"message": "PCC Admin Main Dashboard"})


def pcc_admin_dashboard(request):
    return JsonResponse({"message": "PCC Admin Dashboard"})


def review_applications(request):
    applications = list(Application.objects.filter(status="Under Review").values("id", "title"))
    return JsonResponse({"review_applications": applications})


@csrf_exempt
def manage_attorney(request):
    if request.method == "POST":
        data = json.loads(request.body)
        return JsonResponse({"message": f"Attorney assigned to application {data['app_id']}"})
    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def notify_applicant(request):
    if request.method == "POST":
        data = json.loads(request.body)
        return JsonResponse({"message": f"Notification sent to applicant of application {data['app_id']}"})
    return JsonResponse({"error": "Invalid request method"}, status=405)


def downloads_page(request):
    return JsonResponse({"message": "Downloads Page"})


def insights_page(request):
    return JsonResponse({"message": "Insights Page"})


def pcc_admin_status_view(request):
    return JsonResponse({"message": "PCC Admin Status View"})
