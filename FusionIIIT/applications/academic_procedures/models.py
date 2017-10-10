# from django.db import models
import datetime

from django.db import models
from applications.globals.models import ExtraInfo, Faculty, Student
from applications.academic_information.models import *
class Register(models.Model):
    r_id=models.IntegerField(primary_key=True)
    course_id=models.ForeignKey(Course)
    semester = models.IntegerField(null=True)
    student_id=models.ForeignKey(Student)

    class Meta:
        db_table ='Register'

    def __str__(self):
        return str(self.r_id)
