from django.db import models
import datetime

from django.db.models.fields import IntegerField, PositiveIntegerField

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
    ('Management Science', 'Management Science')
]

class Programme(models.Model):
    category = models.CharField(max_length=3, choices=PROGRAMME_CATEGORY_CHOICES, null=False, blank=False)
    name = models.CharField(max_length=70, null=False, unique=True, blank=False)

    def __str__(self):
        return str(self.category + " - "+ self.name)

    def get_curriculums_objects(self):
        return Curriculum.objects.filter(programme=self.id)

class Discipline(models.Model):
    name = models.CharField(max_length=100, null=False, unique=True, blank=False)
    programmes = models.ManyToManyField(Programme)
    
    def __str__(self):
        return str(self.name)

    def get_programme_objects(self):
        return self.programmes.all()

class Curriculum(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    version = models.PositiveIntegerField(default=1, null=False)
    working_curriculum = models.BooleanField(default=True, null=False)
    no_of_semester = models.PositiveIntegerField(default=1, null=False)

    class Meta:
        unique_together = ('name', 'version',)
    
    def __str__(self):
        return str(self.name + " v" + str(self.version))

    def get_semesters_objects(self):
        return Semester.objects.filter(curriculum=self.id).order_by('semester_no')

class Semester(models.Model):
    curriculum = models.ForeignKey(Curriculum, null=False, on_delete=models.CASCADE)
    semester_no = models.PositiveIntegerField(null=False)

    class Meta:
        unique_together = ('curriculum', 'semester_no',)
    
    def __str__(self):
        return str(Curriculum.__str__(self.curriculum) + ", sem-" + str(self.semester_no))

    def get_courseslots_objects(self):
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
    syllabus = models.TextField()
    evaluation_schema = models.TextField()
    ref_books = models.TextField()
    
    class Meta:
        unique_together = ('code', 'name',)
    
    def __str__(self):
        return str(self.code + " - " +self.name)

class Batch(models.Model):
    name = models.CharField(max_length=50, null=False, unique=True, blank=False)
    discipline = models.ForeignKey(Discipline, null=False, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(default=datetime.date.today().year, null=False)
    curriculum = models.ForeignKey(Curriculum, null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('name', 'discipline', 'year',)

    def __str__(self):
        return str(self.name)

class CourseSlot(models.Model):
    semester = models.ForeignKey(Semester, null=False, on_delete=models.CASCADE)
    name = name = models.CharField(max_length=100, null=False, blank=False)
    type = models.CharField(max_length=70, choices=COURSESLOT_TYPE_CHOICES, null=False)
    for_batches = models.ManyToManyField(Batch)
    course_slot_info = models.TextField(null=True)
    courses = models.ManyToManyField(Course)

    def __str__(self):
        return str(Semester.__str__(self.semester) + ", " + self.name + ", id = " + str(self.id))

    def get_courses_objects(self):
        return self.courses.all()