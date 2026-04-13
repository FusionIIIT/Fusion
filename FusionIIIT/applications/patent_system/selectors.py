"""
Patent Management System — Selectors (Database Queries)

All .objects.* usage is centralised here so views/services stay thin.

────────────────────────────────────────────────────────────────────
MIGRATION SCRIPT — run these commands after deploying this code:
────────────────────────────────────────────────────────────────────

    cd FusionIIIT
    python manage.py makemigrations patent_system
    python manage.py migrate patent_system

If you have existing data in the old Attorney / AssociatedWith tables
and want to preserve it, run the following data-migration SQL *after*
the Django migration completes:

    -- 1. Copy AssociatedWith → Inventor
    INSERT INTO patent_system_inventor (applicant_id, application_id, percentage_share)
    SELECT applicant_id, application_id, percentage_share
    FROM patent_system_associatedwith
    ON CONFLICT DO NOTHING;

    -- 2. (Optional) Drop old tables once verified
    -- DROP TABLE IF EXISTS patent_system_attorney;
    -- DROP TABLE IF EXISTS patent_system_associatedwith;

────────────────────────────────────────────────────────────────────
"""

from django.db.models import Q, Count
from django.shortcuts import get_object_or_404

from .models import (
    Application, ApplicationStatus, DecisionStatus,
    ApplicationSectionI, ApplicationSectionII, ApplicationSectionIII,
    Applicant, Inventor, CommunicationLog, Budget, AuditLog, Document,
    AttorneyAssignment, PatentabilityAssessment, FilingRecord,
    PatentNotification, ApplicationDocument,
)
from applications.globals.models import ExtraInfo, HoldsDesignation


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def get_application_or_404(application_id):
    return get_object_or_404(Application, id=application_id)


def _enrich_applicant_info(user):
    """Return dict with department + designation for a user."""
    extra = ExtraInfo.objects.filter(user=user).select_related("department").first()
    dept = extra.department.name if extra and extra.department else "Unknown"
    hd = HoldsDesignation.objects.filter(user=user).select_related("designation").first()
    desig = hd.designation.name if hd else "Unknown"
    return {"department": dept, "designation": desig}


def _section_i_data(app):
    s = ApplicationSectionI.objects.filter(application=app).first()
    if not s:
        return {}
    return {
        "type_of_ip": s.type_of_ip,
        "area": s.area,
        "problem": s.problem,
        "objective": s.objective,
        "novelty": s.novelty,
        "advantages": s.advantages,
        "is_tested": s.is_tested,
        "poc_details": s.poc_details.url if s.poc_details else None,
        "applications": s.applications,
    }


def _section_ii_data(app):
    s = ApplicationSectionII.objects.filter(application=app).first()
    if not s:
        return {}
    return {
        "funding_details": s.funding_details,
        "funding_source": s.funding_source,
        "source_agreement": s.source_agreement.url if s.source_agreement else None,
        "publication_details": s.publication_details,
        "mou_details": s.mou_details,
        "mou_file": s.mou_file.url if s.mou_file else None,
        "research_details": s.research_details,
    }


def _section_iii_data(app):
    items = ApplicationSectionIII.objects.filter(application=app)
    return [
        {
            "company_name": s.company_name,
            "contact_person": s.contact_person,
            "contact_no": s.contact_no,
            "development_stage": s.development_stage,
            "form_iii": s.form_iii.url if s.form_iii else None,
        }
        for s in items
    ]


def _inventors_data(app):
    return [
        {
            "name": inv.applicant.name,
            "email": inv.applicant.email,
            "mobile": inv.applicant.mobile,
            "address": inv.applicant.address,
            "percentage_share": str(inv.percentage_share),
            "has_consent": inv.has_consent,
            "consent_date": inv.consent_date.isoformat() if inv.consent_date else None,
        }
        for inv in Inventor.objects.filter(application=app).select_related("applicant")
    ]


def _dates_dict(app):
    return {
        "submitted_date": app.submitted_date,
        "reviewed_by_pcc_date": app.reviewed_by_pcc_date,
        "forwarded_to_director_date": app.forwarded_to_director_date,
        "director_approval_date": app.director_approval_date,
        "patentability_check_start_date": app.patentability_check_start_date,
        "patentability_check_completed_date": app.patentability_check_completed_date,
        "search_report_generated_date": app.search_report_generated_date,
        "patent_filed_date": app.patent_filed_date,
        "patent_published_date": app.patent_published_date,
        "decision_date": app.decision_date,
        "withdrawn_date": app.withdrawn_date,
        "resubmission_deadline": app.resubmission_deadline,
    }


def _attorney_assignment_data(app):
    """Return attorney assignment details for an application (UC-006)."""
    try:
        a = AttorneyAssignment.objects.get(application=app)
        return {
            "id": a.id,
            "attorney_name": a.attorney_name,
            "attorney_email": a.attorney_email,
            "attorney_phone": a.attorney_phone,
            "attorney_firm": a.attorney_firm,
            "specialization": a.specialization,
            "assigned_by": a.assigned_by.get_full_name() if a.assigned_by else None,
            "assignment_date": a.assignment_date,
            "engagement_proof": a.engagement_proof.url if a.engagement_proof else None,
            "remarks": a.remarks,
            "is_active": a.is_active,
        }
    except AttorneyAssignment.DoesNotExist:
        return None


def _patentability_assessment_data(app):
    """Return patentability assessment details for an application (UC-007, BR-PMS-014)."""
    try:
        p = PatentabilityAssessment.objects.get(application=app)
        return {
            "id": p.id,
            "assessed_by_attorney": p.assessed_by_attorney,
            "novelty_score": str(p.novelty_score),
            "non_obviousness_score": str(p.non_obviousness_score),
            "utility_score": str(p.utility_score),
            "search_completeness": str(p.search_completeness),
            "recommendation": p.recommendation,
            "opinion_summary": p.opinion_summary,
            "prior_art_references": p.prior_art_references,
            "attorney_report": p.attorney_report.url if p.attorney_report else None,
            "recorded_by": p.recorded_by.get_full_name() if p.recorded_by else None,
            "assessment_date": p.assessment_date,
            "created_at": p.created_at,
        }
    except PatentabilityAssessment.DoesNotExist:
        return None


def _filing_record_data(app):
    """Return filing record details for an application (UC-009, WF-601)."""
    try:
        f = FilingRecord.objects.get(application=app)
        return {
            "id": f.id,
            "filing_office": f.filing_office,
            "jurisdiction": f.jurisdiction,
            "external_filing_id": f.external_filing_id,
            "filing_date": f.filing_date,
            "confirmation_proof": f.confirmation_proof.url if f.confirmation_proof else None,
            "international_filing_justification": f.international_filing_justification,
            "filed_by": f.filed_by.get_full_name() if f.filed_by else None,
            "remarks": f.remarks,
            "created_at": f.created_at,
        }
    except FilingRecord.DoesNotExist:
        return None


def full_application_detail(app):
    """Return complete dict for a single application (used by all detail views)."""
    primary = app.primary_applicant
    info = _enrich_applicant_info(primary.user) if primary else {}
    return {
        "application_id": app.id,
        "title": app.title,
        "status": app.status,
        "decision_status": app.decision_status,
        "token_no": app.token_no or "Token not generated",
        "comments": app.comments,
        "director_feedback": app.director_feedback,
        "primary_applicant_name": primary.name if primary else None,
        "primary_applicant_department": info.get("department"),
        "primary_applicant_designation": info.get("designation"),
        "dates": _dates_dict(app),
        "inventors": _inventors_data(app),
        "section_I": _section_i_data(app),
        "section_II": _section_ii_data(app),
        "section_III": _section_iii_data(app),
        "attorney_assignment": _attorney_assignment_data(app),
        "patentability_assessment": _patentability_assessment_data(app),
        "filing_record": _filing_record_data(app),
        "last_updated_at": app.last_updated_at,
    }


# ---------------------------------------------------------------------------
# Applicant selectors
# ---------------------------------------------------------------------------

def get_applicant_applications(user):
    """All applications where user is an inventor (UC-002 old / UC-005 new)."""
    try:
        applicant = Applicant.objects.get(user=user)
    except Applicant.DoesNotExist:
        return []

    app_ids = Inventor.objects.filter(applicant=applicant).values_list("application_id", flat=True)
    apps = Application.objects.filter(id__in=app_ids).select_related("primary_applicant")

    return [
        {
            "application_id": a.id,
            "title": a.title,
            "status": a.status,
            "token_no": a.token_no,
            "submitted_date": a.submitted_date,
        }
        for a in apps
    ]


