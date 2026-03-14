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
    project_name= models.CharField(max_length=600)
    project_type= models.CharField(max_length=500)
    # financial_outlay= models.IntegerField()
    project_investigator_id=models.ForeignKey(User,related_name='pi_id', on_delete=models.CASCADE)
    # rspc_admin_id=models.CharField(max_length=500)
    co_project_investigator_id=models.ForeignKey(User,related_name='copi_id' ,on_delete=models.CASCADE, null=True)
    sponsored_agency= models.CharField(max_length=500)
    start_date=models.DateField()
    submission_date=models.DateField()
    finish_date=models.DateField()
    years= models.IntegerField()
    status= models.IntegerField(default=0)
    project_info_file=models.FileField( null=True, blank=True)  
    # project_description=models.CharField(max_length=500 ,default="description")
    financial_outlay_status=models.IntegerField(default=0)
    

    def __str__(self):
        return str(self.project_id)

    class Meta:
        ordering = ['-project_id']

class financial_outlay(models.Model):
    financial_outlay_id= models.IntegerField(primary_key=True)
    project_id= models.ForeignKey(projects, on_delete=models.CASCADE)
    category=models.CharField(max_length=500)
    sub_category=models.CharField(max_length=500)
    amount=models.IntegerField()
    year=models.IntegerField()
    status= models.IntegerField(default=0)
    staff_limit=models.IntegerField(default=0)
    utilized_amount=models.IntegerField(default=0,null= True)

    def __str__(self):
        return str(self.financial_outlay_id)

    class Meta:
        ordering = ['-financial_outlay_id']


class category(models.Model):
    category_id= models.IntegerField(primary_key=True)
    category_name= models.CharField(max_length=500)
    sub_category_name= models.CharField(max_length=500)


    def __str__(self):
        return str(self.category_id)

    class Meta:
        ordering = ['-category_id']


class staff_allocations(models.Model):
    staff_allocation_id=models.IntegerField(primary_key=True)
    project_id= models.ForeignKey(projects, on_delete=models.CASCADE)
    staff_id=models.ForeignKey(User, on_delete=models.CASCADE)
    staff_name=models.CharField(max_length=500)
    qualification=models.CharField(max_length=500)
    year=models.IntegerField()
    stipend=models.IntegerField()
    staff_type=models.CharField(max_length=100,default="research")
    start_date=models.DateField(default=datetime.date.today)
    end_date=models.DateField(null=True, blank=True)
    
    def __str__(self):
        return str(self.staff_allocation_id)

    

    class Meta:
        ordering = ['-staff_allocation_id']

class co_pis(models.Model):
    co_pi= models.ForeignKey(User, on_delete=models.CASCADE)
    project_id= models.ForeignKey(projects, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-project_id']

    

class requests(models.Model):
    request_id=models.IntegerField(primary_key=True)
    project_id= models.ForeignKey(projects, on_delete=models.CASCADE)
    request_type=models.CharField(max_length=500)
    project_investigator_id=models.ForeignKey(User, related_name='rj_pi'  , on_delete= models.CASCADE)
    approval_status= models.IntegerField(default=0) #value 0 means pending

    def __str__(self):
        return str(self.request_id)

    class Meta:
        ordering = ['-request_id']
    
class co_project_investigator(models.Model):
    co_pi_id= models.ForeignKey(User, on_delete=models.CASCADE)
    project_id= models.ForeignKey(projects, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.co_pi_id)
    
    class Meta:
        ordering = ['-co_pi_id']
    
    
    
    

    
