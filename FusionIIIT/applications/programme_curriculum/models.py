from django.db import models
import datetime

from django.db.models.fields import IntegerField

# Create your models here.

class Programme_list(models.Model):
    category = models.CharField(max_length=100)
    name = models.charField(max_length=100)

class Curriculum_list(models.Model):
    programme_id = models.ForeignKey(Programme_list ,on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    batch_year = models.IntegerField(default=datetime.date.today().year)
    version = models.IntegerField(default=0)

class Semester_list(models.Model):
    curriculum_id = models.ForeignKey(Curriculum_list ,on_delete=models.CASCADE)
    semseter_no = models.IntegerField()

class Course_list(models.Model):
    semseter_id = models.ForeignKey(Semester_list ,on_delete=models.CASCADE)
    course_code = models.CharField(max_length=10)
    title = models.CharField(max_length=100)
    credits = models.IntegerField(default=0)
    contact_hours_L = IntegerField(default=0)
    contact_hours_T = IntegerField(default=0)
    contact_hours_C = IntegerField(default=0)
    syllabus = models.CharField(max_length=5000)
    evaluation_schema = models.CharField(max_length=1000)
    ref_books = models.CharField(max_length=2000)
