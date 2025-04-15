from django.db import models
from django.db import models
from applications.globals.models import *
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

class Constants:
    RESPONSE_TYPE = (
        ('Approved', 'Approved'),
        ('Disapproved', 'Disapproved'),
        ('Pending' , 'Pending')
    )



class projects(models.Model): 
    ACCESS_SPECIFIERS = (
        ('Co', 'Only PI'),
        ('noCo', 'Either PI or Co-PI(s)'),
    )   
    
    PROJECT_TYPES = (
        ('Research', 'Research'),
        ('Consultancy', 'Consultancy'),
    )   

    CATEGORY_CHOICES = (
        ('Government', 'Governement'),
        ('Private', 'Private Entity'),
        ('IIITDMJ', 'Institute'),
        ('Other', 'Other'),
    )

    STATUS_CHOICES = (
        ('OnGoing', 'OnGoing'),
        ('Submitted', 'Submitted'),
        ('Registered', 'Registered'),
        ('RSPC Approval', 'RSPC Approval'),
        ('HoD Forward', 'HoD Forward'),
        ('Completed', 'Completed'),
    )      

    DEPT_CHOICES = [
        ('CSE', 'Computer Science and Engineering'),
        ('ECE', 'Electronics and Communication Engineering'),
        ('ME', 'Mechanical Engineering'),
        ('SM', 'Smart Manufacturing'),
        ('Design', 'Design'),
        ('NS', 'Natural Sciences'),
        ('Liberal Arts', 'Liberal Arts'),
        ('none', 'None Of The Above'),
    ]

    pid = models.AutoField(primary_key=True)
    name= models.CharField(max_length=600)
    pi_id=models.CharField(max_length=150)
    pi_name=models.CharField(max_length=150)
    access = models.CharField(max_length=10, choices=ACCESS_SPECIFIERS, default='Co')
    type= models.CharField(max_length=50, choices=PROJECT_TYPES)
    dept=models.CharField(max_length=50, choices=DEPT_CHOICES)
    category=models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    sponsored_agency= models.CharField(max_length=500)
    scheme = models.CharField(max_length=300, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    duration = models.IntegerField(default=0)
    submission_date = models.DateField(default=datetime.now().date())
    total_budget=models.IntegerField(default=0)
    sanction_date=models.DateField(null=True, blank=True)
    sanctioned_amount = models.IntegerField(default=0)
    start_date=models.DateField(null=True, blank=True)
    initial_amount = models.IntegerField(default=0)
    file=models.FileField(upload_to="RSPC/", null=True, blank=True)
    registration_form=models.FileField(upload_to="RSPC/", null=True, blank=True)
    status= models.CharField(max_length=50, choices=STATUS_CHOICES)
    end_report=models.FileField(upload_to="RSPC/", null=True, blank=True)
    end_approval=models.CharField(max_length=50, choices=STATUS_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.pid})"
    class Meta:
        ordering = ['-pid']

class budget(models.Model):
    pid = models.OneToOneField(projects, on_delete=models.CASCADE, related_name="budgets")
    manpower = ArrayField(models.IntegerField(), default=list)       # Year-wise manpower
    travel = ArrayField(models.IntegerField(), default=list)         # Year-wise travel
    contingency = ArrayField(models.IntegerField(), default=list)    # Year-wise contingency
    consumables = ArrayField(models.IntegerField(), default=list)    # Year-wise consumables
    equipments = ArrayField(models.IntegerField(), default=list) 
    overhead = models.IntegerField(default=0)
    current_funds = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self):
        return f"Budget Year {self.year} for {self.pid.name}"


class expenditure(models.Model):
    EXPENDITURE_TYPES = (
        ('Tangible', 'Physical Item'),
        ('Non-tangible', 'Non-tangible Resource'),
    )
    APPROVAL_CHOICES = (
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Pending' , 'Pending')
    )
    id = models.AutoField(primary_key=True)
    file_id=models.IntegerField(default=0)
    pid=models.ForeignKey(projects, on_delete=models.CASCADE)
    exptype = models.CharField(max_length=50, choices=EXPENDITURE_TYPES)
    item = models.CharField(max_length=300)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    lastdate = models.DateField(null=True, blank=True)
    mode = models.CharField(max_length=50)
    inventory = models.CharField(max_length=50)
    desc = models.TextField(null=True, blank=True)
    file = models.FileField( null=True, blank=True)
    approval= models.CharField(max_length=50, choices=APPROVAL_CHOICES)

    def clean(self):
        if self.cost <= 0:
            raise ValidationError('Estimated cost must be greater than zero')

        if self.lastdate != '' and self.lastdate < datetime.datetime.now().date():
            raise ValidationError('Last date must not be a past date')
        
    def __str__(self):
        return f"{self.item} ({self.exptype})"

