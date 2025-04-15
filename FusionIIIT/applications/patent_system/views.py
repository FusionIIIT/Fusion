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
from django.db.models import Count

from .models import (
    Application,
    ApplicationSectionI,
    ApplicationSectionII,
    ApplicationSectionIII,
    AssociatedWith,
    Applicant,
    Attorney,
    Document
)

from applications.globals.models import (
    Designation,
    DepartmentInfo,
    ExtraInfo,
    HoldsDesignation,
)

from .serializers import AttorneySerializer, DocumentSerializer

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

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
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
        source_file = request.FILES.get("source_file")
        mou_file = request.FILES.get("mou_file")
        form_iii_file = request.FILES.get("form_iii")

        required_fields = [
            "title", "inventors", "area_of_invention", "problem_statement", "objective",
            "novelty", "advantages", "tested_experimentally", "applications",
            "funding_details", "funding_source", "publication_details", "mou_details",
            "research_details", "company_details",
            "development_stage"
        ]
        
        for field in required_fields:
            if field not in data:
                return JsonResponse({"error": f"Missing required field: {field}"}, status=400)

        # Get the logged-in user
        user = request.user

        # Check if the user has an applicant profile, create one if not
        applicant, created = Applicant.objects.get_or_create(
            user=user,
            defaults={
                "email": user.email,  # Assuming User model has email
                "name": user.get_full_name() or user.username,  # Use full name or username
                "mobile": "",  # Set to empty initially
                "address": "",  # Set to empty initially
            }
        )

        # Create application entry with the logged-in user as the primary applicant
        application = Application.objects.create(
            title=data["title"],
            status="Submitted",
            decision_status="Pending",
            submitted_date=now(),
            primary_applicant=applicant,  # Store the Applicant instance here
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
            type_of_ip=data["type_of_ip"],
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
        
        for company in company_details:
            company_name = company.get("company_name")
            contact_person = company.get("contact_person")
            contact_no = company.get("contact_no")

            if not (company_name and contact_person and contact_no):
                return JsonResponse({"error": "Each company entry must have company_name, contact_person, and contact_no"}, status=400)

            ApplicationSectionIII.objects.create(
                application=application,
                company_name=company_name,
                contact_person=contact_person,
                contact_no=contact_no,
                development_stage=data["development_stage"],
                form_iii=form_iii_file_path
            )

        # Associate inventors with the application
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
                    user=user,
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
def view_application_details_for_applicant(request, application_id):
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
        "type_of_ip": section_i.type_of_ip if section_i else None,
        "area": section_i.area if section_i else None,
        "problem": section_i.problem if section_i else None,
        "objective": section_i.objective if section_i else None,
        "novelty": section_i.novelty if section_i else None,
        "advantages": section_i.advantages if section_i else None,
        "is_tested": section_i.is_tested if section_i else None,
        "poc_details": section_i.poc_details.url if section_i else None,
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

# For new applications tab
def new_applications(request):
    REVIEW_STATUSES = ["Submitted", "Reviewed by PCC Admin"]

    applications = Application.objects.filter(status__in=REVIEW_STATUSES).select_related("primary_applicant")

    application_dict = {}  # Using a dictionary instead of a list

    for app in applications:
        applicant = app.primary_applicant  # Get the Applicant instance

        # Ensure applicant exists and fetch the linked User
        user = applicant.user if applicant else None

        # Fetch extra info (assuming ExtraInfo is linked to User)
        extra_info = ExtraInfo.objects.filter(user=user).first()

        # Fetch department
        department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

        # Fetch designation (get latest held designation)
        holds_designation = HoldsDesignation.objects.filter(user=user).select_related("designation").first()
        designation_name = holds_designation.designation.name if holds_designation else "Unknown"

        # Format response as a dictionary
        application_dict[app.id] = {
            # "application_no": app.id,
            "title": app.title,
            "submitted_by": applicant.name,
            "designation": designation_name,
            "department": department_name,
            "submitted_on": app.submitted_date.strftime("%Y-%m-%d") if app.submitted_date else "Unknown"
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def review_applications(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            application_id = data.get("application_id")

            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            application.status = "Reviewed by PCC Admin"
            application.save()

            return JsonResponse({
                "message": "Application status updated to 'Reviewed by PCC Admin'.",
                "application_id": application.id,
                "new_status": application.status
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def forward_application(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            application_id = data.get("application_id")

            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            application.status = "Forwarded for Director's Review"
            application.save()

            return JsonResponse({
                "message": "Application status updated to 'Forwarded for Director's Review'.",
                "application_id": application.id,
                "new_status": application.status
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def reject_application(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            application_id = data.get("application_id")

            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            application.status = "Rejected"
            application.decision_date = now()
            application.decision_status = "Rejected"
            application.save()

            return JsonResponse({
                "message": "Application status updated to 'Forwarded for Director's Review'.",
                "application_id": application.id,
                "new_status": application.status
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

# For ongoing applications tab
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def ongoing_applications(request):
    REVIEW_STATUSES = [
    "Forwarded for Director's Review",
    "Director's Approval Received",
    "Patentability Check Started",
    "Patentability Check Completed",
    "Patentability Search Report Generated",
    "Patent Filed",
    "Patent Published",
    ]

    applications = Application.objects.filter(status__in=REVIEW_STATUSES).select_related("primary_applicant")


    application_dict = {}  # Using a dictionary instead of a list

    for app in applications:
        applicant = app.primary_applicant  # Get the Applicant instance

        # Ensure applicant exists and fetch the linked User
        user = applicant.user if applicant else None

        # Fetch extra info (assuming ExtraInfo is linked to User)
        extra_info = ExtraInfo.objects.filter(user=user).first()

        # Fetch department
        department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

        # Fetch designation (get latest held designation)
        holds_designation = HoldsDesignation.objects.filter(user=user).select_related("designation").first()
        designation_name = holds_designation.designation.name if holds_designation else "Unknown"

        # Format response as a dictionary
        application_dict[app.id] = {
            # "application_no": app.id,
            "token_no": app.token_no if app.token_no else "Token not generated yet",
            "title": app.title,
            "submitted_by": applicant.name if applicant else "Unknown",
            "designation": designation_name,
            "department": department_name,
            "submitted_on": app.submitted_date.strftime("%Y-%m-%d") if app.submitted_date else "Unknown",
            "status": app.status,
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def past_applications(request):
    DECISION_STATUSES = [
        "Accepted", 
        "Rejected",
    ]

    applications = Application.objects.filter(decision_status__in=DECISION_STATUSES).select_related("primary_applicant")

    application_dict = {}  # Using a dictionary instead of a list

    for app in applications:
        applicant = app.primary_applicant  # Get the Applicant instance

        # Ensure applicant exists and fetch the linked User
        user = applicant.user if applicant else None

        # Fetch extra info (assuming ExtraInfo is linked to User)
        extra_info = ExtraInfo.objects.filter(user=user).first()

        # Fetch department
        department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

        # Fetch designation (get latest held designation)
        holds_designation = HoldsDesignation.objects.filter(user=user).select_related("designation").first()
        designation_name = holds_designation.designation.name if holds_designation else "Unknown"

        # Format response as a dictionary
        application_dict[app.id] = {
            "token_no": app.token_no if app.token_no else "Token not generated yet",
            "title": app.title,
            "submitted_by": applicant.name if applicant else "Unknown",
            "designation": designation_name,
            "department": department_name,
            "submitted_on": app.submitted_date.strftime("%Y-%m-%d") if app.submitted_date else "Unknown",
            "status": app.status,
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def view_past_application_details_for_pccAdmin(request, application_id):
    # Fetch application details
    application = get_object_or_404(Application, id=application_id)

    # Fetch primary applicant details using primary_applicant_id
    primary_applicant_name = None
    if application.primary_applicant_id:
        primary_applicant = Applicant.objects.filter(id=application.primary_applicant_id).first()
        primary_applicant_name = primary_applicant.name if primary_applicant else None  # Get primary applicant name safely

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
        "poc_details": section_i.poc_details.url if section_i else None,
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
        "primary_applicant_name": primary_applicant_name,
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

# -----------------------------------------
# 🔹 PCC Admin Attorney Management Views
# -----------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attorney_list(request):
    try:
        # Get all attorneys with their application count
        attorneys = Attorney.objects.annotate(
            assigned_applications_count=Count('applications')
        ).all()
        
        # Serialize the data
        serializer = AttorneySerializer(attorneys, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_attorney(request):
    try:
        serializer = AttorneySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_attorney(request, attorney_id):
    try:
        attorney = Attorney.objects.get(id=attorney_id)
        attorney.delete()
        return Response({'message': 'Attorney removed successfully'}, status=status.HTTP_200_OK)
    except Attorney.DoesNotExist:
        return Response({'error': 'Attorney not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attorney_applications(request, attorney_id):
    try:
        # Get the attorney
        attorney = Attorney.objects.get(id=attorney_id)
        
        # Get all applications assigned to this attorney
        applications = Application.objects.filter(attorney=attorney).values('id', 'title', 'status')
        
        # Get the count of assigned applications
        assigned_count = applications.count()
        
        response_data = {
            'attorney_id': attorney.id,
            'attorney_name': attorney.name,
            'assigned_applications_count': assigned_count,
            'applications': list(applications)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Attorney.DoesNotExist:
        return Response({'error': 'Attorney not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def update_attorney_details(request, attorney_id):
    try:
        attorney = Attorney.objects.get(id=attorney_id)
        serializer = AttorneySerializer(attorney, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Attorney.DoesNotExist:
        return Response({'error': 'Attorney not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -----------------------------------------
# 🔹 Document Management Views
# -----------------------------------------

@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manage_documents(request):
    """
    GET: List all documents
    POST: Create a new document
    """
    if request.method == 'GET':
        try:
            documents = Document.objects.all().order_by('-created_at')
            serializer = DocumentSerializer(documents, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}")
            return Response(
                {'error': 'Failed to fetch documents'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    elif request.method == 'POST':
        try:
            serializer = DocumentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            return Response(
                {'error': 'Failed to create document'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_document(request, document_id):
    """
    Delete a document by ID
    """
    try:
        document = Document.objects.get(id=document_id)
        document.delete()
        return Response(
            {'message': 'Document deleted successfully'},
            status=status.HTTP_200_OK
        )
    except Document.DoesNotExist:
        return Response(
            {'error': 'Document not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return Response(
            {'error': 'Failed to delete document'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )