"""
Patent Management System — Services (Business Logic)
All business rules, validations, status transitions, token generation.
"""

import logging
from datetime import timedelta
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.db import transaction, models
from django.shortcuts import get_object_or_404

from .models import (
    Application, ApplicationStatus, DecisionStatus,
    Applicant, Inventor, AuditLog, Budget, BudgetDecision,
    ApplicationSectionI, ApplicationSectionII, ApplicationSectionIII,
    CommunicationLog, CommunicationDirection, ConfidentialityLevel,
    AttorneyAssignment, PatentabilityAssessment,
    FilingRecord, PatentabilityRecommendation,
    PatentNotification, NotificationType, ApplicationDocument,
)

from applications.globals.models import ExtraInfo, HoldsDesignation

logger = logging.getLogger(__name__)

BUDGET_THRESHOLD = 100000  # ₹1,00,000 — escalation threshold (BR-PMS-008)
REVISION_WINDOW_DAYS = 60  # BR-PMS-016


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class PatentServiceError(Exception):
    """Base exception for patent service errors."""
    def __init__(self, message, code=400):
        self.message = message
        self.code = code
        super().__init__(self.message)


class UnauthorizedError(PatentServiceError):
    def __init__(self, message="You are not authorized to perform this action."):
        super().__init__(message, code=403)


class NotFoundError(PatentServiceError):
    def __init__(self, message="Resource not found."):
        super().__init__(message, code=404)


class ValidationError(PatentServiceError):
    def __init__(self, message="Validation failed."):
        super().__init__(message, code=400)


class ConflictOfInterestError(PatentServiceError):
    def __init__(self, message="Conflict of interest detected."):
        super().__init__(message, code=409)


# ---------------------------------------------------------------------------
# Role Helpers  (BR-PMS-002)
# ---------------------------------------------------------------------------

def _get_user_designation(user):
    """Return the designation name for a user, or None."""
    hd = HoldsDesignation.objects.filter(user=user).select_related("designation").first()
    return hd.designation.name if hd else None


def _get_user_extra_info(user):
    return ExtraInfo.objects.filter(user=user).first()


def is_pcc_admin(user):
    designation = _get_user_designation(user)
    return designation and "PCC" in designation.upper()


def is_director(user):
    designation = _get_user_designation(user)
    return designation and "director" in designation.lower()


def assert_pcc_admin(user):
    if not is_pcc_admin(user):
        raise UnauthorizedError("Only PCC Admin can perform this action.")


def assert_director(user):
    if not is_director(user):
        raise UnauthorizedError("Only Director can perform this action.")


def assert_applicant(user, application):
    """User must be associated with the application as inventor."""
    try:
        applicant = Applicant.objects.get(user=user)
    except Applicant.DoesNotExist:
        raise UnauthorizedError("User is not a registered applicant.")
    if not Inventor.objects.filter(applicant=applicant, application=application).exists():
        raise UnauthorizedError("You are not associated with this application.")
    return applicant


# ---------------------------------------------------------------------------
# Audit helper  (BR-PMS-018)
# ---------------------------------------------------------------------------

def _audit(application, user, action, prev="", new="", details=""):
    AuditLog.objects.create(
        application=application,
        user=user,
        action=action,
        previous_state=prev,
        new_state=new,
        details=details,
    )


# ---------------------------------------------------------------------------
# VALID STATUS TRANSITIONS  (BR-PMS-004, BR-PMS-009)
# ---------------------------------------------------------------------------

