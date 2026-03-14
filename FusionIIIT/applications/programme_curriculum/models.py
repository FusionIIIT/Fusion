from django.db import models
from django import forms
import datetime
import json
from django.utils import timezone
from django.db.models.fields import IntegerField, PositiveIntegerField
from django.db.models import CheckConstraint, Q, F
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from applications.globals.models import ExtraInfo,Faculty
from django.core.validators import MinValueValidator, MaxValueValidator, DecimalValidator
from applications.globals.models import (DepartmentInfo, Designation,
                                         ExtraInfo, Faculty, HoldsDesignation)
from django.contrib.auth.models import User

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
    ('Open Elective', 'Open Elective'),
    ('Swayam', 'Swayam'),
    ('Project', 'Project'),
    ('Optional', 'Optional'),
    ('Backlog', 'Backlog'),
    ('Others', 'Others')
]

BATCH_NAMES = [
    ('B.Tech', 'B.Tech'),
    ('M.Tech', 'M.Tech'),
    ('M.Tech AI & ML', 'M.Tech AI & ML'),
    ('M.Tech Data Science', 'M.Tech Data Science'),
    ('M.Tech Communication and Signal Processing', 'M.Tech Communication and Signal Processing'),
    ('M.Tech Nanoelectronics and VLSI Design', 'M.Tech Nanoelectronics and VLSI Design'),
    ('M.Tech Power & Control', 'M.Tech Power & Control'),
    ('M.Tech Design', 'M.Tech Design'),
    ('M.Tech CAD/CAM', 'M.Tech CAD/CAM'),
    ('M.Tech Manufacturing and Automation', 'M.Tech Manufacturing and Automation'),
    ('B.Des', 'B.Des'),
    ('M.Des', 'M.Des'),
    ('Phd', 'Phd')
]

VERSION_BUMP_CHOICES = [
    ('NONE', 'No Version Bump'),
    ('PATCH', 'Patch (0.0.1)'),
    ('MINOR', 'Minor (0.1.0)'),
    ('MAJOR', 'Major (1.0.0)'),
]

class CourseAuditLog(models.Model):
    """Store audit trail for all course changes"""
    
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=20, choices=[
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete')
    ], default='UPDATE')
    old_values = models.JSONField(null=True, blank=True)  # Store old field values
    new_values = models.JSONField(null=True, blank=True)  # Store new field values
    changed_fields = models.JSONField(default=list)  # List of field names that changed
    version_bump_type = models.CharField(max_length=10, choices=VERSION_BUMP_CHOICES, default='NONE')
    old_version = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    new_version = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    admin_override = models.BooleanField(default=False)  # True if admin manually decided version bump
    reason = models.TextField(blank=True)  # Optional reason for changes
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.course.code} - {self.action} by {self.user.username} at {self.timestamp}"


class Programme(models.Model):
    """Store programme details"""

    category = models.CharField(
        max_length=3, choices=PROGRAMME_CATEGORY_CHOICES, null=False, blank=False)
    name = models.CharField(max_length=70, null=False,
                            unique=True, blank=False)
    programme_begin_year = models.PositiveIntegerField(
        default=datetime.date.today().year, null=False)

    def __str__(self):
        return str(self.category + " - " + self.name)

    @property
    def curriculums(self):
        return Curriculum.objects.filter(programme=self.id)

    @property
    def get_discipline_objects(self):
        return Discipline.objects.filter(programmes=self.id)


class Discipline(models.Model):
    """Store discipline details"""

    name = models.CharField(max_length=100, null=False,
                            unique=True, blank=False)
    acronym = models.CharField(
        max_length=10, null=False, default="", blank=False)
    programmes = models.ManyToManyField(Programme, blank=True)

    def __str__(self):
        return str(self.name) + " " + str(self.acronym)

    @property
    def batches(self):
        return Batch.objects.filter(discipline=self.id).order_by('year')


