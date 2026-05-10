from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class RequestStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    FINANCE_VALIDATED = "FINANCE_VALIDATED", "Finance Validated"
    ESCALATED = "ESCALATED", "Escalated"
    VALIDATED = "VALIDATED", "Validated"
    HOD_APPROVED = "HOD_APPROVED", "HoD Approved"
    DEAN_APPROVED = "DEAN_APPROVED", "Dean Approved"
    DIRECTOR_APPROVED = "DIRECTOR_APPROVED", "Director Approved"
    APPROVED = "APPROVED", "Approved"
    PROCESSED = "PROCESSED", "Processed"
    CLOSED = "CLOSED", "Closed"
    REJECTED = "REJECTED", "Rejected"


class RequestType(models.TextChoices):
    EXPENSE = "EXPENSE", "Expense"
    VOUCHER = "VOUCHER", "Voucher"


class WorkflowType(models.TextChoices):
    EXPENSE = "EXPENSE", "Expense / Voucher"
    TA = "TA", "Travel Allowance"
    AUDIT_OBSERVATION = "AUDIT_OBSERVATION", "Audit Observation"


class TARequestStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    VERIFIED = "VERIFIED", "Verified"
    APPROVED = "APPROVED", "Approved"
    CLOSED = "CLOSED", "Closed"
    REJECTED = "REJECTED", "Rejected"


class AuditObservationStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    RESPONDED = "RESPONDED", "Responded"
    CLOSED = "CLOSED", "Closed"


class ActionDecision(models.TextChoices):
    CREATED = "CREATED", "Created"
    SUBMITTED = "SUBMITTED", "Submitted"
    VALIDATED = "VALIDATED", "Validated"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    ESCALATED = "ESCALATED", "Escalated"
    RESPONDED = "RESPONDED", "Responded"
    CLOSED = "CLOSED", "Closed"
    UPDATED = "UPDATED", "Updated"


def request_attachment_path(instance, filename):
    return f"audit_account/requests/{instance.request_id}/{filename}"


def ta_attachment_path(instance, filename):
    return f"audit_account/ta/{instance.travel_allowance_id}/{filename}"


def observation_attachment_path(instance, filename):
    return f"audit_account/observations/{instance.observation_id}/{filename}"


class DepartmentBudget(models.Model):
    department = models.CharField(max_length=100)
    budget_head = models.CharField(max_length=100)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("department", "budget_head")

    def __str__(self):
        return f"{self.department} - {self.budget_head}"


class Request(models.Model):
    type = models.CharField(max_length=20, choices=RequestType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    department = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    document_names = models.JSONField(default=list, blank=True)
    budget_head = models.CharField(max_length=100, blank=True)
    budget_remaining = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=30,
        choices=RequestStatus.choices,
        default=RequestStatus.DRAFT,
    )
    current_approver_role = models.CharField(max_length=40, blank=True)
    validation_remarks = models.TextField(blank=True)
    approval_remarks = models.TextField(blank=True)
    rejection_remarks = models.TextField(blank=True)
    anomaly_reason = models.TextField(blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    created_by = models.IntegerField()  # legacy compatibility
    created_by_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.type} - {self.status}"


class TravelAllowance(models.Model):
    employee = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="ta_forms"
    )
    employee_name = models.CharField(max_length=150, blank=True)
    department = models.CharField(max_length=100)
    travel_from = models.CharField(max_length=120)
    travel_to = models.CharField(max_length=120)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    purpose = models.TextField()
    amount_claimed = models.DecimalField(max_digits=12, decimal_places=2)
    document_names = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=30, choices=TARequestStatus.choices, default=TARequestStatus.SUBMITTED
    )
    finance_remarks = models.TextField(blank=True)
    approval_remarks = models.TextField(blank=True)
    rejection_remarks = models.TextField(blank=True)
    high_value = models.BooleanField(default=False)
    current_approver_role = models.CharField(max_length=40, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TA-{self.id} - {self.status}"


class AuditObservation(models.Model):
    target_workflow = models.CharField(max_length=30, choices=WorkflowType.choices)
    request = models.ForeignKey(
        Request, null=True, blank=True, on_delete=models.SET_NULL, related_name="observations"
    )
    travel_allowance = models.ForeignKey(
        TravelAllowance,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="observations",
    )
    title = models.CharField(max_length=200)
    details = models.TextField()
    response_deadline = models.DateField(null=True, blank=True)
    response_text = models.TextField(blank=True)
    response_document_names = models.JSONField(default=list, blank=True)
    closure_remarks = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=AuditObservationStatus.choices,
        default=AuditObservationStatus.OPEN,
    )
    raised_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="raised_observations"
    )
    responded_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_observation_responses"
    )
    closed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="closed_observations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"OBS-{self.id} - {self.status}"


class ObservationAttachmentKind(models.TextChoices):
    OBSERVATION = "OBSERVATION", "Observation"
    RESPONSE = "RESPONSE", "Response"


class RequestAttachment(models.Model):
    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to=request_attachment_path)
    original_name = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="uploaded_audit_request_files"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name or self.file.name


class TravelAllowanceAttachment(models.Model):
    travel_allowance = models.ForeignKey(
        TravelAllowance, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to=ta_attachment_path)
    original_name = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="uploaded_audit_ta_files"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name or self.file.name


class ObservationAttachment(models.Model):
    observation = models.ForeignKey(
        AuditObservation, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to=observation_attachment_path)
    original_name = models.CharField(max_length=255, blank=True)
    attachment_kind = models.CharField(
        max_length=20,
        choices=ObservationAttachmentKind.choices,
        default=ObservationAttachmentKind.OBSERVATION,
    )
    uploaded_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="uploaded_audit_observation_files"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name or self.file.name


class ActionLog(models.Model):
    workflow = models.CharField(max_length=30, choices=WorkflowType.choices)
    request = models.ForeignKey(
        Request, null=True, blank=True, on_delete=models.CASCADE, related_name="action_logs"
    )
    travel_allowance = models.ForeignKey(
        TravelAllowance, null=True, blank=True, on_delete=models.CASCADE, related_name="action_logs"
    )
    observation = models.ForeignKey(
        AuditObservation, null=True, blank=True, on_delete=models.CASCADE, related_name="action_logs"
    )
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    actor_role = models.CharField(max_length=80, blank=True)
    decision = models.CharField(max_length=30, choices=ActionDecision.choices)
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.workflow} {self.decision} by {self.actor_id}"


def mark_closed(instance):
    instance.closed_at = timezone.now()
    return instance
