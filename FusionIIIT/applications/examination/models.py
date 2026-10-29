from django.db import models
from applications.academic_procedures.models import (course_registration)
from applications.online_cms.models import (Student_grades)
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


# ─── Seating Arrangement ─────────────────────────────────────────────────────

class ExamRoom(models.Model):
    """Classrooms / halls used for exams, with their seating capacity."""
    room_no = models.CharField(max_length=20, unique=True)
    seating_capacity = models.PositiveIntegerField(default=45)
    # cols: number of columns in the physical room layout
    # rows = ceil(seating_capacity / cols)
    cols = models.PositiveIntegerField(default=9, help_text="Number of columns in the room layout")
    block = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['room_no']

    def __str__(self):
        return f"{self.room_no} (cap: {self.seating_capacity}, {self.cols} cols)"


class SeatingArrangement(models.Model):
    """One row = one student assigned to a seat for a given exam slot."""
    TITLE_CHOICES = [
        ('midsem', 'Mid-Semester Examination'),
        ('endsem', 'End-Semester Examination'),
    ]
    SHIFT_CHOICES = [
        ('morning', 'Morning Shift'),
        ('evening', 'Evening Shift'),
        ('afternoon', 'Evening Shift'),
    ]
    PROGRAMME_CHOICES = [
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate'),
        ('PHD', 'PhD'),
        ('ALL', 'All'),
    ]

    exam_title = models.CharField(max_length=20, choices=TITLE_CHOICES)
    exam_date = models.DateField()
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    academic_year = models.CharField(max_length=10)
    programme_type = models.CharField(max_length=10, choices=PROGRAMME_CHOICES, default='ALL')
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=200)
    room_no = models.CharField(max_length=20)
    student_roll = models.CharField(max_length=20)
    student_name = models.CharField(max_length=200)
    seat_no = models.PositiveIntegerField()
    row_no = models.PositiveIntegerField(default=1)  # physical row in classroom (1-indexed)
    col_no = models.PositiveIntegerField(default=1)  # physical column in classroom (1-indexed)
    is_excluded = models.BooleanField(default=False)  # exclude from seating
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['exam_date', 'shift', 'room_no', 'seat_no']
        constraints = [
            models.UniqueConstraint(
                fields=['exam_date', 'shift', 'room_no', 'seat_no'],
                name='unique_seat_per_slot',
            )
        ]

    def __str__(self):
        return f"{self.exam_date} {self.shift} | {self.room_no} #{self.seat_no} | {self.student_roll}"
