"""
Audit trail logging models for tracking all changes across otheracademic module.
Records: who, what, when, old_value, new_value for all important state changes.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class AuditLog(models.Model):
    """Generic audit trail for tracking changes to critical models."""
    
    # Change metadata
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    
    # What changed
    model_name = models.CharField(max_length=100, db_index=True)  # 'LeavePG', 'NoDues', etc.
    object_id = models.CharField(max_length=200, db_index=True)  # Primary key of changed object
    action = models.CharField(
        max_length=20,
        choices=[
            ('create', 'Created'),
            ('update', 'Updated'),
            ('delete', 'Deleted'),
            ('escalate', 'Escalated'),
            ('approve', 'Approved'),
            ('reject', 'Rejected'),
        ],
        db_index=True
    )
    
    # Field details
    field_name = models.CharField(max_length=100, blank=True)  # Which field changed (for updates)
    old_value = models.TextField(blank=True)  # Previous value (JSON serialized)
    new_value = models.TextField(blank=True)  # New value (JSON serialized)
    
    # Additional context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)  # Human-readable description
    
    # Linking related objects
    department = models.CharField(max_length=100, blank=True)
    related_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_audit_logs'
    )  # For tracking student whose record changed
    
    class Meta:
        db_table = 'audit_log'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.action.upper()} {self.model_name}({self.object_id}) by {self.user} at {self.timestamp}"
    
    @staticmethod
    def log_change(user, model_name, object_id, action, field_name='', old_value='', new_value='',
                   description='', department='', related_user=None, request=None):
        """
        Create an audit log entry.
        
        Args:
            user: User making the change
            model_name: Name of model being changed (e.g., 'LeavePG')
            object_id: Primary key of the object
            action: Type of change (create, update, delete, approve, reject, escalate)
            field_name: Which field was changed (for updates)
            old_value: Previous value (will be JSON serialized if dict)
            new_value: New value (will be JSON serialized if dict)
            description: Human-readable description
            department: Department name if applicable
            related_user: User whose record is being changed (for audit trail of student records)
            request: HTTP request object (to extract IP and user agent)
        """
        # Serialize complex types
        if isinstance(old_value, (dict, list)):
            old_value = json.dumps(old_value)
        if isinstance(new_value, (dict, list)):
            new_value = json.dumps(new_value)
        
        ip_address = None
        user_agent = ''
        if request:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return AuditLog.objects.create(
            timestamp=timezone.now(),
            user=user,
            model_name=model_name,
            object_id=str(object_id),
            action=action,
            field_name=field_name,
            old_value=str(old_value)[:1000],  # Truncate to 1000 chars
            new_value=str(new_value)[:1000],
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            department=department,
            related_user=related_user,
        )
    
    @staticmethod
    def get_history(model_name, object_id):
        """Get full change history for an object."""
        return AuditLog.objects.filter(
            model_name=model_name,
            object_id=str(object_id)
        ).order_by('timestamp')
    
    @staticmethod
    def get_user_actions(user, limit=100):
        """Get recent actions by a user."""
        return AuditLog.objects.filter(user=user).order_by('-timestamp')[:limit]
    
    @staticmethod
    def get_actions_for_student(student_user, limit=100):
        """Get all audit events related to a student."""
        return AuditLog.objects.filter(related_user=student_user).order_by('-timestamp')[:limit]


class NoDuesEscalation(models.Model):
    """Track escalation events for No Dues clearance."""
    
    ESCALATION_TYPES = [
        ('reminder_7day', '7-Day Reminder'),
        ('reminder_14day', '14-Day Reminder'),
        ('reminder_21day', '21-Day Reminder'),
        ('auto_mark_30day', 'Auto-marked after 30 days'),
        ('escalate_dean', 'Escalated to Dean'),
        ('escalate_director', 'Escalated to Director'),
        ('resolved', 'Resolved'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Reference to No Dues record
    no_dues = models.ForeignKey(
        'NoDues',
        on_delete=models.CASCADE,
        related_name='escalations'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='nodues_escalations'
    )
    
    # Escalation details
    escalation_type = models.CharField(max_length=50, choices=ESCALATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    triggered_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Department tracking
    department = models.CharField(max_length=100)
    clear_field = models.CharField(max_length=100)  # Which field (e.g., 'library_clear')
    
    # Notification
    notification_sent_to = models.EmailField(blank=True)
    notification_response = models.TextField(blank=True)  # Response from email service, if any
    
    class Meta:
        db_table = 'nodues_escalation'
        indexes = [
            models.Index(fields=['student', 'created_at']),
            models.Index(fields=['no_dues', 'escalation_type']),
            models.Index(fields=['status', 'created_at']),
        ]
        verbose_name = 'No Dues Escalation'
        verbose_name_plural = 'No Dues Escalations'
    
    def __str__(self):
        return f"{self.escalation_type} for {self.student.username} ({self.status})"


class NoDuesClearanceHistory(models.Model):
    """Track changes to each no dues clearance field with timestamps."""
    
    no_dues = models.ForeignKey(
        'NoDues',
        on_delete=models.CASCADE,
        related_name='clearance_history'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='nodues_clearance_history'
    )
    
    # Which department/field
    department = models.CharField(max_length=100)
    clear_field = models.CharField(max_length=100)
    
    # Status transitions
    previous_status = models.CharField(max_length=20)  # 'pending', 'clear', 'notclear'
    new_status = models.CharField(max_length=20)
    
    # Who changed it
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='nodues_changes')
    changed_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Why (reason/remarks)
    reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'nodues_clearance_history'
        indexes = [
            models.Index(fields=['student', 'changed_at']),
            models.Index(fields=['department', 'changed_at']),
        ]
        verbose_name = 'No Dues Clearance History'
        verbose_name_plural = 'No Dues Clearance Histories'
    
    def __str__(self):
        return f"{self.department}: {self.previous_status} → {self.new_status}"


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