def get_applicant_application_detail(user, application_id):
    """Single application detail for an applicant (UC-003)."""
    app = get_application_or_404(application_id)
    # verify association
    try:
        applicant = Applicant.objects.get(user=user)
    except Applicant.DoesNotExist:
        return None
    if not Inventor.objects.filter(applicant=applicant, application=app).exists():
        return None
    return full_application_detail(app)


def get_pending_consent_applications(user):
    """Get applications where current user is an inventor and consent is pending."""
    try:
        applicant = Applicant.objects.get(user=user)
    except Applicant.DoesNotExist:
        return []

    # Find applications where user is an inventor but hasn't given consent yet
    pending_inventions = Inventor.objects.filter(
        applicant=applicant,
        has_consent=False
    ).select_related("application", "application__primary_applicant")

    result = []
    for invention in pending_inventions:
        app = invention.application

        # Get total inventors and consents received
        all_inventors = Inventor.objects.filter(application=app)
        total_inventors = all_inventors.count()
        consents_received = all_inventors.filter(has_consent=True).count()

        result.append({
            "application_id": app.id,
            "title": app.title,
            "token_number": app.token_no,
            "status": app.status,
            "primary_applicant": app.primary_applicant.name if app.primary_applicant else "Unknown",
            "submitted_date": app.submitted_date.isoformat() if app.submitted_date else None,
            "your_percentage": invention.percentage_share,
            "total_inventors": total_inventors,
            "consents_received": consents_received,
        })

    return result


# ---------------------------------------------------------------------------
# PCC Admin selectors
# ---------------------------------------------------------------------------

def get_new_applications_pcc():
    """Applications with Submitted / Reviewed / Resubmitted status (UC-005 old)."""
    statuses = [ApplicationStatus.SUBMITTED, ApplicationStatus.REVIEWED, ApplicationStatus.RESUBMITTED]
    apps = Application.objects.filter(status__in=statuses).select_related("primary_applicant")
    result = {}
    for a in apps:
        info = _enrich_applicant_info(a.primary_applicant.user) if a.primary_applicant else {}
        result[a.id] = {
            "title": a.title,
            "submitted_by": a.primary_applicant.name if a.primary_applicant else "Unknown",
            "designation": info.get("designation", "Unknown"),
            "department": info.get("department", "Unknown"),
            "submitted_on": a.submitted_date.strftime("%Y-%m-%d") if a.submitted_date else "Unknown",
            "status": a.status,
        }
    return result


def get_ongoing_applications_pcc():
    """Applications in active processing (post-director) for PCC Admin."""
    statuses = [
        ApplicationStatus.FORWARDED,
        ApplicationStatus.APPROVED,
        ApplicationStatus.PATENTABILITY_CHECK_STARTED,
        ApplicationStatus.PATENTABILITY_CHECK_COMPLETED,
        ApplicationStatus.SEARCH_REPORT_GENERATED,
        ApplicationStatus.PATENT_FILED,
        ApplicationStatus.PATENT_PUBLISHED,
    ]
    apps = Application.objects.filter(status__in=statuses).select_related("primary_applicant")
    result = {}
    for a in apps:
        info = _enrich_applicant_info(a.primary_applicant.user) if a.primary_applicant else {}
        result[a.id] = {
            "token_no": a.token_no or "Token not generated",
            "title": a.title,
            "submitted_by": a.primary_applicant.name if a.primary_applicant else "Unknown",
            "designation": info.get("designation", "Unknown"),
            "department": info.get("department", "Unknown"),
            "submitted_on": a.submitted_date.strftime("%Y-%m-%d") if a.submitted_date else "Unknown",
            "status": a.status,
        }
    return result


def get_past_applications_pcc():
    """Decided applications for PCC Admin."""
    apps = Application.objects.filter(
        decision_status__in=[DecisionStatus.APPROVED, DecisionStatus.REJECTED]
    ).select_related("primary_applicant")
    result = {}
    for a in apps:
        info = _enrich_applicant_info(a.primary_applicant.user) if a.primary_applicant else {}
        result[a.id] = {
            "token_no": a.token_no or "Token not generated",
            "title": a.title,
            "submitted_by": a.primary_applicant.name if a.primary_applicant else "Unknown",
            "designation": info.get("designation", "Unknown"),
            "department": info.get("department", "Unknown"),
            "submitted_on": a.submitted_date.strftime("%Y-%m-%d") if a.submitted_date else "Unknown",
            "decision_status": a.decision_status,
        }
    return result


