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


class ResearchGroup(models.Model):
    name = models.CharField(max_length=120)
    faculty_under_group = models.ManyToManyField(User,related_name="allfaculty")
    students_under_group = models.ManyToManyField(User,related_name="allstudents")
    description = models.TextField()

    def _str_(self):
        return str(self.name)


class ResearchProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    ptype = models.CharField(max_length=100, default="Research")
    pi = models.CharField(max_length=1000, default=" ")
    co_pi = models.CharField(max_length=1500, default=" ")
    title = models.TextField(max_length=5000, default=" ")
    funding_agency = models.CharField(max_length=250, default=" ", null=True)
    financial_outlay = models.CharField(max_length=150, default=" ", null=True)
    STATUS_TYPE_CHOICES = (
        ('Awarded', 'Awarded'),
        ('Submitted', 'Submitted'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed')
    )
    status = models.CharField(max_length = 10, choices = STATUS_TYPE_CHOICES)
    start_date = models.DateField(null=True, blank=True)
    finish_date = models.DateField(null=True, blank=True)
    date_submission = models.DateField(null=True, blank=True)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)

    def __str__(self):
        return 'PF No.: {}   pi: {}  title: {}'.format(self.pf_no,self.pi, self.title)

class ConsultancyProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    consultants = models.CharField(max_length=150)
    title = models.CharField(max_length=1000)
    client = models.CharField(max_length=1000)
    financial_outlay = models.IntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    duration = models.CharField(max_length=500, null=True, blank=True)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)
    STATUS_TYPE_CHOICES = (
        ('Completed', 'Completed'),
        ('Submitted', 'Submitted'),
        ('Ongoing', 'Ongoing')
    )
    status = models.CharField(default = 'Ongoing', max_length = 10, choices = STATUS_TYPE_CHOICES, null=True, blank=True)
    remarks = models.CharField(max_length=1000, null=True, blank=True)
    
    def __str__(self):
        return 'PF No.: {}  Consultants: {}'.format(self.pf_no, self.consultants)

class TechTransfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    details = models.CharField(max_length=500, default=" ")
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)
    start_date = models.DateField(null=True,blank=True)
    end_date = models.DateField(null=True,blank=True)

    def __str__(self):
        return 'PF No.: {}   Details: {}'.format(self.pf_no, self.details)