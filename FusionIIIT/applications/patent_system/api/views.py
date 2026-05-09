"""
Patent Management System — API Views (thin).
Each view delegates to services.py (writes) or selectors.py (reads).
"""

import json
import logging

from django.http import JsonResponse
from django.utils.timezone import now

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view, permission_classes, authentication_classes,
)

from applications.globals.models import Designation, HoldsDesignation

from ..models import ApplicationStatus, Document, PatentNotification, ApplicationDocument
from .. import services, selectors
from .serializers import (
    DocumentSerializer, CommunicationLogSerializer,
    BudgetSerializer, AuditLogSerializer,
    AttorneyAssignmentSerializer, PatentabilityAssessmentSerializer,
    FilingRecordSerializer, PatentNotificationSerializer, ApplicationDocumentSerializer,
)

logger = logging.getLogger(__name__)

# Shared decorator stack
_auth = [api_view, permission_classes, authentication_classes]


def _service_response(func, *args, **kwargs):
    """Call a service function and convert PatentServiceError → JsonResponse."""
    try:
        return func(*args, **kwargs)
    except services.PatentServiceError as e:
        return JsonResponse({"error": e.message}, status=e.code)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.exception("Unhandled error")
        return JsonResponse({"error": str(e)}, status=500)


# =========================================================================
# APPLICANT VIEWS
# =========================================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def submit_application(request):
    """UC-001 — Submit patent application."""
    def _do():
        json_data = request.POST.get("json_data")
        if not json_data:
            return JsonResponse({"error": "Missing json_data"}, status=400)
        data = json.loads(json_data)
        app = services.submit_application(request.user, data, request.FILES)
        return JsonResponse({
            "message": "Application submitted successfully.",
            "application_id": app.id,
        }, status=201)
    return _service_response(_do)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def view_applications(request):
    """UC-005 — Applicant views own applications."""
    data = selectors.get_applicant_applications(request.user)
    return JsonResponse({"applications": data}, safe=False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def view_application_details_for_applicant(request, application_id):
    """UC-003 — Applicant views single application detail."""
    detail = selectors.get_applicant_application_detail(request.user, application_id)
    if detail is None:
        return JsonResponse({"error": "Not found or not authorized."}, status=403)
    return JsonResponse(detail, safe=False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def view_pending_consent_applications(request):
    """Get applications where current user is an inventor and consent is pending."""
    data = selectors.get_pending_consent_applications(request.user)
    return JsonResponse(data, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def give_inventor_consent(request, application_id):
    """Inventor gives consent for an application."""
    def _do():
        try:
            inventor = services.give_inventor_consent(request.user, application_id)
            return JsonResponse({
                "message": "Consent given successfully.",
                "consent_date": inventor.consent_date.isoformat() if inventor.consent_date else None,
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return _do()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def resubmit_application(request, application_id):
    """UC-004 — Applicant resubmits after revision."""
    def _do():
        json_data = request.POST.get("json_data", "{}")
        data = json.loads(json_data)
        app = services.resubmit_application(request.user, application_id, data, request.FILES)
        return JsonResponse({
            "message": "Application resubmitted.",
            "application_id": app.id,
            "status": app.status,
        })
    return _service_response(_do)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def withdraw_application(request, application_id):
    """UC-014 — Applicant withdraws application."""
    def _do():
        data = json.loads(request.body or "{}")
        reason = data.get("reason", "")
        app = services.withdraw_application(request.user, application_id, reason)
        return JsonResponse({
            "message": "Application withdrawn.",
            "application_id": app.id,
        })
    return _service_response(_do)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def saved_drafts(request):
    """UC-004 old — placeholder for saved drafts."""
    return JsonResponse({"message": "No saved drafts."})


# =========================================================================
# PCC ADMIN VIEWS
# =========================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_applications(request):
    """UC-005 old — PCC Admin views new / resubmitted applications."""
    return JsonResponse({"applications": selectors.get_new_applications_pcc()}, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def review_application(request, application_id):
    """UC-006 — PCC Admin marks reviewed."""
    def _do():
        data = json.loads(request.body or "{}")
        comments = data.get("comments", "")
        app = services.pcc_review_application(request.user, application_id, comments)
        return JsonResponse({
            "message": "Application reviewed.",
            "application_id": app.id,
            "status": app.status,
        })
    return _service_response(_do)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_directors(request):
    """Get list of users with Director designation."""
    try:
        designation = Designation.objects.get(name="Director")
        holds_designation = HoldsDesignation.objects.filter(designation=designation).select_related('user')
        directors = [
            {
                "id": hd.user.id,
                "name": f"{hd.user.first_name} {hd.user.last_name}".strip() or hd.user.username,
                "email": hd.user.email
            }
            for hd in holds_designation
        ]
        return JsonResponse({"directors": directors}, safe=False)
    except Designation.DoesNotExist:
        return JsonResponse({"directors": []}, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def forward_application(request, application_id):
    """UC-007 — PCC Admin forwards to Director."""
    def _do():
        data = json.loads(request.body or "{}")
        comments = data.get("comments", "")
        director_id = data.get("director_id", None)
        app = services.forward_to_director(request.user, application_id, comments, director_id)
        return JsonResponse({
            "message": "Application forwarded to Director.",
            "application_id": app.id,
            "status": app.status,
        })
    return _service_response(_do)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def request_application_modification(request, application_id):
    """UC-008 old — PCC Admin sends back to draft."""
    def _do():
        data = json.loads(request.body or "{}")
        comments = data.get("comments", "")
        app = services.request_modification(request.user, application_id, comments)
        return JsonResponse({
            "message": "Modification requested.",
            "application_id": app.id,
            "status": app.status,
        })
    return _service_response(_do)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def ongoing_applications(request):
    return JsonResponse({"applications": selectors.get_ongoing_applications_pcc()}, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def change_application_status(request, application_id):
    """PCC Admin advances status."""
    def _do():
        data = json.loads(request.body or "{}")
        next_status = data.get("next_status", "").strip()
        if not next_status:
            return JsonResponse({"error": "next_status is required."}, status=400)
        app = services.change_status(request.user, application_id, next_status)
        return JsonResponse({
            "message": f"Status changed to '{app.status}'.",
            "application_id": app.id,
            "status": app.status,
        })
    return _service_response(_do)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def past_applications(request):
    return JsonResponse({"applications": selectors.get_past_applications_pcc()}, safe=False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def view_application_details_for_pccAdmin(request, application_id):
    detail = selectors.get_pcc_application_detail(application_id)
    return JsonResponse(detail, safe=False)


# ── Communication Log (replaces Attorney Management) ─────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def communication_logs(request, application_id):
    """
    GET  — list logs for an application.
    POST — add a new communication log entry (with optional attachment).
    """
    if request.method == "GET":
        logs = selectors.get_communication_logs(application_id)
        serializer = CommunicationLogSerializer(logs, many=True)
        return Response(serializer.data)

    # POST
    def _do():
        app = services.add_communication_log(
            user=request.user,
            application_id=application_id,
            direction=request.POST.get("direction", request.data.get("direction", "")),
            subject=request.POST.get("subject", request.data.get("subject", "")),
            body=request.POST.get("body", request.data.get("body", "")),
            external_party_name=request.POST.get("external_party_name", request.data.get("external_party_name", "")),
            external_party_email=request.POST.get("external_party_email", request.data.get("external_party_email", "")),
            attachment=request.FILES.get("attachment"),
            confidentiality_level=request.POST.get("confidentiality_level", request.data.get("confidentiality_level", "Internal")),
        )
        return JsonResponse({
            "message": "Communication logged.",
            "id": app.id,
        }, status=201)
    return _service_response(_do)


# ── Budget endpoints ─────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def budget_view(request, application_id):
    """GET — budget details; POST — create/update budget."""
    if request.method == "GET":
        budget = selectors.get_budget(application_id)
        if budget is None:
            return JsonResponse({"budget": None})
        serializer = BudgetSerializer(budget)
        return Response(serializer.data)

    def _do():
        data = json.loads(request.body or "{}")
        budget = services.create_or_update_budget(
            user=request.user,
            application_id=application_id,
            filing_cost=data.get("filing_cost", 0),
            attorney_fees=data.get("attorney_fees", 0),
            administrative_cost=data.get("administrative_cost", 0),
            remarks=data.get("remarks", ""),
        )
        return JsonResponse({
            "message": "Budget saved.",
            "total_cost": str(budget.total_cost),
            "decision": budget.decision,
        })
    return _service_response(_do)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_budget_decision(request, application_id):
    """Director views or decides on escalated budget."""
    if request.method == "GET":
        # View budget details
        budget = selectors.get_budget(application_id)
        if not budget:
            return JsonResponse({"error": "No budget found for this application."}, status=404)
        serializer = BudgetSerializer(budget)
        return Response(serializer.data)
    
    # POST - make decision
    def _do():
        data = json.loads(request.body or "{}")
        # Support both 'approve' boolean and 'decision' string
        decision_str = data.get("decision", "").strip()
        if decision_str:
            approve = decision_str.lower() in ["approved", "approve", "yes"]
        else:
            approve = data.get("approve", False)
        remarks = data.get("remarks", "")
        budget = services.director_budget_decision(request.user, application_id, approve, remarks)
        return JsonResponse({
            "message": f"Budget {'approved' if approve else 'denied'}.",
            "decision": budget.decision,
        })
    return _service_response(_do)


# ── Audit Logs ───────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def audit_logs(request, application_id):
    logs = selectors.get_audit_logs(application_id)
    serializer = AuditLogSerializer(logs, many=True)
    return Response(serializer.data)


# ── Analytics ────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def analytics(request):
    """UC-015 — Application stats for dashboards."""
    year = request.GET.get("year")
    stats = list(selectors.get_application_stats(year=year))
    available_years = selectors.get_available_years()
    return JsonResponse({"stats": stats, "available_years": available_years}, safe=False)


# =========================================================================
# DIRECTOR VIEWS
# =========================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_new_applications(request):
    return JsonResponse({"applications": selectors.get_director_new_applications(user=request.user)}, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_accept(request):
    """Director approves application."""
    def _do():
        data = json.loads(request.body or "{}")
        app_id = data.get("application_id")
        feedback = data.get("comments", data.get("feedback", ""))
        if not app_id:
            return JsonResponse({"error": "application_id required."}, status=400)
        app = services.director_review(request.user, app_id, "Approve", feedback)
        return JsonResponse({
            "message": "Application approved by Director.",
            "application_id": app.id,
            "token_no": app.token_no,
            "status": app.status,
        })
    return _service_response(_do)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_reject(request):
    """Director rejects or requests revision."""
    def _do():
        data = json.loads(request.body or "{}")
        app_id = data.get("application_id")
        feedback = data.get("comments", data.get("feedback", ""))
        decision = data.get("decision", "Reject")  # "Reject" or "Needs Revision"
        if not app_id:
            return JsonResponse({"error": "application_id required."}, status=400)
        app = services.director_review(request.user, app_id, decision, feedback)
        return JsonResponse({
            "message": f"Application {decision}.",
            "application_id": app.id,
            "status": app.status,
        })
    return _service_response(_do)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_reviewed_applications(request):
    return JsonResponse({"applications": selectors.get_director_reviewed_applications(user=request.user)}, safe=False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def active_applications(request):
    """Same as director reviewed but only pending decision."""
    return JsonResponse({"applications": selectors.get_director_reviewed_applications()}, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_application_view(request):
    """Director detail view — accepts application_id in body."""
    try:
        data = json.loads(request.body or "{}")
        app_id = data.get("application_id")
        if not app_id:
            return JsonResponse({"error": "application_id required."}, status=400)
        detail = selectors.get_director_application_detail(app_id)
        return JsonResponse(detail, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_notifications(request):
    return JsonResponse({"notifications": []})


# =========================================================================
# ATTORNEY ASSIGNMENT (UC-006, BR-PMS-007) — PCC Admin only
# =========================================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def attorney_assignment_view(request, application_id):
    """
    GET  — View current attorney assignment for an application.
    POST — Assign/update external attorney details (PCC Admin only).
    """
    if request.method == "GET":
        assignment = selectors.get_attorney_assignment(application_id)
        if assignment is None:
            return JsonResponse({"attorney_assignment": None})
        serializer = AttorneyAssignmentSerializer(assignment)
        return Response(serializer.data)

    # POST — assign attorney
    def _do():
        assignment = services.assign_attorney(
            user=request.user,
            application_id=application_id,
            attorney_name=request.POST.get("attorney_name", request.data.get("attorney_name", "")),
            attorney_email=request.POST.get("attorney_email", request.data.get("attorney_email", "")),
            attorney_phone=request.POST.get("attorney_phone", request.data.get("attorney_phone", "")),
            attorney_firm=request.POST.get("attorney_firm", request.data.get("attorney_firm", "")),
            specialization=request.POST.get("specialization", request.data.get("specialization", "")),
            remarks=request.POST.get("remarks", request.data.get("remarks", "")),
            engagement_proof=request.FILES.get("engagement_proof"),
        )
        return JsonResponse({
            "message": "Attorney assigned successfully.",
            "id": assignment.id,
            "attorney_name": assignment.attorney_name,
        }, status=201)
    return _service_response(_do)


# =========================================================================
# PATENTABILITY ASSESSMENT (UC-007, BR-PMS-014) — PCC Admin records
# =========================================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def patentability_assessment_view(request, application_id):
    """
    GET  — View current patentability assessment.
    POST — Record/update the external attorney's assessment (PCC Admin only).
    """
    if request.method == "GET":
        assessment = selectors.get_patentability_assessment(application_id)
        if assessment is None:
            return JsonResponse({"patentability_assessment": None})
        serializer = PatentabilityAssessmentSerializer(assessment)
        return Response(serializer.data)

    # POST — record assessment
    def _do():
        data = request.data if hasattr(request, 'data') else {}
        assessment = services.record_patentability_assessment(
            user=request.user,
            application_id=application_id,
            recommendation=request.POST.get("recommendation", data.get("recommendation", "")),
            opinion_summary=request.POST.get("opinion_summary", data.get("opinion_summary", "")),
            novelty_score=request.POST.get("novelty_score", data.get("novelty_score", 0)),
            non_obviousness_score=request.POST.get("non_obviousness_score", data.get("non_obviousness_score", 0)),
            utility_score=request.POST.get("utility_score", data.get("utility_score", 0)),
            search_completeness=request.POST.get("search_completeness", data.get("search_completeness", 0)),
            prior_art_references=request.POST.get("prior_art_references", data.get("prior_art_references", "")),
            assessed_by_attorney=request.POST.get("assessed_by_attorney", data.get("assessed_by_attorney", "")),
            attorney_report=request.FILES.get("attorney_report"),
        )
        return JsonResponse({
            "message": "Patentability assessment recorded.",
            "id": assessment.id,
            "recommendation": assessment.recommendation,
        }, status=201)
    return _service_response(_do)


# =========================================================================
# FILING RECORD (UC-009, BR-PMS-017, WF-601) — PCC Admin logs filing
# =========================================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def filing_record_view(request, application_id):
    """
    GET  — View filing record for an application.
    POST — Record/update filing details with patent office (PCC Admin only).
    """
    if request.method == "GET":
        filing = selectors.get_filing_record(application_id)
        if filing is None:
            return JsonResponse({"filing_record": None})
        serializer = FilingRecordSerializer(filing)
        return Response(serializer.data)

    # POST — record filing
    def _do():
        data = request.data if hasattr(request, 'data') else {}
        filing = services.record_filing(
            user=request.user,
            application_id=application_id,
            filing_office=request.POST.get("filing_office", data.get("filing_office", "Indian Patent Office")),
            jurisdiction=request.POST.get("jurisdiction", data.get("jurisdiction", "India")),
            external_filing_id=request.POST.get("external_filing_id", data.get("external_filing_id", "")),
            international_filing_justification=request.POST.get(
                "international_filing_justification",
                data.get("international_filing_justification", ""),
            ),
            confirmation_proof=request.FILES.get("confirmation_proof"),
            remarks=request.POST.get("remarks", data.get("remarks", "")),
        )
        return JsonResponse({
            "message": "Filing recorded successfully.",
            "id": filing.id,
            "external_filing_id": filing.external_filing_id,
        }, status=201)
    return _service_response(_do)


# =========================================================================
# DOCUMENT MANAGEMENT (shared)
# =========================================================================

@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manage_documents(request):
    if request.method == "GET":
        docs = selectors.get_all_documents()
        serializer = DocumentSerializer(docs, many=True)
        return Response(serializer.data)
    serializer = DocumentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_document(request, document_id):
    doc = selectors.get_document_or_404(document_id)
    doc.delete()
    return Response({"message": "Document deleted."}, status=status.HTTP_200_OK)


# =========================================================================
# FEATURE 1: APPEAL ENDPOINTS
# =========================================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def lodge_appeal(request, application_id):
    """Applicant lodges a formal appeal against rejection."""
    def _do():
        data = json.loads(request.body or "{}")
        reason = data.get("reason", "")
        app = services.lodge_appeal(request.user, application_id, reason)
        return JsonResponse({
            "message": "Appeal lodged successfully.",
            "application_id": app.id,
            "status": app.status,
        }, status=201)
    return _service_response(_do)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def pcc_review_appeal(request, application_id):
    """PCC Admin forwards appeal to Director for review."""
    def _do():
        app = services.pcc_review_appeal(request.user, application_id)
        return JsonResponse({
            "message": "Appeal forwarded to Director for review.",
            "application_id": app.id,
            "status": app.status,
        })
    return _service_response(_do)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def director_appeal_decision(request, application_id):
    """Director decides on the appeal."""
    def _do():
        data = json.loads(request.body or "{}")
        approve = data.get("approve", False)
        feedback = data.get("feedback", data.get("comments", ""))
        app = services.director_appeal_decision(request.user, application_id, approve, feedback)
        return JsonResponse({
            "message": f"Appeal {'approved' if approve else 'rejected'}.",
            "application_id": app.id,
            "status": app.status,
        })
    return _service_response(_do)


# =========================================================================
# FEATURE 2: INVENTOR CONSENT ENDPOINTS
# =========================================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def give_consent(request, application_id):
    """Inventor gives consent for the application."""
    def _do():
        inventor = services.give_inventor_consent(request.user, application_id)
        return JsonResponse({
            "message": "Consent given successfully.",
            "has_consent": inventor.has_consent,
            "consent_date": inventor.consent_date.isoformat() if inventor.consent_date else None,
        })
    return _service_response(_do)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def revoke_consent(request, application_id):
    """Inventor revokes consent for the application."""
    def _do():
        inventor = services.revoke_inventor_consent(request.user, application_id)
        return JsonResponse({
            "message": "Consent revoked successfully.",
            "has_consent": inventor.has_consent,
        })
    return _service_response(_do)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_consent_status(request, application_id):
    """Get consent status for all inventors on an application."""
    consent_info = selectors.get_inventors_consent_status(application_id)
    return JsonResponse(consent_info, safe=False)


# =========================================================================
# FEATURE 4: NOTIFICATION ENDPOINTS
# =========================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_notifications(request):
    """Get notifications for the current user."""
    unread_only = request.GET.get("unread_only", "false").lower() == "true"
    notifications = services.get_user_notifications(request.user, unread_only)
    serializer = PatentNotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    def _do():
        services.mark_notification_read(request.user, notification_id)
        return JsonResponse({"message": "Notification marked as read."})
    return _service_response(_do)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    count = services.mark_all_notifications_read(request.user)
    return JsonResponse({"message": f"{count} notifications marked as read."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_unread_count(request):
    """Get count of unread notifications."""
    count = PatentNotification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({"unread_count": count})


# =========================================================================
# FEATURE 5: DOCUMENT VERSION CONTROL ENDPOINTS
# =========================================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def application_documents(request, application_id):
    """
    GET  — Get all documents for an application (with version history).
    POST — Upload a new document version.
    """
    if request.method == "GET":
        document_type = request.GET.get("document_type")
        current_only = request.GET.get("current_only", "false").lower() == "true"

        if current_only:
            docs = services.get_current_documents(application_id)
        else:
            docs = services.get_document_versions(application_id, document_type)

        serializer = ApplicationDocumentSerializer(docs, many=True)
        return Response(serializer.data)

    # POST - upload new document
    def _do():
        doc = services.upload_document(
            user=request.user,
            application_id=application_id,
            document_type=request.POST.get("document_type", request.data.get("document_type", "")),
            title=request.POST.get("title", request.data.get("title", "")),
            file=request.FILES.get("file"),
            description=request.POST.get("description", request.data.get("description", "")),
        )
        return JsonResponse({
            "message": "Document uploaded successfully.",
            "id": doc.id,
            "version": doc.version,
            "title": doc.title,
        }, status=201)
    return _service_response(_do)


# =========================================================================
# FEATURE 6: SEARCH & GLOBAL FILTERING ENDPOINTS
# =========================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def search_applications(request):
    """Search and filter applications."""
    query = request.GET.get("q", "")
    status_filter = request.GET.getlist("status")
    decision_filter = request.GET.get("decision")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    department = request.GET.get("department")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    # Parse dates
    from datetime import datetime
    if date_from:
        try:
            date_from = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            date_from = None
    if date_to:
        try:
            date_to = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            date_to = None

    results = services.search_applications(
        user=request.user,
        query=query,
        status_filter=status_filter if status_filter else None,
        date_from=date_from,
        date_to=date_to,
        department_filter=department,
        decision_filter=decision_filter,
        limit=limit,
        offset=offset,
    )

    return JsonResponse(results, safe=False)


# =========================================================================
# FEATURE 7: ENHANCED ANALYTICS ENDPOINTS
# =========================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def analytics_summary(request):
    """Get comprehensive analytics summary."""
    year = request.GET.get("year")
    department = request.GET.get("department")

    try:
        if year:
            year = int(year)
    except ValueError:
        year = None

    summary = services.get_analytics_summary(year=year, department=department)
    return JsonResponse(summary, safe=False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_departments(request):
    """Get list of all departments for filtering."""
    from applications.globals.models import DepartmentInfo
    departments = list(DepartmentInfo.objects.values_list("name", flat=True))
    return JsonResponse({"departments": departments})