def get_pcc_application_detail(application_id):
    app = get_application_or_404(application_id)
    detail = full_application_detail(app)
    # Attach communication logs (with confidentiality level — BR-PMS-019)
    logs = CommunicationLog.objects.filter(application=app)
    detail["communications"] = [
        {
            "id": l.id,
            "direction": l.direction,
            "subject": l.subject,
            "body": l.body,
            "external_party_name": l.external_party_name,
            "external_party_email": l.external_party_email,
            "attachment": l.attachment.url if l.attachment else None,
            "confidentiality_level": l.confidentiality_level,
            "created_at": l.created_at,
        }
        for l in logs
    ]
    # Attach budget
    try:
        b = Budget.objects.get(application=app)
        detail["budget"] = {
            "filing_cost": str(b.filing_cost),
            "attorney_fees": str(b.attorney_fees),
            "administrative_cost": str(b.administrative_cost),
            "total_cost": str(b.total_cost),
            "decision": b.decision,
            "remarks": b.remarks,
        }
    except Budget.DoesNotExist:
        detail["budget"] = None
    return detail


# ---------------------------------------------------------------------------
# Director selectors
# ---------------------------------------------------------------------------

def get_director_new_applications():
    """Applications forwarded for Director's review."""
    apps = Application.objects.filter(
        status=ApplicationStatus.FORWARDED
    ).select_related("primary_applicant")
    result = {}
    for a in apps:
        info = _enrich_applicant_info(a.primary_applicant.user) if a.primary_applicant else {}
        result[a.id] = {
            "token_no": a.token_no or "Token not generated",
            "title": a.title,
            "submitted_by": a.primary_applicant.name if a.primary_applicant else "Unknown",
            "department": info.get("department", "Unknown"),
            "forwarded_on": a.forwarded_to_director_date.strftime("%Y-%m-%d %H:%M") if a.forwarded_to_director_date else "Unknown",
        }
    return result


def get_director_reviewed_applications():
    """Applications the director has already acted on."""
    statuses = [
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.NEEDS_REVISION,
        ApplicationStatus.PATENTABILITY_CHECK_STARTED,
        ApplicationStatus.PATENTABILITY_CHECK_COMPLETED,
        ApplicationStatus.SEARCH_REPORT_GENERATED,
        ApplicationStatus.PATENT_FILED,
        ApplicationStatus.PATENT_PUBLISHED,
        ApplicationStatus.PATENT_GRANTED,
        ApplicationStatus.PATENT_REFUSED,
    ]
    apps = Application.objects.filter(status__in=statuses).select_related("primary_applicant")
    result = {}
    for a in apps:
        info = _enrich_applicant_info(a.primary_applicant.user) if a.primary_applicant else {}
        result[a.id] = {
            "token_no": a.token_no or "Token not generated",
            "title": a.title,
            "submitted_by": a.primary_applicant.name if a.primary_applicant else "Unknown",
            "department": info.get("department", "Unknown"),
            "forwarded_on": a.forwarded_to_director_date if a.forwarded_to_director_date else None,
            "decision_date": a.decision_date if a.decision_date else None,
            "status": a.status,
        }
    return result


def get_director_application_detail(application_id):
    app = get_application_or_404(application_id)
    return full_application_detail(app)


# ---------------------------------------------------------------------------
# Analytics / Reports  (UC-015)
# ---------------------------------------------------------------------------

def get_application_stats(year=None):
    """Aggregate counts per status for analytics dashboards.
    Optionally filter by year of submission.
    """
    qs = Application.objects.all()
    if year:
        try:
            qs = qs.filter(submitted_date__year=int(year))
        except (ValueError, TypeError):
            pass
    return (
        qs.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )


def get_available_years():
    """Return sorted list of years that have at least one application."""
    from django.db.models.functions import ExtractYear
    years = (
        Application.objects
        .annotate(year=ExtractYear("submitted_date"))
        .values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )
    return [y for y in years if y is not None]


# ---------------------------------------------------------------------------
# Communication logs
# ---------------------------------------------------------------------------

def get_communication_logs(application_id):
    return CommunicationLog.objects.filter(application_id=application_id)


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

def get_budget(application_id):
    try:
        return Budget.objects.get(application_id=application_id)
    except Budget.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------

def get_audit_logs(application_id):
    return AuditLog.objects.filter(application_id=application_id)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

