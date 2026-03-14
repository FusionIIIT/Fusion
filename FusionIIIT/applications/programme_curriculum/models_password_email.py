# Password Email Management Models for Student Management

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .models_student_management import StudentBatchUpload


class PasswordEmailLog(models.Model):
    """
    Model to log password emails sent to students for audit purposes
    """
    EMAIL_STATUS_CHOICES = [
        ('SENT', 'Successfully Sent'),
        ('FAILED', 'Failed to Send'),
        ('PENDING', 'Pending'),
        ('BOUNCED', 'Email Bounced'),
    ]
    
    student = models.ForeignKey(
        StudentBatchUpload, 
        on_delete=models.CASCADE, 
        related_name='password_emails'
    )
    sent_to_email = models.EmailField(help_text="Email address where password was sent")
    sent_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Admin who triggered the password email"
    )
    email_status = models.CharField(
        max_length=10, 
        choices=EMAIL_STATUS_CHOICES, 
        default='PENDING'
    )
    password_generated = models.CharField(
        max_length=100, 
        help_text="The password that was generated (for audit)",
        blank=True,
        null=True
    )
    email_subject = models.CharField(max_length=255, blank=True, null=True)
    email_content_preview = models.TextField(
        blank=True, 
        null=True, 
        help_text="First 200 chars of email content"
    )
    error_message = models.TextField(blank=True, null=True)
    attempts_count = models.IntegerField(default=1)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    last_attempt_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'password_email_log'
        verbose_name = 'Password Email Log'
        verbose_name_plural = 'Password Email Logs'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['email_status']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['student']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.sent_to_email} ({self.email_status}) at {self.sent_at}"
    
    def mark_as_sent(self, password=None):
        """Mark email as successfully sent"""
        self.email_status = 'SENT'
        if password:
            self.password_generated = password
        self.save(update_fields=['email_status', 'password_generated', 'last_attempt_at'])
    
    def mark_as_failed(self, error_message=None):
        """Mark email as failed"""
        self.email_status = 'FAILED'
        if error_message:
            self.error_message = error_message
        self.attempts_count += 1
        self.save(update_fields=['email_status', 'error_message', 'attempts_count', 'last_attempt_at'])


class BulkPasswordEmailOperation(models.Model):
    """
    Model to track bulk password email operations
    """
    OPERATION_STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    operation_id = models.CharField(max_length=100, unique=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    programme_type = models.CharField(max_length=10, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    branch_filter = models.CharField(max_length=200, blank=True, null=True)
    
    total_students = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    emails_failed = models.IntegerField(default=0)
    emails_pending = models.IntegerField(default=0)
    
    operation_status = models.CharField(
        max_length=15, 
        choices=OPERATION_STATUS_CHOICES, 
        default='INITIATED'
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    error_summary = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'bulk_password_email_operation'
        verbose_name = 'Bulk Password Email Operation'
        verbose_name_plural = 'Bulk Password Email Operations'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"Bulk Email {self.operation_id} - {self.operation_status} ({self.emails_sent}/{self.total_students})"
    
    def calculate_completion_rate(self):
        """Calculate completion percentage"""
        if self.total_students == 0:
            return 0
        completed = self.emails_sent + self.emails_failed
        return round((completed / self.total_students) * 100, 2)
    
    def mark_completed(self):
        """Mark operation as completed"""
        self.operation_status = 'COMPLETED'
        self.end_time = timezone.now()
        if self.start_time and self.end_time:
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())
        self.save(update_fields=['operation_status', 'end_time', 'duration_seconds'])
    
    def update_stats(self):
        """Update email statistics from related PasswordEmailLog entries"""
        logs = PasswordEmailLog.objects.filter(
            student__in=self.get_target_students()
        ).filter(sent_at__gte=self.start_time)
        
        self.emails_sent = logs.filter(email_status='SENT').count()
        self.emails_failed = logs.filter(email_status='FAILED').count()
        self.emails_pending = logs.filter(email_status='PENDING').count()
        
        self.save(update_fields=['emails_sent', 'emails_failed', 'emails_pending'])
    
    def get_target_students(self):
        """Get the students targeted by this bulk operation"""
        queryset = StudentBatchUpload.objects.all()
        
        if self.programme_type:
            queryset = queryset.filter(programme_type=self.programme_type)
        if self.year:
            queryset = queryset.filter(year=self.year)
        if self.branch_filter:
            queryset = queryset.filter(branch__icontains=self.branch_filter)
            
        return queryset


class StudentPasswordHistory(models.Model):
    """
    Model to track password changes for students
    """
    student = models.ForeignKey(
        StudentBatchUpload, 
        on_delete=models.CASCADE, 
        related_name='password_history'
    )
    password_hash = models.CharField(max_length=128)  # Store hashed passwords
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_initial_password = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    password_changed_at = models.DateTimeField(blank=True, null=True)
    change_reason = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'student_password_history'
        verbose_name = 'Student Password History'
        verbose_name_plural = 'Student Password History'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.name} - Password created at {self.created_at}"


class EmailTemplate(models.Model):
    """
    Model to store customizable email templates for password emails
    """
    TEMPLATE_TYPE_CHOICES = [
        ('INITIAL_PASSWORD', 'Initial Password Email'),
        ('PASSWORD_RESET', 'Password Reset Email'),
        ('BULK_PASSWORD', 'Bulk Password Email'),
        ('REMINDER', 'Login Reminder Email'),
    ]
    
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, unique=True)
    subject_template = models.CharField(max_length=255)
    html_template = models.TextField()
    text_template = models.TextField(blank=True, null=True)
    variables_info = models.JSONField(
        default=dict,
        help_text="JSON object describing available template variables"
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_template'
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
    
    def __str__(self):
        return f"{self.get_template_type_display()} Template"
    
    def render_subject(self, context):
        """Render subject with provided context"""
        from django.template import Context, Template
        template = Template(self.subject_template)
        return template.render(Context(context))
    
    def render_html(self, context):
        """Render HTML content with provided context"""
        from django.template import Context, Template
        template = Template(self.html_template)
        return template.render(Context(context))
