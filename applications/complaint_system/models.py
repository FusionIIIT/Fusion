# imports
from django.db import models
from django.utils import timezone

from applications.globals.models import ExtraInfo

# Class definations:


class Constants:
    AREA = (
        ('hall-1', 'hall-1'),
        ('hall-3', 'hall-3'),
        ('hall-4', 'hall-4'),
        ('CC1', 'CC1'),
        ('CC2', 'CC2'),
        ('core_lab', 'core_lab'),
        ('LHTC', 'LHTC'),
        ('NR2', 'NR2'),
        ('Rewa_Residency', 'Rewa_Residency'),
    )
    COMPLAINT_TYPE = (
        ('Electricity', 'Electricity'),
        ('carpenter', 'carpenter'),
        ('plumber', 'plumber'),
        ('garbage', 'garbage'),
        ('dustbin', 'dustbin'),
        ('internet', 'internet'),
        ('other', 'other'),
    )


class Caretaker(models.Model):
    staff_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    area = models.CharField(choices=Constants.AREA, max_length=20, default='hall-3')
    rating = models.IntegerField(default=0)

    def __str__(self):
        return str(self.id) + '-' + self.area


class Workers(models.Model):
    caretaker_id = models.ForeignKey(Caretaker, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    age = models.CharField(max_length=10)
    phone = models.IntegerField(blank=True)
    worker_type = models.CharField(choices=Constants.COMPLAINT_TYPE,
                                   max_length=20, default='internet')

    def __str__(self):
        return str(self.id) + '-' + self.name


class StudentComplain(models.Model):
    complainer = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    complaint_date = models.DateTimeField(default=timezone.now)
    complaint_finish = models.DateField(blank=True, null=True)
    complaint_type = models.CharField(choices=Constants.COMPLAINT_TYPE,
                                      max_length=20, default='internet')
    location = models.CharField(max_length=20, choices=Constants.AREA)
    specific_location = models.CharField(max_length=50, blank=True)
    details = models.CharField(max_length=100)
    status = models.IntegerField(default='0')
    remarks = models.CharField(max_length=300, default="Pending")
    flag = models.IntegerField(default='0')
    reason = models.CharField(max_length=100, blank=True, default="None")
    feedback = models.CharField(max_length=500, blank=True)
    worker_id = models.ForeignKey(Workers, blank=True, null=True)

    def __str__(self):
        return str(self.complainer.user.username)


class Supervisor(models.Model):
    sup_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    area = models.CharField(choices=Constants.AREA, max_length=20)

    def __str__(self):
        return str(self.sup_id.user.username)
