import datetime

from django.db import models

from applications.academic_information.models import Course, Student, Curriculum
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

    PaymentMode = (
        ('NEFT','NEFT'),
        ('RTGS','RTGS'),
        ('Bank Challan','Bank Challan')
        )

    BRANCH = (
        ('CSE','CSE'),
        ('ECE','ECE'),
        ('ME','ME'),
        ('Design','Design'),
        ('Common','Common'),
    )

    GRADE = (
        ('O','O'),
        ('A+','A+'),
        ('A','A'),
        ('B+','B+'),
        ('B','B'),
        ('C+','C+'),
        ('C','C'),
        ('D+','D+'),
        ('D','D'),
        ('F','F'),
        ('S','S'),
        ('X','X'),
    )


class Register(models.Model):
    r_id = models.IntegerField(primary_key=True)
    curr_id = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    year = models.IntegerField(default=datetime.datetime.now().year)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.IntegerField()

    class Meta:
        db_table = 'Register'

    def __str__(self):
        return str(self.curr_id)





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

###
#
#
#
#
#
#
class StudentRegistrationCheck(models.Model):
    student = models.ForeignKey(Student, on_delete = models.CASCADE)
    pre_registration_flag = models.BooleanField(default = False)
    final_registration_flag = models.BooleanField(default = False)
    semester = models.IntegerField(default=1)

    class Meta:
        db_table = 'StudentRegistrationCheck'
        

class InitialRegistrations(models.Model):
    curr_id = models.ForeignKey(Curriculum, on_delete = models.CASCADE)
    semester = models.IntegerField()
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    batch = models.IntegerField(default =datetime.datetime.now().year )

    class Meta:
        db_table = 'InitialRegistrations'


class FinalRegistrations(models.Model):
    curr_id = models.ForeignKey(Curriculum, on_delete = models.CASCADE)
    semester = models.IntegerField()
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    batch = models.IntegerField(default =datetime.datetime.now().year )
    verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'FinalRegistrations'


class Thesis(models.Model):
    reg_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    supervisor_id = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    topic = models.CharField(max_length=1000)

    class Meta:
        db_table = 'Thesis'

    def __str__(self):
        return str(self.topic) + " " + str(self.student_id)

class ThesisTopicProcess(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    research_area = models.CharField(max_length=50)
    thesis_topic = models.CharField(max_length = 1000)
    curr_id = models.ForeignKey(Curriculum, on_delete=models.CASCADE, null=True)
    supervisor_id = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='%(class)s_supervisor')
    co_supervisor_id = models.ForeignKey(Faculty, on_delete = models.CASCADE, related_name='%(class)s_co_supervisor', null = True)
    submission_by_student = models.BooleanField(default = False)
    pending_supervisor = models.BooleanField(default=True)
    member1 = models.ForeignKey(Faculty, on_delete = models.CASCADE,related_name='%(class)s_member1', null = True)
    member2 = models.ForeignKey(Faculty, on_delete = models.CASCADE, related_name='%(class)s_member2', null = True)
    member3 = models.ForeignKey(Faculty, on_delete = models.CASCADE, related_name='%(class)s_member3', null = True)
    approval_supervisor = models.BooleanField(default = False)
    forwarded_to_hod = models.BooleanField(default = False)
    pending_hod = models.BooleanField(default=True)
    approval_by_hod = models.BooleanField(default = False)
    date = models.DateField(default=datetime.datetime.now)

    class Meta:
        db_table = 'ThesisTopicProcess'

    def __str__(self):
        return str(self.thesis_topic) + " " + str(self.student_id)


class FeePayment(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.IntegerField(default= 1)
    batch = models.IntegerField(default= 2016)
    mode = models.CharField(max_length = 20, choices=Constants.PaymentMode)
    transaction_id = models.CharField(max_length = 40)

class TeachingCreditRegistration(models.Model):
    student_id = models.ForeignKey(Student, on_delete = models.CASCADE)
    curr_1 = models.ForeignKey(Curriculum, on_delete = models.CASCADE, related_name='%(class)s_curr1')
    curr_2 = models.ForeignKey(Curriculum, on_delete = models.CASCADE, related_name='%(class)s_curr2')
    curr_3 = models.ForeignKey(Curriculum, on_delete = models.CASCADE, related_name='%(class)s_curr3')
    curr_4 = models.ForeignKey(Curriculum, on_delete = models.CASCADE, related_name='%(class)s_curr4')
    req_pending = models.BooleanField(default = True)
    approved_course = models.ForeignKey(Curriculum, on_delete = models.CASCADE, related_name='%(class)s_approved_course', null = True)
    course_completion = models.BooleanField(default=False)
    supervisor_id = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='%(class)s_supervisor_id',null = True)
    class Meta:
        db_table = 'TeachingCreditRegistration'


class SemesterMarks(models.Model):
    student_id = models.ForeignKey(Student, on_delete = models.CASCADE)
    q1 = models.FloatField(default = None)
    mid_term = models.FloatField(default = None)
    q2 = models.FloatField(default = None)
    end_term = models.FloatField(default = None)
    other = models.FloatField(default = None)
    grade = models.CharField(max_length=5, choices=Constants.GRADE, null=True)
    curr_id = models.ForeignKey(Curriculum, on_delete=models.CASCADE)

    class Meta:
        db_table = 'SemesterMarks'


class MarkSubmissionCheck(models.Model):
    curr_id = models.ForeignKey(Curriculum)
    verified = models.BooleanField(default = False)
    submitted = models.BooleanField(default = False)
    announced = models.BooleanField(default = False)

    class Meta:
        db_table = 'MarkSubmissionCheck'