class staff_positions(models.Model):
    spid = models.AutoField(primary_key=True)
    pid = models.OneToOneField(projects, on_delete=models.CASCADE)
    positions = models.JSONField()
    incumbents = models.JSONField()


class staff(models.Model):
    BOOLEAN_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]
    TYPE_CHOICES = [
        ('Research Associate', 'Research Associate'),
        ('Senior Research Fellow', 'Senior Research Fellow'),
        ('Junior Research Fellow', 'Junior Research Fellow'),
        ('Supporting Staff', 'Supporting Staff'),
        ('Project Trainee', 'Project Trainee'),
    ]

    APPROVAL_CHOICES = [
        ('Approved', 'Approved'),
        ('RSPC Approval', 'RSPC Approval'),
        ('HoD Forward', 'HoD Forward'),
        ('Hiring', 'Hiring'),
        ('Pending' , 'Pending'),
        ('Committee Approval', 'Committee Approval'),
    ]

    sid = models.AutoField(primary_key=True)
    pid=models.ForeignKey(projects, on_delete=models.CASCADE)
    person = models.CharField(max_length=300, null=True, blank=True)
    uname = models.CharField(max_length=150, null=True, blank=True)
    biodata_number = models.IntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)

    duration = models.IntegerField(default=0)
    eligibility = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Supporting Staff')
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    has_funds = models.CharField(max_length=10, choices=BOOLEAN_CHOICES, default='Yes')
    post_on_website = models.FileField(upload_to="RSPC/", null=True, blank=True)
    submission_date = models.DateField(default=datetime.now().date())
    interview_date = models.DateField(default=datetime.now().date())
    test_date = models.DateField(default=datetime.now().date())
    test_mode = models.CharField(max_length=100, default='Written')
    interview_place = models.CharField(max_length=100, default='IIITDM Jabalpur')
    selection_committee = models.JSONField(default={})

    candidates_applied = models.IntegerField(null=True, blank=True)
    candidates_called = models.IntegerField(null=True, blank=True)
    candidates_interviewed = models.IntegerField(null=True, blank=True)
    final_selection = ArrayField(models.JSONField(), default=list)
    waiting_list = ArrayField(models.JSONField(), default=list)
    biodata_final = ArrayField(models.CharField(max_length=500), default=list)
    biodata_waiting = ArrayField(models.CharField(max_length=500), default=list)
    ad_file = models.FileField(upload_to="RSPC/", null=True, blank=True)
    comparative_file = models.FileField(upload_to="RSPC/", null=True, blank=True)
    approval= models.CharField(max_length=50, choices=APPROVAL_CHOICES)
    gave_verdict = ArrayField(models.CharField(max_length=150), default=list)
    current_approver = models.CharField(max_length=150, null=True, blank=True)

    joining_report = models.FileField(upload_to="RSPC/", null=True, blank=True)
    doc_approval= models.CharField(max_length=50, choices=APPROVAL_CHOICES, null=True, blank=True)
    salary_per_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    id_card = models.FileField(upload_to="RSPC/", null=True, blank=True)

    def clean(self):
        if self.deadline <= self.startdate:
            raise ValidationError('End date must be after the start date.')
        if self.salary < 0:
            raise ValidationError('Stipend must be atleast zero')

    def __str__(self):
        return f"{self.person} ({self.uname}) - {self.designation}"

    

# class requests(models.Model):
#     APPROVAL_CHOICES = [
#     ('Approved', 'Approved'),
#     ('Rejected', 'Rejected'),
#     ('Pending' , 'Pending')
#     ]
#     REQUEST_TYPES = [
#     ('Expenditure', 'Expenditure'),
#     ('Staff', 'Staff'),
#     ]
#     id=models.AutoField(primary_key=True)
#     pid= models.ForeignKey(projects, on_delete=models.CASCADE)
#     file_id=models.IntegerField()  
#     request_type=models.CharField(max_length=50, choices=REQUEST_TYPES)
#     rid=models.IntegerField()
#     subject=models.CharField(max_length=300)
#     requestor=models.CharField(max_length=150)
#     holder=models.CharField(max_length=150)
#     approval= models.CharField(max_length=50, choices=APPROVAL_CHOICES) 

#     def __str__(self):
#         return f"{self.pid} ({self.request_type}) - {self.rid}"

#     class Meta:
#         ordering = ['-id']


    
class project_access(models.Model):
    aid=models.AutoField(primary_key=True)
    pid= models.ForeignKey(projects, on_delete=models.CASCADE, related_name="co_pis")
    type = models.CharField(max_length=10)
    copi_id = models.CharField(max_length=150)
    affiliation = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return f"Co-PI for {self.pid.name}"  
    class Meta:
        ordering = ['-pid']
    
    
    
    

    
