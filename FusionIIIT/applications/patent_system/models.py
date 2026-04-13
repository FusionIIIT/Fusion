"""
Patent Management System — Models
Aligned with New BRs (BR-PMS-001 → 019), UCs (PMS-UC-001 → 020), WFs (PMS-WF-101 → 601).
Attorney role removed: PCC_ADMIN performs all attorney duties and logs external communications.
"""

import os
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


# ---------------------------------------------------------------------------
# Choices (TextChoices / IntegerChoices)
# ---------------------------------------------------------------------------

class ApplicationStatus(models.TextChoices):
    DRAFT = "Draft", "Draft"
    PENDING_INVENTOR_CONSENT = "Pending Inventor Consent", "Pending Inventor Consent"
    SUBMITTED = "Submitted", "Submitted"
    UNDER_REVIEW = "Under Review", "Under Review"
    REVIEWED = "Reviewed by PCC Admin", "Reviewed by PCC Admin"
    FORWARDED = "Forwarded for Director's Review", "Forwarded for Director's Review"
    APPROVED = "Approved", "Approved"
    NEEDS_REVISION = "Needs Revision", "Needs Revision"
    REJECTED = "Rejected", "Rejected"
    RESUBMITTED = "Resubmitted", "Resubmitted"
    APPEAL = "Appeal", "Appeal"  # Feature 1: Lodge Formal Appeal
    APPEAL_UNDER_REVIEW = "Appeal Under Review", "Appeal Under Review"
    APPEAL_APPROVED = "Appeal Approved", "Appeal Approved"
    APPEAL_REJECTED = "Appeal Rejected", "Appeal Rejected"
    PATENTABILITY_CHECK_STARTED = "Patentability Check Started", "Patentability Check Started"
    PATENTABILITY_CHECK_COMPLETED = "Patentability Check Completed", "Patentability Check Completed"
    SEARCH_REPORT_GENERATED = "Search Report Generated", "Search Report Generated"
    PATENT_FILED = "Patent Filed", "Patent Filed"
    PATENT_PUBLISHED = "Patent Published", "Patent Published"
    PATENT_GRANTED = "Patent Granted", "Patent Granted"
    PATENT_REFUSED = "Patent Refused", "Patent Refused"
    WITHDRAWN = "Withdrawn", "Withdrawn"
    EXPIRED = "Expired", "Expired"


class DecisionStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    APPROVED = "Approved", "Approved"
    REJECTED = "Rejected", "Rejected"
    NEEDS_REVISION = "Needs Revision", "Needs Revision"


class IPType(models.TextChoices):
    PATENT = "Patent", "Patent"
    COPYRIGHT = "Copyright", "Copyright"
    TRADEMARK = "Trademark", "Trademark"
    INDUSTRIAL_DESIGN = "Industrial Design", "Industrial Design"
    TRADE_SECRET = "Trade Secret", "Trade Secret"
    GI = "Geographical Indication", "Geographical Indication"


class DevelopmentStage(models.TextChoices):
    EMBRYONIC = "Embryonic", "Embryonic"
    PARTIALLY_DEVELOPED = "Partially developed", "Partially developed"
    OFF_THE_SHELF = "Off-the-shelf", "Off-the-shelf"


class CommunicationDirection(models.TextChoices):
    INCOMING = "Incoming", "Incoming"
    OUTGOING = "Outgoing", "Outgoing"


class BudgetDecision(models.TextChoices):
    PENDING = "Pending", "Pending"
    APPROVED_PCC = "Approved by PCC", "Approved by PCC"
    ESCALATED = "Escalated to Director", "Escalated to Director"
    APPROVED_DIRECTOR = "Approved by Director", "Approved by Director"
    DENIED = "Denied", "Denied"


class ConfidentialityLevel(models.TextChoices):
    """BR-PMS-019 — Confidentiality markings for legal communications."""
    PUBLIC = "Public", "Public"
    INTERNAL = "Internal", "Internal"
    CONFIDENTIAL = "Confidential", "Confidential"
    PRIVILEGED = "Attorney-Client Privileged", "Attorney-Client Privileged"


