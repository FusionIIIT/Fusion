import datetime

from django.db import models
from django.utils.translation import gettext as _

from applications.globals.models import ExtraInfo


class Constants:

    APPROVAL_TYPE = (
        ('APPROVED', 'Approved'),
        ('PENDING', 'Pending'),
    )

    HALL_NO = (
        ('HALL-1','hall-1'),
        ('HALL-3','hall-3'),
        ('HALL-4','hall-4'),
    )

    CLUB_TYPE = (
        ('TECHNICAL', 'technical'),
        ('CULTURAL', 'cultural'),
        ('SPORTS', 'sports'),
    )



class DeanS_approve_committes(models.Model):
    id = models.AutoField(primary_key=True)
    convener=models.ForeignKey(ExtraInfo, on_delete=models.CASCADE ,related_name='convener')
    faculty_incharge=models.ForeignKey(ExtraInfo, on_delete=models.CASCADE ,related_name='facultyincharge')
    date_approved=models.DateField(null=True, blank=True)
    description=models.CharField(max_length=200)

    def __str__(self):
        return self.convener + '-' + self.dateofapproval

class hostel_guestroom_approval(models.Model):
    id = models.AutoField(primary_key=True)
    intender=models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    hall_no=models.CharField(max_length=5, choices=Constants.HALL_NO ,default='')
    arrival_date=models.DateField(_("Date"), default=datetime.date.today)
    departure_date=models.DateField(null=True, blank=True)
    status=models.CharField(max_length=20, choices=Constants.APPROVAL_TYPE ,default='Pending')

    def __str__(self):
        return self.hall_no + '-' + self.status


class hostel_allotment(models.Model):
    id = models.AutoField(primary_key=True)
    hall_no=models.CharField(max_length=5, choices=Constants.HALL_NO ,default='')
    allotment_file=models.FileField(upload_to='uploads/')
    description=models.CharField(max_length=200)
    
    def __str__(self):
        return '{} - {}'.format(self.hall_no, self.allotment_file)

class Budget(models.Model):
    id=models.AutoField(primary_key=True)
    budget_type=models.CharField(max_length=20)
    club_type=models.CharField(max_length=20, choices=Constants.CLUB_TYPE, default='')
    budget_allocated=models.PositiveIntegerField(default=0)
    budget_expenditure=models.PositiveIntegerField(default=0)
    budget_available=models.PositiveIntegerField(default=0)
    # def __str__(self):
    #         return self.budget_type + '-' + self.budget_allocated
