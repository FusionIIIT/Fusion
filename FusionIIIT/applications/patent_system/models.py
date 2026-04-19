from django.db import models
import os
from django.contrib.auth.models import User
from django.utils.timezone import now

class Applicant(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="applicant")
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    address = models.CharField(max_length=255)

    def str(self):
        return self.name

    class Meta:
        db_table = 'patent_system_applicant'

class Attorney(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    firm_name = models.CharField(max_length=255, blank=True, null=True)
    expertise_domain = models.CharField(max_length=255, blank=True, null=True)
    is_panel_approved = models.BooleanField(default=True)
    current_workload = models.PositiveIntegerField(default=0)

    def str(self):
        return self.name

    class Meta:
        db_table = 'patent_system_attorney'

class Application(models.Model):
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Needs Revision", "Needs Revision"),
        ("Revision Expired", "Revision Expired"),
        ("Withdrawn", "Withdrawn"),
        ("Reviewed by PCC Admin", "Reviewed by PCC Admin"),
        ("Forwarded for Director's Review", "Forwarded for Director's Review"),
        ("Director's Approval Received", "Director's Approval Received"),
        ("Attorney Assigned", "Attorney Assigned"),
        ("Attorney Reviewed", "Attorney Reviewed"),
        ("Returned to Director", "Returned to Director"),
        ("Patentability Check Started", "Patentability Check Started"),
        ("Patentability Check Completed", "Patentability Check Completed"),
        ("Patentability Search Report Generated", "Patentability Search Report Generated"),
        ("Patent Filed", "Patent Filed"),
        ("Patent Published", "Patent Published"),
        ("Patent Granted", "Patent Granted"),
        ("Patent Refused", "Patent Refused"),
    ]
    
    DECISION_STATUS_CHOICES = [
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Pending", "Pending"),
    ]
    id = models.AutoField(primary_key=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    token_no = models.CharField(max_length=100, blank=True, null=True)
    primary_applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name="applications")  
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default = "Draft")
    attorney = models.ForeignKey(Attorney, on_delete=models.CASCADE, related_name="applications", blank=True, null=True)
    assigned_pcc_admin = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="patent_assigned_applications", blank=True, null=True)
    submitted_date = models.DateField(blank=True, null=True)
    reviewed_by_pcc_date = models.DateField(blank=True, null=True)
    forwarded_to_director_date = models.DateField(blank=True, null=True)
    director_approval_date = models.DateField(blank=True, null=True)
    patentability_check_start_date = models.DateField(blank=True, null=True)
    patentability_check_completed_date = models.DateField(blank=True, null=True)
    search_report_generated_date = models.DateField(blank=True, null=True)
    patent_filed_date = models.DateField(blank=True, null=True)
    patent_published_date = models.DateField(blank=True, null=True)
    decision_date = models.DateField(blank=True, null=True)
    decision_status = models.CharField(max_length=50, choices=DECISION_STATUS_CHOICES, default = "Pending")
    comments = models.TextField(blank=True, null=True)
    attorney_review_notes = models.TextField(blank=True, null=True)
    attorney_reviewed_at = models.DateTimeField(blank=True, null=True)
    revision_requested_at = models.DateTimeField(blank=True, null=True)
    revision_due_date = models.DateField(blank=True, null=True)
    revised_submitted_at = models.DateTimeField(blank=True, null=True)
    is_revision_locked = models.BooleanField(default=False)
    budget_status = models.CharField(max_length=50, default="Not Initiated")
    budget_estimate = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    external_filing_status = models.CharField(max_length=50, default="Not Initiated")
    maintenance_tracking_active = models.BooleanField(default=False)
    priority_score = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'patent_system_application'

# Function to give path for poc_details
def poc_file_upload_path(instance, filename):
    """
    Generate a unique file path for POC (Proof of Concept) details.

    Args:
        instance: The model instance that the file is associated with.
        filename: The original filename of the uploaded file.

    Returns:
        str: A custom file path where the file will be stored.
    """
    # Extract base name and extension from the filename
    base, extension = os.path.splitext(filename)

    # Sanitize the base filename (replace spaces with underscores)
    base = base.replace(" ", "_")

    # Generate a timestamp to ensure filename uniqueness
    timestamp = now().strftime("%Y%m%d%H%M%S")

    # Construct the new filename by appending timestamp
    new_filename = f"{base}_{timestamp}{extension}"

    # Define the custom upload path
    return os.path.join("patent/Application/Section-I/poc_details", new_filename)


