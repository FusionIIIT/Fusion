from django.db import models
from django.utils import timezone
from applications.globals.models import ExtraInfo

class Announcement(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    announcer = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_archived = models.BooleanField(default=False)

    class Meta:
        db_table = 'notifications_announcement'
        ordering = ['-timestamp']

    def __str__(self):
        return self.title