class PatentabilityRecommendation(models.TextChoices):
    """BR-PMS-014 — Attorney assessment recommendation."""
    FILE_PATENT = "File Patent", "File Patent"
    DO_NOT_FILE = "Do Not File", "Do Not File"
    NEEDS_AMENDMENT = "Needs Amendment", "Needs Amendment"


# ---------------------------------------------------------------------------
# File-upload helpers
# ---------------------------------------------------------------------------

def _unique_path(subfolder, filename):
    base, ext = os.path.splitext(filename)
    base = base.replace(" ", "_")
    ts = now().strftime("%Y%m%d%H%M%S")
    return os.path.join(f"patent/{subfolder}", f"{base}_{ts}{ext}")


def poc_file_upload_path(instance, filename):
    return _unique_path("Section-I/poc_details", filename)


def source_agreement_upload_path(instance, filename):
    return _unique_path("Section-II/source_agreement_files", filename)


def mou_file_upload_path(instance, filename):
    return _unique_path("Section-II/mou_files", filename)


def form_iii_upload_path(instance, filename):
    return _unique_path("Section-III/form_iii_files", filename)


def communication_attachment_path(instance, filename):
    return _unique_path("communications", filename)


def assessment_report_upload_path(instance, filename):
    return _unique_path("patentability_assessments", filename)


def filing_confirmation_upload_path(instance, filename):
    return _unique_path("filing_records", filename)


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class Applicant(models.Model):
    """Faculty / Staff who can submit patent applications."""
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patent_applicant")
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "patent_system_applicant"


class Application(models.Model):
    """
    Central entity for a patent application.
    Attorney FK removed — PCC_ADMIN handles all legal interactions externally.
    """
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    primary_applicant = models.ForeignKey(
        Applicant, on_delete=models.CASCADE, related_name="applications"
    )
    status = models.CharField(
        max_length=60, choices=ApplicationStatus.choices, default=ApplicationStatus.DRAFT
    )
    decision_status = models.CharField(
        max_length=30, choices=DecisionStatus.choices, default=DecisionStatus.PENDING
    )
    token_no = models.CharField(max_length=120, blank=True, null=True)
    comments = models.TextField(blank=True, default="")

    # Director assignment (BR-PMS-012)
    assigned_director = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="directed_patent_apps"
    )
    director_feedback = models.TextField(blank=True, default="")

    # Key dates
    submitted_date = models.DateTimeField(blank=True, null=True)
    reviewed_by_pcc_date = models.DateTimeField(blank=True, null=True)
    forwarded_to_director_date = models.DateTimeField(blank=True, null=True)
    director_approval_date = models.DateTimeField(blank=True, null=True)
    patentability_check_start_date = models.DateTimeField(blank=True, null=True)
    patentability_check_completed_date = models.DateTimeField(blank=True, null=True)
    search_report_generated_date = models.DateTimeField(blank=True, null=True)
    patent_filed_date = models.DateTimeField(blank=True, null=True)
    patent_published_date = models.DateTimeField(blank=True, null=True)
    decision_date = models.DateTimeField(blank=True, null=True)
    withdrawn_date = models.DateTimeField(blank=True, null=True)
    resubmission_deadline = models.DateTimeField(blank=True, null=True)

    last_updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Feature 1: Appeal fields
    appeal_date = models.DateTimeField(blank=True, null=True)
    appeal_reason = models.TextField(blank=True, default="")
    appeal_decision = models.CharField(max_length=60, blank=True, default="")
    appeal_decision_date = models.DateTimeField(blank=True, null=True)
    appeal_decision_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="appeal_decisions"
    )

    def __str__(self):
        return f"[{self.id}] {self.title}"

    class Meta:
        db_table = "patent_system_application"
        ordering = ["-created_at"]