class Curriculum(models.Model):
    """Store curriculum details"""
    
    programme = models.ForeignKey(
        Programme, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    version = models.DecimalField(
    max_digits=5, 
    decimal_places=1,  
    default=1.0, 
    validators=[MinValueValidator(1.0), DecimalValidator(max_digits=5, decimal_places=1)])
    working_curriculum = models.BooleanField(default=True, null=False)
    no_of_semester = models.PositiveIntegerField(default=1, null=False)
    min_credit = models.PositiveIntegerField(default=0, null=False)
    latest_version = models.BooleanField(default=True)

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
    """Store semester details"""
    
    curriculum = models.ForeignKey(
        Curriculum, null=False, on_delete=models.CASCADE)
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
    """Store course details"""
    
    code = models.CharField(max_length=10, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    version = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=1.0,
        validators=[MinValueValidator(1.0), DecimalValidator(max_digits=5, decimal_places=1)])
    credit = models.PositiveIntegerField(default=0, null=False, blank=False)
    lecture_hours = PositiveIntegerField(null=True, )
    tutorial_hours = PositiveIntegerField(null=True)
    pratical_hours = PositiveIntegerField(null=True)
    discussion_hours = PositiveIntegerField(null=True)
    project_hours = PositiveIntegerField(null=True)
    pre_requisits = models.TextField(null=True, blank=True)
    pre_requisit_courses = models.ManyToManyField('self', blank=True)
    syllabus = models.TextField()
    percent_quiz_1 = models.PositiveIntegerField(
        default=10, null=False, blank=False)
    percent_midsem = models.PositiveIntegerField(
        default=20, null=False, blank=False)
    percent_quiz_2 = models.PositiveIntegerField(
        default=10, null=False, blank=False)
    percent_endsem = models.PositiveIntegerField(
        default=30, null=False, blank=False)
    percent_project = models.PositiveIntegerField(
        default=15, null=False, blank=False)
    percent_lab_evaluation = models.PositiveIntegerField(
        default=10, null=False, blank=False)
    percent_course_attendance = models.PositiveIntegerField(
        default=5, null=False, blank=False)
    ref_books = models.TextField()
    working_course = models.BooleanField(default=True)
    disciplines = models.ManyToManyField(Discipline, blank=True)
    latest_version = models.BooleanField(default=True)
    max_seats = models.IntegerField(default=90)
    class Meta:
        unique_together = ('code', 'version')

    def __str__(self):
        return str(self.code + " - " + self.name+"- v"+str(self.version))

    @property
    def courseslots(self):
        return CourseSlot.objects.filter(courses=self.id)


class Batch(models.Model):
    """Store batch details"""

    name = models.CharField(choices=BATCH_NAMES,
                            max_length=50, null=False, blank=False)
    discipline = models.ForeignKey(
        Discipline, null=False, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(
        default=datetime.date.today().year, null=False)
    curriculum = models.ForeignKey(
        Curriculum, null=True, blank=True, on_delete=models.SET_NULL)
    curriculum_options = models.JSONField(null=True, blank=True)
    running_batch = models.BooleanField(default=True)
    total_seats = models.PositiveIntegerField(default=60, null=False, blank=False)

    class Meta:
        unique_together = ('name', 'discipline', 'year',)

    def __str__(self):
        return str(self.name) + " " + str(self.discipline.acronym) + " " + str(self.year)


class CourseSlot(models.Model):
    """Store course slot details"""
    
    semester = models.ForeignKey(
        Semester, null=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=False, blank=False)
    type = models.CharField(
        max_length=70, choices=COURSESLOT_TYPE_CHOICES, null=False)
    course_slot_info = models.TextField(null=True)
    courses = models.ManyToManyField(Course, blank=True)
    duration = models.PositiveIntegerField(default=1)
    min_registration_limit = models.PositiveIntegerField(default=0)
    max_registration_limit = models.PositiveIntegerField(default=1000)

    def __str__(self):
        return str(Semester.__str__(self.semester) + ", " + self.name)

    class Meta:
        unique_together = ('semester', 'name', 'type')

    @property
    def for_batches(self):
        return ((Semester.objects.get(id=self.semester.id)).curriculum).batches


class CourseInstructor(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor_id = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    year = models.IntegerField(default=datetime.date.today().year, null=False)
    SEMESTER_TYPE_CHOICES = [
        ("Odd Semester", "Odd Semester"),
        ("Even Semester", "Even Semester"),
        ("Summer Semester", "Summer Semester"),
    ]
    semester_type = models.CharField(
        max_length=20,
        choices=SEMESTER_TYPE_CHOICES,
        null=True
    )

    class Meta:
        unique_together = ('course_id', 'instructor_id', 'year', 'semester_type')

    @property
    def academic_year(self):
        """Returns academic year in format 'YYYY-YY'"""
        if self.semester_type == "Even Semester":
            start_year = self.year - 1
            end_year = self.year
        else:
            start_year = self.year
            end_year = self.year + 1

        return f"{start_year}-{str(end_year)[-2:]}"


class NewProposalFile(models.Model):
    
    uploader = models.CharField(max_length=100, null=False, blank=False)
    designation = models.CharField(max_length=100, null=False, blank=False)
    code = models.CharField(max_length=10, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    credit = models.PositiveIntegerField(default=3, null=False, blank=False)
    lecture_hours = PositiveIntegerField(default=3, null=True, )
    tutorial_hours = PositiveIntegerField(default=0, null=True)
    pratical_hours = PositiveIntegerField(default=0, null=True)
    discussion_hours = PositiveIntegerField(default=0, null=True)
    project_hours = PositiveIntegerField(default=0, null=True)
    pre_requisits = models.TextField(null=True, blank=True)
    pre_requisit_courses = models.ManyToManyField(Course, blank=True)
    syllabus = models.TextField()
    max_seats = models.IntegerField(default=90)
    percent_quiz_1 = models.PositiveIntegerField(
        default=10, null=False, blank=False)
    percent_midsem = models.PositiveIntegerField(
        default=20, null=False, blank=False)
    percent_quiz_2 = models.PositiveIntegerField(
        default=10, null=False, blank=False)
    percent_endsem = models.PositiveIntegerField(
        default=30, null=False, blank=False)
    percent_project = models.PositiveIntegerField(
        default=15, null=False, blank=False)
    percent_lab_evaluation = models.PositiveIntegerField(
        default=10, null=False, blank=False)
    percent_course_attendance = models.PositiveIntegerField(
        default=5, null=False, blank=False)
    ref_books = models.TextField()
    subject = models.CharField(max_length=100, null=True, blank=False)
    description = models.CharField(max_length=400, null=True, blank=False)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_update = models.BooleanField(default=False)
    is_archive = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('code', 'uploader', 'name')
    
    def __str__(self):
        return str(self.uploader + " - " + self.designation + " - " + self.code + " - " + self.name)


class Proposal_Tracking(models.Model):

    file_id = models.CharField(max_length=100, null=False, blank=False)
    current_id = models.CharField(max_length=100, null=False, blank=False)
    current_design = models.CharField(max_length=100, null=False, blank=False)
    receive_id = models.ForeignKey(User, blank=False, on_delete=models.CASCADE)
    receive_design = models.ForeignKey(Designation, blank=False, on_delete=models.CASCADE)
    disciplines = models.ForeignKey(Discipline, blank=False, on_delete=models.CASCADE)
    receive_date = models.DateTimeField(auto_now_add=True)
    forward_date = models.DateTimeField(auto_now_add=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    is_added = models.BooleanField(default=False)
    is_submitted = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    sender_archive = models.BooleanField(default=False)
    receiver_archive = models.BooleanField(default=False)

    class Meta:
        unique_together = ('file_id', 'current_id', 'current_design', 'disciplines')

        