VALID_TRANSITIONS = {
    ApplicationStatus.DRAFT: [ApplicationStatus.PENDING_INVENTOR_CONSENT],
    ApplicationStatus.PENDING_INVENTOR_CONSENT: [ApplicationStatus.SUBMITTED, ApplicationStatus.NEEDS_REVISION, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.SUBMITTED: [ApplicationStatus.UNDER_REVIEW, ApplicationStatus.REVIEWED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.UNDER_REVIEW: [ApplicationStatus.REVIEWED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.REVIEWED: [ApplicationStatus.FORWARDED, ApplicationStatus.DRAFT, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.FORWARDED: [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED, ApplicationStatus.NEEDS_REVISION],
    ApplicationStatus.APPROVED: [
        ApplicationStatus.PATENTABILITY_CHECK_STARTED,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.NEEDS_REVISION: [ApplicationStatus.RESUBMITTED, ApplicationStatus.EXPIRED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.REJECTED: [ApplicationStatus.APPEAL, ApplicationStatus.RESUBMITTED, ApplicationStatus.EXPIRED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.RESUBMITTED: [ApplicationStatus.UNDER_REVIEW],
    # Feature 1: Appeal workflow transitions
    ApplicationStatus.APPEAL: [ApplicationStatus.APPEAL_UNDER_REVIEW],
    ApplicationStatus.APPEAL_UNDER_REVIEW: [ApplicationStatus.APPEAL_APPROVED, ApplicationStatus.APPEAL_REJECTED],
    ApplicationStatus.APPEAL_APPROVED: [ApplicationStatus.FORWARDED],  # Goes back to director review
    ApplicationStatus.APPEAL_REJECTED: [ApplicationStatus.EXPIRED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.PATENTABILITY_CHECK_STARTED: [ApplicationStatus.PATENTABILITY_CHECK_COMPLETED, ApplicationStatus.NEEDS_REVISION],
    ApplicationStatus.PATENTABILITY_CHECK_COMPLETED: [ApplicationStatus.SEARCH_REPORT_GENERATED, ApplicationStatus.NEEDS_REVISION],
    ApplicationStatus.SEARCH_REPORT_GENERATED: [ApplicationStatus.PATENT_FILED],
    ApplicationStatus.PATENT_FILED: [ApplicationStatus.PATENT_PUBLISHED],
    ApplicationStatus.PATENT_PUBLISHED: [ApplicationStatus.PATENT_GRANTED, ApplicationStatus.PATENT_REFUSED, ApplicationStatus.REJECTED],
}


def _validate_transition(current, target):
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise ValidationError(
            f"Invalid status transition from '{current}' to '{target}'. "
            f"Allowed: {[s.value for s in allowed]}"
        )


# ---------------------------------------------------------------------------
# Token generation  (BR-PMS-010)
# ---------------------------------------------------------------------------

def _generate_token(application):
    applicant = application.primary_applicant
    user = applicant.user
    extra = _get_user_extra_info(user)
    dept = extra.department.name[:3].upper() if extra and extra.department else "UNK"
    date_str = application.submitted_date.strftime("%Y%m%d") if application.submitted_date else now().strftime("%Y%m%d")
    app_id = f"{application.id:06d}"
    last = Application.objects.filter(token_no__isnull=False).order_by("-id").first()
    serial = int(last.token_no.split("/")[-1]) + 1 if last and last.token_no else 104
    return f"IIITDMJ/{dept}/{date_str}/{app_id}/{serial:03d}"


# ---------------------------------------------------------------------------
# Conflict-of-interest check  (BR-PMS-003)
# ---------------------------------------------------------------------------

def _check_director_conflict(director_user, application):
    """Director must NOT be listed as an inventor on the application."""
    try:
        applicant = Applicant.objects.get(user=director_user)
        if Inventor.objects.filter(applicant=applicant, application=application).exists():
            raise ConflictOfInterestError(
                "Director is listed as an inventor on this application and cannot review it."
            )
    except Applicant.DoesNotExist:
        pass  # Director is not an applicant — no conflict


# ===========================================================================
# SERVICE FUNCTIONS  (one per use-case / action)
# ===========================================================================

# ── UC-001: Submit Application ────────────────────────────────────────────

@transaction.atomic
def submit_application(user, data, files):
    """
    Create and submit a new patent application (WF-101).
    Returns the created Application instance.
    """
    required = [
        "title", "inventors", "area_of_invention", "problem_statement",
        "objective", "ip_type", "novelty", "advantages",
        "tested_experimentally", "applications",
        "funding_details", "funding_source", "publication_details",
        "mou_details", "research_details", "company_details",
        "development_stage",
    ]
    for f in required:
        if f not in data:
            raise ValidationError(f"Missing required field: {f}")

    inventors_data = data["inventors"]
    if not isinstance(inventors_data, list) or len(inventors_data) == 0:
        raise ValidationError("At least one inventor is required.")

    # Applicant profile
    applicant, _ = Applicant.objects.get_or_create(
        user=user,
        defaults={
            "email": user.email,
            "name": user.get_full_name() or user.username,
        },
    )

    application = Application.objects.create(
        title=data["title"],
        status=ApplicationStatus.PENDING_INVENTOR_CONSENT,
        decision_status=DecisionStatus.PENDING,
        submitted_date=now(),
        primary_applicant=applicant,
    )

    # Section I
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
        poc_details=files.get("poc_details"),
    )

    # Section II
    ApplicationSectionII.objects.create(
        application=application,
        funding_details=data["funding_details"],
        funding_source=data["funding_source"],
        source_agreement=files.get("source_file"),
        publication_details=data["publication_details"],
        mou_details=data["mou_details"],
        mou_file=files.get("mou_file"),
        research_details=data["research_details"],
    )

    # Section III  (multiple companies)
    companies = data.get("company_details", [])
    if not isinstance(companies, list):
        raise ValidationError("company_details must be a list.")
    for c in companies:
        if not all(k in c for k in ("company_name", "contact_person", "contact_no")):
            raise ValidationError("Each company must have company_name, contact_person, contact_no.")
        ApplicationSectionIII.objects.create(
            application=application,
            company_name=c["company_name"],
            contact_person=c["contact_person"],
            contact_no=c["contact_no"],
            development_stage=data["development_stage"],
            form_iii=files.get("form_iii"),
        )

    # Inventors (AssociatedWith → now Inventor)
    total_percentage = 0
    for inv in inventors_data:
        email = inv.get("institute_mail", "")
        if not email:
            raise ValidationError("Each inventor must have an institute_mail.")
        try:
            inv_user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise NotFoundError(f"Inventor with email {email} not found in system.")
        inv_applicant, _ = Applicant.objects.update_or_create(
            user=inv_user,
            defaults={
                "email": inv.get("personal_mail", inv_user.email),
                "name": inv.get("name", inv_user.get_full_name()),
                "mobile": inv.get("mobile", ""),
                "address": inv.get("address", ""),
            },
        )
        percentage = inv.get("percentage", 0)
        # Convert percentage to float/int to handle string inputs from frontend
        try:
            percentage = float(percentage) if percentage else 0
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid percentage value for inventor: {percentage}")

        total_percentage += percentage
        Inventor.objects.create(
            application=application,
            applicant=inv_applicant,
            percentage_share=percentage,
        )

    # CRITICAL: Validate inventor shares sum to exactly 100%
    if total_percentage != 100:
        raise ValidationError(f"Inventor percentage shares must sum to exactly 100%. Current total: {total_percentage}%")

    # Create notifications for all inventors to review and consent
    for inventor in Inventor.objects.filter(application=application):
        _create_notification_for_applicant(
            application,
            NotificationType.CONSENT_REQUIRED,
            "Inventor Consent Required",
            f"Please review and provide consent for patent application '{application.title}'. "
            f"Your percentage share is {inventor.percentage_share}%."
        )

    _audit(application, user, "Application Created - Pending Inventor Consent", "", ApplicationStatus.PENDING_INVENTOR_CONSENT)
    return application


# ── UC-002: Assign to Director (PCC Admin) ──────────────────────────────

@transaction.atomic
def assign_to_director(user, application_id, director_user_id=None):
    """PCC Admin assigns an application to a Director for review."""
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    if application.status not in (ApplicationStatus.SUBMITTED, ApplicationStatus.REVIEWED, ApplicationStatus.RESUBMITTED):
        raise ValidationError("Application is not in a state that can be assigned to a director.")

    # CRITICAL VALIDATION: Check inventor requirements before director assignment
    try:
        validate_inventor_shares(application)
    except ValidationError:
        raise ValidationError("Cannot assign to director: Inventor percentage shares must sum to exactly 100%.")

    if not check_all_consents(application):
        raise ValidationError("Cannot assign to director: All inventors must give their consent before director assignment.")

    if director_user_id:
        try:
            director = User.objects.get(id=director_user_id)
        except User.DoesNotExist:
            raise NotFoundError("Director user not found.")
        
        # pass the User object to the conflict checker
        _check_director_conflict(director, application)
        application.assigned_director = director

    prev = application.status
    application.status = ApplicationStatus.UNDER_REVIEW
    application.save()
    _audit(application, user, "Assigned to Director", prev, application.status)
    return application


# ── UC-003: Director reviews application ─────────────────────────────────

@transaction.atomic
def director_review(user, application_id, decision, feedback=""):
    """
    Director makes decision: Approve / Reject / Needs Revision  (WF-003, BR-PMS-004/005).
    """
    assert_director(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    if application.status != ApplicationStatus.FORWARDED:
        raise ValidationError(
            f"Application must be 'Forwarded for Director's Review'. Current: {application.status}"
        )

    if application.assigned_director and application.assigned_director != user:
        raise UnauthorizedError("You are not the assigned director for this application.")

    _check_director_conflict(user, application)

    # CRITICAL VALIDATION: Check inventor requirements before any director decision
    try:
        validate_inventor_shares(application)
    except ValidationError:
        raise ValidationError("Cannot make director decision: Inventor percentage shares must sum to exactly 100%.")

    if not check_all_consents(application):
        raise ValidationError("Cannot make director decision: All inventors must give their consent before director review.")

    if decision not in ("Approve", "Reject", "Needs Revision"):
        raise ValidationError("Decision must be 'Approve', 'Reject', or 'Needs Revision'.")

    # BR-PMS-005: rejection requires feedback ≥50 chars
    if decision in ("Reject", "Needs Revision"):
        if not feedback or len(feedback.strip()) < 50:
            raise ValidationError("Feedback must be at least 50 characters for Reject / Needs Revision.")

    prev = application.status

    if decision == "Approve":
        application.status = ApplicationStatus.APPROVED
        application.decision_status = DecisionStatus.APPROVED
        application.director_approval_date = now()
        application.token_no = _generate_token(application)
    elif decision == "Reject":
        application.status = ApplicationStatus.REJECTED
        application.decision_status = DecisionStatus.REJECTED
        application.decision_date = now()
        application.resubmission_deadline = now() + timedelta(days=REVISION_WINDOW_DAYS)
    else:  # Needs Revision
        application.status = ApplicationStatus.NEEDS_REVISION
        application.decision_status = DecisionStatus.NEEDS_REVISION
        application.decision_date = now()
        application.resubmission_deadline = now() + timedelta(days=REVISION_WINDOW_DAYS)

    application.director_feedback = feedback
    application.save()
    _audit(application, user, f"Director decision: {decision}", prev, application.status, feedback)
    return application


# ── UC-004: Revise and resubmit (WF-201) ─────────────────────────────────

@transaction.atomic
def resubmit_application(user, application_id, data, files):
    """Applicant resubmits after revision within 60-day window."""
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    applicant = assert_applicant(user, application)

    if application.status not in (ApplicationStatus.NEEDS_REVISION, ApplicationStatus.REJECTED):
        raise ValidationError("Application is not in a revisable state.")

    # BR-PMS-016: 60-day window
    if application.resubmission_deadline and now() > application.resubmission_deadline:
        application.status = ApplicationStatus.EXPIRED
        application.save()
        _audit(application, user, "Resubmission expired", application.status, ApplicationStatus.EXPIRED)
        raise ValidationError("The 60-day resubmission window has expired.")

    prev = application.status

    # NOTE: During resubmission, inventor data is LOCKED and cannot be changed
    # Only technical content (Sections I, II, III) can be updated
    # Inventor percentages and consent status remain from original submission

    # Update sections if data provided
    if "title" in data:
        application.title = data["title"]

    # Update Section I
    sec1 = ApplicationSectionI.objects.filter(application=application).first()
    if sec1:
        for k, attr in [("area_of_invention", "area"), ("problem_statement", "problem"),
                         ("objective", "objective"), ("novelty", "novelty"),
                         ("advantages", "advantages"), ("ip_type", "type_of_ip"),
                         ("tested_experimentally", "is_tested"), ("applications", "applications")]:
            if k in data:
                setattr(sec1, attr, data[k])
        if files.get("poc_details"):
            sec1.poc_details = files["poc_details"]
        sec1.save()

    # Update Section II
    sec2 = ApplicationSectionII.objects.filter(application=application).first()
    if sec2:
        for k in ["funding_details", "funding_source", "publication_details",
                   "mou_details", "research_details"]:
            if k in data:
                setattr(sec2, k, data[k])
        if files.get("source_file"):
            sec2.source_agreement = files["source_file"]
        if files.get("mou_file"):
            sec2.mou_file = files["mou_file"]
        sec2.save()

    application.status = ApplicationStatus.RESUBMITTED
    application.decision_status = DecisionStatus.PENDING
    application.submitted_date = now()
    application.comments = data.get("comments", application.comments)
    application.save()

    _audit(application, user, "Application resubmitted", prev, ApplicationStatus.RESUBMITTED)
    return application


# ── UC-006: PCC Admin reviews application ─────────────────────────────────

@transaction.atomic
def pcc_review_application(user, application_id, comments=""):
    """PCC Admin marks application as reviewed (WF-002)."""
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    if application.status == ApplicationStatus.REVIEWED:
        raise ValidationError("Application is already reviewed.")

    if application.status not in (ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW, ApplicationStatus.RESUBMITTED):
        raise ValidationError("Application cannot be reviewed in its current state.")

    # CRITICAL VALIDATION: Check inventor requirements before PCC Admin can process
    try:
        validate_inventor_shares(application)
    except ValidationError:
        raise ValidationError("Cannot process application: Inventor percentage shares must sum to exactly 100%.")

    if not check_all_consents(application):
        raise ValidationError("Cannot process application: All inventors must give their consent before PCC Admin review.")

    prev = application.status
    application.status = ApplicationStatus.REVIEWED
    application.reviewed_by_pcc_date = now()
    if comments:
        application.comments = comments
    application.save()

    _audit(application, user, "PCC Admin reviewed", prev, ApplicationStatus.REVIEWED, comments)
    return application


# ── UC-007: Forward to Director (PCC Admin) ──────────────────────────────

@transaction.atomic
def forward_to_director(user, application_id, comments="", director_id=None):
    """PCC Admin forwards a reviewed application to Director."""
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    if application.status == ApplicationStatus.FORWARDED:
        raise ValidationError("Application is already forwarded.")

    if application.status not in [ApplicationStatus.REVIEWED, ApplicationStatus.SUBMITTED, ApplicationStatus.RESUBMITTED]:
        raise ValidationError("Application must be reviewed or submitted before forwarding.")

    # CRITICAL VALIDATION: Check inventor requirements before forwarding to director
    try:
        validate_inventor_shares(application)
    except ValidationError:
        raise ValidationError("Cannot forward to director: Inventor percentage shares must sum to exactly 100%.")

    if not check_all_consents(application):
        raise ValidationError("Cannot forward to director: All inventors must give their consent before forwarding.")

    if comments and len(comments) > 1000:
        raise ValidationError("Comments must be ≤ 1000 characters.")

    if director_id:
        try:
            director_user = User.objects.get(id=director_id)
            application.assigned_director = director_user
        except User.DoesNotExist:
            raise ValidationError("Specified Director does not exist.")

    prev = application.status
    application.status = ApplicationStatus.FORWARDED
    application.forwarded_to_director_date = now()
    if comments:
        application.comments = comments
    application.save()

    _audit(application, user, "Forwarded to Director", prev, ApplicationStatus.FORWARDED, comments)
    return application


# ── UC-008: Request modification (PCC Admin) ─────────────────────────────

@transaction.atomic
def request_modification(user, application_id, comments):
    """Send application back for applicant edits (Needs Revision)."""
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    if application.status in [ApplicationStatus.DRAFT, ApplicationStatus.NEEDS_REVISION]:
        raise ValidationError(f"Application is already in {application.status}.")

    if not comments or len(comments.strip()) < 10:
        raise ValidationError("Comments are required (min 10 characters).")
    if len(comments) > 1000:
        raise ValidationError("Comments must be ≤ 1000 characters.")

    prev = application.status
    application.status = ApplicationStatus.NEEDS_REVISION
    application.decision_status = DecisionStatus.NEEDS_REVISION
    application.comments = comments
    from datetime import timedelta
    application.resubmission_deadline = now() + timedelta(days=60)
    application.save()

    try:
        from notifications.signals import notify
        
        applicant_user = application.primary_applicant.user
        notify.send(sender=user, recipient=applicant_user, 
                    verb='requested modification for your patent application',
                    description=comments, target=application)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Could not send notification: %s", e)

    _audit(application, user, "Modification requested", prev, ApplicationStatus.NEEDS_REVISION, comments)
    return application


# ── PCC Admin: Change ongoing application status ─────────────────────────

ONGOING_DATE_MAP = {
    ApplicationStatus.PATENTABILITY_CHECK_STARTED: "patentability_check_start_date",
    ApplicationStatus.PATENTABILITY_CHECK_COMPLETED: "patentability_check_completed_date",
    ApplicationStatus.SEARCH_REPORT_GENERATED: "search_report_generated_date",
    ApplicationStatus.PATENT_FILED: "patent_filed_date",
    ApplicationStatus.PATENT_PUBLISHED: "patent_published_date",
    ApplicationStatus.PATENT_GRANTED: "decision_date",
    ApplicationStatus.PATENT_REFUSED: "decision_date",
}


@transaction.atomic
def change_status(user, application_id, next_status):
    """PCC Admin advances an ongoing application through the pipeline."""
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    _validate_transition(application.status, next_status)

    # CRITICAL VALIDATION: Check inventor requirements before advancing status
    try:
        validate_inventor_shares(application)
    except ValidationError:
        raise ValidationError("Cannot advance status: Inventor percentage shares must sum to exactly 100%.")

    if not check_all_consents(application):
        raise ValidationError("Cannot advance status: All inventors must give their consent before status advancement.")

    prev = application.status
    application.status = next_status

    date_field = ONGOING_DATE_MAP.get(next_status)
    if date_field:
        setattr(application, date_field, now())

    if next_status == ApplicationStatus.PATENT_GRANTED:
        application.decision_status = DecisionStatus.APPROVED
    elif next_status == ApplicationStatus.PATENT_REFUSED:
        application.decision_status = DecisionStatus.REJECTED

    application.save()
    _audit(application, user, f"Status changed to {next_status}", prev, next_status)
    return application


# ── UC-014: Withdraw application ─────────────────────────────────────────

NON_WITHDRAWABLE = {
    ApplicationStatus.PATENT_FILED, ApplicationStatus.PATENT_PUBLISHED,
    ApplicationStatus.PATENT_GRANTED, ApplicationStatus.PATENT_REFUSED,
    ApplicationStatus.WITHDRAWN, ApplicationStatus.EXPIRED,
}


@transaction.atomic
def withdraw_application(user, application_id, reason=""):
    """Applicant withdraws an application before filing."""
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    assert_applicant(user, application)

    if application.status in NON_WITHDRAWABLE:
        raise ValidationError("Application cannot be withdrawn in its current state.")

    prev = application.status
    application.status = ApplicationStatus.WITHDRAWN
    application.withdrawn_date = now()
    application.comments = reason or application.comments
    application.save()

    _audit(application, user, "Application withdrawn", prev, ApplicationStatus.WITHDRAWN, reason)
    return application


# ── UC-008 / WF-301: Budget management ───────────────────────────────────

@transaction.atomic
def create_or_update_budget(user, application_id, filing_cost=0, attorney_fees=0,
                            administrative_cost=0, remarks=""):
    """PCC Admin creates / updates budget for an application."""
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    budget, created = Budget.objects.update_or_create(
        application=application,
        defaults={
            "filing_cost": filing_cost,
            "attorney_fees": attorney_fees,
            "administrative_cost": administrative_cost,
            "remarks": remarks,
        },
    )

    total = budget.total_cost
    if total > BUDGET_THRESHOLD:
        budget.decision = BudgetDecision.ESCALATED
    else:
        budget.decision = BudgetDecision.APPROVED_PCC
        budget.decision_by = user
        budget.decision_date = now()
    budget.save()

    _audit(application, user, "Budget updated", "", "", f"Total: ₹{total}")
    return budget


@transaction.atomic
def director_budget_decision(user, application_id, approve, remarks=""):
    """Director approves / denies an escalated budget."""
    assert_director(user)
    try:
        budget = Budget.objects.select_related("application").get(application_id=application_id)
    except Budget.DoesNotExist:
        raise NotFoundError("Budget not found for this application.")

    if budget.decision != BudgetDecision.ESCALATED:
        raise ValidationError("Budget is not pending director approval.")

    # CRITICAL VALIDATION: Check inventor requirements before budget decision
    application = budget.application
    try:
        validate_inventor_shares(application)
    except ValidationError:
        raise ValidationError("Cannot approve budget: Inventor percentage shares must sum to exactly 100%.")

    if not check_all_consents(application):
        raise ValidationError("Cannot approve budget: All inventors must give their consent before budget approval.")

    budget.decision = BudgetDecision.APPROVED_DIRECTOR if approve else BudgetDecision.DENIED
    budget.decision_by = user
    budget.decision_date = now()
    budget.remarks = remarks
    budget.save()

    _audit(budget.application, user, f"Budget {'approved' if approve else 'denied'} by Director")
    return budget


# ── Communication Log (replaces Attorney interactions) ───────────────────

@transaction.atomic
def add_communication_log(user, application_id, direction, subject, body="",
                          external_party_name="", external_party_email="",
                          attachment=None, confidentiality_level="Internal"):
    """PCC Admin logs a communication with external party (BR-PMS-019)."""
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    log = CommunicationLog.objects.create(
        application=application,
        logged_by=user,
        direction=direction,
        subject=subject,
        body=body,
        external_party_name=external_party_name,
        external_party_email=external_party_email,
        attachment=attachment,
        confidentiality_level=confidentiality_level,
    )
    _audit(application, user, f"Communication logged: {subject}")
    return log


# ── UC-006: Assign Attorney (PCC Admin fills external attorney details) ──

@transaction.atomic
def assign_attorney(user, application_id, attorney_name, attorney_email="",
                    attorney_phone="", attorney_firm="", specialization="",
                    remarks="", engagement_proof=None):
    """
    PCC Admin assigns an external attorney to an approved application (UC-006, BR-PMS-007).
    The attorney is external — PCC Admin enters their details and uploads proof.
    """
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    if application.status != ApplicationStatus.APPROVED:
        raise ValidationError(
            "Attorney can only be assigned to an approved application (BR-PMS-004)."
        )

    # CRITICAL VALIDATION: Check inventor requirements before attorney assignment
    try:
        validate_inventor_shares(application)
    except ValidationError:
        raise ValidationError("Cannot assign attorney: Inventor percentage shares must sum to exactly 100%.")

    if not check_all_consents(application):
        raise ValidationError("Cannot assign attorney: All inventors must give their consent before attorney assignment.")

    if not attorney_name or len(attorney_name.strip()) < 2:
        raise ValidationError("Attorney name is required (min 2 characters).")

    # Create or update the assignment
    assignment, created = AttorneyAssignment.objects.update_or_create(
        application=application,
        defaults={
            "attorney_name": attorney_name.strip(),
            "attorney_email": attorney_email.strip(),
            "attorney_phone": attorney_phone.strip(),
            "attorney_firm": attorney_firm.strip(),
            "specialization": specialization.strip(),
            "assigned_by": user,
            "remarks": remarks,
            "engagement_proof": engagement_proof,
            "is_active": True,
        },
    )

    action = "Attorney assigned" if created else "Attorney assignment updated"
    _audit(application, user, action, "", "",
           f"Attorney: {attorney_name}, Firm: {attorney_firm}")
    return assignment


# ── UC-007: Record Patentability Assessment (PCC Admin enters attorney opinion) ──

@transaction.atomic
def record_patentability_assessment(user, application_id, recommendation,
                                     opinion_summary="", novelty_score=0,
                                     non_obviousness_score=0, utility_score=0,
                                     search_completeness=0, prior_art_references="",
                                     assessed_by_attorney="", attorney_report=None,
                                     assessment_date=None):
    """
    PCC Admin records the external attorney's patentability assessment (UC-007, BR-PMS-014).
    Must have valid scores and recommendation before filing can proceed.
    """
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    # Assessment is only valid for applications in patentability check stages
    valid_statuses = [
        ApplicationStatus.APPROVED,
        ApplicationStatus.PATENTABILITY_CHECK_STARTED,
        ApplicationStatus.PATENTABILITY_CHECK_COMPLETED,
    ]
    if application.status not in valid_statuses:
        raise ValidationError(
            f"Assessment can only be recorded for applications in status: "
            f"{[s.value for s in valid_statuses]}. Current: {application.status}"
        )

    # CRITICAL VALIDATION: Check inventor requirements before patentability assessment
    try:
        validate_inventor_shares(application)
    except ValidationError:
        raise ValidationError("Cannot record patentability assessment: Inventor percentage shares must sum to exactly 100%.")

    if not check_all_consents(application):
        raise ValidationError("Cannot record patentability assessment: All inventors must give their consent before assessment.")

    # BR-PMS-014: Validate recommendation
    valid_recommendations = [r.value for r in PatentabilityRecommendation]
    if recommendation not in valid_recommendations:
        raise ValidationError(
            f"Recommendation must be one of: {valid_recommendations}"
        )

    # BR-PMS-014: Validate scores (0-100)
    for name, score in [("novelty_score", novelty_score),
                        ("non_obviousness_score", non_obviousness_score),
                        ("utility_score", utility_score),
                        ("search_completeness", search_completeness)]:
        try:
            val = float(score)
        except (TypeError, ValueError):
            raise ValidationError(f"{name} must be a numeric value.")
        if val < 0 or val > 100:
            raise ValidationError(f"{name} must be between 0 and 100.")

    # BR-PMS-014: opinion_summary is required
    if not opinion_summary or len(opinion_summary.strip()) < 20:
        raise ValidationError("Opinion summary must be at least 20 characters (BR-PMS-014).")

    assessment, created = PatentabilityAssessment.objects.update_or_create(
        application=application,
        defaults={
            "assessed_by_attorney": assessed_by_attorney.strip(),
            "novelty_score": novelty_score,
            "non_obviousness_score": non_obviousness_score,
            "utility_score": utility_score,
            "search_completeness": search_completeness,
            "recommendation": recommendation,
            "opinion_summary": opinion_summary.strip(),
            "prior_art_references": prior_art_references.strip(),
            "attorney_report": attorney_report,
            "recorded_by": user,
            "assessment_date": assessment_date or now(),
        },
    )

    action = "Patentability assessment recorded" if created else "Patentability assessment updated"
    _audit(application, user, action, "", "",
           f"Recommendation: {recommendation}, Novelty: {novelty_score}")
    return assessment


# ── UC-009 / WF-601: Record Filing with Patent Office ───────────────────

@transaction.atomic
def record_filing(user, application_id, filing_office="Indian Patent Office",
                  jurisdiction="India", external_filing_id="",
                  filing_date=None, confirmation_proof=None,
                  international_filing_justification="", remarks=""):
    """
    PCC Admin logs the filing of a patent with a patent office (UC-009, BR-PMS-017, WF-601).
    International filings require justification.
    """
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    # Filing can only happen for applications at SEARCH_REPORT_GENERATED or PATENT_FILED status
    if application.status not in (ApplicationStatus.SEARCH_REPORT_GENERATED,
                                   ApplicationStatus.PATENT_FILED):
        raise ValidationError(
            "Filing can only be recorded when status is 'Search Report Generated' or 'Patent Filed'."
        )

    # CRITICAL VALIDATION: Check inventor requirements before patent filing
    try:
        validate_inventor_shares(application)
    except ValidationError:
        raise ValidationError("Cannot record patent filing: Inventor percentage shares must sum to exactly 100%.")

    if not check_all_consents(application):
        raise ValidationError("Cannot record patent filing: All inventors must give their consent before filing.")

    # BR-PMS-017: International filing requires justification
    if filing_office.strip().lower() != "indian patent office" and jurisdiction.strip().lower() != "india":
        if not international_filing_justification or len(international_filing_justification.strip()) < 10:
            raise ValidationError(
                "International filings require a justification of at least 10 characters (BR-PMS-017)."
            )

    filing, created = FilingRecord.objects.update_or_create(
        application=application,
        defaults={
            "filing_office": filing_office.strip(),
            "jurisdiction": jurisdiction.strip(),
            "external_filing_id": external_filing_id.strip(),
            "filing_date": filing_date or now(),
            "confirmation_proof": confirmation_proof,
            "international_filing_justification": international_filing_justification.strip(),
            "filed_by": user,
            "remarks": remarks,
        },
    )

    # Auto-advance status to PATENT_FILED if at SEARCH_REPORT_GENERATED
    if application.status == ApplicationStatus.SEARCH_REPORT_GENERATED:
        prev = application.status
        application.status = ApplicationStatus.PATENT_FILED
        application.patent_filed_date = filing.filing_date or now()
        application.save()
        _audit(application, user, "Status changed to Patent Filed", prev,
               ApplicationStatus.PATENT_FILED, f"Filing ID: {external_filing_id}")

    action = "Filing recorded" if created else "Filing record updated"
    _audit(application, user, action, "", "",
           f"Office: {filing_office}, ID: {external_filing_id}")
    return filing


# ===========================================================================
# FEATURE 1: LODGE FORMAL APPEAL
# ===========================================================================

@transaction.atomic
def lodge_appeal(user, application_id, reason):
    """
    Applicant lodges a formal appeal against a rejected application.
    Only allowed within 60 days of rejection.
    """
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    applicant = assert_applicant(user, application)

    if application.status != ApplicationStatus.REJECTED:
        raise ValidationError("Appeals can only be lodged for rejected applications.")

    # Check if within appeal window (60 days from rejection)
    if application.decision_date:
        appeal_deadline = application.decision_date + timedelta(days=REVISION_WINDOW_DAYS)
        if now() > appeal_deadline:
            raise ValidationError("The 60-day appeal window has expired.")

    if not reason or len(reason.strip()) < 50:
        raise ValidationError("Appeal reason must be at least 50 characters.")

    prev = application.status
    application.status = ApplicationStatus.APPEAL
    application.appeal_date = now()
    application.appeal_reason = reason.strip()
    application.save()

    # Create notification for PCC Admin
    _create_notification_for_role(
        application,
        NotificationType.ACTION_REQUIRED,
        "New Appeal Filed",
        f"An appeal has been filed for application: {application.title}",
        is_pcc_admin
    )

    _audit(application, user, "Appeal lodged", prev, ApplicationStatus.APPEAL, reason[:100])
    return application


@transaction.atomic
def pcc_review_appeal(user, application_id):
    """PCC Admin reviews and forwards appeal to Director."""
    assert_pcc_admin(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    if application.status != ApplicationStatus.APPEAL:
        raise ValidationError("Application is not in Appeal status.")

    prev = application.status
    application.status = ApplicationStatus.APPEAL_UNDER_REVIEW
    application.save()

    _audit(application, user, "Appeal forwarded for Director review", prev, ApplicationStatus.APPEAL_UNDER_REVIEW)
    return application


@transaction.atomic
def director_appeal_decision(user, application_id, approve, feedback=""):
    """Director decides on the appeal - approve or reject."""
    assert_director(user)
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    if application.status != ApplicationStatus.APPEAL_UNDER_REVIEW:
        raise ValidationError("Application is not under appeal review.")

    _check_director_conflict(user, application)

    if not approve and (not feedback or len(feedback.strip()) < 50):
        raise ValidationError("Feedback must be at least 50 characters when rejecting an appeal.")

    prev = application.status

    if approve:
        application.status = ApplicationStatus.APPEAL_APPROVED
        application.appeal_decision = "Approved"
        # Create notification for applicant
        _create_notification_for_applicant(
            application,
            NotificationType.APPEAL_UPDATE,
            "Appeal Approved",
            f"Your appeal for '{application.title}' has been approved. The application will be reconsidered."
        )
    else:
        application.status = ApplicationStatus.APPEAL_REJECTED
        application.appeal_decision = "Rejected"
        _create_notification_for_applicant(
            application,
            NotificationType.APPEAL_UPDATE,
            "Appeal Rejected",
            f"Your appeal for '{application.title}' has been rejected. Reason: {feedback[:100]}"
        )

    application.appeal_decision_date = now()
    application.appeal_decision_by = user
    application.director_feedback = feedback
    application.save()

    _audit(application, user, f"Appeal {'approved' if approve else 'rejected'}", prev, application.status, feedback)
    return application


# ===========================================================================
# FEATURE 2: INVENTOR CONSENT & SHARE VALIDATION
# ===========================================================================

def validate_inventor_shares(application):
    """Validate that inventor shares sum to exactly 100%."""
    total_share = Inventor.objects.filter(application=application).aggregate(
        total=models.Sum('percentage_share')
    )['total'] or 0
    if total_share != 100:
        raise ValidationError(f"Inventor shares must sum to 100%. Current total: {total_share}%")
    return True


def check_all_consents(application):
    """Check if all inventors have given consent."""
    inventors = Inventor.objects.filter(application=application)
    if not inventors.exists():
        return False
    return all(inv.has_consent for inv in inventors)


@transaction.atomic
def give_inventor_consent(user, application_id):
    """Inventor gives consent for the application."""
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    try:
        applicant = Applicant.objects.get(user=user)
    except Applicant.DoesNotExist:
        raise UnauthorizedError("User is not a registered applicant.")

    try:
        inventor = Inventor.objects.get(applicant=applicant, application=application)
    except Inventor.DoesNotExist:
        raise UnauthorizedError("You are not an inventor on this application.")

    if inventor.has_consent:
        raise ValidationError("You have already given consent.")

    inventor.has_consent = True
    inventor.consent_date = now()
    inventor.save()

    _audit(application, user, f"Inventor consent given by {applicant.name}")

    # Create notification for primary applicant and auto-transition if all consents received
    if check_all_consents(application):
        # Auto-transition from PENDING_INVENTOR_CONSENT to SUBMITTED
        if application.status == ApplicationStatus.PENDING_INVENTOR_CONSENT:
            prev_status = application.status
            application.status = ApplicationStatus.SUBMITTED
            application.save()

            _audit(application, user, "Auto-transitioned to Submitted - All Consents Received", prev_status, ApplicationStatus.SUBMITTED)

            # Notify primary applicant
            _create_notification_for_applicant(
                application,
                NotificationType.STATUS_CHANGE,
                "Application Submitted - All Consents Received",
                f"All inventors have given consent for '{application.title}'. "
                f"Your application has been automatically submitted and is now awaiting PCC Admin review."
            )
        else:
            # For other statuses, just notify
            _create_notification_for_applicant(
                application,
                NotificationType.STATUS_CHANGE,
                "All Inventor Consents Received",
                f"All inventors have given consent for '{application.title}'."
            )

    return inventor


@transaction.atomic
def revoke_inventor_consent(user, application_id):
    """Inventor revokes consent (only allowed in draft/needs revision status)."""
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    if application.status not in [ApplicationStatus.DRAFT, ApplicationStatus.NEEDS_REVISION]:
        raise ValidationError("Consent can only be revoked when application is in Draft or Needs Revision status.")

    try:
        applicant = Applicant.objects.get(user=user)
    except Applicant.DoesNotExist:
        raise UnauthorizedError("User is not a registered applicant.")

    try:
        inventor = Inventor.objects.get(applicant=applicant, application=application)
    except Inventor.DoesNotExist:
        raise UnauthorizedError("You are not an inventor on this application.")

    inventor.has_consent = False
    inventor.consent_date = None
    inventor.save()

    _audit(application, user, f"Inventor consent revoked by {applicant.name}")
    return inventor


# ===========================================================================
# FEATURE 4: DEADLINE & ALERT SYSTEM (Notifications)
# ===========================================================================

def _create_notification_for_applicant(application, notification_type, title, message, deadline_date=None):
    """Create notification for the primary applicant."""
    if application.primary_applicant and application.primary_applicant.user:
        PatentNotification.objects.create(
            recipient=application.primary_applicant.user,
            application=application,
            notification_type=notification_type,
            title=title,
            message=message,
            deadline_date=deadline_date,
            action_url=f"/patent/applicant/applications/{application.id}",
        )


def _create_notification_for_role(application, notification_type, title, message, role_check_func):
    """Create notification for users with a specific role."""
    from django.contrib.auth.models import User
    for user in User.objects.filter(is_active=True):
        if role_check_func(user):
            PatentNotification.objects.create(
                recipient=user,
                application=application,
                notification_type=notification_type,
                title=title,
                message=message,
                action_url=f"/patent/pccAdmin/applications/{application.id}",
            )


def get_user_notifications(user, unread_only=False):
    """Get notifications for a user."""
    qs = PatentNotification.objects.filter(recipient=user)
    if unread_only:
        qs = qs.filter(is_read=False)
    return qs


@transaction.atomic
def mark_notification_read(user, notification_id):
    """Mark a notification as read."""
    try:
        notification = PatentNotification.objects.get(id=notification_id, recipient=user)
    except PatentNotification.DoesNotExist:
        raise NotFoundError("Notification not found.")
    notification.is_read = True
    notification.save()
    return notification


@transaction.atomic
def mark_all_notifications_read(user):
    """Mark all notifications as read for a user."""
    return PatentNotification.objects.filter(recipient=user, is_read=False).update(is_read=True)


def check_approaching_deadlines():
    """
    Check for applications with approaching deadlines and create notifications.
    Should be called periodically (e.g., daily via celery task).
    """
    from datetime import timedelta

    # Check resubmission deadlines (7 days before)
    warning_date = now() + timedelta(days=7)
    apps_with_deadlines = Application.objects.filter(
        status__in=[ApplicationStatus.NEEDS_REVISION, ApplicationStatus.REJECTED],
        resubmission_deadline__lte=warning_date,
        resubmission_deadline__gt=now()
    )

    for app in apps_with_deadlines:
        # Check if notification already sent
        existing = PatentNotification.objects.filter(
            application=app,
            notification_type=NotificationType.DEADLINE_APPROACHING,
            created_at__gte=now() - timedelta(days=1)
        ).exists()

        if not existing:
            days_left = (app.resubmission_deadline - now()).days
            _create_notification_for_applicant(
                app,
                NotificationType.DEADLINE_APPROACHING,
                f"Deadline in {days_left} days",
                f"Your resubmission deadline for '{app.title}' is approaching. Please submit before {app.resubmission_deadline.strftime('%Y-%m-%d')}.",
                deadline_date=app.resubmission_deadline
            )

    # Check for expired deadlines
    expired_apps = Application.objects.filter(
        status__in=[ApplicationStatus.NEEDS_REVISION, ApplicationStatus.REJECTED],
        resubmission_deadline__lt=now()
    )

    for app in expired_apps:
        existing = PatentNotification.objects.filter(
            application=app,
            notification_type=NotificationType.DEADLINE_EXPIRED
        ).exists()

        if not existing:
            app.status = ApplicationStatus.EXPIRED
            app.save()
            _create_notification_for_applicant(
                app,
                NotificationType.DEADLINE_EXPIRED,
                "Resubmission Deadline Expired",
                f"The resubmission deadline for '{app.title}' has expired. The application has been marked as expired."
            )


# ===========================================================================
# FEATURE 5: DOCUMENT VERSION CONTROL
# ===========================================================================

@transaction.atomic
def upload_document(user, application_id, document_type, title, file, description=""):
    """Upload a new version of a document."""
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        raise NotFoundError("Application not found.")

    # Check authorization (must be inventor or PCC admin)
    is_inventor = False
    try:
        applicant = Applicant.objects.get(user=user)
        is_inventor = Inventor.objects.filter(applicant=applicant, application=application).exists()
    except Applicant.DoesNotExist:
        pass

    if not is_inventor and not is_pcc_admin(user):
        raise UnauthorizedError("Only inventors or PCC Admin can upload documents.")

    doc = ApplicationDocument.objects.create(
        application=application,
        document_type=document_type.strip(),
        title=title.strip(),
        file=file,
        description=description.strip(),
        uploaded_by=user,
    )

    _audit(application, user, f"Document uploaded: {title} v{doc.version}")
    return doc


def get_document_versions(application_id, document_type=None):
    """Get all document versions for an application."""
    qs = ApplicationDocument.objects.filter(application_id=application_id)
    if document_type:
        qs = qs.filter(document_type=document_type)
    return qs


def get_current_documents(application_id):
    """Get only the current (latest) version of each document type."""
    return ApplicationDocument.objects.filter(
        application_id=application_id,
        is_current=True
    )


# ===========================================================================
# FEATURE 6: SEARCH & GLOBAL FILTERING
# ===========================================================================

def search_applications(
    user,
    query="",
    status_filter=None,
    date_from=None,
    date_to=None,
    department_filter=None,
    decision_filter=None,
    limit=50,
    offset=0
):
    """
    Search and filter applications based on various criteria.
    Returns applications the user has access to.
    """
    from django.db.models import Q

    qs = Application.objects.all()

    # Role-based filtering
    if is_pcc_admin(user) or is_director(user):
        pass  # Can see all applications
    else:
        # Applicant can only see their own applications
        try:
            applicant = Applicant.objects.get(user=user)
            app_ids = Inventor.objects.filter(applicant=applicant).values_list("application_id", flat=True)
            qs = qs.filter(id__in=app_ids)
        except Applicant.DoesNotExist:
            return []

    # Text search (title, token_no, comments)
    if query:
        qs = qs.filter(
            Q(title__icontains=query) |
            Q(token_no__icontains=query) |
            Q(comments__icontains=query) |
            Q(primary_applicant__name__icontains=query)
        )

    # Status filter
    if status_filter:
        if isinstance(status_filter, list):
            qs = qs.filter(status__in=status_filter)
        else:
            qs = qs.filter(status=status_filter)

    # Decision filter
    if decision_filter:
        qs = qs.filter(decision_status=decision_filter)

    # Date range filter
    if date_from:
        qs = qs.filter(submitted_date__gte=date_from)
    if date_to:
        qs = qs.filter(submitted_date__lte=date_to)

    # Department filter
    if department_filter:
        # Filter by primary applicant's department
        from applications.globals.models import ExtraInfo
        user_ids = ExtraInfo.objects.filter(
            department__name__icontains=department_filter
        ).values_list("user_id", flat=True)
        applicant_ids = Applicant.objects.filter(user_id__in=user_ids).values_list("id", flat=True)
        qs = qs.filter(primary_applicant_id__in=applicant_ids)

    total_count = qs.count()
    results = qs.select_related("primary_applicant")[offset:offset + limit]

    return {
        "total": total_count,
        "applications": [
            {
                "id": app.id,
                "title": app.title,
                "status": app.status,
                "decision_status": app.decision_status,
                "token_no": app.token_no,
                "submitted_date": app.submitted_date,
                "primary_applicant": app.primary_applicant.name if app.primary_applicant else None,
            }
            for app in results
        ]
    }


# ===========================================================================
# FEATURE 7: REPORTING & ANALYTICS
# ===========================================================================

def get_analytics_summary(year=None, department=None):
    """Get comprehensive analytics summary."""
    from django.db.models import Count, Avg
    from django.db.models.functions import TruncMonth

    qs = Application.objects.all()

    if year:
        qs = qs.filter(submitted_date__year=year)

    if department:
        from applications.globals.models import ExtraInfo
        user_ids = ExtraInfo.objects.filter(
            department__name__icontains=department
        ).values_list("user_id", flat=True)
        applicant_ids = Applicant.objects.filter(user_id__in=user_ids).values_list("id", flat=True)
        qs = qs.filter(primary_applicant_id__in=applicant_ids)

    # Status distribution
    status_dist = list(qs.values("status").annotate(count=Count("id")).order_by("-count"))

    # Decision distribution
    decision_dist = list(qs.values("decision_status").annotate(count=Count("id")).order_by("-count"))

    # Monthly submissions
    monthly_submissions = list(
        qs.filter(submitted_date__isnull=False)
        .annotate(month=TruncMonth("submitted_date"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # Calculate approval rate
    total = qs.count()
    approved = qs.filter(decision_status=DecisionStatus.APPROVED).count()
    rejected = qs.filter(decision_status=DecisionStatus.REJECTED).count()
    pending = qs.filter(decision_status=DecisionStatus.PENDING).count()

    approval_rate = (approved / total * 100) if total > 0 else 0

    # Department-wise distribution
    dept_dist = []
    from applications.globals.models import ExtraInfo, DepartmentInfo
    for dept in DepartmentInfo.objects.all():
        user_ids = ExtraInfo.objects.filter(department=dept).values_list("user_id", flat=True)
        applicant_ids = Applicant.objects.filter(user_id__in=user_ids).values_list("id", flat=True)
        count = qs.filter(primary_applicant_id__in=applicant_ids).count()
        if count > 0:
            dept_dist.append({"department": dept.name, "count": count})

    return {
        "total_applications": total,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "approval_rate": round(approval_rate, 2),
        "status_distribution": status_dist,
        "decision_distribution": decision_dist,
        "monthly_submissions": [
            {"month": item["month"].strftime("%Y-%m") if item["month"] else None, "count": item["count"]}
            for item in monthly_submissions
        ],
        "department_distribution": dept_dist,
    }


# ---------------------------------------------------------------------------
# UC-011: Receive & Respond to Office Actions
# ---------------------------------------------------------------------------

@transaction.atomic
def record_office_action(user, application_id, data, attachment=None):
    """
    PCC Admin logs a new Office Action received from the Patent Office.
    We don't have an OfficeAction model, so we use CommunicationLog
    and set the application status to NEEDS_REVISION.
    """
    assert_pcc_admin(user)
    app = get_object_or_404(Application, id=application_id)
    
    subject = data.get("subject", "Office Action Received")
    body = data.get("body", "")
    deadline = data.get("deadline_date")
    
    comm = CommunicationLog.objects.create(
        application=app,
        logged_by=user,
        direction=CommunicationDirection.INCOMING,
        external_party_name="Patent Office",
        subject=f"[Office Action] {subject}",
        body=body,
        attachment=attachment,
        confidentiality_level=ConfidentialityLevel.CONFIDENTIAL
    )
    
    _audit(app, user, "Recieved Office Action", prev=app.status, new=ApplicationStatus.NEEDS_REVISION, details=subject)
    
    app.status = ApplicationStatus.NEEDS_REVISION
    app.resubmission_deadline = deadline if deadline else (now() + timedelta(days=60))
    app.save()

    PatentNotification.objects.create(
        recipient=app.primary_applicant.user,
        application=app,
        notification_type=NotificationType.ACTION_REQUIRED,
        title="Office Action Received: Revision Required",
        message=f"The patent office has issued an objection/requirement. Deadline: {app.resubmission_deadline.strftime('%Y-%m-%d')}.",
        deadline_date=app.resubmission_deadline
    )
    return comm

@transaction.atomic
def submit_office_action_response(user, application_id, data, attachment=None):
    """
    Applicant provides materials to respond to the Office Action.
    """
    app = get_object_or_404(Application, id=application_id)
    assert_applicant(user, app)
    
    body = data.get("body", "Applicant responded with revisions.")
    
    comm = CommunicationLog.objects.create(
        application=app,
        logged_by=user,
        direction=CommunicationDirection.OUTGOING,
        subject="[Office Action Response] Revisions Submitted",
        body=body,
        attachment=attachment,
        confidentiality_level=ConfidentialityLevel.INTERNAL
    )
    
    _audit(app, user, "Submitted Office Action Response", prev=app.status, new=ApplicationStatus.RESUBMITTED)
    app.status = ApplicationStatus.RESUBMITTED
    app.save()
    
    # Notify PCC Admin
    pcc_admins = User.objects.filter(extrainfo__designation__name__icontains="PCC")
    for admin in pcc_admins:
        PatentNotification.objects.create(
            recipient=admin,
            application=app,
            notification_type=NotificationType.STATUS_CHANGE,
            title="Applicant Responded to Office Action",
            message=f"Applicant {user.username} has provided revisions for {app.title}."
        )
    return comm


# ---------------------------------------------------------------------------
# UC-013: Track Post-Grant Maintenance & Renewals
# ---------------------------------------------------------------------------

@transaction.atomic
def record_maintenance_fee(user, application_id, data, receipt=None):
    """
    PCC Admin pays a renewal/maintenance fee. Track via the Budget and CommunicationLog.
    """
    assert_pcc_admin(user)
    app = get_object_or_404(Application, id=application_id)
    amount = float(data.get("amount", 0.0))
    remarks = data.get("remarks", "Maintenance fee / Renewal paid.")
    
    # Update the Budget's administrative_cost tally
    budget, _ = Budget.objects.get_or_create(application=app)
    budget.administrative_cost += amount
    budget.remarks = f"{budget.remarks}\n[Renewal] Added {amount}: {remarks}"
    budget.save()
    
    comm = CommunicationLog.objects.create(
        application=app,
        logged_by=user,
        direction=CommunicationDirection.OUTGOING,
        external_party_name="Patent Office (Renewal)",
        subject="[Maintenance/Renewal Fee Provided]",
        body=remarks,
        attachment=receipt,
        confidentiality_level=ConfidentialityLevel.INTERNAL
    )
    
    _audit(app, user, "Recorded Patent Renewal/Maintenance Fee", details=f"Amount: {amount}. {remarks}")
    return comm


# ---------------------------------------------------------------------------
# UC-017: Track Licensing & Tech Transfer Requests
# ---------------------------------------------------------------------------

@transaction.atomic
def record_licensing_interest(user, application_id, data, document=None):
    """
    Record that a third party is interested in licensing the patent.
    """
    app = get_object_or_404(Application, id=application_id)
    
    company_name = data.get("company_name", "Unknown Company")
    contact_email = data.get("contact_email", "")
    terms = data.get("proposed_terms", "Awaiting formal terms.")
    
    comm = CommunicationLog.objects.create(
        application=app,
        logged_by=user,
        direction=CommunicationDirection.INCOMING,
        external_party_name=company_name,
        external_party_email=contact_email,
        subject=f"[Licensing Interest] {company_name}",
        body=f"Proposed Terms/Notes:\n{terms}",
        attachment=document,
        confidentiality_level=ConfidentialityLevel.CONFIDENTIAL
    )
    
    _audit(app, user, "Recorded Licensing Inquiry", details=f"Company: {company_name}")
    
    PatentNotification.objects.create(
        recipient=app.primary_applicant.user,
        application=app,
        notification_type=NotificationType.ACTION_REQUIRED,
        title="New Licensing Opportunity",
        message=f"{company_name} is interested in licensing your patent {app.title}."
    )
    return comm
