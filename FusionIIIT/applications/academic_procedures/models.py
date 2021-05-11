import datetime

from django.db import models

from applications.academic_information.models import Course, Student, Curriculum
from applications.programme_curriculum.models import Course as Courses, Semester, CourseSlot
from applications.globals.models import DepartmentInfo, ExtraInfo, Faculty
from django.utils import timezone


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
    curr_id = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    year = models.IntegerField(default=datetime.datetime.now().year)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.IntegerField()

    class Meta:
        db_table = 'Register'
        unique_together = ['curr_id','student_id']

    def __str__(self):
        return '{} - {}'.format(self.student_id.id.user.username,self.curr_id.course_code)





class BranchChange(models.Model):
    c_id = models.AutoField(primary_key=True)
    branches = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE)
    user = models.ForeignKey(Student, on_delete=models.CASCADE)
    applied_date = models.DateField(default=datetime.datetime.now)

    def __str__(self):
        return str(self.user) + " " + str(self.branches)


class CoursesMtech(models.Model):
    c_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=40, choices=Constants.MTechSpecialization)

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

# THE THREE TABLES BELOW ARE OLD. PLEASE REFRAIN FROM USING THEM FURTHER.
# USE THE TABLES AT THE BOTTOM OF THE FILE INSTEAD.
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
    
    def __str__(self):
        return str(self.curr_id) + "-" + str(self.student_id)


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


# THIS IS AN OLD TABLE. PLEASE REFRAIN FROM USING IT.
# USE THE TABLE AT THE BOTTOM INSTEAD.
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
    curr_id = models.ForeignKey(Curriculum,on_delete=models.CASCADE)
    verified = models.BooleanField(default = False)
    submitted = models.BooleanField(default = False)
    announced = models.BooleanField(default = False)

    class Meta:
        db_table = 'MarkSubmissionCheck'


