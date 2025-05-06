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
from django.db import transaction

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def submit_application(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        # Start a transaction
        with transaction.atomic():
            json_data = request.POST.get("json_data")
            if not json_data:
                return JsonResponse({"error": "Missing JSON data"}, status=400)
            
            data = json.loads(json_data)

            print("Parsed data keys:", data.keys())

            # Required file fields
            poc_file = request.FILES.get("poc_details")
            source_file = request.FILES.get("source_file")
            mou_file = request.FILES.get("mou_file")
            form_iii_file = request.FILES.get("form_iii")

            required_fields = [
                "title", "inventors", "area_of_invention", "problem_statement", "objective", "ip_type",
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
                    "email": user.email,
                    "name": user.get_full_name() or user.username,
                    "mobile": "",
                    "address": "",
                }
            )

            # Create application entry with the logged-in user as the primary applicant
            application = Application.objects.create(
                title=data["title"],
                status="Submitted",
                decision_status="Pending",
                submitted_date=now(),
                primary_applicant=applicant,
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
                type_of_ip=data["ip_type"],
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
                    applicant, created = Applicant.objects.update_or_create(
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
                    # This will rollback all database changes made in this transaction
                    return JsonResponse({"error": f"Inventor {email} not found in auth_user"}, status=404)

            # Generate token
            application_id = application.id
            application.save()

            return JsonResponse({
                "message": "Application submitted successfully",
                "application_id": application_id,
            })
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

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
        "type_of_ip": section_i.type_of_ip if section_i else None,
        "area": section_i.area if section_i else None,
        "problem": section_i.problem if section_i else None,
        "objective": section_i.objective if section_i else None,
        "novelty": section_i.novelty if section_i else None,
        "advantages": section_i.advantages if section_i else None,
        "is_tested": section_i.is_tested if section_i else None,
        "poc_details": section_i.poc_details.url if section_i and section_i.poc_details else None,
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
        "token_no": application.token_no if application.token_no else "Token not generated",
        "attorney_name": attorney_name,
        "dates": {
            "submitted_date": application.submitted_date if application.submitted_date else None,
            "reviewed_by_pcc_date": application.reviewed_by_pcc_date,
            "forwarded_to_director_date": application.forwarded_to_director_date,
            "director_approval_date": application.director_approval_date,
            "patentability_check_start_date": application.patentability_check_start_date,
            "patentability_check_completed_date": application.patentability_check_completed_date,
            "search_report_generated_date": application.search_report_generated_date,
            "patent_filed_date": application.patent_filed_date,
            "patent_published_date": application.patent_published_date,
            "decision_date": application.decision_date
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
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
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
            "submitted_by": applicant.name,
            "designation": designation_name,
            "department": department_name,
            "submitted_on": app.submitted_date.strftime("%Y-%m-%d") if app.submitted_date else "Unknown"
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def review_application(request, application_id):
    # Check if request method is POST
    if request.method == "POST":
        try:
            # Validate that application_id is provided
            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            # Try to fetch the application by its ID
            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            # Optional: Check if it's already reviewed to prevent redundant updates
            if application.status == "Reviewed by PCC Admin":
                return JsonResponse({"message": "Application already reviewed."})

            # Parse JSON body
            try:
                data = json.loads(request.body)
                comments = data.get("comments", "")
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON body."}, status=400)

            # Update application status and review date
            application.status = "Reviewed by PCC Admin"
            if comments != "":
                application.comments = comments
            application.reviewed_by_pcc_date = now()
            application.save()

            # Return success response with updated status and date
            return JsonResponse({
                "message": "Application status updated to 'Reviewed by PCC Admin'.",
                "application_id": application.id,
                "new_status": application.status,
                "reviewed_by_pcc_date": application.reviewed_by_pcc_date,
            })

        # Handle invalid JSON (though not used directly here)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

    # Handle non-POST requests
    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def forward_application(request, application_id):
    if request.method == "POST":
        try:
            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            # Get the application
            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            # Prevent double forwarding
            if application.status == "Forwarded for Director's Review":
                return JsonResponse({"message": "Application is already forwarded for Director's review."}, status=400)

            # Parse JSON body
            try:
                data = json.loads(request.body)
                attorney_name = data.get("attorney_name", "").strip()
                comments = data.get("comments", "")
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON body."}, status=400)

            if not attorney_name:
                return JsonResponse({"error": "attorney_name is required in the request body."}, status=400)

            # Get attorney (case-insensitive)
            attorney = Attorney.objects.filter(name__iexact=attorney_name).first()
            if not attorney:
                return JsonResponse({"error": f"Attorney with name '{attorney_name}' not found."}, status=404)

            # Optional: Limit comment length
            if comments and len(comments) > 1000:
                return JsonResponse({"error": "Comments too long. Max 1000 characters allowed."}, status=400)

            # Update the application
            application.status = "Forwarded for Director's Review"
            application.forwarded_to_director_date = now()
            application.attorney = attorney
            if comments != "":
                application.comments = comments
            application.save()

            return JsonResponse({
                "message": "Application forwarded to director.",
                "application_id": application.id,
                "new_status": application.status,
                "forwarded_to_director_date": application.forwarded_to_director_date,
                "attorney_id": attorney.id,
                "attorney_name": attorney.name,
                "comments": comments
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def request_application_modification(request, application_id):
    if request.method == "POST":
        try:
            # Validate if application_id is provided
            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            # Fetch the application object from the database
            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            # Check if the application is already in Draft status to prevent redundant updates
            if application.status == "Draft":
                return JsonResponse({"message": "Application is already in Draft status."}, status=400)

            # Parse the request body for comments
            try:
                data = json.loads(request.body)
                comments = data.get("comments", "").strip()  # Remove leading/trailing whitespace
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON body."}, status=400)

            # Validate comments field
            if not comments:
                return JsonResponse({"error": "Comments are required."}, status=400)
            if len(comments) > 1000:
                return JsonResponse({"error": "Comments too long. Maximum 1000 characters allowed."}, status=400)

            # Update application fields
            application.status = "Draft" 
            application.decision_date = now() 
            application.decision_status = "Draft"  
            application.comments = comments 
            application.save() 

            # Return a success response
            return JsonResponse({
                "message": "Application status updated to 'Draft'.",
                "application_id": application.id,
                "new_status": application.status,
                "last_updated_at": application.last_updated_at,
                "comments": comments,
            })

        except Exception as e:
            # Catch-all for any unexpected exceptions
            return JsonResponse({"error": str(e)}, status=500)

    # Return error for methods other than POST
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
    "Patentability Check Started",
    "Patentability Check Completed",
    "Patentability Search Report Generated",
    "Patent Filed",
    "Patent Published",
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
            "token_no": app.token_no if app.token_no else "Token not generated yet",
            "title": app.title,
            "submitted_by": applicant.name if applicant else "Unknown",
            "designation": designation_name,
            "department": department_name,
            "submitted_on": app.submitted_date.strftime("%Y-%m-%d") if app.submitted_date else "Unknown",
            "status": app.status,
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def change_application_status(request, application_id):
    REVIEW_STATUSES = [
    "Forwarded for Director's Review",
    "Director's Approval Received",
    "Patentability Check Started",
    "Patentability Check Completed",
    "Patentability Search Report Generated",
    "Patent Filed",
    "Patent Published",
    "Patent Granted",
    "Patent Refused",
    ]
    if request.method == "POST":
        try:
            # Validate if application_id is provided
            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            # Fetch the application object from the database
            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            # Parse the request body for the next status
            try:
                data = json.loads(request.body)
                next_status = data.get("next_status", "").strip()  # Remove leading/trailing whitespace
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON body."}, status=400)

            # Validate next_status field
            if not next_status:
                return JsonResponse({"error": "next_status is required."}, status=400)
            if next_status not in REVIEW_STATUSES:
                return JsonResponse({"error": f"Invalid next_status. Allowed statuses: {REVIEW_STATUSES}"}, status=400)

            # Check if the current status allows transitioning to the next status
            current_status_index = REVIEW_STATUSES.index(application.status) if application.status in REVIEW_STATUSES else -1
            next_status_index = REVIEW_STATUSES.index(next_status)

            # if next_status_index != current_status_index + 1:
            #     return JsonResponse({
            #         "error": f"Invalid status transition. Current status: '{application.status}', "
            #                  f"allowed next status: '{REVIEW_STATUSES[current_status_index + 1]}'" if current_status_index + 1 < len(REVIEW_STATUSES) else "None"
            #     }, status=400)

            # Update application status and save
            application.status = next_status
            if application.status == "Patentability Check Started":
                application.patentability_check_start_date = now()
            elif application.status == "Patentability Check Completed":
                application.patentability_check_completed_date = now()
            elif application.status == "Patentability Search Report Generated":
                application.search_report_generated_date = now()
            elif application.status == "Patent Filed":
                application.patent_filed_date = now()
            elif application.status == "Patent Published":
                application.patent_published_date = now()
            elif application.status == "Patent Granted":
                application.patent_granted_date = now()
                application.decision_status = "Approved"
                application.decision_date = now()
            elif application.status == "Patent Refused":
                application.patent_refused_date = now()
                application.decision_status = "Rejected"
                application.decision_date = now()
            application.save()

            # Return a success response
            return JsonResponse({
                "message": f"Application status updated to '{next_status}'.",
                "application_id": application.id,
                "new_status": application.status,
                "last_updated_at": application.last_updated_at,
            })

        except Exception as e:
            # Catch-all for any unexpected exceptions
            return JsonResponse({"error": str(e)}, status=500)

    # Return error for methods other than POST
    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

# For past applications tab
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def past_applications(request):
    DECISION_STATUSES = [
        "Approved", 
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
            "decision_status": app.decision_status,
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def view_application_details_for_pccAdmin(request, application_id):
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
        "type_of_ip": section_i.type_of_ip if section_i else None,
        "area": section_i.area if section_i else None,
        "problem": section_i.problem if section_i else None,
        "objective": section_i.objective if section_i else None,
        "novelty": section_i.novelty if section_i else None,
        "advantages": section_i.advantages if section_i else None,
        "is_tested": section_i.is_tested if section_i else None,
        "poc_details": section_i.poc_details.url if section_i and section_i.poc_details else None,
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
        "last_updated_at": application.last_updated_at,
        "token_no": application.token_no,
        "primary_applicant_name": primary_applicant_name,
        "title": application.title,
        "status": application.status,
        "attorney_name": attorney_name,
        "dates": {
            "submitted_date": application.submitted_date if application.submitted_date else None,
            "reviewed_by_pcc_date": application.reviewed_by_pcc_date,
            "forwarded_to_director_date": application.forwarded_to_director_date,
            "director_approval_date": application.director_approval_date,
            "patentability_check_start_date": application.patentability_check_start_date,
            "patentability_check_completed_date": application.patentability_check_completed_date,
            "search_report_generated_date": application.search_report_generated_date,
            "patent_filed_date": application.patent_filed_date,
            "patent_published_date": application.patent_published_date,
            "decision_date": application.decision_date
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_new_applications(request):
    applications = Application.objects.filter(
        status="Forwarded for Director's Review"
    ).select_related("primary_applicant", "attorney")

    application_dict = {}

    for app in applications:
        applicant = app.primary_applicant
        user = applicant.user if applicant else None

        # Get department name from ExtraInfo
        extra_info = ExtraInfo.objects.filter(user=user).first()
        department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

        # Get attorney name using foreign key
        assigned_attorney = app.attorney.name if app.attorney else "Not Assigned"

        # Unique key for dictionary
        key = app.id

        # Build the application summary
        application_dict[key] = {
            "token_no": app.token_no if app.token_no else "Token not generated",
            "title": app.title,
            "submitted_by": applicant.name if applicant else "Unknown",
            "department": department_name,
            "forwarde_on": app.forwarded_to_director_date.strftime("%Y-%m-%d %H:%M:%S") if app.forwarded_to_director_date else "Unknown",
            "assigned_attorney": assigned_attorney,
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_reject(request):
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
                "message": "Application status updated to Rejected",
                "application_id": application.id,
                "new_status": application.status
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_accept(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            application_id = data.get("application_id")
            attorney_id = data.get("attorney_id")
            comments = data.get("comments", "")

            # Validate required fields
            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            # Status check
            if application.status != "Forwarded for Director's Review":
                return JsonResponse({
                    "error": f"Application must be in 'Forwarded for Director's Review' status. Current status: {application.status}"
                }, status=400)

            # Process attorney assignment
            attorney = None
            if attorney_id:
                try:
                    attorney = Attorney.objects.get(id=attorney_id)
                    if not application.attorney or application.attorney.id != attorney.id:
                        application.attorney = attorney
                except Attorney.DoesNotExist:
                    return JsonResponse({"error": f"Attorney with ID '{attorney_id}' not found."}, status=404)

            # Get department name using your provided logic
            applicant = application.primary_applicant
            user = applicant.user if applicant else None
            extra_info = ExtraInfo.objects.filter(user=user).first() if user else None
            department_name = (
                extra_info.department.name[:3].upper() 
                if extra_info and extra_info.department 
                else "UNK"
            )
            
            # Retrieving the submission date
            submitted_date = application.submitted_date

            # Generate reference number components
            app_id_part = f"{application.id:06d}"  # 6-digit format
            attorney_initials = (
                attorney.name.replace(" ", "")[:3].upper() 
                if attorney 
                else "XXX"
            )
            
            # Generate serial number (example implementation - adjust as needed)
            last_serial = Application.objects.filter(
                token_no__isnull=False
            ).order_by('-id').first()
            serial_number = int(last_serial.token_no.split('/')[-1]) + 1 if last_serial else 104

            # Construct the complete reference number
            token_no = (
                f"IIITDMJ/"
                f"{department_name}/"
                f"{submitted_date}/"
                f"{app_id_part}/"
                f"{attorney_initials}/"
                f"{serial_number:03d}"  # 3-digit serial number
            )

            # Update application fields
            if comments:
                if len(comments) > 1000:
                    return JsonResponse({"error": "Comments too long. Max 1000 characters allowed."}, status=400)
                application.comments = comments

            application.status = "Director's Approval Received"
            application.decision_date = now()
            application.decision_status = "Director's Approval Received"
            application.token_no = token_no
            application.save()

            return JsonResponse({
                "message": "Director's Approval Received",
                "application_id": application.id,
                "new_status": application.status,
                "token_no": token_no,
                "attorney_id": application.attorney.id if application.attorney else None,
                "attorney_name": application.attorney.name if application.attorney else None,
                "comments": comments
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_reviewed_applications(request):
    # Define the list of statuses to include
    reviewed_statuses = [
        "Director's Approval Received",
        "Patentability Check Started",
        "Patentability Check Completed",
        "Patentability Search Report Generated",
        "Patent Filed",
        "Patent Published",
        "Patent Granted",
        "Patent Refused",
    ]

    applications = Application.objects.filter(
        status__in=reviewed_statuses
    ).select_related("primary_applicant", "attorney")

    application_dict = {}

    for app in applications:
        applicant = app.primary_applicant
        user = applicant.user if applicant else None

        # Get department name from ExtraInfo
        extra_info = ExtraInfo.objects.filter(user=user).first()
        department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

        # Get attorney name using foreign key
        assigned_attorney = app.attorney.name if app.attorney else "Not Assigned"

        # Unique key for dictionary
        key = app.id

        # Build the application summary
        application_dict[key] = {
            "token_no": app.token_no if app.token_no else "Token not generated",
            "title": app.title, 
            "submitted_by": applicant.name if applicant else "Unknown",
            "department": department_name,
            "arrival_date": app.forwarded_to_director_date if app.submitted_date else "Unknown",
            "reviewed_date": app.decision_date if app.decision_date else "Unknown",
            "assigned_attorney": assigned_attorney,
            "current_status": app.status,
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def active_applications(request):
    # Define statuses relevant to active applications
    active_statuses = [
        "Director's Approval Received",
        "Patentability Check Started",
        "Patentability Check Completed",
        "Patentability Search Report Generated",
        "Patent Filed",
        "Patent Published",
        "Patent Granted",
        "Patent Refused",
    ]

    applications = Application.objects.filter(
        status__in=active_statuses,
        decision_status="Pending"
    ).select_related("primary_applicant", "attorney")

    application_dict = {}

    for app in applications:
        applicant = app.primary_applicant
        user = applicant.user if applicant else None

        # Get department name from ExtraInfo
        extra_info = ExtraInfo.objects.filter(user=user).first()
        department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

        # Get attorney name using foreign key
        assigned_attorney = app.attorney.name if app.attorney else "Not Assigned"

        # Unique key for dictionary
        key = str(app.token_no) if app.token_no else f"app_{app.id}"

        # Build the application summary
        application_dict[key] = {
            "token_no": app.token_no if app.token_no else "Token not generated",
            "title": app.title,
            "submitted_by": applicant.name if applicant else "Unknown",
            "department": department_name,
            "submitted_on": app.submitted_date if app.submitted_date else "Unknown",
            "assigned_attorney": assigned_attorney,
            "current_status": app.status,
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_notifications(request):
    return JsonResponse({"notifications": ["New submission", "Pending review"]})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_application_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')

        if not application_id:
            return JsonResponse({'error': 'application_id is required in the request body.'}, status=400)

        # Fetch application details
        application = get_object_or_404(Application, id=application_id)

        # Fetch primary applicant details
        primary_applicant_name = None
        if application.primary_applicant_id:
            primary_applicant = Applicant.objects.filter(id=application.primary_applicant_id).first()
            primary_applicant_name = primary_applicant.name if primary_applicant else None

        # Fetch attorney details
        attorney_name = None
        if application.attorney_id:
            attorney = Attorney.objects.filter(id=application.attorney_id).first()
            attorney_name = attorney.name if attorney else None

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

        # Fetch Section I
        section_i = ApplicationSectionI.objects.filter(application=application).first()
        section_i_data = {
            "type_of_ip": section_i.type_of_ip if section_i else None,
            "area": section_i.area if section_i else None,
            "problem": section_i.problem if section_i else None,
            "objective": section_i.objective if section_i else None,
            "novelty": section_i.novelty if section_i else None,
            "advantages": section_i.advantages if section_i else None,
            "is_tested": section_i.is_tested if section_i else None,
            "poc_details": section_i.poc_details.url if section_i and section_i.poc_details else None,
            "applications": section_i.applications if section_i else None,
        }

        # Fetch Section II
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

        # Fetch Section III
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
            "last_updated_at": application.last_updated_at,
            "token_no": application.token_no,
            "primary_applicant_name": primary_applicant_name,
            "title": application.title,
            "status": application.status,
            "attorney_name": attorney_name,
            "dates": {
                "submitted_date": application.submitted_date,
                "reviewed_by_pcc_date": application.reviewed_by_pcc_date,
                "forwarded_to_director_date": application.forwarded_to_director_date,
                "director_approval_date": application.director_approval_date,
                "patentability_check_start_date": application.patentability_check_start_date,
                "patentability_check_completed_date": application.patentability_check_completed_date,
                "search_report_generated_date": application.search_report_generated_date,
                "patent_filed_date": application.patent_filed_date,
                "patent_published_date": application.patent_published_date,
                "decision_date": application.decision_date,
            },
            "decision_status": application.decision_status,
            "comments": application.comments,
            "applicants": applicants_data,
            "section_I": section_i_data,
            "section_II": section_ii_data,
            "section_III": section_iii_data
        }

        return JsonResponse(response_data, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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