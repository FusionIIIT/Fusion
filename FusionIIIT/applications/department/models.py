from datetime import timezone
from django.db import models
from datetime import date

# Create your models here.
from applications.globals.models import ExtraInfo
  
class SpecialRequest(models.Model):
    request_maker = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    request_date = models.DateTimeField(default=date.today)
    brief = models.CharField(max_length=20, default='--')
    request_details = models.CharField(max_length=200)
    upload_request = models.FileField(blank=True)
    status = models.CharField(max_length=50,default='Pending')
    remarks = models.CharField(max_length=300, default="--")
    request_receiver = models.CharField(max_length=30, default="--")

    def __str__(self):
        return str(self.request_maker.user.username)


class Announcements(models.Model):
    maker_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    ann_date = models.DateTimeField(default="04-04-2021")
    message = models.CharField(max_length=200)
    batch = models.CharField(max_length=40,default="Year-1")
    department = models.CharField(max_length=40,default="ALL")
    programme = models.CharField(max_length=10)
    upload_announcement = models.FileField(upload_to='department/upload_announcement', null=True, default=" ")
    def __str__(self):
        return str(self.maker_id.user.username)
