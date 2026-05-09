from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, DepartmentInfo


class FileType(models.Model):
    """Types of files that can be tracked"""
    FILE_CATEGORIES = [
        ('ACADEMIC', 'Academic'),
        ('ADMINISTRATIVE', 'Administrative'),
        ('FINANCIAL', 'Financial'),
        ('HR', 'Human Resource'),
        ('ESTABLISHMENT', 'Establishment'),
        ('RESEARCH', 'Research'),
        ('STUDENT', 'Student Related'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=FILE_CATEGORIES)
    description = models.TextField(blank=True)
    default_workflow = models.TextField(blank=True)  # JSON workflow definition
    workflow_config = models.JSONField(default=dict)  # JSON workflow configuration
    requires_attachments = models.BooleanField(default=False)
    max_processing_days = models.IntegerField(default=7)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class File(models.Model):
    """Main file tracking entity"""
    FILE_STATUS = [
        ('CREATED', 'Created'),
        ('PENDING', 'Pending'),
        ('SUBMITTED', 'Submitted (Legacy)'),
        ('IN_PROGRESS', 'In Progress'),
        ('FORWARDED', 'Forwarded'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CLOSED', 'Closed'),
        ('ARCHIVED', 'Archived'),
    ]

    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    # File identification
    file_number = models.CharField(max_length=50, unique=True)
    file_type = models.ForeignKey(FileType, on_delete=models.PROTECT)
    subject = models.CharField(max_length=500)
    description = models.TextField(blank=True)

    # Creation details
    created_by = models.ForeignKey(ExtraInfo, on_delete=models.PROTECT, related_name='created_files')
    created_at = models.DateTimeField(auto_now_add=True)
    source_department = models.ForeignKey(DepartmentInfo, on_delete=models.PROTECT, related_name='outgoing_files')

    # Current status
    status = models.CharField(max_length=20, choices=FILE_STATUS, default='CREATED')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='NORMAL')

    # Current holder
    current_holder = models.ForeignKey(ExtraInfo, on_delete=models.PROTECT, related_name='holding_files')
    current_designation = models.ForeignKey(Designation, on_delete=models.PROTECT)
    current_department = models.ForeignKey(DepartmentInfo, on_delete=models.PROTECT, related_name='current_files')
    received_at = models.DateTimeField(auto_now=True)

    # Completion
    closed_at = models.DateTimeField(null=True, blank=True)
    closure_remarks = models.TextField(blank=True)

    # Reference to source module
    source_module = models.CharField(max_length=50, blank=True)  # e.g., 'academic_procedures'
    source_object_id = models.IntegerField(null=True, blank=True)  # ID of source object

    class Meta:
        ordering = ['-created_at']
        db_table = 'filetracking_newfile'

    def __str__(self):
        return f"{self.file_number} - {self.subject}"


class FileAttachment(models.Model):
    """Attachments to files"""
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='attachments')
    name = models.CharField(max_length=200)
    document = models.FileField(upload_to='fts/attachments/')
    uploaded_by = models.ForeignKey(ExtraInfo, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class FileMovement(models.Model):
    """Track file movement history"""
    ACTION_TYPES = [
        ('CREATE', 'Created'),
        ('FORWARD', 'Forwarded'),
        ('RECEIVE', 'Received'),
        ('APPROVE', 'Approved'),
        ('REJECT', 'Rejected'),
        ('RETURN', 'Returned'),
        ('COMMENT', 'Comment Added'),
        ('CLOSE', 'Closed'),
        ('ARCHIVE', 'Archived'),
        ('REOPEN', 'Reopened'),
    ]

    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='movements')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)

    # Sender details
    sender = models.ForeignKey(ExtraInfo, on_delete=models.PROTECT, related_name='sent_movements')
    sender_designation = models.ForeignKey(Designation, on_delete=models.PROTECT, related_name='sent_from_designation')
    sender_department = models.ForeignKey(DepartmentInfo, on_delete=models.PROTECT, related_name='sent_from_dept')

    # Receiver details
    receiver = models.ForeignKey(ExtraInfo, on_delete=models.PROTECT, related_name='received_movements', null=True, blank=True)
    receiver_designation = models.ForeignKey(Designation, on_delete=models.PROTECT, related_name='sent_to_designation', null=True, blank=True)
    receiver_department = models.ForeignKey(DepartmentInfo, on_delete=models.PROTECT, related_name='sent_to_dept', null=True, blank=True)

    # Movement details
    remarks = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.file.file_number} - {self.action} - {self.timestamp}"


