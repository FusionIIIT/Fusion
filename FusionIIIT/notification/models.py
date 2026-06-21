from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo


class RegisteredModule(models.Model):
    """
    Whitelist of modules authorized to trigger the notification API.
    Implements BR-NT-03: API Authorization
    """
    PRIORITY_CHOICES = [
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Medium'),
        (4, 'Low'),
    ]
    
    module_name = models.CharField(max_length=100, unique=True, help_text="Name of the registered module")
    api_key = models.CharField(max_length=255, unique=True, help_text="API key for module authentication")
    is_active = models.BooleanField(default=True, help_text="Whether this module is allowed to send notifications")
    default_priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3, help_text="Default priority for notifications from this module")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='registered_modules')
    
    class Meta:
        ordering = ['module_name']
        verbose_name = "Registered Module"
        verbose_name_plural = "Registered Modules"
    
    def __str__(self):
        return f"{self.module_name} ({'Active' if self.is_active else 'Inactive'})"


class Announcements(models.Model):
    """
    Announcements model for system-wide and module-specific announcements.
    Used by all modules to broadcast messages to specific user groups.
    """
    
    TARGET_GROUP_CHOICES = [
        ('all_users', 'All Users'),
        ('students', 'All Students'),
        ('faculty', 'All Faculty'),
        ('staff', 'Staff Members'),
        ('specific_users', 'Specific Users'),
        ('department', 'Department Wide'),
        ('batch', 'Specific Batch'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Medium'),
        (4, 'Low'),
    ]

    # Content
    message = models.TextField(help_text="Announcement message content")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='announcements_created')
    
    # Targeting
    target_group = models.CharField(max_length=20, choices=TARGET_GROUP_CHOICES, default='all_users')
    department = models.ForeignKey('globals.DepartmentInfo', on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.CharField(max_length=100, blank=True, null=True)
    
    # Module association
    module = models.CharField(max_length=100, default='Fusion', help_text="Module this announcement belongs to")
    
    # Priority (T-NT-05)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3, help_text="Priority level (1=Critical, 4=Low)")
    
    # Expiry (T-NT-02)
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="Announcement automatically expires at this date/time")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name_plural = "Announcements"
        indexes = [
            models.Index(fields=['is_active', 'is_published']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.module} - {self.message[:50]}"
    
    def is_expired(self):
        """Check if announcement has expired (T-NT-02)"""
        from django.utils import timezone
        if self.expiry_date and timezone.now() > self.expiry_date:
            return True
        return False


class AnnouncementRecipients(models.Model):
    """
    Stores which specific users should receive an announcement.
    Used when target_group is 'specific_users'.
    """
    
    announcement = models.ForeignKey(Announcements, on_delete=models.CASCADE, related_name='recipients')
    user = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('announcement', 'user')
        verbose_name_plural = "Announcement Recipients"
    
    def __str__(self):
        return f"{self.announcement.id} - {self.user.user.username}"