class ApplicationSectionI(models.Model):
    IP_TYPE_CHOICES = [
        ("Patent", "Patent"),
        ("Copyright", "Copyright"),
        ("Trademark", "Trademark"),
        ("Industrial Design", "Industrial Design"),
        ("Trade Secret", "Trade Secret"),
        ("Geographical Indication", "Geographical Indication"),
    ]
    id = models.AutoField(primary_key=True)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="section_i")
    type_of_ip = models.CharField(max_length=255, choices=IP_TYPE_CHOICES, default="Patent")
    area = models.TextField()
    problem = models.TextField()
    objective = models.TextField()
    novelty = models.TextField()
    advantages = models.TextField()
    is_tested = models.BooleanField(default=False)
    poc_details = models.FileField(upload_to=poc_file_upload_path, blank=True, null=True)  # FileField with custom path
    applications = models.TextField()

    class Meta:
        db_table = 'patent_system_application_section_i'

# Function to give path for mou_details
def generate_mou_file_path(instance, filename):
    """
    Generate a unique file path for MOU file.

    Args:
        instance: The model instance that the file is associated with.
        filename: The original filename of the uploaded file.

    Returns:
        str: A custom file path where the file will be stored.
    """
    base, extension = os.path.splitext(filename)  # Split filename and extension
    base = base.replace(" ", "_")  # Replace spaces with underscores for safety
    timestamp = now().strftime("%Y%m%d%H%M%S")  # Generate timestamp
    new_filename = f"{base}_{timestamp}{extension}"  # Append timestamp
    return os.path.join("patent/Application/Section-II/mou_files", new_filename)

def generate_source_agreement_file_path(instance, filename):
    """
    Generate a unique file path for MOU file.

    Args:
        instance: The model instance that the file is associated with.
        filename: The original filename of the uploaded file.

    Returns:
        str: A custom file path where the file will be stored.
    """
    base, extension = os.path.splitext(filename)  # Split filename and extension
    base = base.replace(" ", "_")  # Replace spaces with underscores for safety
    timestamp = now().strftime("%Y%m%d%H%M%S")  # Generate timestamp
    new_filename = f"{base}_{timestamp}{extension}"  # Append timestamp
    return os.path.join("patent/Application/Section-II/source_agreement_files", new_filename)

class ApplicationSectionII(models.Model):
    id = models.AutoField(primary_key=True)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="section_ii")
    funding_details = models.TextField()
    funding_source = models.TextField()
    source_agreement = models.FileField(upload_to=generate_source_agreement_file_path, blank=True, null=True) 
    publication_details = models.TextField()
    mou_details = models.TextField()
    mou_file = models.FileField(upload_to=generate_mou_file_path, blank=True, null=True)  # FileField for MOU file
    research_details = models.TextField()

    class Meta:
        db_table = 'patent_system_application_section_ii'

# Function to give path for form_iii
def generate_form_iii_file_path(instance, filename):
    """
    Generate a unique file path for Form III uploads.

    Args:
        instance: The model instance that the file is associated with.
        filename: The original filename of the uploaded file.

    Returns:
        str: A custom file path where the file will be stored.
    """
    base, extension = os.path.splitext(filename)  # Split filename and extension
    base = base.replace(" ", "_")  # Replace spaces with underscores for safety
    timestamp = now().strftime("%Y%m%d%H%M%S")  # Generate timestamp
    new_filename = f"{base}_{timestamp}{extension}"  # Append timestamp
    return os.path.join("patent/Application/Section-III/form_iii_files", new_filename)

class ApplicationSectionIII(models.Model):
    DEVELOPMENT_STAGE_CHOICES = [
        ("Embryonic", "Embryonic"),
        ("Partially developed", "Partially developed"),
        ("Off-the-shelf", "Off-the-shelf"),
    ]
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="section_iii")
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=15)
    development_stage = models.CharField(max_length=30, choices=DEVELOPMENT_STAGE_CHOICES)
    form_iii = models.FileField(upload_to=generate_form_iii_file_path)

    class Meta:
        db_table = 'patent_system_application_section_iii'


