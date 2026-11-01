from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from applications.iwdModuleV2.workflow_engine import IWDStates, CostBands


class MaintenanceComplaint(models.Model):
    """
    UC-IWD-001, UC-IWD-005, UC-IWD-015
    CFR-IWD-01, CFR-IWD-02, BR-IWD-001, BR-IWD-002
    """
    CATEGORY_CHOICES = (
        ('Civil', 'Civil'),
        ('Electrical', 'Electrical'),
    )
    URGENCY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    )

    complaint_id = models.AutoField(primary_key=True)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='iwd_complaints')
    issue_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=255)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='Low')
    remarks = models.TextField(blank=True, default='')

    assigned_engineer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='iwd_assigned_complaints')
    status = models.CharField(max_length=100, default=IWDStates.SUBMITTED)

    assessment_details = models.TextField(blank=True, default='')
    assessment_date = models.DateTimeField(null=True, blank=True)

    is_urgent_escalated = models.BooleanField(default=False)
    urgent_remarks = models.TextField(blank=True, default='')

    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    rework_count = models.IntegerField(default=0)  # BR-IWD-014, BW-IWD-10 max 1 traversal

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Complaint #{self.complaint_id} - {self.issue_category} ({self.status})"


class RepairEstimate(models.Model):
    """
    UC-IWD-021, UC-IWD-031, UC-IWD-041, UC-IWD-051
    BR-IWD-003, BR-IWD-004, BR-IWD-005, BR-IWD-006, BR-IWD-007, BR-IWD-009
    """
    BAND_CHOICES = (
        ('LOW', 'Low (< Rs.25,000)'),
        ('MID', 'Mid (Rs.25,000 to Rs.2.5 Lakh)'),
        ('HIGH', 'High (> Rs.2.5 Lakh)'),
    )

    complaint = models.ForeignKey(MaintenanceComplaint, on_delete=models.CASCADE, related_name='estimates')
    engineer = models.ForeignKey(User, on_delete=models.CASCADE)
    estimated_time_days = models.IntegerField(default=1)
    materials_details = models.TextField(blank=True, default='')
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    cost_band = models.CharField(max_length=20, choices=BAND_CHOICES)

    # Committee Review (BR-IWD-005)
    committee_outcome = models.TextField(blank=True, default='')
    committee_approved = models.BooleanField(null=True, blank=True)

    # Department Head Decision (BR-IWD-006)
    dept_head_decision = models.CharField(max_length=50, blank=True, default='')  # approve, reject, forward
    dept_head_remarks = models.TextField(blank=True, default='')

    # Director Decision (BR-IWD-007)
    director_decision = models.CharField(max_length=50, blank=True, default='')  # approve, reject
    director_remarks = models.TextField(blank=True, default='')

    # Rejection and Resubmission (BR-IWD-009)
    rejection_reason = models.TextField(blank=True, default='')
    resubmission_count = models.IntegerField(default=0)

    status = models.CharField(max_length=100, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.cost_band and self.total_cost is not None:
            self.cost_band = CostBands.classify(self.total_cost)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Estimate for #{self.complaint_id} - Rs.{self.total_cost} ({self.cost_band})"


class InventoryStock(models.Model):
    """
    UC-IWD-061, BR-IWD-010
    """
    item_name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=50, default='General')  # Civil / Electrical / General
    quantity_available = models.IntegerField(default=0)
    unit = models.CharField(max_length=50, default='pcs')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return f"{self.item_name} ({self.quantity_available} {self.unit})"


class MaterialIssueRecord(models.Model):
    """
    UC-IWD-061, BR-IWD-011 (Inventory audit trail)
    """
    complaint = models.ForeignKey(MaintenanceComplaint, on_delete=models.CASCADE, related_name='material_issues')
    material = models.ForeignKey(InventoryStock, on_delete=models.CASCADE)
    quantity_issued = models.IntegerField(default=1)
    issued_by = models.ForeignKey(User, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Issued {self.quantity_issued} {self.material.item_name} for Complaint #{self.complaint_id}"


class PhysicalVerification(models.Model):
    """
    UC-IWD-101, BR-IWD-014, BW-IWD-09, BW-IWD-10
    """
    OUTCOME_CHOICES = (
        ('Approved', 'Approved'),
        ('Rework Required', 'Rework Required'),
    )

    complaint = models.ForeignKey(MaintenanceComplaint, on_delete=models.CASCADE, related_name='verifications')
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE)
    outcome = models.CharField(max_length=50, choices=OUTCOME_CHOICES)
    remarks = models.TextField(blank=True, default='')
    verification_date = models.DateTimeField(auto_now_add=True)
    traversal_number = models.IntegerField(default=0)

    def __str__(self):
        return f"Verification for #{self.complaint_id}: {self.outcome}"


class FinalBillRecord(models.Model):
    """
    UC-IWD-111, UC-IWD-121, UC-IWD-131
    BR-IWD-015, BR-IWD-016, BW-IWD-11
    """
    complaint = models.ForeignKey(MaintenanceComplaint, on_delete=models.CASCADE, related_name='final_bills')
    engineer = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    invoice_doc = models.FileField(upload_to='iwd/final_bills/', null=True, blank=True)

    # Auditor Validation (BR-IWD-015)
    auditor_status = models.CharField(max_length=50, default='Pending')  # Pending, Validated, Query
    auditor_remarks = models.TextField(blank=True, default='')
    audited_at = models.DateTimeField(null=True, blank=True)

    # Director Payment Approval (BR-IWD-016)
    director_payment_approval = models.BooleanField(default=False)
    director_approved_at = models.DateTimeField(null=True, blank=True)

    # Accounts Settlement (BR-IWD-016)
    accounts_settled = models.BooleanField(default=False)
    settled_at = models.DateTimeField(null=True, blank=True)
    settlement_reference = models.CharField(max_length=100, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bill for #{self.complaint_id}: Rs.{self.total_amount} (Audited: {self.auditor_status})"


class ComplaintFeedback(models.Model):
    """
    UC-IWD-141, UC-IWD-145, BR-IWD-017
    """
    complaint = models.ForeignKey(MaintenanceComplaint, on_delete=models.CASCADE, related_name='feedbacks')
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comments = models.TextField(blank=True, default='')
    post_repair_issue = models.BooleanField(default=False)
    post_repair_remarks = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for #{self.complaint_id}: Rating {self.rating}"


class IWDAuditTrail(models.Model):
    """
    BR-IWD-011, BR-IWD-013: Full audit trail of decisions, modifications, and rejections.
    """
    complaint = models.ForeignKey(MaintenanceComplaint, on_delete=models.CASCADE, related_name='audit_trails', null=True, blank=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    actor_role = models.CharField(max_length=50)
    action = models.CharField(max_length=100)
    previous_state = models.CharField(max_length=100)
    new_state = models.CharField(max_length=100)
    remarks = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.actor_role} - {self.action} ({self.previous_state} -> {self.new_state})"
