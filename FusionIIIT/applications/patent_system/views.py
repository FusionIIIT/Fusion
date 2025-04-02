import os
import json
import logging

from django.http import JsonResponse
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from .models import (
    Application,
    ApplicationSectionI,
    ApplicationSectionII,
    ApplicationSectionIII,
    AssociatedWith,
    Applicant,
    Attorney
)

# Logger setup - used for debugging and logging errors
logger = logging.getLogger(__name__)

# -----------------------------------------
# 🔹 Applicant Views
# -----------------------------------------

def generate_file_path(folder, filename):
    """Helper function to generate a unique file path."""
    base, extension = os.path.splitext(filename)
    timestamp = now().strftime("%Y%m%d%H%M%S")
    return os.path.join(f"patent/{folder}", f"{base}_{timestamp}{extension}")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
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
        source_file=request.FILES.get("source_file")
        mou_file = request.FILES.get("mou_file")
        form_iii_file = request.FILES.get("form_iii")

        required_fields = [
            "title", "inventors", "area_of_invention", "problem_statement", "objective",
            "novelty", "advantages", "tested_experimentally", "applications",
            "funding_details", "funding_source", "publication_details", "mou_details",
            "research_details", "company_details",
            "development_stage", "user_id"
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
        source_file_path = None
        mou_file_path = None
        form_iii_file_path = None

        if poc_file:
            poc_file_path = default_storage.save(
                generate_file_path("Section-I/poc_details", poc_file.name), poc_file
            )
        if source_file:
            source_file_path = default_storage.save(
                generate_file_path("Section-II/source_details", source_file.name), source_file
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
            source_agreement=source_file_path,
            publication_details=data["publication_details"],
            mou_details=data["mou_details"],
            mou_file=mou_file_path,
            research_details=data["research_details"]
        )

        # Process multiple companies
        company_details = data.get("company_details", [])
        if not isinstance(company_details, list):
            return JsonResponse({"error": "company_details should be a list"}, status=400)
        # print("Company Details:", company_details)
        
        for company in data.get("company_details", []):
            # print("Processing Company:", company)
            company_name = company.get("company_name")
            contact_person = company.get("contact_person")
            contact_no = company.get("contact_no")

            if not (company_name and contact_person and contact_no):
                return JsonResponse({"error": "Each company entry must have company_name, contact_person, and contact_no"}, status=400)

            # Create an entry for each company
            ApplicationSectionIII.objects.create(
                application=application,
                company_name=company_name,
                contact_person=contact_person,
                contact_no=contact_no,
                development_stage=data["development_stage"],
                form_iii=form_iii_file_path
            )

        for inventor in data["inventors"]:
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def view_applications(request):
    user_id = request.user.id
    try:
        # Get the applicant based on user_id
        applicant = get_object_or_404(Applicant, user_id=user_id)
        
        # Get all application IDs associated with this applicant
        associated_apps = AssociatedWith.objects.filter(applicant=applicant).values_list('application_id', flat=True)
        
        # Retrieve applications based on application IDs
        applications = Application.objects.filter(id__in=associated_apps)
        
        # Prepare response data
        applications_data = []
        for app in applications:
            applications_data.append({
                "application_id": app.id,
                "title": app.title,
                "token_no": app.token_no,
                "attorney_name": app.attorney.name if app.attorney else None,
                "submitted_date": app.submitted_date if app.submitted_date else None
            })
        
        return JsonResponse({"applications": applications_data}, safe=False)

    except Applicant.DoesNotExist:
        return JsonResponse({"error": "Applicant not found"}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def view_application_details(request, application_id):
    user = request.user

    # Check if the logged-in user is an applicant
    try:
        applicant = Applicant.objects.get(user=user)
    except Applicant.DoesNotExist:
        return JsonResponse({"error": "Unauthorized: User is not an applicant"}, status=403)

    # Verify if the user is associated with the application
    is_associated = AssociatedWith.objects.filter(application_id=application_id, applicant=applicant).exists()
    if not is_associated:
        return JsonResponse({"error": "Forbidden: You are not associated with this application"}, status=403)

    # Fetch application details
    application = get_object_or_404(Application, id=application_id)

    # Fetch attorney details using attorney_id
    attorney_name = None
    if application.attorney_id:
        attorney = Attorney.objects.filter(id=application.attorney_id).first()
        attorney_name = attorney.name if attorney else None  # Get attorney name safely

    # Fetch associated applicants
    associated_applicants = AssociatedWith.objects.filter(application=application)
    applicants_data = [
        {
            "name": app.applicant.name,
            "email": app.applicant.email,
            "mobile": app.applicant.mobile,
            "address": app.applicant.address,
            "percentage_share": app.percentage_share 
        }
        for app in associated_applicants
    ]

    # Fetch Section I details
    section_i = ApplicationSectionI.objects.filter(application=application).first()
    section_i_data = {
        "area": section_i.area if section_i else None,
        "problem": section_i.problem if section_i else None,
        "objective": section_i.objective if section_i else None,
        "novelty": section_i.novelty if section_i else None,
        "advantages": section_i.advantages if section_i else None,
        "is_tested": section_i.is_tested if section_i else None,
        "poc_details": section_i.poc_details if section_i else None,
        "applications": section_i.applications if section_i else None,
    }

   # Fetch Section II details
    section_ii = ApplicationSectionII.objects.filter(application=application).first()
    section_ii_data = {
        "funding_details": section_ii.funding_details if section_ii else None,
        "funding_source": section_ii.funding_source if section_ii else None,
        "source_agreement": section_ii.source_agreement.url if section_ii and section_ii.source_agreement else None,
        "publication_details": section_ii.publication_details if section_ii else None,
        "mou_details": section_ii.mou_details if section_ii else None,
        "mou_file": section_ii.mou_file.url if section_ii and section_ii.mou_file else None,
        "research_details": section_ii.research_details if section_ii else None
    }

    # Fetch Section III details
    section_iii = ApplicationSectionIII.objects.filter(application=application).first()
    section_iii_data = {
        "company_name": section_iii.company_name if section_iii else None,
        "contact_person": section_iii.contact_person if section_iii else None,
        "contact_no": section_iii.contact_no if section_iii else None,
        "development_stage": section_iii.development_stage if section_iii else None,
        "form_iii": section_iii.form_iii.url if section_iii and section_iii.form_iii else None
    }

    # Prepare response
    response_data = {
        "application_id": application.id,
        "title": application.title,
        "status": application.status,
        "token_no": application.token_no,
        "attorney_name": attorney_name,
        "dates": {
            "patentability_check_date": application.patentability_check_date,
            "patentability_file_date": application.patentability_file_date,
            "assigned_date": application.assigned_date,
            "decision_date": application.decision_date,
            "submitted_date": application.submitted_date if application.submitted_date else None
        },
        "decision_status": application.decision_status,
        "comments": application.comments if application.comments else None,
        "applicants": applicants_data,
        "section_I": section_i_data,
        "section_II": section_ii_data,
        "section_III": section_iii_data
    }

    return JsonResponse(response_data, safe=False)

def saved_drafts(request):
    return JsonResponse({"message": "save drafts"})

# -----------------------------------------
# 🔹 PCC Admin Views
# -----------------------------------------

# For dashboard tab
def insights_by_year(request):
    return JsonResponse({"message": "Insights by Year"})

# For new applications tab
def new_applications(request):
    return JsonResponse({"message": "New Applications"})

def review_applications(request):
    return JsonResponse({"message": "Review Applications"})

def forward_applications(request):
    return JsonResponse({"message": "Forward Applications"})

# For status of applications tab
def reviewed_applications(request):
    return JsonResponse({"message": "Reviewed Applications"})

# For manage attorney tab
def add_attorney(request):
    return JsonResponse({"message": "Attorney added successfully"})

def remove_attorney(request):
    return JsonResponse({"message": "Attorney removed successfully"})   

def view_attorney_list(request):
    return JsonResponse({"message": "List of attorneys", "attorneys": []}) 

def view_attorney_details(request, attorney_id):
    return JsonResponse({"message": f"Details of attorney {attorney_id}"})

def edit_attorney_details(request, attorney_id):
    return JsonResponse({"message": f"Attorney {attorney_id} details updated successfully"})

# -----------------------------------------
# 🔹 Director Views
# -----------------------------------------

def director_main_dashboard(request):
    return JsonResponse({"message": "Director Main Dashboard"})


def director_dashboard(request):
    return JsonResponse({"message": "Director Dashboard"})

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



