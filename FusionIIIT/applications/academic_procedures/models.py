import datetime

from django.db import models

from applications.academic_information.models import Course, Student
from applications.globals.models import DepartmentInfo, ExtraInfo, Faculty


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

    MTechSpecialization = (
        ('Power and Control', 'Power and Control'),
        ('Microwave and Communication Engineering', 'Microwave and Communication Engineering'),
        ('Micro-nano Electronics', 'Micro-nano Electronics'),
        ('CAD/CAM', 'CAD/CAM'),
        ('Design', 'Design'),
        ('Manufacturing', 'Manufacturing'),
        ('CSE', 'CSE'),
        ('Mechatronics', 'Mechatronics'),
        ('MDes', 'MDes'),
        ('all', 'all')
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
        return str(self.course_id)


class Thesis(models.Model):
    reg_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    supervisor_id = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    topic = models.CharField(max_length=1000)

    class Meta:
        db_table = 'Thesis'

    def __str__(self):
        return str(self.topic) + " " + str(self.student_id)


class FinalRegistrations(models.Model):
    reg_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    semester = models.IntegerField()
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    registration = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class BranchChange(models.Model):
    c_id = models.AutoField(primary_key=True)
    branches = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE)
    user = models.ForeignKey(Student, on_delete=models.CASCADE)
    applied_date = models.DateField(default=datetime.datetime.now)

    def __str__(self):
        return str(self.user) + " " + str(self.branches)


class CoursesMtech(models.Model):
    c_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=30, choices=Constants.MTechSpecialization)

    def __str__(self):
        return str(self.c_id)


class MinimumCredits(models.Model):
    semester = models.IntegerField()
    credits = models.IntegerField()

    def __str__(self):
        return "Semester: " + str(self.semester)+" Credits:" + str(self.credits)
