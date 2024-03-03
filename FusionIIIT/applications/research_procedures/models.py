from django.db import models
from django.db import models
from applications.globals.models import *
from django.contrib.auth.models import User
import datetime

class Constants:
    RESPONSE_TYPE = (
        ('Approved', 'Approved'),
        ('Disapproved', 'Disapproved'),
        ('Pending' , 'Pending')
    )


class projects(models.Model):
    project_id= models.IntegerField(primary_key= True)
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
    request_id=models.IntegerField(primary_key=True)
    project_id= models.IntegerField()
    request_type=models.CharField(max_length=500)
    project_investigator_id=models.CharField(max_length=500)
    status= models.IntegerField() #value 0 means pending
    description=models.CharField(max_length=400,default=None, null= True)
    amount= models.IntegerField(default=0) #value 0 means pending
    
class rspc_inventory(models.Model):
    inventory_id=models.IntegerField(primary_key=True)
    project_id= models.IntegerField()
    project_investigator_id=models.CharField(max_length=500)
    status= models.IntegerField() #value 0 means pending
    description=models.CharField(max_length=400)
    amount= models.IntegerField(default=0) #value 0 means pending

class project_staff_info(models.Model):
    staff_id=models.CharField(primary_key=True,max_length=400)
    project_investigator_id= models.CharField(max_length=500)
    project_id=models.IntegerField()
    staff_name=models.CharField(max_length=400)
    status=models.IntegerField()
    description=models.CharField(max_length=400)

    
    
    
    

    
