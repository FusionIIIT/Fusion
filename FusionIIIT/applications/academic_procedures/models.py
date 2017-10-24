import datetime

from django.db import models

from applications.academic_information.models import Course, Student
from applications.globals.models import ExtraInfo, Faculty

# Create your models here.


class Constants:
    SEM_CHOICES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
    )


class Register(models.Model):
    r_id = models.IntegerField(primary_key=True)
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    year = models.IntegerField(default=datetime.datetime.now().year)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.IntegerField()

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


class FinalRegistrations(models.Model):
    reg_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    semester = models.IntegerField()
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    registration = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)
