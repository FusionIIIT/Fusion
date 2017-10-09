from django.db import models
from applications.globals.models import Student
from applications.academic_information.models import Course

import datetime

# Create your models here.

class Register(models.Model):

	r_id =  models.IntegerField(primary_key = True)
	course_id = models.ForeignKey(Course)
	year = models.IntegerField(max_length=4, default=datetime.datetime.now().year)
	student_id = models.ForeignKey(Student)
	
