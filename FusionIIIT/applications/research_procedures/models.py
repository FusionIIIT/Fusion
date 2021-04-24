# group 8 and group 9
from django.db import models
from applications.academic_information.models import Student
from django.db import models
from applications.globals.models import ExtraInfo

class Constants:
    RESPONSE_TYPE = (
        ('Approved', 'Approved'),
        ('Disapproved', 'Disapproved'),
        ('Pending' , 'Pending')
    )

class Patent(models.Model):
    application_id = models.AutoField(primary_key=True)
    faculty_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    ipd_form = models.FileField(null=True)
    project_details = models.FileField(null=True)
    file1=models.TextField(null=True)
    file2=models.TextField(null=True)
    status = models.CharField(choices=Constants.RESPONSE_TYPE, max_length=20, default='Pending')

    def _str_(self):
        return str(self.title)