# ---------------------------------------------------------------------------
# Application Section Models
# ---------------------------------------------------------------------------

class ApplicationSectionI(models.Model):
    """Technical details of the invention."""
    id = models.AutoField(primary_key=True)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="section_i")
    type_of_ip = models.CharField(max_length=50, choices=IPType.choices, default=IPType.PATENT)
    area = models.TextField()
    problem = models.TextField()
    objective = models.TextField()
    novelty = models.TextField()
    advantages = models.TextField()
    is_tested = models.BooleanField(default=False)
    poc_details = models.FileField(upload_to=poc_file_upload_path, blank=True, null=True)
    applications = models.TextField()

    class Meta:
        db_table = "patent_system_application_section_i"


class ApplicationSectionII(models.Model):
    """Funding & collaboration details."""
    id = models.AutoField(primary_key=True)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="section_ii")
    funding_details = models.TextField()
    funding_source = models.TextField()
    source_agreement = models.FileField(upload_to=source_agreement_upload_path, blank=True, null=True)
    publication_details = models.TextField()
    mou_details = models.TextField()
    mou_file = models.FileField(upload_to=mou_file_upload_path, blank=True, null=True)
    research_details = models.TextField()

    class Meta:
        db_table = "patent_system_application_section_ii"


class ApplicationSectionIII(models.Model):
    """Industry / commercialisation details."""
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="section_iii")
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=15)
    development_stage = models.CharField(max_length=30, choices=DevelopmentStage.choices)
    form_iii = models.FileField(upload_to=form_iii_upload_path, blank=True, null=True)

    class Meta:
        db_table = "patent_system_application_section_iii"


# ---------------------------------------------------------------------------
# Inventor association
# ---------------------------------------------------------------------------

class Inventor(models.Model):
    """Many-to-many link between applicants and applications with share %."""
    id = models.AutoField(primary_key=True)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name="inventions")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="inventors")
    percentage_share = models.DecimalField(max_digits=5, decimal_places=2)
    # Feature 2: Inventor consent
    has_consent = models.BooleanField(default=False)
    consent_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "patent_system_inventor"
        unique_together = ("applicant", "application")

    def __str__(self):
        return f"{self.applicant.name} – {self.application.title} ({self.percentage_share}%)"


# ---------------------------------------------------------------------------
# Communication Log  (replaces Attorney model – BR-PMS-019, UC-007/009)
# ---------------------------------------------------------------------------

class CommunicationLog(models.Model):
    """
    PCC_ADMIN logs all external communications (emails, calls, meetings with
    external attorneys / patent offices) here.  Stores mail screenshots,
    proof pictures, notes, etc.
    """
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="communications")
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="pcc_comm_logs")
    direction = models.CharField(max_length=10, choices=CommunicationDirection.choices)
    subject = models.CharField(max_length=500)
    body = models.TextField(blank=True, default="")
    external_party_name = models.CharField(max_length=255, blank=True, default="")
    external_party_email = models.EmailField(blank=True, default="")
    attachment = models.FileField(upload_to=communication_attachment_path, blank=True, null=True)
    confidentiality_level = models.CharField(
        max_length=30, choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
        help_text="BR-PMS-019: Confidentiality marking for legal communications.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_communication_log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.direction}] {self.subject}"


# ---------------------------------------------------------------------------
# Budget / Financial Tracking  (BR-PMS-008, UC-008, WF-301)
# ---------------------------------------------------------------------------

class Budget(models.Model):
    """Tracks costs and approval for a patent application."""
    id = models.AutoField(primary_key=True)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="budget")
    filing_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    attorney_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    administrative_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    decision = models.CharField(max_length=30, choices=BudgetDecision.choices, default=BudgetDecision.PENDING)
    decision_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    decision_date = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patent_system_budget"

    def save(self, *args, **kwargs):
        self.total_cost = self.filing_cost + self.attorney_fees + self.administrative_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Budget for {self.application.title}: ₹{self.total_cost}"


