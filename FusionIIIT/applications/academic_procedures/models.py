import datetime

from django.db import models

from applications.academic_information.models import Course
from applications.globals.models import Student

# Create your models here.


class Register(models.Model):
    r_id = models.IntegerField(primary_key=True)
    course_id = models.ForeignKey(Course)
    year = models.IntegerField(max_length=4, default=datetime.datetime.now().year)
    student_id = models.ForeignKey(Student)

    class Meta:
        db_table = 'Register'

    def __str__(self):
        return self.r_id
