from django.db import models
from applications.academic_procedures.models import (course_registration)
from applications.academic_information.models import Course
from applications.programme_curriculum.models import Course as Courses, CourseInstructor, Batch
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
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE, default=1)
    course_year = models.IntegerField(default=2024)

    @property
    def working_year(self):
        return self.year.year

    def __str__(self):
        return f"{self.course_id} , {self.course_year}"


class grade(models.Model):
    student = models.CharField(max_length=20)
    curriculum = models.CharField(max_length=50)
    semester_id = models.CharField(max_length=10, default='')
    grade = models.CharField(max_length=5, default="B")

class ResultAnnouncement(models.Model):
    SEMESTER_TYPE_CHOICES = [
        ("Odd Semester", "Odd Semester"),
        ("Even Semester", "Even Semester"),
        ("Summer Semester", "Summer Semester"),
    ]
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    semester = models.PositiveIntegerField()
    semester_type = models.CharField(
        max_length=20,
        choices=SEMESTER_TYPE_CHOICES,
        null=True,
        blank=True,
    )
    announced = models.BooleanField(default=False)
    # True once the result is published via per-student selection. When True,
    # only students listed in PublishedResultStudent see their result; when
    # False the announcement is published for the whole batch (legacy).
    per_student_selection = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("batch", "semester", "semester_type")]

    def __str__(self):
        status = "Announced" if self.announced else "Not Announced"
        if self.semester_type == "Summer Semester":
            sem_label = f"Summer {self.semester // 2}"
        else:
            sem_label = f"Sem {self.semester}"
        return f"{self.batch.name} - {sem_label} - {status}"


class PublishedResultStudent(models.Model):
    """Per-student selection for a result announcement.

    When the academic admin publishes a result they can pick exactly which
    students of the batch are included. A row here means "this student's result
    for this announcement is published". If an announcement has no rows at all,
    it is treated as published for the whole batch (legacy behaviour).
    """

    announcement = models.ForeignKey(
        ResultAnnouncement,
        on_delete=models.CASCADE,
        related_name="published_students",
    )
    roll_no = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("announcement", "roll_no")]

    def __str__(self):
        return f"{self.announcement_id} - {self.roll_no}"


class Student_grades(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    semester = models.IntegerField(default=1)
    year = models.IntegerField(default=2016)
    roll_no = models.TextField(max_length=2000)
    grade = models.TextField(max_length=2000)
    batch = models.IntegerField(default=2021)
    remarks = models.CharField(max_length=500,null=True)
    verified = models.BooleanField(default=False) 
    reSubmit = models.BooleanField(default=True) 
    academic_year = models.CharField(max_length=9, null=True)
    
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
    # The offering (course+section+faculty) that produced this grade. Grade
    # submission is scoped to the offering's instructor, and this disambiguates
    # section-wise rows for the same course. Nullable for pre-feature rows.
    course_instructor = models.ForeignKey(CourseInstructor, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        # The table is still the one online_cms created; renaming it is a
        # separate change.
        db_table = 'online_cms_student_grades'
        # Transcripts, SPI/CPI and the grade reports read a student's grades by
        # roll number; without this each read scanned every grade row.
        indexes = [models.Index(fields=['roll_no'], name='student_grades_roll_no_idx')]

    def __str__(self):
        return '{} - {}'.format(self.pk, self.course_id)
