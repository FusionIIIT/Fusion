import os
import json
import logging
from datetime import timedelta
from decimal import Decimal

from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.db.models import Count

from ..models import (
    Application,
    ApplicationSectionI,
    ApplicationSectionII,
    ApplicationSectionIII,
    AssociatedWith,
    Applicant,
    AppealRequest,
    Attorney,
    AuditLog,
    BudgetApproval,
    Document,
    DocumentVersion,
    ExternalFilingRecord,
    InventorConsent,
    LegalAdviceMemo,
    LegalAssessment,
    LicensingRequest,
    MaintenanceSchedule,
    NotificationEvent,
    OfficeAction,
    OfficeActionResponse,
    PriorArtReference,
    CommunicationLog,
    ConflictDeclaration,
)

from applications.globals.models import (
    Designation,
    DepartmentInfo,
    ExtraInfo,
    HoldsDesignation,
)

from .serializers import (
    AppealRequestSerializer,
    AttorneySerializer,
    AuditLogSerializer,
    BudgetApprovalSerializer,
    CommunicationLogSerializer,
    ConflictDeclarationSerializer,
    DocumentSerializer,
    DocumentVersionSerializer,
    ExternalFilingRecordSerializer,
    InventorConsentSerializer,
    LegalAdviceMemoSerializer,
    LegalAssessmentSerializer,
    LicensingRequestSerializer,
    MaintenanceScheduleSerializer,
    NotificationEventSerializer,
    OfficeActionResponseSerializer,
    OfficeActionSerializer,
    PriorArtReferenceSerializer,
)

from ..selectors import (
    applicant_applications,
    applications_by_status,
    applications_by_decision_status,
    get_communication_logs,
    get_budget_approvals,
    get_office_actions,
    get_prior_art_references,
    get_legal_assessments,
    get_legal_advice_memos,
    get_licensing_requests,
    get_inventor_consents,
    get_maintenance_schedules,
    get_appeal_requests,
    get_external_filing_records,
    get_conflict_declarations,
    get_documents,
    get_document_versions,
    get_attorney_applications,
    get_pcc_admin_queue,
    get_director_queue,
    count_by_status,
    count_by_decision_status,
)

from ..services import (
    role_names_for_user as _role_names,
    is_pcc_admin_user as _is_pcc_admin_user,
    is_director_user as _is_director_user,
    get_director_users as _get_director_users,
    is_authorized_applicant_user as _is_authorized_applicant_user,
    get_attorney_for_user as _get_attorney_for_user,
    is_attorney_user as _is_attorney_user,
    require_comments as _require_comments,
    create_audit as _create_audit,
    notify as _notify,
    reviewer_workload as _reviewer_workload,
    move_application_to_revision as _move_application_to_revision,
    record_budget_request as _record_budget_request,
)

logger = logging.getLogger(__name__)


