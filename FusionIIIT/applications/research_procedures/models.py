from django.db import models
from django.db import models
from applications.globals.models import ExtraInfo
from django.contrib.auth.models import User
import datetime

class Constants:
    RESPONSE_TYPE = (
        ('Approved', 'Approved'),
        ('Disapproved', 'Disapproved'),
        ('Pending' , 'Pending')
    )

class Patent(models.Model):
    """
        Holds Patents filed by faculty.

        @fields:
            faculty_id - Extra information of the faculty who filed the patent.
            title - Title of the patent
            ipd_form - IPD form of the patent
            ipd_form_file - Contains the url of the ipd_form pdf uploaded by the faculty
            project_details - Project details of the patent
            project_details_file - Contains the url of the project_details pdf uploaded by the faculty
            status - Status of the patent
    """

    application_id = models.AutoField(primary_key=True)
    faculty_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    ipd_form = models.FileField(null = True, blank= True)
    project_details = models.FileField(null = True, blank= True)
    ipd_form_file = models.TextField(null=True, blank=True)
    project_details_file = models.TextField(null=True, blank=True)
    status = models.CharField(choices=Constants.RESPONSE_TYPE, max_length=20, default='Pending')

    def _str_(self):
        return str(self.title)

class pr_test(models.Model):
    
    name = models.CharField(max_length=120)
    age = models.IntegerField()

    def _str_(self):
        return str(self.name)
    

class projects(models.Model):
    project_id= models.IntegerField()
    project_name= models.CharField(max_length=500)
    project_type= models.CharField(max_length=500)
    status= models.IntegerField()
    financial_outlay= models.IntegerField()
    project_investigator_id=models.CharField(max_length=500)
    rspc_admin_id=models.CharField(max_length=500)
    co_project_investigator_id=models.CharField(max_length=500)
    sponsored_agency= models.CharField(max_length=500)
    start_date=models.DateField()
    submission_date=models.DateField()
    finish_date=models.DateField()

    def __str__(self):
        return str(self.project_id)
    
class requests(models.Model):
    request_id=models.IntegerField()
    project_id= models.IntegerField()
    request_type=models.CharField(max_length=500)
    project_investigator_id=models.CharField(max_length=400)
    status= models.IntegerField() #value 0 means pending
    
    
    def __str__(self):
        return str(self.request_id)
    
