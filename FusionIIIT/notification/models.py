from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, DepartmentInfo

# Create your models here.
class Announcements(models.Model):
    TARGET_GROUPS = [
        ('faculty', 'Faculty'),
        ('students', 'Students'),
        ('all', 'All Staff and Students'),
        ('specific_users', 'Specific Users'),
    ]
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=200)
    target_group = models.CharField(max_length=20, choices=TARGET_GROUPS)
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, null=True, blank=True)
    batch = models.IntegerField(null=True, blank=True)
    upload_announcement = models.FileField(upload_to='notifications/upload_announcement', null=True, default=" ")
    module = models.CharField(max_length=200, default='Fusion')
    def __str__(self):
        return str(self.created_by.username)
    
class AnnouncementRecipients(models.Model):
    announcement = models.ForeignKey(Announcements, on_delete=models.CASCADE, related_name='recipients')
    user = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.id} - {self.announcement.message}"