class FileVersion(models.Model):
    """Version snapshots created when files are amended."""
    VERSION_ACTIONS = [
        ('SAVE', 'Save Amendment'),
        ('FORWARD', 'Amend and Forward'),
    ]

    # Keep ORM relation but avoid DB-level FK due legacy/new file table coexistence.
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='versions', db_constraint=False)
    version_number = models.PositiveIntegerField()
    changed_by = models.ForeignKey(ExtraInfo, on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=VERSION_ACTIONS, default='SAVE')
    comment = models.TextField(blank=True)
    snapshot = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = ['file', 'version_number']

    def __str__(self):
        return f"{self.file.file_number} v{self.version_number}"


class FileWorkflow(models.Model):
    """Define workflow templates"""
    file_type = models.ForeignKey(FileType, on_delete=models.CASCADE)
    step_order = models.IntegerField(db_column='step_number')
    designation = models.ForeignKey(Designation, on_delete=models.PROTECT, db_column='required_designation_id')
    department = models.ForeignKey(
        DepartmentInfo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column='required_department_id',
    )
    action_required = models.CharField(max_length=50, db_column='step_name')  # approve, review, sign, etc.
    max_days = models.IntegerField(default=3, db_column='estimated_days')
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        ordering = ['file_type', 'step_order', 'designation']
        unique_together = ['file_type', 'step_order', 'designation', 'department']

    def __str__(self):
        return f"{self.file_type.name} - Step {self.step_order} - {self.designation.name}"


class DraftFile(models.Model):
    """Draft files not yet submitted"""
    created_by = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    file_type = models.ForeignKey(FileType, on_delete=models.PROTECT)
    subject = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    draft_data = models.JSONField(default=dict)  # Store draft form data

    def __str__(self):
        return f"Draft: {self.subject}"


class FTAccessPolicy(models.Model):
    """Stores FT module access-control policy entries editable by admins."""
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key


class FTAdminAuditLog(models.Model):
    """Security audit trail for FT admin user, role, and policy changes."""
    ACTION_TYPES = [
        ('CREATE_USER', 'Create User'),
        ('UPDATE_USER', 'Update User'),
        ('DELETE_USER', 'Delete User'),
        ('ASSIGN_ROLE', 'Assign Role'),
        ('REMOVE_ROLE', 'Remove Role'),
        ('UPDATE_POLICY', 'Update Policy'),
    ]

    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ft_admin_actions')
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ft_admin_targets')
    target_identifier = models.CharField(max_length=120, blank=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'system'
        return f"{self.action} by {actor_name}"


# Legacy models for backward compatibility (can be removed after migration)
class LegacyFile(models.Model):
    """
    Legacy File table - keeping for backward compatibility during migration
    """
    uploader = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='uploaded_files_legacy')
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, null=True, related_name='upload_designation_legacy')
    subject = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=400, null=True, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    upload_file = models.FileField(blank=True)
    src_module = models.CharField(max_length=100, null=True, blank=True, default='')
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'File'

    def __str__(self):
        return str(self.subject or self.id)


class LegacyTracking(models.Model):
    """
    Legacy Tracking table - keeping for backward compatibility during migration
    """
    file_id = models.ForeignKey(LegacyFile, on_delete=models.CASCADE, null=True)
    current_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    current_design = models.ForeignKey(HoldsDesignation, null=True, on_delete=models.CASCADE)
    receiver_id = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name='receiver_id_legacy')
    receive_design = models.ForeignKey(Designation, null=True, on_delete=models.CASCADE, related_name='rec_design_legacy')
    receive_date = models.DateTimeField(auto_now_add=True)
    forward_date = models.DateTimeField(auto_now_add=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    upload_file = models.FileField(blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'Tracking'