# ---------------------------------------------------------------------------
# Audit Log  (BR-PMS-018)
# ---------------------------------------------------------------------------

class AuditLog(models.Model):
    """Immutable record of every action taken on a patent application."""
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="audit_logs")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    previous_state = models.CharField(max_length=60, blank=True, default="")
    new_state = models.CharField(max_length=60, blank=True, default="")
    details = models.TextField(blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_audit_log"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} on App#{self.application_id} by {self.user}"


# ---------------------------------------------------------------------------
# Document  (reusable across roles – UC-020)
# ---------------------------------------------------------------------------

class Document(models.Model):
    """Shared / reference documents (guidelines, forms, templates)."""
    title = models.CharField(max_length=255)
    link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patent_system_document"


# ---------------------------------------------------------------------------
# Attorney Assignment  (UC-006, BR-PMS-007)
# PCC_ADMIN records which external attorney is assigned to an application.
# ---------------------------------------------------------------------------

class AttorneyAssignment(models.Model):
    """
    Records the external attorney assigned by PCC_ADMIN to a patent application.
    Since attorneys are external to the system, PCC_ADMIN fills in their details
    and uploads proof (engagement letter, email confirmation, etc.).
    """
    id = models.AutoField(primary_key=True)
    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="attorney_assignment"
    )
    attorney_name = models.CharField(max_length=255)
    attorney_email = models.EmailField(blank=True, default="")
    attorney_phone = models.CharField(max_length=20, blank=True, default="")
    attorney_firm = models.CharField(max_length=255, blank=True, default="")
    specialization = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Domain expertise of the attorney relevant to this application.",
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="attorney_assignments_made"
    )
    assignment_date = models.DateTimeField(auto_now_add=True)
    engagement_proof = models.FileField(
        upload_to=communication_attachment_path, blank=True, null=True,
        help_text="Upload engagement letter, email screenshot, or other proof of assignment.",
    )
    remarks = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "patent_system_attorney_assignment"

    def __str__(self):
        return f"Attorney {self.attorney_name} → {self.application.title}"


# ---------------------------------------------------------------------------
# Patentability Assessment  (UC-007, BR-PMS-014)
# PCC_ADMIN records the external attorney's patentability opinion.
# ---------------------------------------------------------------------------

class PatentabilityAssessment(models.Model):
    """
    Stores the external attorney's patentability opinion, prior-art search
    results, scores, and recommendation.  All data is entered by PCC_ADMIN
    based on the attorney's report.
    """
    id = models.AutoField(primary_key=True)
    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="patentability_assessment"
    )
    assessed_by_attorney = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Name of the external attorney who performed the assessment.",
    )
    novelty_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Novelty score (0-100) as per attorney's evaluation.",
    )
    non_obviousness_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Non-obviousness score (0-100).",
    )
    utility_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Utility / industrial applicability score (0-100).",
    )
    search_completeness = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Prior-art search completeness percentage (0-100).",
    )
    recommendation = models.CharField(
        max_length=30, choices=PatentabilityRecommendation.choices,
        default=PatentabilityRecommendation.FILE_PATENT,
    )
    opinion_summary = models.TextField(
        blank=True, default="",
        help_text="Summary of the attorney's patentability opinion.",
    )
    prior_art_references = models.TextField(
        blank=True, default="",
        help_text="Prior art references identified during the search.",
    )
    attorney_report = models.FileField(
        upload_to=assessment_report_upload_path, blank=True, null=True,
        help_text="Full attorney report / opinion document.",
    )
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="recorded_assessments"
    )
    assessment_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patent_system_patentability_assessment"

    def __str__(self):
        return f"Assessment for {self.application.title}: {self.recommendation}"


# ---------------------------------------------------------------------------
# Filing Record  (UC-009, BR-PMS-017, WF-601)
# PCC_ADMIN logs external filing details with patent office.
# ---------------------------------------------------------------------------

