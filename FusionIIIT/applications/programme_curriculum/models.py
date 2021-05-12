from django.db import models
from django import forms
import datetime
from django.utils import timezone
from django.db.models.fields import IntegerField, PositiveIntegerField
from django.db.models import CheckConstraint, Q, F
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


# Create your models here.

PROGRAMME_CATEGORY_CHOICES = [
    ('UG', 'Undergraduate'),
    ('PG', 'Postgraduate'),
    ('PHD', 'Doctor of Philosophy')
]

COURSESLOT_TYPE_CHOICES = [
    ('Professional Core', 'Professional Core'),
    ('Professional Elective', 'Professional Elective'),
    ('Professional Lab', 'Professional Lab'),
    ('Engineering Science', 'Engineering Science'),
    ('Natural Science', 'Natural Science'),
    ('Humanities', 'Humanities'),
    ('Design', 'Design'),
    ('Manufacturing', 'Manufacturing'),
    ('Management Science', 'Management Science'),
    ('Project', 'Project'),
    ('Optional', 'Optional'),
    ('Others', 'Others')
]

class Programme(models.Model):
    category = models.CharField(max_length=3, choices=PROGRAMME_CATEGORY_CHOICES, null=False, blank=False)
    name = models.CharField(max_length=70, null=False, unique=True, blank=False)
    programme_begin_year = models.PositiveIntegerField(default=datetime.date.today().year, null=False)

    def __str__(self):
        return str(self.category + " - "+ self.name)

    @property
    def curriculums(self):
        return Curriculum.objects.filter(programme=self.id)

    @property
    def get_discipline_objects(self):
        return Discipline.objects.filter(programmes=self.id)


class Discipline(models.Model):
    name = models.CharField(max_length=100, null=False, unique=True, blank=False)
    acronym = models.CharField(max_length=10, null=False, default="", blank=False)
    programmes = models.ManyToManyField(Programme, blank=True)    
    
    def __str__(self):
        return str(self.name) + " " + str(self.acronym)

    @property
    def batches(self):
        return Batch.objects.filter(discipline=self.id)
        

class Curriculum(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    version = models.PositiveIntegerField(default=1, null=False)
    working_curriculum = models.BooleanField(default=True, null=False)
    no_of_semester = models.PositiveIntegerField(default=1, null=False)
    min_credit = models.PositiveIntegerField(default=0, null=False)

    class Meta:
        unique_together = ('name', 'version',)
    
    def __str__(self):
        return str(self.name + " v" + str(self.version))

    @property
    def batches(self):
        return Batch.objects.filter(curriculum=self.id)


    @property
    def semesters(self):
        return Semester.objects.filter(curriculum=self.id).order_by('semester_no')



class Semester(models.Model):
    curriculum = models.ForeignKey(Curriculum, null=False, on_delete=models.CASCADE)
    semester_no = models.PositiveIntegerField(null=False)
    instigate_semester = models.BooleanField(default=False, null=True)
    start_semester = models.DateField(blank=True, null=True)
    end_semester = models.DateField(blank=True, null=True)
    semester_info = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('curriculum', 'semester_no',)
    
    def __str__(self):
        return str(Curriculum.__str__(self.curriculum) + ", sem-" + str(self.semester_no))

    @property
    def courseslots(self):
        return CourseSlot.objects.filter(semester=self.id).order_by("id")


class Course(models.Model):
    code = models.CharField(max_length=10, null=False, unique=True, blank=False)
    name = models.CharField(max_length=100, null=False, unique=True, blank=False)
    credit = models.PositiveIntegerField(default=0, null=False, blank=False)
    lecture_hours = PositiveIntegerField(null=True, )
    tutorial_hours = PositiveIntegerField(null=True)
    pratical_hours = PositiveIntegerField(null=True)
    discussion_hours = PositiveIntegerField(null=True)
    project_hours = PositiveIntegerField(null=True)
    pre_requisits = models.TextField(null=True, blank=True)
    pre_requisit_courses = models.ManyToManyField('self', blank=True)
    syllabus = models.TextField()
    percent_quiz_1 = models.PositiveIntegerField(default=10, null=False, blank=False)
    percent_midsem = models.PositiveIntegerField(default=20, null=False, blank=False)
    percent_quiz_2 = models.PositiveIntegerField(default=10, null=False, blank=False)
    percent_endsem = models.PositiveIntegerField(default=30, null=False, blank=False)
    percent_project = models.PositiveIntegerField(default=15, null=False, blank=False)
    percent_lab_evaluation = models.PositiveIntegerField(default=10, null=False, blank=False)
    percent_course_attendance = models.PositiveIntegerField(default=5, null=False, blank=False)
    ref_books = models.TextField()
    working_course = models.BooleanField(default=True)
    disciplines = models.ManyToManyField(Discipline, blank=True)
    
    class Meta:
        unique_together = ('code', 'name',)        
    
    def __str__(self):
        return str(self.code + " - " +self.name)

    @property
    def courseslots(self):
        return CourseSlot.objects.filter(courses=self.id)


class Batch(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    discipline = models.ForeignKey(Discipline, null=False, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(default=datetime.date.today().year, null=False)
    curriculum = models.ForeignKey(Curriculum, null=True, blank=True, on_delete=models.SET_NULL)
    running_batch = models.BooleanField(default=True)

    class Meta:
        unique_together = ('name', 'discipline', 'year',)

    def __str__(self):
        return str(self.name) + " " + str(self.discipline.acronym) + " " + str(self.year)

class CourseSlot(models.Model):
    semester = models.ForeignKey(Semester, null=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=False, blank=False)
    type = models.CharField(max_length=70, choices=COURSESLOT_TYPE_CHOICES, null=False)
    course_slot_info = models.TextField(null=True)
    courses = models.ManyToManyField(Course, blank=True)
    duration = models.PositiveIntegerField(default=1)
    min_registration_limit = models.PositiveIntegerField(default = 0)
    max_registration_limit = models.PositiveIntegerField(default = 1000)


    def __str__(self):
        return str(Semester.__str__(self.semester) + ", " + self.name)

    class Meta:
        unique_together = ('semester', 'name', 'type')

    @property
    def for_batches(self):
        return ((Semester.objects.get(id=self.semester.id)).curriculum).batches