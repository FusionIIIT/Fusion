from datetime import datetime

from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.db import models
from django.contrib.auth.models import User
from applications.academic_information.models import Student


class LeaveFormTable(models.Model):
    """
    Records information related to student leave requests.

    'leave_from' and 'leave_to' store the start and end date of the leave request.
    'date_of_application' stores the date when the leave request was applied.
    'related_document' stores any related documents or notes for the leave request.
    'place' stores the location where the leave is requested.
    'reason' stores the reason for the leave request.
    'leave_type' stores the type of leave from a dropdown.
    """
    LEAVE_TYPES = (
        ('Casual', 'Casual'),
        ('Medical', 'Medical'),
        
    )
    

    student_name = models.CharField(max_length=100)
    roll_no = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    date_from = models.DateField()
    date_to = models.DateField()
    date_of_application = models.DateField()
    upload_file = models.FileField(blank=True)
    address = models.CharField(max_length=100)
    purpose = models.TextField()
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    approved = models.BooleanField()
    rejected = models.BooleanField()

    class Meta:
        db_table='LeaveFormTable'
        






class GraduateSeminarFormTable(models.Model):
   
    roll_no = models.CharField(max_length=20)
    semester= models.CharField(max_length=100)
    date_of_seminar = models.DateField()
   

    class Meta:
        db_table='GraduateSeminarFormTable'
        




class BonafideFormTableUpdated(models.Model):
   
    

    student_names = models.CharField(max_length=100)
    roll_nos = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    branch_types = models.CharField(max_length=50)
    semester_types = models.CharField(max_length=20)
    purposes = models.TextField()
    date_of_applications= models.DateField()
    approve = models.BooleanField()
    reject = models.BooleanField()
    download_file = models.FileField(blank=True)
   
    

    class Meta:
        db_table='BonafideFormTableUpdated'
        



class AssistantshipClaimFormStatusUpd(models.Model):
    roll_no = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=100)
    discipline = models.CharField(max_length=100)
    dateFrom = models.DateField()
    dateTo = models.DateField()
    # month = models.CharField(max_length=50)
    # year = models.CharField(max_length=50)
    bank_account = models.CharField(max_length=100)
    student_signature = models.FileField(upload_to='student_signatures/')  # Change to FileField
    dateApplied = models.DateField()
    ta_supervisor = models.CharField(max_length=100)
    thesis_supervisor = models.CharField(max_length=100)
    applicability = models.CharField(max_length=100)
   
    TA_approved = models.BooleanField()
    TA_rejected = models.BooleanField()
    Ths_approved = models.BooleanField()
    Ths_rejected = models.BooleanField()
    HOD_approved = models.BooleanField()
    HOD_rejected = models.BooleanField()
    Acad_approved = models.BooleanField()
    Acad_rejected = models.BooleanField()

    class Meta:
        db_table = 'AssistantshipClaimFormStausUpd'