from django.db import models
from applications.globals.models import ExtraInfo

# Create your models here.


class Constants:
    TYPE = (
        ('restricted', 'restricted'),
        ('closed', 'closed')
    )

    ATTEND_CHOICES = (
        ('present', 'present'),
        ('absent', 'absent')
    )


class Course(models.Model):
    course_id = models.CharField(max_length=100, unique=True)
    course_name = models.CharField(max_length=100)
    sem = models.IntegerField() 
    credits = models.IntegerField()

    class Meta:
        db_table = 'Course'
        unique_together = ('course_id', 'course_name','sem')

    def __str__(self):
        return self.course_name


class Meeting(models.Model):
    venue = models.CharField(max_length=50)
    date = models.DateField()
    time = models.CharField(max_length=20)
    agenda = models.TextField()
    minutes_file = models.CharField(max_length=40)

    class Meta:
        db_table = 'Meeting'

    def __str__(self):
        return self.agenda


class Calendar(models.Model):
    from_date = models.DateField()
    to_date = models.DateField()
    description = models.CharField(max_length=40)

    class Meta:
        db_table = 'Calendar'

    def __str__(self):
        return self.description


class Holiday(models.Model):
    holiday_date = models.DateField()
    holiday_type = models.CharField(max_length=30, choices=Constants.TYPE),
    holiday_name = models.CharField(max_length=40)

    class Meta:
        db_table = 'Holiday'

    def __str__(self):
        return self.holiday_name


class Grades(models.Model):
    grade_id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(ExtraInfo)
    course_id = models.ForeignKey(Course)
    sem = models.IntegerField()
    Grade = models.CharField(max_length=4)

    class Meta:
        db_table = 'Grades'

    def __str__(self):
        return self.grade_id


class Student_attendance(models.Model):
    attend_id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(ExtraInfo)
    course_id = models.ForeignKey(Course)
    attend = models.CharField(max_length=6, choices=Constants.ATTEND_CHOICES)
    date = models.DateField()

    class Meta:
        db_table = 'Student_attendance'

    def __self__(self):
        return self.date


class Instructor(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Instructor'
        unique_together = ('course_id', 'instructor_id')

    def __self__(self):
        return self.course_id


class Spi(models.Model):
    sem = models.IntegerField()
    student_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    spi = models.IntegerField()

    class Meta:
        db_table = 'Spi'
        unique_together = ('student_id', 'sem')

    def __self__(self):
        return self.sem


class Timetable(models.Model):
    upload_date = models.DateTimeField(auto_now_add=True)
    time_table = models.CharField(max_length=20)

    class Meta:
        db_table = 'Timetable'


class Exam_timetable(models.Model):
    upload_date = models.DateField(auto_now_add=True)
    exam_time_table = models.CharField(max_length=20)

    class Meta:
        db_table = 'Exam_Timetable'