def index(request):
    return JsonResponse(
        {
            "message": "Patent Management module is running.",
            "routes": [
                "/patentsystem/applicant/applications/submit/",
                "/patentsystem/applicant/applications/",
                "/patentsystem/pccAdmin/applications/new/",
                "/patentsystem/pccAdmin/applications/past/",
                "/patentsystem/director/applications/new/",
            ],
        }
    )

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
            if not _is_authorized_applicant_user(user):
                return JsonResponse(
                    {
                        "error": (
                            "Only authorized applicants, including faculty roles, can submit patent applications."
                        )
                    },
                    status=403,
                )

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
        
        # Retrieve applications where the user is primary applicant or associated inventor
        applications = (
            Application.objects.filter(
                Q(primary_applicant=applicant) | Q(id__in=associated_apps)
            )
            .select_related("attorney")
            .distinct()
            .order_by("-last_updated_at")
        )
        
        # Prepare response data
        applications_data = []
        for app in applications:
            applications_data.append({
                "application_id": app.id,
                "title": app.title,
                "token_no": app.token_no,
                "application_number": app.token_no,
                "attorney_name": app.attorney.name if app.attorney else None,
                "submitted_date": app.submitted_date if app.submitted_date else None,
                "status": app.status,
                "decision_status": app.decision_status,
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

    # Fetch application details
    application = get_object_or_404(Application, id=application_id)

    # Primary applicant or associated inventor can view details
    is_primary_applicant = application.primary_applicant_id == applicant.id
    is_associated = AssociatedWith.objects.filter(application_id=application_id, applicant=applicant).exists()
    if not (is_primary_applicant or is_associated):
        return JsonResponse({"error": "Forbidden: You are not associated with this application"}, status=403)

    handler_name = None
    if application.assigned_pcc_admin_id:
        handler_name = application.assigned_pcc_admin.get_full_name() or application.assigned_pcc_admin.username

    director_name = None
    if application.assigned_director_id:
        director_name = application.assigned_director.get_full_name() or application.assigned_director.username

    attorney_name = application.attorney.name if application.attorney else None

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
        "assigned_pcc_admin": handler_name,
        "assigned_director": director_name,
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
        "budget_estimate": str(application.budget_estimate) if application.budget_estimate is not None else None,
        "budget_status": application.budget_status,
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
    try:
        REVIEW_STATUSES = ["Submitted", "Reviewed by PCC Admin"]

        applications = Application.objects.filter(status__in=REVIEW_STATUSES).select_related("primary_applicant")

        application_dict = {}  # Using a dictionary instead of a list

        for app in applications:
            try:
                applicant = app.primary_applicant  # Get the Applicant instance

                # Ensure applicant exists and fetch the linked User
                user = applicant.user if applicant else None

                # Fetch extra info (assuming ExtraInfo is linked to User)
                extra_info = ExtraInfo.objects.filter(user=user).first() if user else None

                # Fetch department
                department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

                # Fetch designation (get latest held designation)
                holds_designation = HoldsDesignation.objects.filter(user=user).select_related("designation").first() if user else None
                designation_name = holds_designation.designation.name if holds_designation else "Unknown"

                # Format response as a dictionary
                application_dict[app.id] = {
                    "title": app.title,
                    "submitted_by": applicant.name if applicant else "Unknown",
                    "designation": designation_name,
                    "department": department_name,
                    "submitted_on": app.submitted_date.strftime("%Y-%m-%d") if app.submitted_date else "Unknown"
                }
            except Exception as app_error:
                logger.error(f"Error processing application {app.id}: {str(app_error)}")
                continue

        return JsonResponse({"applications": application_dict}, safe=False)
    except Exception as err:
        logger.error(f"Error in new_applications: {str(err)}")
        return JsonResponse({"error": str(err)}, status=500)

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

            # Enforce workflow stage: only Submitted applications can be reviewed.
            if application.status == "Reviewed by PCC Admin":
                return JsonResponse({"message": "Application already reviewed."})
            if application.status != "Submitted":
                return JsonResponse(
                    {
                        "error": (
                            "Only applications in 'Submitted' state can be reviewed. "
                            f"Current status: {application.status}"
                        )
                    },
                    status=400,
                )

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
            application.assigned_pcc_admin = request.user
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
            if not _is_pcc_admin_user(request.user):
                return JsonResponse(
                    {"error": "Only PCC Admin can assign attorneys and forward applications."},
                    status=403,
                )

            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            # Get the application
            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            # Enforce workflow stage and PCC ownership.
            if application.status == "Forwarded for Director's Review":
                return JsonResponse({"message": "Application is already forwarded for Director's review."}, status=400)
            if application.status != "Reviewed by PCC Admin":
                return JsonResponse(
                    {
                        "error": (
                            "Only applications in 'Reviewed by PCC Admin' state can be forwarded. "
                            f"Current status: {application.status}"
                        )
                    },
                    status=400,
                )
            if application.assigned_pcc_admin_id and application.assigned_pcc_admin_id != request.user.id:
                owner = application.assigned_pcc_admin
                owner_name = owner.get_full_name().strip() if owner and owner.get_full_name() else (owner.username if owner else "Unknown")
                return JsonResponse(
                    {
                        "error": f"Application is assigned to another PCC Admin: {owner_name}.",
                        "assigned_pcc_admin": owner_name,
                    },
                    status=403,
                )

            # Parse JSON body
            try:
                data = json.loads(request.body)
                external_attorney_name = data.get("attorney_name", "").strip()
                external_attorney_email = data.get("attorney_email", "").strip()
                director_user_id = data.get("director_user_id")
                budget_estimate = data.get("budget_estimate")
                comments = _require_comments(data)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON body."}, status=400)
            except ValueError as exc:
                return JsonResponse({"error": str(exc)}, status=400)

            if not external_attorney_name:
                return JsonResponse({"error": "attorney_name is required in the request body."}, status=400)

            attorney = Attorney.objects.filter(name__iexact=external_attorney_name).first()
            if not attorney:
                return JsonResponse(
                    {"error": f"Attorney with name '{external_attorney_name}' not found."},
                    status=404,
                )

            director_users = list(_get_director_users())
            if not director_users:
                return JsonResponse(
                    {"error": "No Director user is configured. Please assign Director designation first."},
                    status=400,
                )

            director_user = None
            if director_user_id not in [None, ""]:
                try:
                    director_user_id = int(director_user_id)
                except (TypeError, ValueError):
                    return JsonResponse({"error": "director_user_id must be an integer."}, status=400)

                director_user = next((u for u in director_users if u.id == director_user_id), None)
                if not director_user:
                    return JsonResponse(
                        {"error": "Selected director is invalid or does not hold Director role."},
                        status=400,
                    )
            elif application.assigned_director_id:
                director_user = application.assigned_director
            elif len(director_users) == 1:
                director_user = director_users[0]
            else:
                return JsonResponse(
                    {
                        "error": "director_user_id is required because multiple directors are available.",
                        "available_directors": [
                            {
                                "id": user.id,
                                "username": user.username,
                                "full_name": (user.get_full_name() or user.username),
                            }
                            for user in director_users
                        ],
                    },
                    status=400,
                )

            # Optional: Limit comment length
            if comments and len(comments) > 1000:
                return JsonResponse({"error": "Comments too long. Max 1000 characters allowed."}, status=400)

            if budget_estimate not in [None, ""]:
                try:
                    budget_estimate = Decimal(str(budget_estimate))
                except Exception:
                    return JsonResponse({"error": "budget_estimate must be a valid number."}, status=400)
                if budget_estimate < 0:
                    return JsonResponse({"error": "budget_estimate cannot be negative."}, status=400)

                application.budget_estimate = budget_estimate
                application.budget_status = "Pending Approval"
            else:
                application.budget_status = application.budget_status or "Not Initiated"

            # Update the application
            application.status = "Forwarded for Director's Review"
            application.forwarded_to_director_date = now()
            application.assigned_pcc_admin = request.user
            application.assigned_director = director_user
            application.attorney = attorney
            application.comments = comments
            application.save()

            if hasattr(attorney, "current_workload"):
                attorney.current_workload = Application.objects.filter(attorney=attorney).count()
                attorney.save(update_fields=["current_workload"])

            if comments or external_attorney_name or external_attorney_email:
                CommunicationLog.objects.create(
                    application=application,
                    logged_by=request.user,
                    external_attorney_name=external_attorney_name or None,
                    external_attorney_email=external_attorney_email or None,
                    message_content=comments or "Application forwarded by PCC Admin",
                    status_or_notes="Forwarded to Director",
                )

            _create_audit(
                "PCC Forwarded Application",
                request.user,
                application,
                f"Forwarded to director with attorney {attorney.name}",
            )
            _notify(
                application,
                f"Application {application.title} has been forwarded to Director {(director_user.get_full_name() or director_user.username)}.",
                recipient=director_user,
                event_type="Status Update",
            )

            return JsonResponse({
                "message": "Application forwarded to director.",
                "application_id": application.id,
                "new_status": application.status,
                "forwarded_to_director_date": application.forwarded_to_director_date,
                "assigned_pcc_admin": request.user.get_full_name() or request.user.username,
                "assigned_director": director_user.get_full_name() or director_user.username,
                "assigned_director_id": director_user.id,
                "budget_estimate": str(application.budget_estimate) if application.budget_estimate is not None else None,
                "budget_status": application.budget_status,
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
            if not _is_pcc_admin_user(request.user):
                return JsonResponse(
                    {"error": "Only PCC Admin can request application modification."},
                    status=403,
                )

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

            allowed_statuses = [
                "Submitted",
                "Reviewed by PCC Admin",
                "Forwarded for Director's Review",
                "Returned to Director",
            ]
            if application.status not in allowed_statuses:
                return JsonResponse(
                    {
                        "error": (
                            "Modification can be requested only before detailed patent processing starts. "
                            f"Current status: {application.status}"
                        )
                    },
                    status=400,
                )

            # Parse the request body for comments
            try:
                data = json.loads(request.body)
                comments = _require_comments(data)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON body."}, status=400)
            except ValueError as exc:
                return JsonResponse({"error": str(exc)}, status=400)

            # Move to revision state and notify applicant.
            application.status = "Needs Revision"
            application.revision_requested_at = now()
            application.revision_due_date = (now() + timedelta(days=60)).date()
            application.is_revision_locked = False
            application.comments = comments
            application.assigned_pcc_admin = request.user
            application.save()

            applicant_user = (
                application.primary_applicant.user
                if application.primary_applicant and application.primary_applicant.user_id
                else None
            )
            _notify(
                application,
                "PCC Admin requested modifications. Please update and resubmit.",
                recipient=applicant_user,
                recipient_role="Applicant",
                event_type="Status Update",
                due_date=application.revision_due_date,
            )

            # Return a success response
            return JsonResponse({
                "message": "Application status updated to 'Needs Revision'.",
                "application_id": application.id,
                "new_status": application.status,
                "last_updated_at": application.last_updated_at,
                "revision_due_date": application.revision_due_date,
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
    try:
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
            try:
                applicant = app.primary_applicant  # Get the Applicant instance

                # Ensure applicant exists and fetch the linked User
                user = applicant.user if applicant else None

                # Fetch extra info (assuming ExtraInfo is linked to User)
                extra_info = ExtraInfo.objects.filter(user=user).first() if user else None

                # Fetch department
                department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

                # Fetch designation (get latest held designation)
                holds_designation = HoldsDesignation.objects.filter(user=user).select_related("designation").first() if user else None
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
            except Exception as app_error:
                logger.error(f"Error processing application {app.id}: {str(app_error)}")
                continue

        return JsonResponse({"applications": application_dict}, safe=False)
    except Exception as err:
        logger.error(f"Error in ongoing_applications: {str(err)}")
        return JsonResponse({"error": str(err)}, status=500)

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
    # Normalize status strings to protect transitions from stray whitespace in DB/UI payloads.
    normalized_statuses = [status.strip() for status in REVIEW_STATUSES]
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
            if next_status not in normalized_statuses:
                return JsonResponse({"error": f"Invalid next_status. Allowed statuses: {normalized_statuses}"}, status=400)

            if application.assigned_pcc_admin_id and application.assigned_pcc_admin_id != request.user.id:
                owner = application.assigned_pcc_admin
                owner_name = owner.get_full_name().strip() if owner and owner.get_full_name() else (owner.username if owner else "Unknown")
                return JsonResponse(
                    {
                        "error": f"Application is assigned to another PCC Admin: {owner_name}.",
                        "assigned_pcc_admin": owner_name,
                    },
                    status=403,
                )

            # Check if the current status allows transitioning to the next status
            current_status = (application.status or "").strip()
            current_status_index = normalized_statuses.index(current_status) if current_status in normalized_statuses else -1
            next_status_index = normalized_statuses.index(next_status)

            if current_status_index == -1:
                return JsonResponse(
                    {
                        "error": (
                            "Current application status is not in ongoing workflow states. "
                            f"Current status: {application.status}"
                        )
                    },
                    status=400,
                )

            if next_status == "Patent Refused":
                if current_status in ["Patent Granted", "Patent Refused"]:
                    return JsonResponse(
                        {
                            "error": (
                                f"Invalid status transition from '{current_status}' to '{next_status}'. "
                                "The application is already in a terminal decision state."
                            )
                        },
                        status=400,
                    )

                application.status = next_status
                application.patent_refused_date = now()
                application.decision_status = "Rejected"
                application.decision_date = now()
                application.save()

                return JsonResponse({
                    "message": f"Application status updated to '{next_status}'.",
                    "application_id": application.id,
                    "new_status": application.status,
                    "last_updated_at": application.last_updated_at,
                })

            if next_status_index != current_status_index + 1:
                allowed_next = normalized_statuses[current_status_index + 1] if current_status_index + 1 < len(normalized_statuses) else None
                return JsonResponse(
                    {
                        "error": (
                            f"Invalid status transition from '{current_status}' to '{next_status}'. "
                            f"Allowed next status: '{allowed_next}'."
                        )
                    },
                    status=400,
                )

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
    try:
        DECISION_STATUSES = [
            "Approved", 
            "Rejected",
        ]

        applications = Application.objects.filter(decision_status__in=DECISION_STATUSES).select_related("primary_applicant")

        application_dict = {}  # Using a dictionary instead of a list

        for app in applications:
            try:
                applicant = app.primary_applicant  # Get the Applicant instance

                # Ensure applicant exists and fetch the linked User
                user = applicant.user if applicant else None

                # Fetch extra info (assuming ExtraInfo is linked to User)
                extra_info = ExtraInfo.objects.filter(user=user).first() if user else None

                # Fetch department
                department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

                # Fetch designation (get latest held designation)
                holds_designation = HoldsDesignation.objects.filter(user=user).select_related("designation").first() if user else None
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
            except Exception as app_error:
                logger.error(f"Error processing application {app.id}: {str(app_error)}")
                continue

        return JsonResponse({"applications": application_dict}, safe=False)
    except Exception as err:
        logger.error(f"Error in past_applications: {str(err)}")
        return JsonResponse({"error": str(err)}, status=500)

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

    handler_name = None
    if application.assigned_pcc_admin_id:
        handler_name = application.assigned_pcc_admin.get_full_name() or application.assigned_pcc_admin.username

    director_name = None
    if application.assigned_director_id:
        director_name = application.assigned_director.get_full_name() or application.assigned_director.username

    attorney_name = application.attorney.name if application.attorney else None

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
        "assigned_pcc_admin": handler_name,
        "assigned_director": director_name,
        "attorney_name": attorney_name,
        "communication_logs": CommunicationLogSerializer(application.communication_logs.all(), many=True).data,
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
        "budget_estimate": str(application.budget_estimate) if application.budget_estimate is not None else None,
        "budget_status": application.budget_status,
        "applicants": applicants_data,
        "section_I": section_i_data,
        "section_II": section_ii_data,
        "section_III": section_iii_data
    }

    return JsonResponse(response_data, safe=False)

# -----------------------------------------
# 🔹 Director Views
# -----------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def attorney_forward_to_director(request, app_id):
    if not _is_attorney_user(request.user):
        return JsonResponse({"error": "Only Attorney users can forward applications to Director."}, status=403)

    application = get_object_or_404(Application, id=app_id)
    attorney = _get_attorney_for_user(request.user)
    if not attorney:
        return JsonResponse({"error": "No attorney profile is linked to this account."}, status=403)

    if application.attorney_id != attorney.id:
        return JsonResponse({"error": "This application is not assigned to the current attorney."}, status=403)

    if application.status != "Attorney Assigned":
        return JsonResponse(
            {"error": f"Application must be in 'Attorney Assigned' status. Current status: {application.status}"},
            status=400,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    try:
        comments = _require_comments(data, key="comments")
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    application.attorney_review_notes = comments
    application.attorney_reviewed_at = now()
    application.status = "Returned to Director"
    application.decision_status = "Reviewed by Attorney"
    application.save()

    _create_audit(
        "Attorney Forwarded Application",
        request.user,
        application,
        f"Attorney {attorney.name} forwarded application back to director",
    )
    _notify(
        application,
        f"Attorney completed the assessment for {application.title} and returned it to Director.",
        recipient_role="Director",
        event_type="Status Update",
    )

    return JsonResponse(
        {
            "message": "Application returned to Director.",
            "application_id": application.id,
            "new_status": application.status,
            "comments": comments,
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def attorney_applications(request):
    if not _is_attorney_user(request.user):
        return JsonResponse({"error": "Only Attorney users can access this queue."}, status=403)

    attorney = _get_attorney_for_user(request.user)
    if not attorney:
        return JsonResponse({"error": "No attorney profile is linked to this account."}, status=403)

    applications = (
        Application.objects.filter(attorney=attorney, status__in=["Attorney Assigned", "Returned to Director"])
        .select_related("primary_applicant", "attorney")
        .order_by("-last_updated_at")
    )

    payload = []
    for application in applications:
        payload.append(
            {
                "application_id": application.id,
                "title": application.title,
                "status": application.status,
                "token_no": application.token_no,
                "comments": application.comments,
                "attorney_review_notes": application.attorney_review_notes,
                "attorney_reviewed_at": application.attorney_reviewed_at,
                "applicant_name": application.primary_applicant.name if application.primary_applicant else None,
                "submitted_date": application.submitted_date,
            }
        )

    return JsonResponse({"applications": payload}, safe=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_new_applications(request):
    try:
        if not _is_director_user(request.user):
            return JsonResponse({"error": "Only Director can access this queue."}, status=403)

        applications = Application.objects.filter(
            status__in=["Forwarded for Director's Review", "Returned to Director"]
        ).filter(
            Q(assigned_director=request.user) | Q(assigned_director__isnull=True)
        ).select_related("primary_applicant", "assigned_pcc_admin", "assigned_director", "attorney")

        application_dict = {}

        for app in applications:
            try:
                applicant = app.primary_applicant
                user = applicant.user if applicant else None

                # Get department name from ExtraInfo
                extra_info = ExtraInfo.objects.filter(user=user).first() if user else None
                department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

                assigned_pcc_admin = app.assigned_pcc_admin.get_full_name() if app.assigned_pcc_admin else "PCC Admin"
                assigned_director = app.assigned_director.get_full_name() if app.assigned_director else "Not Assigned"
                assigned_attorney = app.attorney.name if app.attorney else "Attorney not assigned"

                # Unique key for dictionary
                key = app.id

                # Build the application summary
                application_dict[key] = {
                    "token_no": app.token_no if app.token_no else "Token not generated",
                    "title": app.title,
                    "submitted_by": applicant.name if applicant else "Unknown",
                    "department": department_name,
                    "forwarded_on": app.forwarded_to_director_date.strftime("%Y-%m-%d") if app.forwarded_to_director_date else "Unknown",
                    "assigned_pcc_admin": assigned_pcc_admin,
                    "assigned_director": assigned_director,
                    "assigned_attorney": assigned_attorney,
                    "budget_estimate": str(app.budget_estimate) if app.budget_estimate is not None else None,
                    "budget_status": app.budget_status,
                    "current_status": app.status,
                }
            except Exception as app_error:
                logger.error(f"Error processing application {app.id}: {str(app_error)}")
                continue

        return JsonResponse({"applications": application_dict}, safe=False)
    except Exception as err:
        logger.error(f"Error in director_new_applications: {str(err)}")
        return JsonResponse({"error": str(err)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_reject(request):
    if request.method == "POST":
        try:
            if not _is_director_user(request.user):
                return JsonResponse({"error": "Only Director can reject applications."}, status=403)

            data = json.loads(request.body)
            application_id = data.get("application_id")
            comments = _require_comments(data)

            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            if application.status not in ["Forwarded for Director's Review", "Returned to Director"]:
                return JsonResponse(
                    {
                        "error": (
                            "Application must be in 'Forwarded for Director's Review' or 'Returned to Director' status to reject. "
                            f"Current status: {application.status}"
                        )
                    },
                    status=400,
                )

            if application.assigned_director_id and application.assigned_director_id != request.user.id:
                assigned_name = application.assigned_director.get_full_name() or application.assigned_director.username
                return JsonResponse(
                    {"error": f"Application is assigned to another director: {assigned_name}."},
                    status=403,
                )
            if not application.assigned_director_id:
                application.assigned_director = request.user

            application.comments = comments
            # Director rejection returns the application to PCC Admin for the next routing decision.
            application.status = "Reviewed by PCC Admin"
            application.decision_date = now()
            application.decision_status = "Needs Revision"
            application.is_revision_locked = True
            application.save()

            CommunicationLog.objects.create(
                application=application,
                logged_by=request.user,
                message_content=comments,
                status_or_notes="Director requested revision",
            )

            _create_audit(
                'Director Rejected Application',
                request.user,
                application,
                f'Director requested PCC Admin revision routing. Comments: {comments}',
            )
            _notify(
                application,
                "Director requested revisions. PCC Admin will route feedback to the applicant.",
                recipient_role="PCC Admin",
                event_type="Status Update",
            )

            return JsonResponse({
                "message": "Application sent back to PCC Admin for further action",
                "application_id": application.id,
                "new_status": application.status,
                "comments": comments,
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_accept(request):
    if request.method == "POST":
        try:
            if not _is_director_user(request.user):
                return JsonResponse({"error": "Only Director can approve applications."}, status=403)

            data = json.loads(request.body)
            application_id = data.get("application_id")
            comments = _require_comments(data)

            # Validate required fields
            if not application_id:
                return JsonResponse({"error": "Application ID is required."}, status=400)

            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                return JsonResponse({"error": "Application not found."}, status=404)

            # Status check
            if application.status not in ["Forwarded for Director's Review", "Returned to Director"]:
                return JsonResponse({
                    "error": f"Application must be in 'Forwarded for Director's Review' or 'Returned to Director' status. Current status: {application.status}"
                }, status=400)

            if application.assigned_director_id and application.assigned_director_id != request.user.id:
                assigned_name = application.assigned_director.get_full_name() or application.assigned_director.username
                return JsonResponse(
                    {"error": f"Application is assigned to another director: {assigned_name}."},
                    status=403,
                )
            if not application.assigned_director_id:
                application.assigned_director = request.user

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
            handler_initials = (
                (application.assigned_pcc_admin.get_full_name() or application.assigned_pcc_admin.username).replace(" ", "")[:3].upper()
                if application.assigned_pcc_admin
                else "PCA"
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
                f"{handler_initials}/"
                f"{serial_number:03d}"  # 3-digit serial number
            )

            # Update application fields
            application.comments = comments

            # After director approval, application returns to PCC Admin workflow stage.
            application.status = "Director's Approval Received"
            application.director_approval_date = now()
            application.decision_status = "Pending"
            application.token_no = token_no
            application.save()

            CommunicationLog.objects.create(
                application=application,
                logged_by=request.user,
                message_content=comments,
                status_or_notes="Director approved and forwarded",
            )

            _create_audit(
                'Director Approved Application',
                request.user,
                application,
                f'Director approved application and returned it to PCC Admin stage. Comments: {comments}',
            )
            _notify(
                application,
                f"Director approved application {application.title}.",
                recipient_role="PCC Admin",
                event_type="Status Update",
            )

            return JsonResponse({
                "message": "Director's Approval Received",
                "application_id": application.id,
                "new_status": application.status,
                "token_no": token_no,
                "assigned_pcc_admin": application.assigned_pcc_admin.get_full_name() if application.assigned_pcc_admin else None,
                "attorney_name": application.attorney.name if application.attorney else None,
                "comments": comments
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_reviewed_applications(request):
    if not _is_director_user(request.user):
        return JsonResponse({"error": "Only Director can access this queue."}, status=403)

    # Define the list of statuses to include
    reviewed_statuses = [
        "Director's Approval Received",
        "Attorney Assigned",
        "Returned to Director",
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
    ).filter(
        Q(assigned_director=request.user) | Q(assigned_director__isnull=True)
    ).select_related("primary_applicant", "assigned_pcc_admin", "attorney")

    application_dict = {}

    for app in applications:
        applicant = app.primary_applicant
        user = applicant.user if applicant else None

        # Get department name from ExtraInfo
        extra_info = ExtraInfo.objects.filter(user=user).first()
        department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

        assigned_pcc_admin = app.assigned_pcc_admin.get_full_name() if app.assigned_pcc_admin else "PCC Admin"
        assigned_attorney = app.attorney.name if app.attorney else "Attorney not assigned"

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
            "assigned_pcc_admin": assigned_pcc_admin,
            "assigned_attorney": assigned_attorney,
            "budget_estimate": str(app.budget_estimate) if app.budget_estimate is not None else None,
            "budget_status": app.budget_status,
            "current_status": app.status,
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def active_applications(request):
    if not _is_director_user(request.user):
        return JsonResponse({"error": "Only Director can access this queue."}, status=403)

    # Define statuses relevant to active applications
    active_statuses = [
        "Director's Approval Received",
        "Attorney Assigned",
        "Returned to Director",
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
    ).filter(
        Q(assigned_director=request.user) | Q(assigned_director__isnull=True)
    ).select_related("primary_applicant", "assigned_pcc_admin", "attorney")

    application_dict = {}

    for app in applications:
        applicant = app.primary_applicant
        user = applicant.user if applicant else None

        # Get department name from ExtraInfo
        extra_info = ExtraInfo.objects.filter(user=user).first()
        department_name = extra_info.department.name if extra_info and extra_info.department else "Unknown"

        assigned_pcc_admin = app.assigned_pcc_admin.get_full_name() if app.assigned_pcc_admin else "PCC Admin"

        # Unique key for dictionary
        key = str(app.token_no) if app.token_no else f"app_{app.id}"

        # Build the application summary
        application_dict[key] = {
            "token_no": app.token_no if app.token_no else "Token not generated",
            "title": app.title,
            "submitted_by": applicant.name if applicant else "Unknown",
            "department": department_name,
            "submitted_on": app.submitted_date if app.submitted_date else "Unknown",
            "assigned_pcc_admin": assigned_pcc_admin,
            "assigned_attorney": assigned_pcc_admin,
            "budget_estimate": str(app.budget_estimate) if app.budget_estimate is not None else None,
            "budget_status": app.budget_status,
            "current_status": app.status,
        }

    return JsonResponse({"applications": application_dict}, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_notifications(request):
    notifications = NotificationEvent.objects.filter(
        Q(recipient=request.user) | Q(recipient__isnull=True) | Q(recipient_role__iexact="Director")
    ).order_by("-created_at")
    serializer = NotificationEventSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_application_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)

    try:
        if not _is_director_user(request.user):
            return JsonResponse({'error': 'Only Director can access this view.'}, status=403)

        data = json.loads(request.body)
        application_id = data.get('application_id')

        if not application_id:
            return JsonResponse({'error': 'application_id is required in the request body.'}, status=400)

        # Fetch application details
        application = get_object_or_404(Application, id=application_id)

        if application.assigned_director_id and application.assigned_director_id != request.user.id:
            assigned_name = application.assigned_director.get_full_name() or application.assigned_director.username
            return JsonResponse({'error': f'Application is assigned to another director: {assigned_name}.'}, status=403)

        # Fetch primary applicant details
        primary_applicant_name = None
        if application.primary_applicant_id:
            primary_applicant = Applicant.objects.filter(id=application.primary_applicant_id).first()
            primary_applicant_name = primary_applicant.name if primary_applicant else None

        handler_name = None
        if application.assigned_pcc_admin_id:
            handler_name = application.assigned_pcc_admin.get_full_name() or application.assigned_pcc_admin.username

        director_name = None
        if application.assigned_director_id:
            director_name = application.assigned_director.get_full_name() or application.assigned_director.username

        attorney_name = application.attorney.name if application.attorney else None

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
            "assigned_pcc_admin": handler_name,
            "assigned_director": director_name,
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


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def communication_logs(request, application_id):
    application = get_object_or_404(Application, id=application_id)

    if request.method == 'GET':
        logs = application.communication_logs.select_related('logged_by').all()
        serializer = CommunicationLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    payload = request.data.copy()
    serializer = CommunicationLogSerializer(data=payload)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save(application=application, logged_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# -----------------------------------------
# 🔹 PCC Admin Attorney Management Views
# -----------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_director_list(request):
    try:
        if not _is_pcc_admin_user(request.user):
            return Response({'error': 'Only PCC Admin can access director list.'}, status=status.HTTP_403_FORBIDDEN)

        directors = _get_director_users().order_by('first_name', 'username')
        payload = [
            {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name() or user.username,
                'email': user.email,
            }
            for user in directors
        ]
        return Response(payload, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def withdraw_application(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if application.primary_applicant and application.primary_applicant.user_id != request.user.id:
        return Response({'error': 'Only primary applicant can withdraw.'}, status=status.HTTP_403_FORBIDDEN)
    if application.status in ["Patent Granted", "Patent Refused"]:
        return Response({'error': 'Cannot withdraw after final decision.'}, status=status.HTTP_400_BAD_REQUEST)
    application.status = "Withdrawn"
    application.save(update_fields=['status', 'last_updated_at'])
    create_audit('Withdraw Application', request.user, application, 'Applicant withdrew application')
    return Response({'message': 'Application withdrawn successfully.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def resubmit_application(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    is_owner = application.primary_applicant and application.primary_applicant.user_id == request.user.id
    is_pcc = is_pcc_admin_user(request.user)
    if not (is_owner or is_pcc):
        return Response({'error': 'Only primary applicant can resubmit.'}, status=status.HTTP_403_FORBIDDEN)
    if application.status != "Needs Revision":
        return Response({'error': 'Application is not in revision stage.'}, status=status.HTTP_400_BAD_REQUEST)
    if application.revision_due_date and timezone.now().date() > application.revision_due_date:
        application.status = "Revision Expired"
        application.save(update_fields=['status', 'last_updated_at'])
        return Response({'error': 'Revision deadline expired.'}, status=status.HTTP_400_BAD_REQUEST)
    application.status = "Submitted"
    application.revised_submitted_at = timezone.now()
    application.is_revision_locked = True
    application.save(update_fields=['status', 'revised_submitted_at', 'is_revision_locked', 'last_updated_at'])
    create_audit('Resubmit Application', request.user, application, 'Applicant resubmitted revised application')
    return Response({'message': 'Application resubmitted successfully.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def declare_conflict(request, app_id):
    if not is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can declare conflict.'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(Application, id=app_id)
    serializer = ConflictDeclarationSerializer(data={
        'application': application.id,
        'reviewer': request.user.id,
        'conflict_type': request.data.get('conflict_type', 'General Conflict'),
        'notes': request.data.get('notes', ''),
        'declaration_status': 'Declared',
    })
    if serializer.is_valid():
        serializer.save()
        application.status = "Submitted"
        application.assigned_pcc_admin = None
        application.save(update_fields=['status', 'assigned_pcc_admin', 'last_updated_at'])
        create_audit('Conflict Declared', request.user, application, serializer.validated_data.get('conflict_type', ''))
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def submit_legal_assessment(request, app_id):
    if not is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can submit legal assessment.'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(Application, id=app_id)
    if application.status not in ["Director's Approval Received", "Patentability Check Started", "Patentability Check Completed"]:
        return Response({'error': 'Legal assessment not allowed in current status.'}, status=status.HTTP_400_BAD_REQUEST)
    attorney_id = request.data.get('attorney')
    attorney = get_object_or_404(Attorney, id=attorney_id)
    serializer = LegalAssessmentSerializer(data={
        'application': application.id,
        'attorney': attorney.id,
        'opinion': request.data.get('opinion', 'Review Needed'),
        'prior_art_summary': request.data.get('prior_art_summary', ''),
        'recommended_action': request.data.get('recommended_action', ''),
        'comments': request.data.get('comments', ''),
    })
    if serializer.is_valid():
        serializer.save()
        create_audit('Legal Assessment Submitted', request.user, application, 'Legal assessment saved')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def submit_legal_advice_memo(request, app_id):
    if not is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can create legal memo.'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(Application, id=app_id)
    serializer = LegalAdviceMemoSerializer(data={
        'application': application.id,
        'author': request.user.id,
        'summary': request.data.get('summary', ''),
        'recommendation': request.data.get('recommendation', ''),
    })
    if serializer.is_valid():
        serializer.save()
        create_audit('Legal Memo Submitted', request.user, application, 'Memo added')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def initiate_budget_approval(request, app_id):
    if not is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can initiate budget approval.'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(Application, id=app_id)
    amount = Decimal(str(request.data.get('amount', '0')))
    threshold = Decimal(str(request.data.get('threshold', '50000')))
    budget = record_budget_request(application, request.user, amount, threshold, request.data.get('comments', ''))
    serializer = BudgetApprovalSerializer(budget)
    create_audit('Budget Approval Initiated', request.user, application, f'Amount: {amount}')
    notify(application, f'Budget approval requested for {amount}.', recipient_role='Director', event_type='Budget Approval')
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_decide_budget(request, app_id):
    if not is_director_user(request.user):
        return Response({'error': 'Only Director can decide budget approval.'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(Application, id=app_id)
    budget = BudgetApproval.objects.filter(application=application).order_by('-created_at').first()
    if not budget:
        return Response({'error': 'No budget request found.'}, status=status.HTTP_404_NOT_FOUND)
    decision = request.data.get('decision', '').strip().lower()
    if decision not in ['approve', 'reject']:
        return Response({'error': "decision must be 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)
    budget.status = 'Approved' if decision == 'approve' else 'Rejected'
    budget.decided_by = request.user
    budget.decided_at = timezone.now()
    budget.comments = request.data.get('comments', budget.comments)
    budget.save(update_fields=['status', 'decided_by', 'decided_at', 'comments'])
    application.budget_status = budget.status
    application.save(update_fields=['budget_status', 'last_updated_at'])
    create_audit('Budget Decision', request.user, application, budget.status)
    return Response({'message': f'Budget {budget.status.lower()} successfully.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def initiate_external_filing(request, app_id):
    if not is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can initiate external filing.'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(Application, id=app_id)
    serializer = ExternalFilingRecordSerializer(data={
        'application': application.id,
        'patent_office': request.data.get('patent_office', ''),
        'filing_reference': request.data.get('filing_reference', ''),
        'communication_notes': request.data.get('communication_notes', ''),
        'filed_by': request.user.id,
        'filing_date': request.data.get('filing_date'),
    })
    if serializer.is_valid():
        serializer.save()
        application.external_filing_status = 'Filed'
        if application.status == 'Patentability Search Report Generated':
            application.status = 'Patent Filed'
            application.patent_filed_date = timezone.now().date()
        application.save(update_fields=['external_filing_status', 'status', 'patent_filed_date', 'last_updated_at'])
        create_audit('External Filing Initiated', request.user, application, 'External filing recorded')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def add_office_action(request, app_id):
    if not is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can add office action.'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(Application, id=app_id)
    serializer = OfficeActionSerializer(data={
        'application': application.id,
        'office_name': request.data.get('office_name', ''),
        'action_reference': request.data.get('action_reference', ''),
        'action_summary': request.data.get('action_summary', ''),
        'due_date': request.data.get('due_date'),
        'status': 'Open',
    })
    if serializer.is_valid():
        serializer.save()
        create_audit('Office Action Added', request.user, application, serializer.validated_data.get('action_reference', ''))
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def respond_office_action(request, office_action_id):
    office_action = get_object_or_404(OfficeAction, id=office_action_id)
    if not is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can respond office action.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = OfficeActionResponseSerializer(data={
        'office_action': office_action.id,
        'responder': request.user.id,
        'response_text': request.data.get('response_text', ''),
        'response_reference': request.data.get('response_reference', ''),
    })
    if serializer.is_valid():
        serializer.save()
        office_action.status = 'Responded'
        office_action.save(update_fields=['status'])
        create_audit('Office Action Responded', request.user, office_action.application, office_action.action_reference)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def add_prior_art_reference(request, app_id):
    if not is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can add prior-art reference.'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(Application, id=app_id)
    serializer = PriorArtReferenceSerializer(data={
        'application': application.id,
        'reference_type': request.data.get('reference_type', ''),
        'citation': request.data.get('citation', ''),
        'notes': request.data.get('notes', ''),
    })
    if serializer.is_valid():
        serializer.save()
        create_audit('Prior Art Added', request.user, application, serializer.validated_data.get('citation', ''))
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def submit_appeal(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if application.primary_applicant and application.primary_applicant.user_id != request.user.id:
        return Response({'error': 'Only applicant can submit appeal.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = AppealRequestSerializer(data={
        'application': application.id,
        'appellant': request.data.get('appellant', request.user.get_full_name() or request.user.username),
        'grounds': request.data.get('grounds', ''),
        'status': 'Open',
    })
    if serializer.is_valid():
        serializer.save()
        notify(application, 'Appeal submitted by applicant.', recipient_role='Director', event_type='Appeal')
        create_audit('Appeal Submitted', request.user, application, 'Appeal opened')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def submit_licensing_request(request, app_id):
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can create licensing requests.'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(Application, id=app_id)
    serializer = LicensingRequestSerializer(data={
        'application': application.id,
        'requester_name': request.data.get('requester_name', ''),
        'requester_org': request.data.get('requester_org', ''),
        'request_details': request.data.get('request_details', ''),
        'status': 'Pending',
    })
    if serializer.is_valid():
        serializer.save()
        _create_audit('Licensing Request Submitted', request.user, application, 'Licensing workflow started')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def collect_inventor_consents(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can collect consents.'}, status=status.HTTP_403_FORBIDDEN)
    applicants = [application.primary_applicant] + [rel.applicant for rel in AssociatedWith.objects.filter(application=application).select_related('applicant')]
    created = []
    for applicant in applicants:
        if not applicant:
            continue
        consent, _ = InventorConsent.objects.get_or_create(
            application=application,
            applicant=applicant,
            defaults={
                'consent_given': False,
                'agreement_reference': request.data.get('agreement_reference', f'CONSENT-{application.id}-{applicant.id}'),
            },
        )
        created.append(consent)
    serializer = InventorConsentSerializer(created, many=True)
    _create_audit('Inventor Consents Collected', request.user, application, f'{len(created)} consent records ensured')
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def setup_maintenance_schedule(request, app_id):
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can configure maintenance schedule.'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(Application, id=app_id)
    due_date = request.data.get('due_date')
    amount = request.data.get('amount')
    serializer = MaintenanceScheduleSerializer(data={
        'application': application.id,
        'due_date': due_date,
        'amount': amount,
        'status': 'Upcoming',
    })
    if serializer.is_valid():
        serializer.save()
        application.maintenance_tracking_active = True
        application.save(update_fields=['maintenance_tracking_active', 'last_updated_at'])
        _create_audit('Maintenance Schedule Created', request.user, application, f'Due: {due_date}')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def mark_maintenance_paid(request, schedule_id):
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can mark maintenance paid.'}, status=status.HTTP_403_FORBIDDEN)
    schedule = get_object_or_404(MaintenanceSchedule, id=schedule_id)
    schedule.status = 'Paid'
    schedule.paid_at = timezone.now()
    schedule.save(update_fields=['status', 'paid_at'])
    _create_audit('Maintenance Paid', request.user, schedule.application, f'Schedule {schedule.id}')
    return Response({'message': 'Maintenance marked as paid.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def reviewer_queue(request):
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can view reviewer queue.'}, status=status.HTTP_403_FORBIDDEN)
    apps = Application.objects.filter(status__in=['Submitted', 'Needs Revision']).select_related('primary_applicant', 'assigned_pcc_admin')
    payload = []
    for app in apps:
        score = _reviewer_workload(app.assigned_pcc_admin) if app.assigned_pcc_admin else 0
        app.priority_score = 10 if app.status == 'Needs Revision' else 5
        app.save(update_fields=['priority_score', 'last_updated_at'])
        payload.append({
            'id': app.id,
            'title': app.title,
            'status': app.status,
            'assigned_to': app.assigned_pcc_admin.get_full_name() if app.assigned_pcc_admin else None,
            'priority_score': app.priority_score,
            'reviewer_workload': score,
        })
    payload.sort(key=lambda x: (x['priority_score'], -x['reviewer_workload']), reverse=True)
    return Response(payload)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_notifications(request):
    role = (request.GET.get("role") or "").strip()
    notifications = NotificationEvent.objects.filter(Q(recipient=request.user) | Q(recipient__isnull=True))
    if role:
        notifications = notifications.filter(Q(recipient=request.user) | Q(recipient_role__iexact=role))
    notifications = notifications.order_by('-created_at')
    serializer = NotificationEventSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(NotificationEvent, id=notification_id)
    if notification.recipient_id and notification.recipient_id != request.user.id:
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return Response({'message': 'Notification marked as read.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_audit_logs(request):
    if not (_is_pcc_admin_user(request.user) or _is_director_user(request.user)):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    logs = AuditLog.objects.select_related('actor', 'application').all()[:300]
    serializer = AuditLogSerializer(logs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_applicant_insights(request):
    applicant = Applicant.objects.filter(user=request.user).first()
    if not applicant:
        return Response({'error': 'Applicant profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    apps = Application.objects.filter(primary_applicant=applicant)
    summary = {
        'total': apps.count(),
        'draft': apps.filter(status='Draft').count(),
        'submitted': apps.filter(status='Submitted').count(),
        'under_review': apps.filter(status__in=['Reviewed by PCC Admin', "Forwarded for Director's Review"]).count(),
        'approved': apps.filter(status="Director's Approval Received").count(),
        'granted': apps.filter(status='Patent Granted').count(),
        'refused': apps.filter(status='Patent Refused').count(),
    }
    return Response(summary)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_insights(request):
    if not _is_director_user(request.user):
        return Response({'error': 'Only Director can access this endpoint.'}, status=status.HTTP_403_FORBIDDEN)
    return _insights_response(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def upload_document_version(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    if document.is_locked:
        return Response({'error': 'Document is locked for new versions.'}, status=status.HTTP_400_BAD_REQUEST)
    link = request.data.get('link')
    if not link:
        return Response({'error': 'link is required.'}, status=status.HTTP_400_BAD_REQUEST)
    next_version = (document.versions.first().version_number + 1) if document.versions.exists() else document.current_version + 1
    serializer = DocumentVersionSerializer(data={
        'document': document.id,
        'version_number': next_version,
        'link': link,
        'uploaded_by': request.user.id,
    })
    if serializer.is_valid():
        serializer.save()
        document.current_version = next_version
        document.link = link
        document.save(update_fields=['current_version', 'link', 'updated_at'])
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def lock_document(request, document_id):
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can lock documents.'}, status=status.HTTP_403_FORBIDDEN)
    document = get_object_or_404(Document, id=document_id)
    document.is_locked = True
    document.save(update_fields=['is_locked', 'updated_at'])
    return Response({'message': 'Document locked successfully.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def pcc_insights(request):
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can access this endpoint.'}, status=status.HTTP_403_FORBIDDEN)
    return _insights_response(request)


def _insights_response(request):
    base_qs = Application.objects.all()
    available_years = sorted(
        {
            dt.year
            for dt in base_qs.exclude(submitted_date__isnull=True).values_list('submitted_date', flat=True)
            if dt
        }
    )
    if not available_years:
        available_years = [timezone.now().year]

    requested_year = request.GET.get('year')
    if requested_year and requested_year.isdigit() and int(requested_year) in available_years:
        selected_year = int(requested_year)
    else:
        selected_year = available_years[-1]

    apps = base_qs.filter(submitted_date__year=selected_year)
    color_map = {
        'Submitted': '#4D96FF',
        'Reviewed by PCC Admin': '#00B894',
        "Forwarded for Director's Review": '#F5A623',
        "Director's Approval Received": '#2ECC71',
        'Patent Filed': '#8E44AD',
        'Patent Granted': '#16A085',
        'Patent Refused': '#E74C3C',
        'Needs Revision': '#D35400',
        'Withdrawn': '#7F8C8D',
    }
    status_order = [
        'Submitted',
        'Reviewed by PCC Admin',
        "Forwarded for Director's Review",
        "Director's Approval Received",
        'Patent Filed',
        'Patent Granted',
        'Patent Refused',
        'Needs Revision',
        'Withdrawn',
    ]

    status_counts = apps.values('status').annotate(count=Count('id'))
    status_lookup = {item['status']: item['count'] for item in status_counts}
    applications = [
        {
            'label': status_name,
            'count': status_lookup.get(status_name, 0),
            'color': color_map.get(status_name, '#5B7CFA'),
        }
        for status_name in status_order
    ]

    total = sum(item['count'] for item in applications)
    payload = {
        'applications': applications,
        'available_years': available_years,
        'selected_year': selected_year,
        'total': total,
    }

    if request.GET.get('format') == 'csv':
        rows = ['status,count,percentage']
        for item in applications:
            percentage = (item['count'] / total * 100) if total else 0
            rows.append(f"{item['label']},{item['count']},{percentage:.2f}")
        return HttpResponse('\n'.join(rows), content_type='text/csv')

    return Response(payload)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def pcc_resubmit_application(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    is_owner = application.primary_applicant and application.primary_applicant.user_id == request.user.id
    is_pcc = _is_pcc_admin_user(request.user)
    if not (is_owner or is_pcc):
        return Response({'error': 'Only primary applicant or PCC Admin can resubmit.'}, status=status.HTTP_403_FORBIDDEN)
    if application.status != "Needs Revision":
        return Response({'error': 'Application is not in revision stage.'}, status=status.HTTP_400_BAD_REQUEST)
    if application.revision_due_date and timezone.now().date() > application.revision_due_date:
        application.status = "Revision Expired"
        application.save(update_fields=['status', 'last_updated_at'])
        return Response({'error': 'Revision deadline expired.'}, status=status.HTTP_400_BAD_REQUEST)
    application.status = "Submitted"
    application.revised_submitted_at = timezone.now()
    application.is_revision_locked = True
    application.save(update_fields=['status', 'revised_submitted_at', 'is_revision_locked', 'last_updated_at'])
    _create_audit('Resubmit Application', request.user, application, 'Application resubmitted')
    return Response({'message': 'Application resubmitted successfully.'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def legal_assessment_api(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if request.method == 'GET':
        serializer = LegalAssessmentSerializer(application.legal_assessments.all(), many=True)
        return Response(serializer.data)
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can submit legal assessment.'}, status=status.HTTP_403_FORBIDDEN)
    if application.status not in ["Director's Approval Received", "Patentability Check Started", "Patentability Check Completed"]:
        return Response({'error': 'Legal assessment not allowed in current status.'}, status=status.HTTP_400_BAD_REQUEST)
    attorney = get_object_or_404(Attorney, id=request.data.get('attorney'))
    serializer = LegalAssessmentSerializer(data={
        'application': application.id,
        'attorney': attorney.id,
        'opinion': request.data.get('opinion', 'Review Needed'),
        'prior_art_summary': request.data.get('prior_art_summary', ''),
        'recommended_action': request.data.get('recommended_action', ''),
        'comments': request.data.get('comments', ''),
    })
    if serializer.is_valid():
        serializer.save()
        _create_audit('Legal Assessment Submitted', request.user, application, 'Legal assessment saved')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def budget_api(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if request.method == 'GET':
        serializer = BudgetApprovalSerializer(application.budget_approvals.all(), many=True)
        return Response(serializer.data)
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can initiate budget approval.'}, status=status.HTTP_403_FORBIDDEN)
    amount = Decimal(str(request.data.get('amount', '0')))
    threshold = Decimal(str(request.data.get('threshold', '50000')))
    serializer = BudgetApprovalSerializer(data={
        'application': application.id,
        'requested_by': request.user.id,
        'amount': amount,
        'threshold': threshold,
        'status': 'Pending',
        'comments': request.data.get('comments', ''),
    })
    if serializer.is_valid():
        serializer.save()
        application.budget_status = 'Pending Approval'
        application.budget_estimate = amount
        application.save(update_fields=['budget_status', 'budget_estimate', 'last_updated_at'])
        _notify(application, f'Budget approval requested for {amount}.', recipient_role='Director', event_type='Budget Approval')
        _create_audit('Budget Approval Initiated', request.user, application, f'Amount: {amount}')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def budget_decision_by_id(request, budget_id):
    budget = get_object_or_404(BudgetApproval, id=budget_id)
    if not (_is_director_user(request.user) or _is_pcc_admin_user(request.user)):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    decision = request.data.get('decision', '').strip().lower()
    if decision not in ['approve', 'reject']:
        return Response({'error': "decision must be 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)
    budget.status = 'Approved' if decision == 'approve' else 'Rejected'
    budget.decided_by = request.user
    budget.decided_at = timezone.now()
    budget.comments = request.data.get('comments', budget.comments)
    budget.save(update_fields=['status', 'decided_by', 'decided_at', 'comments'])
    budget.application.budget_status = budget.status
    budget.application.save(update_fields=['budget_status', 'last_updated_at'])
    _create_audit('Budget Decision', request.user, budget.application, budget.status)
    return Response({'message': f'Budget {budget.status.lower()} successfully.'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def external_filing_api(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if request.method == 'GET':
        serializer = ExternalFilingRecordSerializer(application.external_filings.all(), many=True)
        return Response(serializer.data)
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can initiate external filing.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = ExternalFilingRecordSerializer(data={
        'application': application.id,
        'patent_office': request.data.get('patent_office', ''),
        'filing_reference': request.data.get('filing_reference', ''),
        'communication_notes': request.data.get('communication_notes', ''),
        'filed_by': request.user.id,
        'filing_date': request.data.get('filing_date'),
    })
    if serializer.is_valid():
        serializer.save()
        application.external_filing_status = 'Filed'
        if application.status == 'Patentability Search Report Generated':
            application.status = 'Patent Filed'
            application.patent_filed_date = timezone.now().date()
        application.save(update_fields=['external_filing_status', 'status', 'patent_filed_date', 'last_updated_at'])
        _create_audit('External Filing Initiated', request.user, application, 'External filing recorded')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def maintenance_api(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if request.method == 'GET':
        serializer = MaintenanceScheduleSerializer(application.maintenance_schedules.all(), many=True)
        return Response(serializer.data)
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can configure maintenance schedule.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = MaintenanceScheduleSerializer(data={
        'application': application.id,
        'due_date': request.data.get('due_date'),
        'amount': request.data.get('amount'),
        'status': 'Upcoming',
    })
    if serializer.is_valid():
        serializer.save()
        application.maintenance_tracking_active = True
        application.save(update_fields=['maintenance_tracking_active', 'last_updated_at'])
        _create_audit('Maintenance Schedule Created', request.user, application, f"Due: {request.data.get('due_date')}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def queue_prioritized(request):
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can view reviewer queue.'}, status=status.HTTP_403_FORBIDDEN)
    apps = Application.objects.filter(status__in=['Submitted', 'Needs Revision']).select_related('primary_applicant', 'assigned_pcc_admin')
    payload = []
    for app in apps:
        score = _reviewer_workload(app.assigned_pcc_admin) if app.assigned_pcc_admin else 0
        app.priority_score = 10 if app.status == 'Needs Revision' else 5
        app.save(update_fields=['priority_score', 'last_updated_at'])
        payload.append({
            'id': app.id,
            'title': app.title,
            'status': app.status,
            'assigned_to': app.assigned_pcc_admin.get_full_name() if app.assigned_pcc_admin else None,
            'priority_score': app.priority_score,
            'reviewer_workload': score,
        })
    payload.sort(key=lambda x: (x['priority_score'], -x['reviewer_workload']), reverse=True)
    return Response(payload)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def notifications_root(request):
    role = (request.GET.get("role") or "").strip()
    notifications = NotificationEvent.objects.filter(Q(recipient=request.user) | Q(recipient__isnull=True))
    if role:
        notifications = notifications.filter(Q(recipient=request.user) | Q(recipient_role__iexact=role))
    notifications = notifications.order_by('-created_at')
    serializer = NotificationEventSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def audit_logs_root(request):
    if not (_is_pcc_admin_user(request.user) or _is_director_user(request.user)):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    logs = AuditLog.objects.select_related('actor', 'application').all()[:300]
    serializer = AuditLogSerializer(logs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def audit_logs_by_application(request, application_id):
    if not (_is_pcc_admin_user(request.user) or _is_director_user(request.user)):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    logs = AuditLog.objects.filter(application_id=application_id).select_related('actor', 'application').all()
    serializer = AuditLogSerializer(logs, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def office_actions_api(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if request.method == 'GET':
        serializer = OfficeActionSerializer(application.office_actions.all(), many=True)
        return Response(serializer.data)
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can add office action.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = OfficeActionSerializer(data={
        'application': application.id,
        'office_name': request.data.get('office_name', ''),
        'action_reference': request.data.get('action_reference', ''),
        'action_summary': request.data.get('action_summary', ''),
        'due_date': request.data.get('due_date'),
        'status': 'Open',
    })
    if serializer.is_valid():
        serializer.save()
        _create_audit('Office Action Added', request.user, application, serializer.validated_data.get('action_reference', ''))
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def prior_art_api(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if request.method == 'GET':
        q = request.GET.get('q', '').strip()
        refs = application.prior_art_references.all()
        if q:
            refs = refs.filter(Q(citation__icontains=q) | Q(notes__icontains=q))
        serializer = PriorArtReferenceSerializer(refs, many=True)
        return Response(serializer.data)
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can add prior-art reference.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = PriorArtReferenceSerializer(data={
        'application': application.id,
        'reference_type': request.data.get('reference_type', ''),
        'citation': request.data.get('citation', ''),
        'notes': request.data.get('notes', ''),
    })
    if serializer.is_valid():
        serializer.save()
        _create_audit('Prior Art Added', request.user, application, serializer.validated_data.get('citation', ''))
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def appeals_api(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if request.method == 'GET':
        serializer = AppealRequestSerializer(application.appeals.all(), many=True)
        return Response(serializer.data)
    if application.primary_applicant and application.primary_applicant.user_id != request.user.id:
        return Response({'error': 'Only applicant can submit appeal.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = AppealRequestSerializer(data={
        'application': application.id,
        'appellant': request.data.get('appellant', request.user.get_full_name() or request.user.username),
        'grounds': request.data.get('grounds', ''),
        'status': 'Open',
    })
    if serializer.is_valid():
        serializer.save()
        _notify(application, 'Appeal submitted by applicant.', recipient_role='Director', event_type='Appeal')
        _create_audit('Appeal Submitted', request.user, application, 'Appeal opened')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def licensing_api(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if request.method == 'GET':
        serializer = LicensingRequestSerializer(application.licensing_requests.all(), many=True)
        return Response(serializer.data)
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can create licensing requests.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = LicensingRequestSerializer(data={
        'application': application.id,
        'requester_name': request.data.get('requester_name', ''),
        'requester_org': request.data.get('requester_org', ''),
        'request_details': request.data.get('request_details', ''),
        'status': 'Pending',
    })
    if serializer.is_valid():
        serializer.save()
        _create_audit('Licensing Request Submitted', request.user, application, 'Licensing workflow started')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def inventor_consents_api(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if request.method == 'GET':
        serializer = InventorConsentSerializer(application.inventor_consents.all(), many=True)
        return Response(serializer.data)
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can collect consents.'}, status=status.HTTP_403_FORBIDDEN)
    applicants = [application.primary_applicant] + [rel.applicant for rel in AssociatedWith.objects.filter(application=application).select_related('applicant')]
    created = []
    for applicant in applicants:
        if not applicant:
            continue
        consent, _ = InventorConsent.objects.get_or_create(
            application=application,
            applicant=applicant,
            defaults={
                'consent_given': False,
                'agreement_reference': request.data.get('agreement_reference', f'CONSENT-{application.id}-{applicant.id}'),
            },
        )
        created.append(consent)
    serializer = InventorConsentSerializer(created, many=True)
    _create_audit('Inventor Consents Collected', request.user, application, f'{len(created)} consent records ensured')
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def legal_memos_api(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if request.method == 'GET':
        serializer = LegalAdviceMemoSerializer(application.legal_memos.all(), many=True)
        return Response(serializer.data)
    if not _is_pcc_admin_user(request.user):
        return Response({'error': 'Only PCC Admin can create legal memo.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = LegalAdviceMemoSerializer(data={
        'application': application.id,
        'author': request.user.id,
        'summary': request.data.get('summary', ''),
        'recommendation': request.data.get('recommendation', ''),
    })
    if serializer.is_valid():
        serializer.save()
        _create_audit('Legal Memo Submitted', request.user, application, 'Memo added')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def document_versions_api(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    serializer = DocumentVersionSerializer(document.versions.all(), many=True)
    return Response(serializer.data)