class AssociatedWith(models.Model):
    id = models.AutoField(primary_key=True)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    percentage_share = models.DecimalField(max_digits=5, decimal_places=2)

    def str(self):
        return f"{self.applicant.name} - {self.application.title} ({self.percentage_share}%)"
    
    class Meta:
        db_table = 'patent_system_associatedwith'

class Document(models.Model):
    title = models.CharField(max_length=255)
    link = models.URLField()
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="documents", blank=True, null=True)
    is_locked = models.BooleanField(default=False)
    current_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class CommunicationLog(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="communication_logs")
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="patent_communication_logs")
    external_attorney_name = models.CharField(max_length=255, blank=True, null=True)
    external_attorney_email = models.EmailField(blank=True, null=True)
    message_content = models.TextField()
    status_or_notes = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Communication for application {self.application_id}"

    class Meta:
        db_table = 'patent_system_communication_log'
        ordering = ['-created_at']


class ConflictDeclaration(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="conflict_declarations")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patent_conflict_declarations")
    conflict_type = models.CharField(max_length=120)
    declaration_status = models.CharField(max_length=20, default="Declared")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_conflict_declaration"
        ordering = ["-created_at"]


class LegalAssessment(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="legal_assessments")
    attorney = models.ForeignKey(Attorney, on_delete=models.CASCADE, related_name="legal_assessments")
    opinion = models.CharField(max_length=30)
    prior_art_summary = models.TextField()
    recommended_action = models.TextField()
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_legal_assessment"
        ordering = ["-created_at"]


class NotificationEvent(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="notifications", blank=True, null=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patent_notifications", blank=True, null=True)
    recipient_role = models.CharField(max_length=50, blank=True, null=True)
    event_type = models.CharField(max_length=30, default="General")
    message = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    is_escalated = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_notification_event"
        ordering = ["-created_at"]


class BudgetApproval(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="budget_approvals")
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budget_requests")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    threshold = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default="Pending")
    comments = models.TextField(blank=True, null=True)
    decided_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="budget_decisions", blank=True, null=True)
    decided_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_budget_approval"
        ordering = ["-created_at"]


class ExternalFilingRecord(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="external_filings")
    patent_office = models.CharField(max_length=120)
    filing_reference = models.CharField(max_length=120)
    communication_notes = models.TextField(blank=True, null=True)
    filed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="external_filing_records")
    filing_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_external_filing_record"
        ordering = ["-created_at"]


class MaintenanceSchedule(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="maintenance_schedules")
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, default="Upcoming")
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_maintenance_schedule"
        ordering = ["due_date"]


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    link = models.URLField()
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_document_version"
        ordering = ["-version_number"]
        unique_together = ("document", "version_number")


class InventorConsent(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="inventor_consents")
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name="consents")
    consent_given = models.BooleanField(default=False)
    agreement_reference = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_inventor_consent"


class OfficeAction(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="office_actions")
    office_name = models.CharField(max_length=120)
    action_reference = models.CharField(max_length=120)
    action_summary = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, default="Open")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_office_action"
        ordering = ["-created_at"]


class OfficeActionResponse(models.Model):
    office_action = models.ForeignKey(OfficeAction, on_delete=models.CASCADE, related_name="responses")
    responder = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    response_text = models.TextField()
    response_reference = models.CharField(max_length=120, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_office_action_response"
        ordering = ["-created_at"]


class LicensingRequest(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="licensing_requests")
    requester_name = models.CharField(max_length=120)
    requester_org = models.CharField(max_length=120)
    request_details = models.TextField()
    status = models.CharField(max_length=30, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_licensing_request"
        ordering = ["-created_at"]


class AppealRequest(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="appeals")
    appellant = models.CharField(max_length=120)
    grounds = models.TextField()
    status = models.CharField(max_length=30, default="Open")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_appeal_request"
        ordering = ["-created_at"]


class PriorArtReference(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="prior_art_references")
    reference_type = models.CharField(max_length=80)
    citation = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_prior_art_reference"
        ordering = ["-created_at"]


class LegalAdviceMemo(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="legal_memos")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    summary = models.TextField()
    recommendation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_legal_advice_memo"
        ordering = ["-created_at"]


class AuditLog(models.Model):
    action = models.CharField(max_length=120)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    application = models.ForeignKey(Application, on_delete=models.SET_NULL, blank=True, null=True, related_name="audit_entries")
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patent_system_audit_log"
        ordering = ["-created_at"]