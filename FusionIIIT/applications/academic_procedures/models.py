import datetime

from django.db import models

from applications.academic_information.models import Course
from applications.globals.models import ExtraInfo, Faculty, Student

# Create your models here.


class Register(models.Model):
    r_id = models.IntegerField(primary_key=True)
    course_id = models.ForeignKey(Course)
    year = models.IntegerField(default=datetime.datetime.now().year)
    student_id = models.ForeignKey(Student)

    class Meta:
        db_table = 'Register'

    def __str__(self):
        return self.r_id


class Thesis(models.Model):
    reg_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    supervisor_id = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    topic = models.CharField(max_length=1000)

    class Meta:
        db_table = 'Thesis'

    def __str__(self):
        return self.topic & self.reg_id & self.student_id & self.supervisor_id