class FilingRecord(models.Model):
    """
    Captures details when PCC_ADMIN logs a patent filing with a national or
    international patent office.  Stores external filing ID, jurisdiction,
    confirmation proof, etc.
    """
    id = models.AutoField(primary_key=True)
    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="filing_record"
    )
    filing_office = models.CharField(
        max_length=255, default="Indian Patent Office",
        help_text="Name of the patent office where filed.",
    )
    jurisdiction = models.CharField(
        max_length=100, blank=True, default="India",
        help_text="Filing jurisdiction (e.g. India, US, PCT).",
    )
    external_filing_id = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Official filing/application number from the patent office.",
    )
    filing_date = models.DateTimeField(
        blank=True, null=True,
        help_text="Official date of filing as recorded by the patent office.",
    )
    confirmation_proof = models.FileField(
        upload_to=filing_confirmation_upload_path, blank=True, null=True,
        help_text="Upload filing receipt, confirmation email screenshot, etc.",
    )
    international_filing_justification = models.TextField(
        blank=True, default="",
        help_text="BR-PMS-017: Required justification if filing outside Indian Patent Office.",
    )
    filed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="filed_patents"
    )
    remarks = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patent_system_filing_record"

    def __str__(self):
        return f"Filing {self.external_filing_id} for {self.application.title}"


# ---------------------------------------------------------------------------
# Feature 4: Patent Notification (Deadline & Alert System)
# ---------------------------------------------------------------------------

class NotificationType(models.TextChoices):
    DEADLINE_APPROACHING = "Deadline Approaching", "Deadline Approaching"
    DEADLINE_EXPIRED = "Deadline Expired", "Deadline Expired"
    STATUS_CHANGE = "Status Change", "Status Change"
    ACTION_REQUIRED = "Action Required", "Action Required"
    APPEAL_UPDATE = "Appeal Update", "Appeal Update"
    CONSENT_REQUIRED = "Consent Required", "Consent Required"
    REVISION_REQUESTED = "Revision Requested", "Revision Requested"
    APPLICATION_APPROVED = "Application Approved", "Application Approved"
    APPLICATION_REJECTED = "Application Rejected", "Application Rejected"


class PatentNotification(models.Model):
    """
    Feature 4: Deadline & Alert System
    Stores notifications for patent-related events and deadlines.
    """
    id = models.AutoField(primary_key=True)
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="patent_notifications"
    )
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="notifications",
        null=True, blank=True
    )
    notification_type = models.CharField(
        max_length=50, choices=NotificationType.choices
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    deadline_date = models.DateTimeField(blank=True, null=True)
    action_url = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_notification"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.notification_type}] {self.title}"


# ---------------------------------------------------------------------------
# Feature 5: Document Version Control
# ---------------------------------------------------------------------------

def versioned_document_upload_path(instance, filename):
    return _unique_path(f"documents/v{instance.version}", filename)


class ApplicationDocument(models.Model):
    """
    Feature 5: Document Version Control
    Tracks document versions for patent applications.
    """
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(
        max_length=100,
        help_text="Type of document (e.g., POC, MOU, Form III, Supporting Doc)"
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=versioned_document_upload_path)
    version = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True, default="")
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="uploaded_documents"
    )
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_application_document"
        ordering = ["-version", "-created_at"]
        unique_together = ("application", "document_type", "version")

    def __str__(self):
        return f"{self.title} v{self.version}"

    def save(self, *args, **kwargs):
        if not self.pk:
            # Auto-increment version for new documents of same type
            existing = ApplicationDocument.objects.filter(
                application=self.application,
                document_type=self.document_type
            ).order_by("-version").first()
            if existing:
                self.version = existing.version + 1
                # Mark old versions as not current
                ApplicationDocument.objects.filter(
                    application=self.application,
                    document_type=self.document_type
                ).update(is_current=False)
        super().save(*args, **kwargs)