class Dues(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    mess_due = models.IntegerField()
    hostel_due = models.IntegerField()
    library_due = models.IntegerField()
    placement_cell_due = models.IntegerField()
    academic_due = models.IntegerField()

    class Meta:
        db_table = 'Dues'


class MessDue(models.Model):
    Month_Choices = [
        ('Jan', 'January'),
        ('Feb', 'Febuary'),
        ('Mar', 'March'),
        ('Apr', 'April'),
        ('May', 'May'),
        ('Jun', 'June'),
        ('Jul', 'July'),
        ('Aug', 'August'),
        ('Sep', 'September'),
        ('Oct', 'October'),
        ('Nov', 'November'),
        ('Dec', 'December'),

    ]

    Year_Choices = [
        (datetime.date.today().year, datetime.date.today().year),
        (datetime.date.today().year-1, datetime.date.today().year-1)
    ]
    paid_choice = [
        ('Stu_paid', 'Paid'),
        ('Stu_due' , 'Due')
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    month = models.CharField(max_length=10, choices=Month_Choices, null=False , blank=False)
    year = models.IntegerField(choices=Year_Choices)
    description = models.CharField(max_length=15,choices=paid_choice)
    amount = models.IntegerField()
    remaining_amount = models.IntegerField()
    



class Bonafide(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=50)
    purpose = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=15)
    enrolled_course = models.CharField(max_length=10)
    complaint_date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'Bonafide'

class AssistantshipClaim(models.Model):
    Month_Choices = [
        ('Jan', 'January'),
        ('Feb', 'Febuary'),
        ('Mar', 'March'),
        ('Apr', 'April'),
        ('May', 'May'),
        ('Jun', 'June'),
        ('Jul', 'July'),
        ('Aug', 'August'),
        ('Sep', 'September'),
        ('Oct', 'October'),
        ('Nov', 'November'),
        ('Dec', 'December'),

    ]

    Year_Choices = [
        (datetime.date.today().year, datetime.date.today().year),
        (datetime.date.today().year-1, datetime.date.today().year-1)
    ]

    Applicability_choices = [
        ('GATE', 'GATE'),
        ('NET', 'NET'),
        ('CEED', 'CEED'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add = True)  
    month = models.CharField(max_length=10, choices=Month_Choices, null=False , blank=False)
    year = models.IntegerField(choices=Year_Choices)
    bank_account = models.CharField(max_length=11)
    applicability = models.CharField(max_length=5, choices=Applicability_choices)
    ta_supervisor_remark = models.BooleanField(default=False)
    ta_supervisor = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='TA_SUPERVISOR')
    thesis_supervisor_remark = models.BooleanField(default=False)
    thesis_supervisor = models.ForeignKey(Faculty, on_delete=models.CASCADE,related_name='THESIS_SUPERVISOR')
    acad_approval = models.BooleanField(default=False)
    account_approval = models.BooleanField(default=False)
    stipend = models.IntegerField(default=0)

    class meta:
        db_table = 'AssistantshipClaim' 


class MTechGraduateSeminarReport(models.Model):

    Quality_of_work = [
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Satisfactory', 'Satisfactory'),
        ('Unsatisfactory' , 'Unsatisfactory'),
    ]
    

    Quantity_of_work = [
        ('Enough', 'Enough'),
        ('Just Sufficient', 'Just Sufficient'),
        ('Insufficient', 'Insufficient'),
    ]


    Grade = [
        ('A+', 'A+'),
        ('A', 'A'),
        ('B+', 'B+'),
        ('B', 'B'),
        ('C+', 'C+'),
        ('C', 'C'),
        ('D+', 'D'),                   
        ('D', 'D'),
        ('F', 'F'),

    ]


    recommendations = [
        ('Give again','Give again'),
        ('Not Applicable','Not Applicable'),
        ('Approved', 'Approved')
    ]


    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    theme_of_work = models.TextField()
    date = models.DateField()
    place = models.CharField(max_length=30)
    time = models.TimeField()
    work_done_till_previous_sem = models.TextField()
    specific_contri_in_cur_sem = models.TextField()
    future_plan = models.TextField()
    brief_report = models.FileField(upload_to='academic_procedure/Uploaded_document/GraduateSeminarReport/', null=False)
    publication_submitted = models.IntegerField()
    publication_accepted = models.IntegerField()
    paper_presented = models.IntegerField()
    papers_under_review = models.IntegerField()
    quality_of_work = models.CharField(max_length=20, choices=Quality_of_work)
    quantity_of_work = models.CharField(max_length=15, choices=Quantity_of_work)
    Overall_grade = models.CharField(max_length=2, choices=Grade)
    panel_report = models.CharField(max_length=15, choices=recommendations)
    suggestion = models.TextField(null=True)


    class meta:
        db_table =  ' MTechGraduateSeminarReport'


class PhDProgressExamination(models.Model):


    Quality_of_work = [
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Satisfactory', 'Satisfactory'),
        ('Unsatisfactory' , 'Unsatisfactory'),
    ]
    

    Quantity_of_work = [
        ('Enough', 'Enough'),
        ('Just Sufficient', 'Just Sufficient'),
        ('Insufficient', 'Insufficient'),
    ]


    Grade = [
        ('A+', 'A+'),
        ('A', 'A'),
        ('B+', 'B+'),
        ('B', 'B'),
        ('C+', 'C+'),
        ('C', 'C'),
        ('D+', 'D'),                   
        ('D', 'D'),
        ('F', 'F'),

    ]


    recommendations = [
        ('Give again','Give again'),
        ('Not Applicable','Not Applicable'),
        ('Approved', 'Approved')
    ]


    continuation_and_enhancement_choice = [
        ('yes', 'yes'),
        ('no', 'no'),
        ('not applicable', 'not applicable')
    ]


    


    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    theme = models.CharField(max_length=50, null=False)
    seminar_date_time = models.DateTimeField(null=False)
    place = models.CharField(max_length=30, null=False)
    work_done = models.TextField(null=False)
    specific_contri_curr_semester = models.TextField(null=False)
    future_plan =  models.TextField(null=False)
    details =  models.FileField(upload_to= 'academic_procedure/Uploaded_document/PhdProgressDetails/',null=False)
    papers_published = models.IntegerField(null=False)
    presented_papers = models.IntegerField(null=False)
    papers_submitted = models.IntegerField(null=False)
    quality_of_work = models.CharField(max_length=20, choices=Quality_of_work)
    quantity_of_work = models.CharField(max_length=15, choices=Quantity_of_work)
    Overall_grade = models.CharField(max_length=2, choices=Grade)
    completion_period = models.IntegerField(null=True)
    panel_report = models.TextField(null=True)
    continuation_enhancement_assistantship = models.CharField(max_length=20, choices=continuation_and_enhancement_choice,null=True)
    enhancement_assistantship = models.CharField(max_length=15, null=True, choices=continuation_and_enhancement_choice)
    annual_progress_seminar = models.CharField(max_length=20, choices=recommendations,null=True)
    commments = models.TextField(null=True)
          


# THESE ARE THE NEW TABLES AND REPLACEMENT OF THOSE ABOVE.
# PLEASE USE THESE TABLES FOR FURTHER WORK.
class StudentRegistrationChecks(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    pre_registration_flag = models.BooleanField(default=False)
    final_registration_flag = models.BooleanField(default=False)
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)

    class Meta:
        db_table = 'StudentRegistrationChecks'


class InitialRegistration(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_slot_id = models.ForeignKey(CourseSlot, null=True, blank=True,on_delete=models.SET_NULL)

    class Meta:
        db_table = 'InitialRegistration'


class FinalRegistration(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)
    course_slot_id = models.ForeignKey(CourseSlot, null=True, blank=True,on_delete=models.SET_NULL)

    class Meta:
        db_table = 'FinalRegistration'


class CourseRequested(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        db_table = 'CourseRequested'

class FeePayments(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)
    mode = models.CharField(max_length = 20, choices=Constants.PaymentMode)
    transaction_id = models.CharField(max_length = 40)

    class Meta:
        db_table = 'FeePayments'


class course_registration(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    course_slot_id = models.ForeignKey(CourseSlot, null=True, blank=True, on_delete=models.SET_NULL)
    # grade = models.CharField(max_length=10)

    class Meta:
        db_table = 'course_registration'
