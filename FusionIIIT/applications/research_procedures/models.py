# group 8 and group 9
from django.db import models
from django.db import models
from applications.globals.models import ExtraInfo
from django.contrib.auth.models import User

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
    title = models.CharField(max_length=50)
    ipd_form = models.FileField(null=True, blank=True)
    project_details = models.FileField(null=True, blank=True)
    ipd_form_file = models.TextField(null=True, blank=True)
    project_details_file = models.TextField(null=True, blank=True)
    status = models.CharField(choices=Constants.RESPONSE_TYPE, max_length=20, default='Pending')

    def _str_(self):
        return str(self.title)


class ResearchGroup(models.Model):
    name = models.CharField(max_length=50)
    faculty_under_group = models.ManyToManyField(User,related_name="allfaculty")
    students_under_group = models.ManyToManyField(User,related_name="allstudents")
    description = models.TextField()

    def _str_(self):
        return str(self.name)