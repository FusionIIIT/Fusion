from datetime import timezone
from django.db import models

# Create your models here.
from applications.globals.models import ExtraInfo

class Constants:
    BREIF = (
        ('meet_request', 'meet_request'),
        ('hall-3', 'hall-3'),
        ('hall-4', 'hall-4'),
        ('CC1', 'CC1'),
        ('CC2', 'CC2'),
        ('core_lab', 'core_lab'),
        ('LHTC', 'LHTC'),
        ('NR2', 'NR2'),
        ('Rewa_Residency', 'Rewa_Residency'),
    )
    PERSON = (
        ('admin', 'admin'),
        ('hod', 'hod'),
        ('vkjain', 'vkjain')
    )

    PROGRAMME = (
        ('B.tech','B.tech'),
        ('B.Des','B.Des'),
        ('M.tech','M.tech'),
        ('M.Des','M.Des'),
        ('P.hD','P.hD'),
        
    )

   
class Receiver(models.Model):    
    staff_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    area = models.CharField(choices=Constants.PERSON, max_length=20, default='admin')
    #area = models.CharField(choices=Constants.AREA, max_length=20, default='hall-3')

    def __str__(self):
        return str(self.id)

# class StudentRequest(models.Model):
#     request_maker = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
#     request_date = models.DateTimeField(default=timezone.now)
#    # request_date = models.DateTimeField(default=timezone.now)
#     brief = models.CharField(choices=Constants.BRIEF,
#                                       max_length=20, default='meet_request')
#     details = models.CharField(max_length=200)
#     status = models.CharField(max_length=50,default='Pending')
#     remarks = models.CharField(max_length=300, default="--")
#     request_receiver = models.ForeignKey(Receiver, blank=True, null=True,on_delete=models.CASCADE)
#     upload_request = models.FileField(blank=True)
#     def __str__(self):
#         return str(self.id) + '-' + self.area


class Announcements(models.Model):
    maker_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    ann_date = models.DateTimeField(default="04-04-2021")
    message = models.CharField(max_length=200)
    batch = models.IntegerField(default="2016")
    programme = models.CharField(max_length=10, choices=Constants.PROGRAMME)
    upload_announcement = models.FileField(blank=True)
    def __str__(self):
        return str(self.maker_id.user.username)