def get_all_documents():
    return Document.objects.all()


def get_document_or_404(doc_id):
    return get_object_or_404(Document, id=doc_id)


# ---------------------------------------------------------------------------
# Attorney Assignment  (UC-006)
# ---------------------------------------------------------------------------

def get_attorney_assignment(application_id):
    try:
        return AttorneyAssignment.objects.get(application_id=application_id)
    except AttorneyAssignment.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Patentability Assessment  (UC-007)
# ---------------------------------------------------------------------------

def get_patentability_assessment(application_id):
    try:
        return PatentabilityAssessment.objects.get(application_id=application_id)
    except PatentabilityAssessment.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Filing Record  (UC-009)
# ---------------------------------------------------------------------------

def get_filing_record(application_id):
    try:
        return FilingRecord.objects.get(application_id=application_id)
    except FilingRecord.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Feature 2: Inventor Consent Status
# ---------------------------------------------------------------------------

def get_inventors_consent_status(application_id):
    """Get consent status for all inventors on an application."""
    inventors = Inventor.objects.filter(application_id=application_id).select_related("applicant")
    total_share = sum(inv.percentage_share for inv in inventors)
    all_consented = all(inv.has_consent for inv in inventors) if inventors else False

    return {
        "application_id": application_id,
        "total_share": str(total_share),
        "shares_valid": total_share == 100,
        "all_consented": all_consented,
        "inventors": [
            {
                "id": inv.id,
                "applicant_id": inv.applicant.id,
                "name": inv.applicant.name,
                "email": inv.applicant.email,
                "percentage_share": str(inv.percentage_share),
                "has_consent": inv.has_consent,
                "consent_date": inv.consent_date.isoformat() if inv.consent_date else None,
            }
            for inv in inventors
        ]
    }


# ---------------------------------------------------------------------------
# Feature 4: Notifications
# ---------------------------------------------------------------------------

def get_user_notifications(user, unread_only=False, limit=50):
    """Get notifications for a user."""
    qs = PatentNotification.objects.filter(recipient=user)
    if unread_only:
        qs = qs.filter(is_read=False)
    return qs[:limit]


def get_unread_notification_count(user):
    """Get count of unread notifications."""
    return PatentNotification.objects.filter(recipient=user, is_read=False).count()


# ---------------------------------------------------------------------------
# Feature 5: Application Documents
# ---------------------------------------------------------------------------

def get_application_documents(application_id, document_type=None, current_only=False):
    """Get documents for an application with optional filtering."""
    qs = ApplicationDocument.objects.filter(application_id=application_id)
    if document_type:
        qs = qs.filter(document_type=document_type)
    if current_only:
        qs = qs.filter(is_current=True)
    return qs


def get_document_history(application_id, document_type):
    """Get version history for a specific document type."""
    return ApplicationDocument.objects.filter(
        application_id=application_id,
        document_type=document_type
    ).order_by("-version")


# ---------------------------------------------------------------------------
# Feature 6: Applications pending appeal review
# ---------------------------------------------------------------------------

def get_applications_pending_appeal():
    """Get applications with pending appeals for PCC Admin."""
    apps = Application.objects.filter(
        status=ApplicationStatus.APPEAL
    ).select_related("primary_applicant")
    result = {}
    for a in apps:
        info = _enrich_applicant_info(a.primary_applicant.user) if a.primary_applicant else {}
        result[a.id] = {
            "title": a.title,
            "submitted_by": a.primary_applicant.name if a.primary_applicant else "Unknown",
            "department": info.get("department", "Unknown"),
            "appeal_date": a.appeal_date,
            "appeal_reason": a.appeal_reason[:100] + "..." if len(a.appeal_reason) > 100 else a.appeal_reason,
        }
    return result


def get_appeals_under_review():
    """Get appeals under Director review."""
    apps = Application.objects.filter(
        status=ApplicationStatus.APPEAL_UNDER_REVIEW
    ).select_related("primary_applicant")
    result = {}
    for a in apps:
        info = _enrich_applicant_info(a.primary_applicant.user) if a.primary_applicant else {}
        result[a.id] = {
            "title": a.title,
            "submitted_by": a.primary_applicant.name if a.primary_applicant else "Unknown",
            "department": info.get("department", "Unknown"),
            "appeal_date": a.appeal_date,
            "appeal_reason": a.appeal_reason,
        }
    return result
