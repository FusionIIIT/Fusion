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
    # COMPLAINT_TYPE = (
    #     ('Electricity', 'Electricity'),
    #     ('carpenter', 'carpenter'),
    #     ('plumber', 'plumber'),
    #     ('garbage', 'garbage'),
    #     ('dustbin', 'dustbin'),
    #     ('internet', 'internet'),
    #     ('other', 'other'),
    # )

   
class Receiver(models.Model):    ### need thinking
    staff_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    area = models.CharField(choices=Constants.AREA, max_length=20, default='hall-3')
    rating = models.IntegerField(default=0)
    myfeedback = models.CharField(max_length=400, default='this is my feedback')
    # no_of_comps = models.CharField(max_length=1000)

    def __str__(self):
        return str(self.id) + '-' + self.area

class StudentRequest(models.Model):
    request_maker = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    request_date = models.DateTimeField(default=timezone.now)
    brief = models.CharField(choices=Constants.BRIEF,
                                      max_length=20, default='meet_request')
    details = models.CharField(max_length=200)
    status = models.CharField(max_length=50,default='Pending')
    remarks = models.CharField(max_length=300, default="--")
    request_receiver = models.ForeignKey(Receiver, blank=True, null=True,on_delete=models.CASCADE)
    upload_request = models.FileField(blank=True)

    def __str__(self):
        return str(self.request_maker.user.username)
