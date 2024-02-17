from django.db import models
from applications.academic_procedures.models import (course_registration)
# Create your models here.


class hidden_grades(models.Model):
    student_id = models.CharField(max_length=20)
    course_id = models.CharField(max_length=50)
    semester_id = models.CharField(max_length=10)
    grade = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.student_id}, {self.course_id}"





class authentication(models.Model):
    authenticator_1 = models.BooleanField(default=False)
    authenticator_2 = models.BooleanField(default=False)
    authenticator_3 = models.BooleanField(default=False)
    year = models.DateField(auto_now_add=True)
    course = models.CharField(max_length=255, default="")

    @property
    def working_year(self):
        return self.year.year

    def __str__(self):
        return f"{self.course} , {self.working_year}"
    

class grade(models.Model):
    student = models.CharField(max_length=20)
    curriculum = models.CharField(max_length=50)
    semester_id = models.CharField(max_length=10)
    grade = models.CharField(max_length=5,default="B")

# class final_grades(models.Model):
#     student_id = models.CharField(max_length=20)
#     course_id = models.CharField(max_length=50)
#     semester_id = models.CharField(max_length=10)
#     grade = models.CharField(max_length=5,default="")

#     # def __str__(self):
#     #     return f"{self.student_id}, {self.course_id}"
