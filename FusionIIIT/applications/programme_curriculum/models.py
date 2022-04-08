from django.db import models
from django import forms
import datetime
from django.utils import timezone
from django.db.models.fields import IntegerField, PositiveIntegerField
from django.db.models import CheckConstraint, Q, F
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from applications.globals.models import ExtraInfo

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
    ('Optional Elective', 'Optional Elective'),
    ('Project', 'Project'),
    ('Optional', 'Optional'),
    ('Others', 'Others')
]

BATCH_NAMES = [
    ('B.Tech', 'B.Tech'),
    ('M.Tech', 'M.Tech'),
    ('B.Des','B.Des'),
    ('M.Des','M.Des'),
    ('Phd', 'Phd')
]

class Programme(models.Model):
    '''
        Current Purpose : To store the details regardina a programme
        
        

        ATTRIBUTES :

        category(char) - to store the type of program(eg UG/PG)
        name(char) - name of the program(eg 'Btech  CSE' )
        program_begin_year(+ve Integer) -  to store since when the programme is being offered

        ! - the name attribute has ambiguous entries
    '''

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
    '''
        Current Purpose : To store the details regarding a discipline
        
        

        ATTRIBUTES :

        name(char) - to store the name of discipline(eg design, Computer science and engineering)
        acronym(char) - the short form of the discipline(eg : CSE)
        programmes(programme_curriculum.Programme) - to link a programme with the discipline(CSE in Btech, CSE in Mtech)

    '''


    name = models.CharField(max_length=100, null=False, unique=True, blank=False)
    acronym = models.CharField(max_length=10, null=False, default="", blank=False)
    programmes = models.ManyToManyField(Programme, blank=True)    
    
    def __str__(self):
        return str(self.name) + " " + str(self.acronym)

    @property
    def batches(self):
        return Batch.objects.filter(discipline=self.id).order_by('year')
        

class Curriculum(models.Model):
    '''
        Current Purpose : To store the details regarding a curriculum
        Curriculum definition : a set of all courses offered by the institute within a programme

        
        

        ATTRIBUTES :

        programmes(program_curriculum.Programme) - to link a program to a curriculum
        name(char) - to store the name of the curriculum
        version(positive Integer) - to store the version of a curriculum(used in cases of updating an existing curriculum)
        working_curriculum(Boolean) - to check whether the curriculum is currently in execution or not
        no_of_semester(Integer) - the number of semesters defined for the curriculum
        min_credit(Integer) - the minimum credits required for the curriculum
    '''
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
        return Batch.objects.filter(curriculum=self.id).order_by('year')


    @property
    def semesters(self):
        return Semester.objects.filter(curriculum=self.id).order_by('semester_no')



class Semester(models.Model):
    '''
        Current Purpose : To store the details regarding a semester
        

        
        

        ATTRIBUTES :

        curriculum(programme_curriculum.Curriculum) - to store the link for the associated curriculum details for the semester
        semester_no(int) - to store the semester number(format unclear)
        instigate_semester(boolean) - might be used to check whether the semester is currently in action
        start_semester(DateTime) - to store the start date of the semester
        end_semester(DateTime) - to store the end date of the semester

    '''
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
    '''
        Current Purpose : To store the details regarding a course
        

        
        

        ATTRIBUTES :

        code(char) -  the course code (eg CS3005)
        name(char) -  the name of the course(eg Machine Learning)
        credit(Integer) -  the credits defined for the course
        lecture_hours(integer) -  lecture hours defined for the course
        tutorial_hours(Integer) - tutorial hours defined for the course
        practical_hours(Integer)  - practical hours defined for the course
        discussion_hours(Integer) - discussion hours
        project_hours(Integer) - project hours
        pre_requisits(Boolean) -  denote whether  this course has prerequisites(courses that one should take before opting this )
        pre_requisit_courses(programme_curriculum.Course) - link to set of prerequisite courses
        syllabus(text) - syllabus described for the course
        percent_quiz_1(+ve int)  - defined weightage in marking
        percent_midsem(+ve int)  - defined weightage in marking
        percent_quiz_2(+ve int)  - defined weightage in marking
        percent_endsem (+ve int)  - defined weightage in marking
        percent_project(+ve int)  - defined weightage in marking
        percent_lab_evaluation (+ve int)  - defined weightage in marking
        percent_course_attendance (+ve int)  - defined weightage in marking
        ref_books(text) - reference books suggested for the course
        working_course(boolean) - to denote whether the course is currently in execution or not
        disciplines(programme_curriculum.Discipline) - to store which discipline is offering the course


    '''
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



    '''
        Current Purpose : To store the details regarding a batch(eg details of curriculum assigned for batch)
        

        
        

        ATTRIBUTES :

        name(char) -  to store the type of batch(eg Btech/Mtech/Phd, not nullable)
        discipline(programme_curriculum.Discipline) - to link the discipline for the batch[not nullable]
        year(+ve Integer) - to store the year of the batch(eg:2019 batch)
        curriculum(programme_curriculum.Curriculum) - reference to the curriculum for the batch(can be null)
        running_batch(Boolean) - to denote whether the batch is currently active or has graduated

    '''
    name = models.CharField(choices=BATCH_NAMES, max_length=50, null=False, blank=False)
    discipline = models.ForeignKey(Discipline, null=False, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(default=datetime.date.today().year, null=False)
    curriculum = models.ForeignKey(Curriculum, null=True, blank=True, on_delete=models.SET_NULL)
    running_batch = models.BooleanField(default=True)

    class Meta:
        unique_together = ('name', 'discipline', 'year',)

    def __str__(self):
        return str(self.name) + " " + str(self.discipline.acronym) + " " + str(self.year)

    
class CourseSlot(models.Model):
    '''
        Current Purpose : To store the details regarding a course slot 
            Course slot : is defined as per the curriculum for a programme to have specific type of courses 
                            for a given semester
        

        
        

        ATTRIBUTES :

        semester(programme_curriculum.Semester) - [not nullable] to denote link to the semester details for which the courseslot is made
        name(char) - [not nullable] the domain of the course[Professional Elective 1, IT Lab etc ]
        type(char) - [not nullable] the type of course(elective/ core/NS/)
        course slot_info - [can be null] stores textual info regarding course
        courses(programme_curriculum.Course) - the list of courses being floated for the slot(can be null)
        duration(integer) - might be to denote for how many semester will the course run for(eg PR's are run across 2 semesters)
        minimum_registration_limit(integer) - minimum students required for a course
        maximum_registration_limit(integer) - maximum students required for a course 

    '''
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

class CourseInstructor(models.Model):
      course_id = models.ForeignKey(Course, on_delete = models.CASCADE)
      instructor_id = models.ForeignKey(ExtraInfo, on_delete = models.CASCADE)
      batch_id = models.ForeignKey(Batch, on_delete=models.CASCADE, default=1)
      #change extra info to faculty(globals)

      class Meta:
          unique_together = ('course_id', 'instructor_id', 'batch_id')
      

      def __self__(self):
            return '{} - {}'.format(self.course_id, self.instructor_id)
        