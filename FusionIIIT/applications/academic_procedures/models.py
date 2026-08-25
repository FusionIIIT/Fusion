import datetime
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model
from applications.academic_information.models import Course, Student, Curriculum
from applications.programme_curriculum.models import Course as Courses, Semester, CourseSlot, Batch, ThesisSlot, SeminarSlot as ProgressSeminarSlot, TeachingCreditSlot, Thesis as ThesisCatalogEntry, Seminar, TeachingCredit
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
        ('Axis Easypay','Axis Easypay'),
        ('Subpaisa','Subpaisa'),
        ('NEFT','NEFT'),
        ('RTGS','RTGS'),
        ('Bank Challan','Bank Challan'),
        ('Edu Loan','Edu Loan')
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

Year_Choices = [
        (datetime.date.today().year, datetime.date.today().year),
        (datetime.date.today().year-1, datetime.date.today().year-1)
    ]

class Register(models.Model):
    '''
        Current Purpose : Deals with the information regarding the registration of a student in a course

        ATTRIBUTES

        curr_id(academic_information.Curriculum) - reference to the course 
        year(Integer) - the year for which the course is being registered(can be the academic year)
        student_id(acadmemic_information.Student) - reference to the student 
        semester(Integer) - the semester for which the registration is done(format unclear [can be between 1-8 or based on academic year(I or II)])

    '''
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
    '''
        Current Purpose : Deals with the branch change information for which a student applies

        ATTRIBUTES

        c_id(Autofield) -  primary key for the table
        branches(globals.DepartmentInfo) - list of departments from which a student can choose the branch they aspire to be in
        user(academic_information.Student) - reference to the student who has applied for branch change
        appilied_date(DateField) - date of the application for branch change
    '''
    c_id = models.AutoField(primary_key=True)
    branches = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE)
    user = models.ForeignKey(Student, on_delete=models.CASCADE)
    applied_date = models.DateField(default=datetime.datetime.now)

    def __str__(self):
        return str(self.user) + " " + str(self.branches)


class CoursesMtech(models.Model):
    '''
        Current Purpose : this table currently maps a course with the Mtech Specialization it is offered under

        ATTRIBUTES
        c_id(academic_information.Course) - reference to the Course 
        specialization(Char) - the specialization (CAD/CSE etc)



    '''
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


    course_id = models.ForeignKey(Courses, null=True, blank=True, on_delete=models.CASCADE)
    semester_id = models.ForeignKey(Semester,null=True, blank=True, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_slot_id = models.ForeignKey(CourseSlot, null=True, blank=True,on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=timezone.now)
    priority = models.IntegerField(blank=True,null=True)

    class Meta:
        db_table = 'InitialRegistrations'
    
    def __str__(self):
        return str(self.semester_id) + "-" + str(self.student_id)


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

class SemesterMarks(models.Model):
    '''
            Current Purpose : stores information regarding the marks of a student in a course in a semester

            ATTRIBUTES
            student_id(academic_information.Student) - reference to the student
            q1(float) - marks in quiz 1
            mid_term(float) - marks in mid terms
            q2(float) - marks in quiz 2
            end_term(float) - marks in end terms
            other(float) - marks for other categories
            curr_id(academic_information.Curriculum) - the course for which the grade has been awarded


        
    '''


    student_id = models.ForeignKey(Student, on_delete = models.CASCADE)
    q1 = models.FloatField(default = None)
    mid_term = models.FloatField(default = None)
    q2 = models.FloatField(default = None)
    end_term = models.FloatField(default = None)
    other = models.FloatField(default = None)
    grade = models.CharField(max_length=5, choices=Constants.GRADE, null=True)
    # curr_id = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    curr_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    #course_id = models.ForeignKey(Courses, on_delete=models.CASCADE, null=True)
    
    # def __str__(self):
    #     return self.student_id
    class Meta:
        db_table = 'SemesterMarks'


class MarkSubmissionCheck(models.Model):
    '''
            Current Purpose : keeps track of whether the grades of a course in a particular semester
             have been submitted and verified

            ATTRIBUTES
            
            curr_id(academic_information.Curriculum) - reference to the course
            verified(Boolean) - check if the grades are verified or not
            submitted(Boolean) - check if the grades are submitted or not
            announced(Boolean) - check ifthe grades are announced are not


        
    '''

    curr_id = models.ForeignKey(Courses,on_delete=models.CASCADE)
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


class BonafideCertificate(models.Model):
    PURPOSE_CHOICES = (
        ('Scholarship', 'Scholarship'),
        ('Railway Pass', 'Railway Pass'),
        ('Education Loan', 'Education Loan'),
        ('Higher Studies', 'Higher Studies'),
        ('Staff Benefit Fund', 'Staff Benefit Fund'),
        ('Bihar Student Credit Card', 'Bihar Student Credit Card'),
        ('Internship', 'Internship'),
        ('VISA Purpose', 'VISA Purpose'),
        ('Other', 'Other'),
    )

    student = models.ForeignKey(
        Student, on_delete=models.PROTECT, related_name='bonafide_certificates')
    purpose = models.CharField(max_length=40, choices=PURPOSE_CHOICES)
    custom_purpose = models.CharField(max_length=150, blank=True)
    reference_number = models.CharField(max_length=120, db_index=True, null=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='issued_bonafide_certificates')
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'BonafideCertificate'
        ordering = ('-issued_at',)

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
    hod_approval = models.BooleanField(default=False)
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
          

class Assistantship_status(models.Model):
    student_status = models.BooleanField(null=False)
    hod_status = models.BooleanField(null=False)
    account_status = models.BooleanField(null=False)

    

# THESE ARE THE NEW TABLES AND REPLACEMENT OF THOSE ABOVE.
# PLEASE USE THESE TABLES FOR FURTHER WORK.
class StudentRegistrationChecks(models.Model):
    '''
            Current Purpose : stores information regarding the process of registration of a student for a semester


            ATTRIBUTES
            student_id(academic_information.Student) - reference to the student
            pre_registration_flag(Boolean) - to denote whether the pre registration is complete
            final_registration_flag(boolean) - to denote whether the final registration is complete
            semester_id(programme_curriculum.Semester) - reference to the semester for which the registration will be considered

    '''


    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    pre_registration_flag = models.BooleanField(default=False)
    final_registration_flag = models.BooleanField(default=False)
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)

    class Meta:
        db_table = 'StudentRegistrationChecks'


class course_registration(models.Model):
    '''
            Current Purpose : stores information regarding the process of registration of a student for a course 

            ATTRIBUTES
            course_id(programme_curriculum.Course) -  reference to the course details for which the registration is being done
            semester_id(programme_curriculum.Semester) - reference to the semester for which the course registration is done
            student_id(academic_information.Student) - reference to the student
            course_slot_id(programme_curriculum.CourseSlot) - details about under which course slot the course is offered(Optional/Core other details)

    '''
    

    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    working_year=models.IntegerField(null=True,blank=True,choices=Year_Choices)
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    course_slot_id = models.ForeignKey(CourseSlot, null=True, blank=True, on_delete=models.SET_NULL)
    # The offering (programme_curriculum.CourseInstructor = course+section+faculty)
    # this registration is bound to. Set at allotment from the student's section;
    # this is what per-instructor grade submission scopes on. Nullable for
    # rows created before the sectioning feature.
    course_instructor = models.ForeignKey(
        'programme_curriculum.CourseInstructor', null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    REGISTRATION_TYPE_CHOICES = [
        ('Audit', 'Audit'),
        ('Improvement', 'Improvement'),
        ('Backlog', 'Backlog'),
        ('Regular', 'Regular'),
        ('Extra Credits', 'Extra Credits'),
        ('Replacement', 'Replacement'),
    ]
    registration_type = models.CharField(
        max_length=20,
        choices=REGISTRATION_TYPE_CHOICES,
        default='Regular',
    )
    session = models.CharField(max_length=9, null=True)   
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
    # grade = models.CharField(max_length=10)
    #course_registration_year = models.IntegerField()
    def __str__(self):
        return str(self.semester_id.semester_no)
    class Meta:
        db_table = 'course_registration'
        unique_together = ('course_id', 'student_id', 'semester_id', 'registration_type')


class InitialRegistration(models.Model):
    '''
            Current Purpose : stores information regarding the process of registration of a student for a course 


            ATTRIBUTES
            course_id(programme_curriculum.Course) -  reference to the course details for which the registration is being done
            semester_id(programme_curriculum.Semester) - reference to the semester for which the course registration is done
            student_id(academic_information.Student) - reference to the student
            course_slot_id(programme_curriculum.CourseSlot) - details about under which course slot the course is offered(Optional/Core other details)
            timestamp - the time this entry was generated
            priority - priority of the selected course from the list of courses for the corresponding course_slot_it
            registration_type - Type of registration for the course


        
    '''
    course_id = models.ForeignKey(Courses, null=True, blank=True, on_delete=models.CASCADE)
    semester_id = models.ForeignKey(Semester,null=True, blank=True, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE,null=True, blank=True)
    course_slot_id = models.ForeignKey(CourseSlot, null=True, blank=True,on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=timezone.now)
    priority = models.IntegerField(blank=True,null=True)
    old_course_registration=models.ForeignKey(course_registration, null=True, on_delete=models.CASCADE)
    REGISTRATION_TYPE_CHOICES = [
        ('Audit', 'Audit'),
        ('Improvement', 'Improvement'),
        ('Backlog', 'Backlog'),
        ('Regular', 'Regular'),
    ]
    registration_type = models.CharField(
        max_length=20,
        choices=REGISTRATION_TYPE_CHOICES,
        default='Regular',
    )
    
    class Meta:
        db_table = 'InitialRegistration'
        unique_together = ('course_id', 'student_id', 'semester_id', 'registration_type')
    
class FinalRegistration(models.Model):
    '''
            Current Purpose : stores information regarding the process of final(complete) registration of a student for a course 


            ATTRIBUTES
            course_id(programme_curriculum.Course) -  reference to the course details for which the registration is being done
            semester_id(programme_curriculum.Semester) - reference to the semester for which the course registration is done
            student_id(academic_information.Student) - reference to the student
            verified(Boolean) - denotes whether the registration is verified by academic department and complete
            course_slot_id(programme_curriculum.CourseSlot) - details about under which course slot the course is offered(Optional/Core other details)

    '''


    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)
    course_slot_id = models.ForeignKey(CourseSlot, null=True, blank=True,on_delete=models.SET_NULL)
    # Offering this student is bound to (course+section+faculty), set at allotment.
    # Carried onto course_registration at verification. Nullable for pre-feature rows.
    course_instructor = models.ForeignKey(
        'programme_curriculum.CourseInstructor', null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    old_course_registration=models.ForeignKey(course_registration, null=True, on_delete=models.CASCADE)
    REGISTRATION_TYPE_CHOICES = [
        ('Audit', 'Audit'),
        ('Improvement', 'Improvement'),
        ('Backlog', 'Backlog'),
        ('Regular', 'Regular'),
    ]
    registration_type = models.CharField(
        max_length=20,
        choices=REGISTRATION_TYPE_CHOICES,
        default='Regular',
    )

    class Meta:
        db_table = 'FinalRegistration'
        unique_together = ('course_id', 'student_id', 'semester_id', 'registration_type')


class CourseRequested(models.Model):
    '''
            Current Purpose : stores information regarding the courses for which a student has applied for (purpose is unclear and is open to interpretations)


            ATTRIBUTES
            course_id(programme_curriculum.Course) -  reference to the course details for which the student has applied
            student_id(academic_information.Student) - reference to the student
            
        
    '''

    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        db_table = 'CourseRequested'

class FeePayments(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)
    mode = models.CharField(max_length = 20, choices=Constants.PaymentMode)
    transaction_id = models.CharField(max_length = 40)
    fee_receipt = models.FileField(null=True,upload_to='fee_receipt/')
    deposit_date = models.DateField(default = datetime.date.today)
    utr_number = models.CharField(null = True, max_length = 40)
    fee_paid = models.IntegerField(default=0)
    reason = models.CharField(null=True, max_length = 20)
    actual_fee = models.IntegerField(default=0)
    class Meta:
        db_table = 'FeePayments'


class course_replacement(models.Model):
    old_course_registration=models.ForeignKey(course_registration, on_delete=models.CASCADE,related_name="replaced")
    new_course_registration=models.ForeignKey(course_registration, on_delete=models.CASCADE, related_name="replaces")
    class Meta:
        db_table = 'course_replacement'
        unique_together = ('old_course_registration', 'new_course_registration')

class backlog_course(models.Model):
    '''
            Current Purpose : stores information regarding the backlog courses of a student (purpose is unclear and is open to interpretations)

            ATTRIBUTES
            course_id(programme_curriculum.Course) -  reference to the course details for which the registration is being done
            semester_id(programme_curriculum.Semester) - reference to the semester for which the course registration is done
            student_id(academic_information.Student) - reference to the student
            is_summer_course(Boolean) - details about whether this course is available as summer_course or not
    '''
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    is_summer_course = models.BooleanField(default= False)


from django.db.models.signals import post_save
from django.dispatch import receiver


class Assignment(models.Model):
    ta          = models.ForeignKey(Student, on_delete=models.CASCADE)
    faculty     = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    start_year  = models.IntegerField()
    start_month = models.IntegerField()  # 1–12
    end_year    = models.IntegerField()
    end_month   = models.IntegerField()

    def __str__(self):
        return f"{self.ta}→{self.faculty} ({self.start_month}/{self.start_year}–{self.end_month}/{self.end_year})"

class StipendRequest(models.Model):
    PENDING      = 'pending'
    FAC_APPROVED = 'approved_by_faculty'
    HOD_APPROVED = 'approved_by_hod'
    STATUS_CHOICES = [
        (PENDING,      'Pending'),
        (FAC_APPROVED, 'Approved by Faculty'),
        (HOD_APPROVED, 'Approved by HOD'),
    ]

    assignment     = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='stipends')
    year           = models.IntegerField()
    month          = models.IntegerField()
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    faculty_remark = models.TextField(blank=True, null=True)
    hod_remark     = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('assignment','year','month')
        ordering        = ['year','month']

    def __str__(self):
        return f"{self.assignment.ta} - {self.month}/{self.year} [{self.get_status_display()}]"

@receiver(post_save, sender=Assignment)
def create_monthly_stipends(sender, instance, created, **kwargs):
    if not created: return
    sy, sm = instance.start_year, instance.start_month
    ey, em = instance.end_year,   instance.end_month
    year, month = sy, sm
    while (year<ey) or (year==ey and month<=em):
        StipendRequest.objects.create(assignment=instance, year=year, month=month)
        if month==12:
            month, year = 1, year+1
        else:
            month += 1



class CourseReplacementRequest(models.Model):
    STATUS_CHOICES = [
        ("Pending",  "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)
    semester_type = models.CharField(
        max_length=20,
        choices=[
            ("Odd Semester",    "Odd Semester"),
            ("Even Semester",   "Even Semester"),
            ("Summer Semester", "Summer Semester"),
        ],
    )
    course_slot = models.ForeignKey(CourseSlot, on_delete=models.CASCADE)
    old_course = models.ForeignKey(
        Courses,
        related_name='old_course_reqs',
        on_delete=models.CASCADE,
    )
    new_course = models.ForeignKey(
        Courses,
        related_name='new_course_reqs',
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (
            'student',
            'course_slot',
            'academic_year',
            'semester_type',
        )

    def __str__(self):
        return f"{self.old_course.code}→{self.new_course.code} [{self.status}]"

class SwayamReplacementRequest(models.Model):
    """
    Model for Swayam course registration requests (Extra Credits and Replace modes).
    Separate from CourseReplacementRequest which is for regular replacement allocation.
    """
    REQUEST_TYPE_CHOICES = [
        ('Extra_Credits', 'Extra Credits'),
        ('Swayam_Replace', 'Swayam Replace'),
    ]
    
    STATUS_CHOICES = [
        ("Pending",  "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)
    semester_type = models.CharField(
        max_length=20,
        choices=[
            ("Odd Semester",    "Odd Semester"),
            ("Even Semester",   "Even Semester"),
            ("Summer Semester", "Summer Semester"),
        ],
    )
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default='Extra_Credits',
    )

    old_course = models.ForeignKey(
        Courses,
        related_name='swayam_old_course_reqs',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    new_course = models.ForeignKey(
        Courses,
        related_name='swayam_new_course_reqs',
        on_delete=models.CASCADE,
    )

    course_slot = models.ForeignKey(
        CourseSlot,
        related_name='swayam_course_slot_reqs',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    new_course_slot = models.ForeignKey(
        CourseSlot,
        related_name='swayam_new_course_slot_reqs',
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )
    is_current_semester = models.BooleanField(
        default=False,
        help_text="True if the old course is an SW course in an OE slot in the current semester (DROP + REGISTER on approval)"
    )
    submitted_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'academic_procedures_swayamreplacementrequest'
        ordering = ['-submitted_at']

    def __str__(self):
        if self.old_course:
            return f"Swayam Replace: {self.old_course.code}→{self.new_course.code} [{self.status}]"
        return f"Swayam Extra: {self.new_course.code} [{self.status}]"
    

class CourseDropRequest(models.Model):
    STATUS_CHOICES = [
        ("Pending",  "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)
    semester_type = models.CharField(
        max_length=20,
        choices=[
            ("Odd Semester",    "Odd Semester"),
            ("Even Semester",   "Even Semester"),
            ("Summer Semester", "Summer Semester"),
        ],
    )
    course_slot = models.ForeignKey(CourseSlot, on_delete=models.CASCADE)
    course = models.ForeignKey(
        Courses,
        related_name='drop_course_reqs',
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (
            'student',
            'course_slot',
            'academic_year',
            'semester_type',
        )

    def __str__(self):
        return f"{self.course.code} Drop [{self.status}]"


class CourseAddRequest(models.Model):
    STATUS_CHOICES = [
        ("Pending",  "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)
    semester_type = models.CharField(
        max_length=20,
        choices=[
            ("Odd Semester",    "Odd Semester"),
            ("Even Semester",   "Even Semester"),
            ("Summer Semester", "Summer Semester"),
        ],
    )
    course_slot = models.ForeignKey(CourseSlot, on_delete=models.CASCADE)
    course = models.ForeignKey(
        Courses,
        related_name='add_course_reqs',
        on_delete=models.CASCADE,
    )
    old_course_registration = models.ForeignKey(
        course_registration,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Reference to the previous course registration being replaced (for backlog/improvement)"
    )
    # The running section (offering) the student chose when the course isn't run
    # in their own section; applied as course_instructor on approval.
    course_instructor = models.ForeignKey(
        'programme_curriculum.CourseInstructor',
        null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (
            'student',
            'course_slot',
            'academic_year',
            'semester_type',
        )

    def __str__(self):
        return f"{self.course.code} Add [{self.status}]"


class BatchChangeHistory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    old_batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="history_old")
    new_batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="history_new")
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]


SEMESTER_CHOICES = [
    ("Odd Semester", "Odd Semester"),
    ("Even Semester", "Even Semester"),
    ("Summer Semester", "Summer Semester"),
]

class FeedbackQuestion(models.Model):
    SECTION_CHOICES = [
        ("contents", "Course Contents"),
        ("instructor", "Course Instructor"),
        ("tutorial", "Tutorial"),
        ("lab", "Lab Instructor"),
        ("attendance", "Attendance"),
    ]
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    text    = models.TextField()
    order   = models.PositiveIntegerField()
    class Meta:
        ordering = ["section", "order"]

class FeedbackOption(models.Model):
    question = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE, related_name="options")
    text     = models.CharField(max_length=50)
    order    = models.PositiveIntegerField()
    class Meta:
        ordering = ["order"]

class FeedbackResponse(models.Model):
    question      = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE)
    option        = models.ForeignKey(FeedbackOption, on_delete=models.CASCADE, null=True, blank=True)
    text_answer   = models.TextField(blank=True)
    course        = models.ForeignKey(Courses, on_delete=models.CASCADE)
    # Offering this feedback is about (null for no-section / legacy responses).
    course_instructor = models.ForeignKey(
        'programme_curriculum.CourseInstructor', null=True, blank=True,
        on_delete=models.SET_NULL)
    section       = models.CharField(max_length=20, choices=FeedbackQuestion.SECTION_CHOICES)
    session       = models.CharField(max_length=9)
    semester_type = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    submitted_at  = models.DateTimeField(auto_now_add=True)

class FeedbackFilled(models.Model):
    student      = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester_no  = models.PositiveIntegerField()
    filled_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "semester_no")
        

# ============================================================================
# PhD-SPECIFIC MODELS (Added for PhD student management)
# ============================================================================

class ThesisTopic(models.Model):
    """Central thesis record with student submission fields and approval status."""
    STATUS_CHOICES = [
        ('supervisor_pending', 'Pending with Supervisor'),
        ('hod_pending', 'Approved by Supervisor, Pending with HOD'),
        ('hod_rejected', 'Rejected by HOD, Returned to Supervisor'),
        ('dean_pending', 'Approved by HOD, Pending with Dean'),
        ('dean_rejected', 'Rejected by Dean, Returned to HOD'),
        ('dean_approved', 'Approved by Dean'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Faculty, related_name='theses_supervised', on_delete=models.CASCADE)
    co_supervisor = models.ForeignKey(Faculty, related_name='theses_cosupervised', on_delete=models.CASCADE, null=True, blank=True)
    supervisor_consented    = models.BooleanField(default=False)
    co_supervisor_consented = models.BooleanField(default=False)

    category = models.CharField(max_length=20, choices=[
        ('Regular', 'Regular'),
        ('Sponsored', 'Sponsored'),
        ('External', 'External')
    ])
    broad_area = models.CharField(max_length=200)
    research_theme = models.TextField()

    external_name = models.CharField(max_length=100, blank=True)
    external_email = models.EmailField(blank=True)
    external_discipline = models.CharField(max_length=100, blank=True)
    external_institution = models.CharField(max_length=200, blank=True)

    pg_single = models.PositiveIntegerField(default=0)
    pg_shared = models.PositiveIntegerField(default=0)
    phd_single = models.PositiveIntegerField(default=0)
    phd_shared = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='supervisor_pending')
    hod_remarks = models.TextField(blank=True)
    dean_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.student.id.user.get_full_name()
        theme = self.research_theme[:30]
        return f"{name} — {theme}"


class CommitteeMember(models.Model):
    """RPC committee member for each thesis."""
    thesis = models.ForeignKey(ThesisTopic, related_name='committee', on_delete=models.CASCADE)
    member = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('thesis', 'member')

    def __str__(self):
        return f"{self.member} on {self.thesis}"


class ProgressSeminarEntry(models.Model):
    """PhD Seminar reports with versioning and RPC approval."""
    thesis     = models.ForeignKey(ThesisTopic, on_delete=models.CASCADE, related_name='seminars')
    version    = models.PositiveSmallIntegerField()
    semester   = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True,
                                   help_text="Student's semester when this report was created.")
    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('draft',       'Draft'),
        ('rpc_pending', 'Pending RPC Consent'),
        ('rpc_approved','Approved'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Logistics
    seminar_date  = models.DateField(null=True, blank=True)
    seminar_time  = models.TimeField(null=True, blank=True)
    seminar_venue = models.CharField(max_length=200, blank=True)

    # Summaries
    summary_prev = models.TextField(blank=True)
    summary_curr = models.TextField(blank=True)
    future_plan  = models.TextField(blank=True)
    upload_doc   = models.FileField(upload_to='seminar_docs/', null=True, blank=True)

    # Publication counts — matches the official progress-seminar form's three
    # publication questions directly, one field each (no category breakdown).
    pub_published_or_accepted = models.PositiveIntegerField(
        default=0, help_text="Papers published/accepted in journals or conference proceedings")
    pub_presented_unpublished = models.PositiveIntegerField(
        default=0, help_text="Papers presented in conferences/meetings/workshops (unpublished)")
    pub_submitted_under_review = models.PositiveIntegerField(
        default=0, help_text="Papers submitted (under review)")

    # RPC Evaluation fields
    quality         = models.CharField(
        max_length=20,
        choices=[('Excellent','Excellent'),
                 ('Good','Good'),
                 ('Sat','Satisfactory'),
                 ('Unsat','Unsatisfactory')],
        blank=True
    )
    quantity        = models.CharField(
        max_length=20,
        choices=[('Enough','Enough'),
                 ('Just','Just Sufficient'),
                 ('Insuff','Insufficient')],
        blank=True
    )
    overall_grade   = models.CharField(
        max_length=2,
        choices=[('S','S'), ('X','X')],
        blank=True
    )
    expected_period = models.CharField(
        max_length=2,
        choices=[('1','1 year'),
                 ('2','2 years'),
                 ('3','3 years'),
                 ('4','4 years')],
        blank=True
    )
    rec_assist      = models.CharField(
        max_length=3,
        choices=[('Yes','Yes'),
                 ('No','No'),
                 ('NA','Not Applicable')],
        blank=True
    )
    rec_enhance     = models.CharField(
        max_length=3,
        choices=[('Yes','Yes'),
                 ('No','No'),
                 ('NA','Not Applicable')],
        blank=True
    )
    rec_repeat      = models.CharField(
        max_length=3,
        choices=[('Yes','Yes'),
                 ('NA','Not Applicable')],
        blank=True
    )
    rec_open        = models.CharField(
        max_length=3,
        choices=[('Yes','Yes'),
                 ('No','No')],
        blank=True
    )

    def __str__(self):
        return f"Seminar {self.version} for {self.thesis}"


class ProgressSeminarConsent(models.Model):
    """RPC member consent for seminar."""
    seminar   = models.ForeignKey(ProgressSeminarEntry, related_name='consents', on_delete=models.CASCADE)
    member    = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    consented = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('seminar','member')


class ProgressSeminarComment(models.Model):
    """RPC member comments on seminar."""
    seminar   = models.ForeignKey(ProgressSeminarEntry, related_name='comments', on_delete=models.CASCADE)
    member    = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    text      = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('seminar','member')
        ordering = ['-timestamp']


import uuid

def upload_synopsis(instance, filename):
    """Upload path for thesis synopsis."""
    ext = filename.split('.')[-1]
    return f"synopsis/{instance.file_token}.{ext}"

def upload_report(instance, filename):
    """Upload path for thesis report."""
    ext = filename.split('.')[-1]
    return f"reports/{instance.file_token}.{ext}"


class ThesisSubmission(models.Model):
    """PhD Thesis submission with file uploads."""
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('dean_panel_review', 'Pending Dean Panel Approval'),
        ('director_review', 'Pending Director Prioritization'),
        ('dean_invite_pending', 'Pending Dean Invitation'),
        ('in_review', 'In External Review'),
        ('completed', 'Review Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    thesis         = models.OneToOneField(ThesisTopic, on_delete=models.CASCADE, related_name='submission')
    file_token     = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    synopsis       = models.FileField(upload_to=upload_synopsis)
    thesis_report  = models.FileField(upload_to=upload_report)
    submitted_at   = models.DateTimeField(auto_now_add=True, db_index=True)
    supervisor     = models.ForeignKey('auth.User', null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name='supervised_subs')
    supervisor_approved_at = models.DateTimeField(null=True, blank=True)
    dean           = models.ForeignKey('auth.User', null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name='deaned_subs')
    dean_approved_at = models.DateTimeField(null=True, blank=True)
    dean_invited_at  = models.DateTimeField(null=True, blank=True)
    dean_panel_remarks = models.TextField(blank=True)
    director       = models.ForeignKey('auth.User', null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name='directed_subs')
    director_approved_at = models.DateTimeField(null=True, blank=True)
    director_remarks = models.TextField(blank=True)
    status         = models.CharField(max_length=30, choices=STATUS_CHOICES, default='submitted', db_index=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', 'submitted_at']),
        ]

    def __str__(self):
        return f"Submission for {self.thesis.research_theme}"


class ReviewInvitation(models.Model):
    """External reviewer invitation for thesis."""
    EXAMINER_TYPE_CHOICES = [
        ('indian', 'Indian'),
        ('foreign', 'Foreign'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]
    submission      = models.ForeignKey(ThesisSubmission, on_delete=models.CASCADE, related_name='invitations')
    examiner_type   = models.CharField(max_length=10, choices=EXAMINER_TYPE_CHOICES, default='indian', db_index=True)
    prof_name       = models.CharField(max_length=255, db_index=True)
    prof_position   = models.CharField(max_length=255)
    prof_address    = models.TextField()
    prof_phone      = models.CharField(max_length=20)
    prof_fax        = models.CharField(max_length=20, blank=True, default='')
    prof_email      = models.EmailField(db_index=True)
    prof_time_ranking = models.PositiveSmallIntegerField(null=True, blank=True)
    priority        = models.PositiveSmallIntegerField(default=0, db_index=True)
    token           = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    last_sent       = models.DateTimeField(null=True, blank=True)
    review_form_sent= models.DateTimeField(null=True, blank=True)
    expires_at      = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('submission', 'examiner_type', 'priority')]
        ordering = ['submission', 'examiner_type', 'priority']
        indexes = [
            models.Index(fields=['submission', 'status']),
            models.Index(fields=['status', 'last_sent']),
        ]

    def is_expired(self):
        """Check if the invitation has expired."""
        return self.expires_at and timezone.now() >= self.expires_at

    def is_finalized(self):
        """Check if the invitation is in a final state."""
        return self.status in ['completed', 'expired', 'rejected']


class ThesisReview(models.Model):
    """An examiner's formal evaluation, mirroring the institute's official
    'Examination Report of PhD Student' form."""
    CORRECTION_CHOICES = [
        ('none', 'None'),
        ('minor', 'Minor'),
        ('major', 'Major'),
    ]
    RECOMMENDATION_CHOICES = [
        ('accept', 'Acceptable in present form for award of the PhD degree'),
        ('accept_with_corrections', 'Acceptable; suggested corrections/modifications to be incorporated'),
        ('needs_improvement', "Needs technical improvement to the examiner's satisfaction"),
        ('reject', 'Rejected -- thesis does not contain novel work'),
    ]

    invitation = models.OneToOneField(ReviewInvitation, on_delete=models.CASCADE, related_name='review')

    # A. General features of thesis
    originality_presentation = models.TextField(blank=True, default='')
    quality_comparable       = models.BooleanField(null=True, blank=True)
    new_ideas_original        = models.BooleanField(null=True, blank=True)

    # B. Comments
    correction_severity = models.CharField(max_length=10, choices=CORRECTION_CHOICES, blank=True, default='')
    technical_content   = models.TextField(blank=True, default='')
    highlights           = models.TextField(blank=True, default='')

    # C, D
    suggestions        = models.TextField(blank=True, default='')
    defense_questions  = models.TextField(blank=True, default='')

    # E. Specific recommendation
    recommendation = models.CharField(max_length=30, choices=RECOMMENDATION_CHOICES)

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.invitation.prof_name} ({self.recommendation})"


class ExaminerBankDetails(models.Model):
    """Honorarium payment details for an external examiner.

    Kept as its own model, deliberately isolated from ThesisReview /
    ReviewInvitation serialization -- never include this in dashboard or
    listing API responses.
    """
    invitation = models.OneToOneField(ReviewInvitation, on_delete=models.CASCADE, related_name='bank_details')

    beneficiary_name = models.CharField(max_length=255, blank=True, default='')
    bank_name        = models.CharField(max_length=255, blank=True, default='')
    bank_address     = models.TextField(blank=True, default='')
    account_no       = models.CharField(max_length=50, blank=True, default='')
    # Indian examiners provide IFSC + PAN; foreign examiners provide IBAN + SWIFT.
    ifsc_code   = models.CharField(max_length=20, blank=True, default='')
    pan_no      = models.CharField(max_length=20, blank=True, default='')
    iban_no     = models.CharField(max_length=40, blank=True, default='')
    swift_code  = models.CharField(max_length=20, blank=True, default='')

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bank details for {self.invitation.prof_name}"

    def __str__(self):
        return f"{self.prof_name} - {self.submission.thesis.research_theme} ({self.status})"


def upload_pg_synopsis(instance, filename):
    """Upload path for a PG thesis synopsis.

    Extension is hardcoded rather than taken from the client-supplied
    filename -- both are validated as PDF in the view, but deriving the
    stored extension from user input would let a renamed file (e.g.
    "x.html") get served back with a browser-inferred content type,
    opening a stored-XSS path when a supervisor/examiner opens the link.
    """
    return f"pg_thesis/synopsis/{instance.file_token}.pdf"


def upload_pg_report(instance, filename):
    """Upload path for a PG thesis report. See upload_pg_synopsis."""
    return f"pg_thesis/report/{instance.file_token}.pdf"


class PGThesisSubmission(models.Model):
    """PG (M.Tech/M.Des) final thesis submission -- synopsis + full report.

    Deliberately separate from ThesisSubmission: PhD's Dean Panel / Director /
    foreign-examiner workflow doesn't apply to PG. This simpler model just
    holds the uploaded documents that the supervisor (SupervisorThesisDecimalScores)
    and the batch's accepted examiner (ThesisExaminerPanel) reference while
    scoring the student's decimal-mode ThesisEvaluation.
    """
    thesis        = models.OneToOneField(ThesisTopic, on_delete=models.CASCADE, related_name='pg_submission')
    file_token    = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    synopsis      = models.FileField(upload_to=upload_pg_synopsis)
    thesis_report = models.FileField(upload_to=upload_pg_report)
    submitted_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PG thesis submission — {self.thesis.student} ({self.submitted_at:%Y-%m-%d})"


# ===========================================================================
# Thesis Slot & Progress Seminar Semester-Level Registration
# ===========================================================================

class ThesisRegistration(models.Model):
    """Records a PhD student's semester-level thesis slot enrollment.

    Analogous to course_registration / FinalRegistration for courses.
    One record per student per semester; admin verifies after submission.
    """
    STATUS_CHOICES = [
        ('pending',  'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    THESIS_CREDIT_CHOICES = [(3, '3 Credits'), (6, '6 Credits'), (9, '9 Credits'), (12, '12 Credits')]

    student          = models.ForeignKey(Student, on_delete=models.CASCADE,
                                         related_name='thesis_registrations')
    thesis_slot      = models.ForeignKey(ThesisSlot, on_delete=models.CASCADE,
                                         related_name='registrations')
    thesis           = models.ForeignKey(ThesisCatalogEntry, on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         help_text='Catalog entry chosen within thesis_slot (admin manual add/allot only -- '
                                                    'the student self-registration flow does not set this)')
    thesis_topic     = models.ForeignKey('ThesisTopic', on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         related_name='thesis_registrations')
    semester         = models.ForeignKey(Semester, on_delete=models.CASCADE)
    credits          = models.PositiveSmallIntegerField(
                           choices=THESIS_CREDIT_CHOICES,
                           default=6,
                           help_text='Credits the student is registering for this semester (3/6/9/12)',
                       )
    working_year     = models.IntegerField(null=True, blank=True)
    academic_session = models.CharField(max_length=9, null=True, blank=True)  # e.g. "2025-26"
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registered_on    = models.DateTimeField(auto_now_add=True)
    verified_on      = models.DateTimeField(null=True, blank=True)
    remarks          = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = ('student', 'semester')
        db_table = 'ThesisRegistration'

    def __str__(self):
        return f"{self.student} — {self.thesis_slot.name} ({self.semester})"


class ProgressSeminarRegistration(models.Model):
    """Records a PhD student's semester-level progress seminar enrollment.

    Analogous to ThesisRegistration; one record per student per semester.
    """
    STATUS_CHOICES = [
        ('pending',  'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    student               = models.ForeignKey(Student, on_delete=models.CASCADE,
                                              related_name='progress_seminar_registrations')
    progress_seminar_slot = models.ForeignKey(ProgressSeminarSlot, on_delete=models.CASCADE,
                                              related_name='registrations')
    seminar               = models.ForeignKey(Seminar, on_delete=models.SET_NULL,
                                              null=True, blank=True,
                                              help_text='Catalog entry chosen within progress_seminar_slot '
                                                         '(admin manual add/allot only)')
    semester              = models.ForeignKey(Semester, on_delete=models.CASCADE)
    working_year          = models.IntegerField(null=True, blank=True)
    status                = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registered_on         = models.DateTimeField(auto_now_add=True)
    remarks               = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = ('student', 'semester')
        db_table = 'ProgressSeminarRegistration'

    def __str__(self):
        return f"{self.student} — {self.progress_seminar_slot.name} ({self.semester})"


class TeachingCreditRegistration(models.Model):
    """Records a PhD student's semester-level teaching credit enrollment.

    Analogous to ThesisRegistration / ProgressSeminarRegistration; one record
    per student per semester. This is only the enrollment gate -- the actual
    course choice-and-allocation process (TeachingCreditAllocation) happens
    separately, after this enrollment is verified.
    """
    STATUS_CHOICES = [
        ('pending',  'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    student               = models.ForeignKey(Student, on_delete=models.CASCADE,
                                              related_name='teaching_credit_registrations')
    teaching_credit_slot  = models.ForeignKey(TeachingCreditSlot, on_delete=models.CASCADE,
                                              related_name='registrations')
    teaching_credit       = models.ForeignKey(TeachingCredit, on_delete=models.SET_NULL,
                                              null=True, blank=True,
                                              help_text='Catalog entry chosen within teaching_credit_slot '
                                                         '(admin manual add/allot only)')
    semester              = models.ForeignKey(Semester, on_delete=models.CASCADE)
    working_year          = models.IntegerField(null=True, blank=True)
    academic_session      = models.CharField(max_length=9, null=True, blank=True)  # e.g. "2025-26"
    status                = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registered_on         = models.DateTimeField(auto_now_add=True)
    remarks               = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = ('student', 'semester')
        db_table = 'TeachingCreditRegistration'

    def __str__(self):
        return f"{self.student} — {self.teaching_credit_slot.name} ({self.semester})"


# ===========================================================================
# Thesis & Progress Seminar Grade Evaluation
# ===========================================================================

class ThesisEvaluation(models.Model):
    """Grade record for one evaluation block within a ThesisRegistration.

    A student who registers for N credits gets N÷3 blocks (1 block per 3 credits).
    e.g. 12 credits → 4 blocks, each graded S or X independently.
    Blocks are auto-created when the admin verifies the ThesisRegistration.
    """
    GRADE_CHOICES = [('S', 'Satisfactory'), ('X', 'Unsatisfactory')]

    registration  = models.ForeignKey(
        ThesisRegistration,
        on_delete=models.CASCADE,
        related_name='evaluations',
    )
    block_number  = models.PositiveSmallIntegerField(
        help_text='Sequential block index starting at 1 (max = registration.credits ÷ 3)',
    )

    # Grade — null until supervisor submits. Blocks mode (PhD, PG sem 2/3)
    # uses `grade`; decimal mode (PG's final thesis semester) uses
    # `numeric_grade` instead, computed from ThesisEvaluationScore once both
    # the supervisor and examiner scores are in. A row only ever populates one.
    grade         = models.CharField(
        max_length=1, choices=GRADE_CHOICES, null=True, blank=True,
    )
    numeric_grade = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        help_text='Decimal-mode final grade: average of supervisor_score and examiner_score',
    )
    submitted_by  = models.ForeignKey(
        Faculty, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='thesis_grades_submitted',
    )
    submitted_at  = models.DateTimeField(null=True, blank=True)
    remarks       = models.TextField(blank=True)

    # Admin lifecycle
    verified      = models.BooleanField(default=False)
    verified_by   = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='thesis_grades_verified',
    )
    verified_at   = models.DateTimeField(null=True, blank=True)

    announced     = models.BooleanField(default=False)
    announced_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('registration', 'block_number')
        ordering = ['registration', 'block_number']
        db_table = 'ThesisEvaluation'

    def __str__(self):
        g = self.grade or '—'
        return (
            f"Block {self.block_number}/{self.registration.credits // 3} "
            f"| {self.registration.student} | Sem {self.registration.semester.semester_no} "
            f"| Grade: {g}"
        )

    @property
    def total_blocks(self):
        if self.registration.thesis_slot.evaluation_type == 'decimal':
            return 1
        return self.registration.credits // 3


class ThesisExaminerPanel(models.Model):
    """A batch-wide (i.e. per-specialization, not per-student) examiner panel
    for PG's decimal-graded final thesis semester -- mirrors the real paper
    form, which is one sheet of 4 examiners per specialization. HOD nominates
    4 Indian examiner candidates for the whole batch; Dean ranks and invites
    them; whichever candidate accepts first examines every student in that
    batch. Multiple specialization batches within the same discipline+year
    (e.g. CSE's "AI & ML" and "Data Science") each get their own independent
    panel -- the HOD nomination screen and Dean ranking screen just group
    those panels together for convenience (see hod_examiner_panel_dashboard /
    dean_examiner_panel_dashboard), they don't merge the underlying process.
    """
    STATUS_CHOICES = [
        ('hod_pending',   'Awaiting HOD Nomination'),
        ('dean_pending',  'Awaiting Dean Ranking'),
        ('invited',       'Invitations Sent'),
        ('accepted',      'Examiner Confirmed'),
        ('all_declined',  'All Candidates Declined'),
    ]

    batch             = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name='thesis_examiner_panel')
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='hod_pending')
    hod_submitted_by  = models.ForeignKey(Faculty, null=True, blank=True,
                                          on_delete=models.SET_NULL, related_name='thesis_panels_nominated')
    hod_submitted_at  = models.DateTimeField(null=True, blank=True)
    dean_reviewed_by  = models.ForeignKey('auth.User', null=True, blank=True,
                                          on_delete=models.SET_NULL, related_name='thesis_panels_ranked')
    dean_invited_at   = models.DateTimeField(null=True, blank=True)
    accepted_candidate = models.OneToOneField(
        'ThesisExaminerCandidate', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Examiner panel — {self.batch} [{self.status}]"


class ThesisExaminerCandidate(models.Model):
    """One HOD-nominated examiner candidate within a ThesisExaminerPanel.
    Same token-based accept/decline pattern as ReviewInvitation, minus the
    Indian/foreign split -- PG examiners are Indian-only.
    """
    STATUS_CHOICES = [
        ('pending',  'Not Yet Invited'),
        ('invited',  'Invited'),
        ('accepted', 'Accepted'),
        ('rejected', 'Declined'),
        ('expired',  'Expired'),
    ]

    panel        = models.ForeignKey(ThesisExaminerPanel, on_delete=models.CASCADE, related_name='candidates')
    name         = models.CharField(max_length=255)
    position     = models.CharField(max_length=255, blank=True)
    address      = models.TextField(blank=True)
    phone        = models.CharField(max_length=20, blank=True)
    fax          = models.CharField(max_length=20, blank=True)
    email        = models.EmailField()
    priority     = models.PositiveSmallIntegerField(default=0)
    token        = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_sent    = models.DateTimeField(null=True, blank=True)
    expires_at   = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('panel', 'priority')
        ordering = ['panel', 'priority']

    def is_expired(self):
        return bool(self.expires_at and timezone.now() >= self.expires_at)

    def is_finalized(self):
        """Unlike ReviewInvitation.is_finalized() (which excludes 'accepted',
        since an accepted PhD reviewer still has more steps ahead), 'accepted'
        counts as finalized here on purpose: an examiner candidate who has
        accepted shouldn't be able to accept/reject again. Don't assume parity
        between the two if refactoring to share logic."""
        return self.status in ('accepted', 'rejected', 'expired')

    def __str__(self):
        return f"{self.name} — {self.panel.batch} [{self.status}]"


class ThesisEvaluationScore(models.Model):
    """Raw supervisor/examiner input scores (out of 100) for a decimal-mode
    ThesisEvaluation. ThesisEvaluation.numeric_grade holds the averaged
    result once both scores are in; this table only ever holds rows for
    decimal-mode evaluations, so nothing here is sparse.
    """
    evaluation           = models.OneToOneField(ThesisEvaluation, on_delete=models.CASCADE, related_name='score_inputs')
    supervisor_score     = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    supervisor_scored_at = models.DateTimeField(null=True, blank=True)
    examiner_candidate   = models.ForeignKey(ThesisExaminerCandidate, null=True, blank=True,
                                             on_delete=models.SET_NULL, related_name='scores_given')
    examiner_score       = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    examiner_scored_at   = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Scores for {self.evaluation} (sup={self.supervisor_score}, exam={self.examiner_score})"


class ProgressSeminarEvaluation(models.Model):
    """Grade record for a ProgressSeminarRegistration.

    Progress seminars are fixed at 3 credits → always exactly 1 evaluation block.
    """
    GRADE_CHOICES = [('S', 'Satisfactory'), ('X', 'Unsatisfactory')]

    registration  = models.OneToOneField(
        ProgressSeminarRegistration,
        on_delete=models.CASCADE,
        related_name='evaluation',
    )

    grade         = models.CharField(
        max_length=1, choices=GRADE_CHOICES, null=True, blank=True,
    )
    submitted_by  = models.ForeignKey(
        Faculty, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='seminar_grades_submitted',
    )
    submitted_at  = models.DateTimeField(null=True, blank=True)
    remarks       = models.TextField(blank=True)

    verified      = models.BooleanField(default=False)
    verified_by   = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='seminar_grades_verified',
    )
    verified_at   = models.DateTimeField(null=True, blank=True)

    announced     = models.BooleanField(default=False)
    announced_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ProgressSeminarEvaluation'

    def __str__(self):
        g = self.grade or '—'
        return (
            f"{self.registration.student} | Sem {self.registration.semester.semester_no} "
            f"| Grade: {g}"
        )


DEFAULT_PROGRESS_SEMINAR_CREDIT = 0
# 0, not some plausible-looking number: today ProgressSeminarEntry (the RPC-approval
# grade record) has no required link to a ProgressSeminarRegistration (the credit
# enrollment-gate record) at all -- create_report() creates a graded entry from just
# a Dean-approved ThesisTopic, with no registration check. So this fallback fires on
# a genuine data gap (missing/unlinked registration), not a rare fluke, and it should
# under-count rather than guess -- guessing already produced a wrong "3" once.


def resolve_progress_seminar_catalog_entry(student, semester):
    """Resolve the programme_curriculum.Seminar catalog row (code/name/credit) that
    applies to a student's progress seminar in a given semester, via their
    ProgressSeminarRegistration -> SeminarSlot -> seminars M2M, preferring the
    student's own discipline when a slot serves more than one. Returns None if no
    registration/catalog match exists (e.g. semester is None, or the student never
    had a ProgressSeminarRegistration for that semester).

    This is the single source of truth for "how many credits is one progress
    seminar worth" -- do not hardcode that number elsewhere; call this instead."""
    if not semester:
        return None
    reg = ProgressSeminarRegistration.objects.filter(
        student=student, semester=semester
    ).select_related('progress_seminar_slot').prefetch_related(
        'progress_seminar_slot__seminars'
    ).first()
    if not reg or not reg.progress_seminar_slot:
        return None
    discipline = getattr(getattr(student, 'batch_id', None), 'discipline', None)
    manager = reg.progress_seminar_slot.seminars
    entry = (manager.filter(discipline=discipline).first() if discipline else None) or manager.first()
    return entry


def resolve_progress_seminar_credit(student, semester):
    """Credit value for one progress seminar, sourced from the catalog via
    resolve_progress_seminar_catalog_entry(), falling back to
    DEFAULT_PROGRESS_SEMINAR_CREDIT only when no catalog entry can be found."""
    entry = resolve_progress_seminar_catalog_entry(student, semester)
    return entry.credit if entry and entry.credit else DEFAULT_PROGRESS_SEMINAR_CREDIT


DEFAULT_TEACHING_CREDIT = 0
# Mirrors DEFAULT_PROGRESS_SEMINAR_CREDIT's reasoning: 0, not a guess, so a
# missing/unlinked TeachingCreditRegistration under-counts rather than
# fabricates a plausible-looking credit value.


def resolve_teaching_credit_catalog_entry(student, semester):
    """Resolve the programme_curriculum.TeachingCredit catalog row (code/name/credit)
    that applies to a student's teaching credit in a given semester, via their
    TeachingCreditRegistration -> TeachingCreditSlot -> teaching_credits M2M,
    preferring the student's own discipline when a slot serves more than one.
    Returns None if no registration/catalog match exists.

    This is the single source of truth for "how many credits is one semester of
    teaching credit worth" -- do not hardcode that number elsewhere; call this instead."""
    if not semester:
        return None
    reg = TeachingCreditRegistration.objects.filter(
        student=student, semester=semester
    ).select_related('teaching_credit_slot').prefetch_related(
        'teaching_credit_slot__teaching_credits'
    ).first()
    if not reg or not reg.teaching_credit_slot:
        return None
    discipline = getattr(getattr(student, 'batch_id', None), 'discipline', None)
    manager = reg.teaching_credit_slot.teaching_credits
    entry = (manager.filter(discipline=discipline).first() if discipline else None) or manager.first()
    return entry


def resolve_teaching_credit_credit(student, semester):
    """Credit value for one semester of teaching credit, sourced from the catalog
    via resolve_teaching_credit_catalog_entry(), falling back to
    DEFAULT_TEACHING_CREDIT only when no catalog entry can be found."""
    entry = resolve_teaching_credit_catalog_entry(student, semester)
    return entry.credit if entry and entry.credit else DEFAULT_TEACHING_CREDIT


# ===========================================================================
# PhD Course (Coursework) Registration
# ===========================================================================

class PhDCourseRegistrationRequest(models.Model):
    """A PhD student's self-submitted request to register for a curriculum
    course in their current semester. Independent of CourseAddRequest
    (which is the UG/PG backlog add-course flow) — PhD students don't go
    through pre-registration/final-registration, so this is a standalone
    request-and-verify workflow, verified separately by acadadmin.
    """
    STATUS_CHOICES = [
        ("Pending",  "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE,
                                 related_name='phd_course_requests')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)
    semester_type = models.CharField(
        max_length=20,
        choices=[
            ("Odd Semester",    "Odd Semester"),
            ("Even Semester",   "Even Semester"),
            ("Summer Semester", "Summer Semester"),
        ],
    )
    course_slot = models.ForeignKey(CourseSlot, on_delete=models.CASCADE)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE,
                                related_name='phd_course_requests')
    # BL slots clear a past course. source_course is the one being cleared; it
    # differs from course only when the past course sat in an OE slot and the
    # student picked a different course to replace it with.
    source_course = models.ForeignKey(Courses, null=True, blank=True,
                                       on_delete=models.SET_NULL,
                                       related_name='phd_source_course_requests')
    registration_type = models.CharField(max_length=20, blank=True, choices=[
        ("Backlog", "Backlog"),
        ("Improvement", "Improvement"),
    ])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    remarks = models.CharField(max_length=500, blank=True)
    requested_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(ExtraInfo, null=True, blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name='phd_course_requests_processed')

    class Meta:
        unique_together = ('student', 'semester', 'course_slot')
        db_table = 'PhDCourseRegistrationRequest'

    def __str__(self):
        return f"{self.student} — {self.course.code} [{self.status}]"


# ===========================================================================
# Comprehensive Examination
# ===========================================================================

class ComprehensiveExam(models.Model):
    """PhD Comprehensive Examination eligibility & DPGC approval.

    One record per student. The exam itself — RPC review, dates, result — is
    tracked per-attempt in ComprehensiveExamAttempt, since a student may
    retake it up to MAX_ATTEMPTS times. There is no separate examination
    committee here: the student's existing RPC (Progress Seminar committee,
    CommitteeMember via their ThesisTopic) doubles as the examination
    committee and is read live, never proposed/stored here.
    """
    ENTRY_QUALIFICATION_CHOICES = [
        ('masters', 'ME/M.Tech/M.Des/M.Phil (16 credits required)'),
        ('bachelors', 'B.Tech/B.E./M.Sc./MA (40 credits required)'),
    ]
    STATUS_CHOICES = [
        ('academic_office_pending', 'Pending Academic Office Verification'),
        ('academic_office_rejected', 'Rejected by Academic Office'),
        ('dpgc_pending', 'Pending Convener (DPGC) Approval'),
        ('dpgc_rejected', 'Rejected by Convener (DPGC)'),
        ('in_progress', 'Approved by DPGC — In Progress'),
        ('passed', 'Passed'),
        ('failed_final', 'Failed — Attempts Exhausted'),
    ]

    MAX_ATTEMPTS = 2
    MIN_CPI = Decimal('7.00')

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='comprehensive_exam')
    supervisor = models.ForeignKey(Faculty, related_name='comprehensive_exams_supervised', on_delete=models.CASCADE)
    co_supervisor = models.ForeignKey(Faculty, related_name='comprehensive_exams_cosupervised', on_delete=models.CASCADE, null=True, blank=True)

    possible_thesis_title = models.CharField(max_length=300, blank=True)
    proposed_exam_date = models.DateField(
        null=True, blank=True,
        help_text="Set by the supervisor at proposal time; seeds attempt 1's exam_date once DPGC approves.",
    )

    entry_qualification = models.CharField(max_length=10, choices=ENTRY_QUALIFICATION_CHOICES)
    credits_completed = models.PositiveIntegerField(default=0)
    current_cpi = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    research_methodology_completed = models.BooleanField(default=False)

    # Academic Office verification
    credits_verified = models.BooleanField(default=False)
    cpi_verified = models.BooleanField(default=False)
    research_methodology_verified = models.BooleanField(default=False)
    academic_office_remarks = models.TextField(blank=True)
    academic_office_verified_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='comprehensive_exams_office_verified',
    )
    academic_office_verified_at = models.DateTimeField(null=True, blank=True)

    # Convener (DPGC) approval — HOD of the student's department stands in for
    # the DPGC convener.
    dpgc_remarks = models.TextField(blank=True)
    dpgc_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='comprehensive_exams_dpgc_reviewed',
    )
    dpgc_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='academic_office_pending')
    current_attempt_number = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def required_credits(self):
        return 16 if self.entry_qualification == 'masters' else 40

    def __str__(self):
        return f"Comprehensive Exam — {self.student.id.user.get_full_name()}"


class ComprehensiveExamAttempt(models.Model):
    """One attempt (max ComprehensiveExam.MAX_ATTEMPTS) of the exam: RPC
    review, dates, result.

    The RPC (the student's existing committee) collectively records the
    result + qualitative comments, each member individually consenting —
    mirroring ProgressSeminarEntry/ProgressSeminarConsent. Convener (PGCS,
    also HOD) then reviews the RPC's finalized result before forwarding to
    Dean Academic for final approval.
    """
    STATUS_CHOICES = [
        ('rpc_pending', 'Pending RPC Consensus'),
        ('pgcs_pending', 'RPC Finalized — Pending Convener (PGCS) Review'),
        ('dean_pending', 'Approved by PGCS — Pending Dean Academic'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ]
    RESULT_CHOICES = [('passed', 'Passed'), ('failed', 'Failed')]

    exam = models.ForeignKey(ComprehensiveExam, related_name='attempts', on_delete=models.CASCADE)
    attempt_number = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='rpc_pending')

    exam_date = models.DateField(null=True, blank=True, help_text="Settable by the supervisor or any RPC member; may be updated again when RPC finalizes the report.")

    # Result — mirrors the official "Comprehensive Examination Report" form;
    # filled collectively by the RPC (shared panel, like Progress Seminar).
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, null=True, blank=True)
    fundamentals_comment = models.TextField(blank=True)
    problem_identification_comment = models.TextField(blank=True)
    plan_of_work_comment = models.TextField(blank=True)
    suggestions_comment = models.TextField(blank=True)
    additional_literature_comment = models.TextField(blank=True)
    milestone_plan_upload = models.FileField(upload_to='comprehensive_exam_milestones/', null=True, blank=True)

    reported_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='comprehensive_attempts_reported',
        help_text="Whichever RPC member finalized the panel (moved rpc_pending -> pgcs_pending).",
    )
    reported_at = models.DateTimeField(null=True, blank=True)

    # Convener (PGCS) review — HOD of the student's department stands in.
    pgcs_remarks = models.TextField(blank=True)
    pgcs_reviewed_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='comprehensive_attempts_pgcs_reviewed',
    )
    pgcs_reviewed_at = models.DateTimeField(null=True, blank=True)

    # Dean Academic — forward-only final approval, no remarks/rejection.
    dean_approved_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='comprehensive_attempts_dean_approved',
    )
    dean_approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('exam', 'attempt_number')
        ordering = ['exam', 'attempt_number']

    def __str__(self):
        return f"Attempt {self.attempt_number} — {self.exam}"


class ComprehensiveExamConsent(models.Model):
    """RPC member consent for a comprehensive exam attempt's shared result panel."""
    attempt = models.ForeignKey(ComprehensiveExamAttempt, related_name='consents', on_delete=models.CASCADE)
    member = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    consented = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('attempt', 'member')


class ComprehensiveExamRPCComment(models.Model):
    """RPC member's personal comment on a comprehensive exam attempt."""
    attempt = models.ForeignKey(ComprehensiveExamAttempt, related_name='rpc_comments', on_delete=models.CASCADE)
    member = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('attempt', 'member')
        ordering = ['-timestamp']


# ===========================================================================
# Open Seminar
# ===========================================================================

class OpenSeminar(models.Model):
    """PhD Open Seminar — parent record, one per student.

    Holds the one-time gate: eligibility snapshot + Convener (DPGC, HOD of
    the student's department) review + Dean Academic approval (which
    appoints the Dean Nominee). This only happens once per student -- unlike
    ComprehensiveExam, retries skip straight back to RPC review, not through
    this gate again. There is no separate examination committee here: the
    student's existing RPC (Progress Seminar committee, CommitteeMember via
    their ThesisTopic) doubles as the examination committee and is read
    live, never proposed/stored here.
    """
    STATUS_CHOICES = [
        ('hod_pending', 'Pending Convener (DPGC) Review'),
        ('hod_rejected', 'Rejected by Convener (DPGC)'),
        ('dean_pending', 'Pending Dean Academic Approval'),
        ('dean_rejected', 'Rejected by Dean Academic'),
        ('in_progress', 'Approved — In Progress'),
        ('satisfactory', 'Satisfactory'),
    ]

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='open_seminar')
    supervisor = models.ForeignKey(Faculty, related_name='open_seminars_supervised', on_delete=models.CASCADE)
    co_supervisor = models.ForeignKey(Faculty, related_name='open_seminars_cosupervised', on_delete=models.CASCADE, null=True, blank=True)

    possible_thesis_title = models.CharField(max_length=300, blank=True)
    proposed_date = models.DateField(
        null=True, blank=True,
        help_text="Set by the supervisor at proposal time; seeds attempt 1's seminar_date once Dean approves.",
    )

    # Eligibility snapshot -- computed once at proposal, not re-verified per
    # attempt (moved here from the attempt, since this gate is one-time).
    # course_work/progress_seminar/thesis_research are computed server-side
    # from the student's own records; teaching_credits has no numeric source
    # anywhere in Fusion and stays manual.
    course_work_credits = models.PositiveIntegerField(default=0)
    progress_seminar_credits = models.PositiveIntegerField(default=0)
    thesis_research_credits = models.PositiveIntegerField(default=0)
    teaching_credits = models.PositiveIntegerField(default=0)
    semesters_completed = models.PositiveIntegerField(default=0)
    rpc_recommended_open_seminar = models.BooleanField(default=False)
    first_draft_document = models.FileField(upload_to='open_seminar_first_drafts/', null=True, blank=True)

    # Convener (DPGC) early review -- HOD of the student's department stands in.
    hod_remarks = models.TextField(blank=True)
    hod_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='open_seminars_hod_reviewed',
    )
    hod_at = models.DateTimeField(null=True, blank=True)

    # Dean Academic early approval -- appoints the Dean Nominee (on attempt 1).
    dean_remarks = models.TextField(blank=True)
    dean_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='open_seminars_dean_approved',
    )
    dean_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='hod_pending')
    current_attempt_number = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_credits(self):
        return (
            self.course_work_credits + self.progress_seminar_credits
            + self.thesis_research_credits + self.teaching_credits
        )

    def __str__(self):
        return f"Open Seminar — {self.student.id.user.get_full_name()}"


class OpenSeminarAttempt(models.Model):
    """One attempt (unlimited) of the Open Seminar: RPC review, verdict, and
    (attempt 1 only) the Dean Nominee's separate confidential report.

    The RPC (the student's existing committee) collectively records the
    result + comments, each member individually consenting — mirroring
    ProgressSeminarEntry/ProgressSeminarConsent and ComprehensiveExamAttempt.
    Convener (DPGC) then reviews the finalized result before forwarding to
    Dean Academic for final approval.
    """
    STATUS_CHOICES = [
        ('rpc_pending', 'Pending RPC Consensus'),
        ('hod_review_pending', 'RPC Finalized — Pending Convener (DPGC) Review'),
        ('dean_pending', 'Approved by Convener — Pending Dean Academic'),
        ('satisfactory', 'Satisfactory'),
        ('not_satisfactory', 'Not Satisfactory'),
    ]
    RESULT_CHOICES = [('satisfactory', 'Satisfactory'), ('not_satisfactory', 'Not Satisfactory')]

    RATING_3WAY = [('Enough', 'Enough'), ('Just', 'Just Sufficient'), ('Insuff', 'Insufficient')]
    QUALITY_CHOICES = [('Excellent', 'Excellent'), ('Good', 'Good'), ('Sat', 'Satisfactory'), ('Unsat', 'Unsatisfactory')]

    open_seminar = models.ForeignKey(OpenSeminar, related_name='attempts', on_delete=models.CASCADE)
    attempt_number = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='rpc_pending')

    seminar_date = models.DateField(
        null=True, blank=True,
        help_text="Settable by the supervisor or any RPC member; may be updated again when RPC finalizes.",
    )

    # Committee's joint verdict -- filled collectively by the RPC (shared
    # panel, like Progress Seminar / Comprehensive Exam).
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, null=True, blank=True)
    committee_comments = models.TextField(blank=True)
    reported_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='open_seminar_attempts_reported',
        help_text="Whichever RPC member finalized the panel (moved rpc_pending -> hod_review_pending).",
    )
    reported_at = models.DateTimeField(null=True, blank=True)

    # Convener (DPGC) review, post-RPC -- HOD of the student's department stands in.
    hod_review_remarks = models.TextField(blank=True)
    hod_reviewed_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='open_seminar_attempts_hod_reviewed',
    )
    hod_reviewed_at = models.DateTimeField(null=True, blank=True)

    # Dean Academic final approval -- forward-only, no remarks/rejection.
    dean_approved_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='open_seminar_attempts_dean_approved',
    )
    dean_approved_at = models.DateTimeField(null=True, blank=True)

    # Dean Nominee -- ad-hoc faculty appointment, made once by the Dean at
    # OpenSeminar's early-approval step (attempt 1 only; retries skip that
    # gate and never get a new nominee). Submits their own confidential
    # report independently -- mirrors "Report of Dean Nominee" form. Kept
    # out of any dict/serializer shown to student/supervisor/committee; only
    # Convener/Dean Academic and the nominee themselves should ever see
    # the dn_* fields.
    dean_nominee = models.ForeignKey(
        Faculty, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='open_seminar_nominations',
    )
    dn_quality = models.CharField(max_length=20, choices=QUALITY_CHOICES, blank=True)
    dn_quantity = models.CharField(max_length=10, choices=RATING_3WAY, blank=True)
    dn_publications = models.CharField(max_length=10, choices=RATING_3WAY, blank=True)
    dn_overall = models.CharField(max_length=20, choices=RESULT_CHOICES, blank=True)
    dn_comments = models.TextField(blank=True)
    dn_submitted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('open_seminar', 'attempt_number')
        ordering = ['open_seminar', 'attempt_number']

    def __str__(self):
        return f"Open Seminar Attempt {self.attempt_number} — {self.open_seminar}"


class OpenSeminarConsent(models.Model):
    """RPC member consent for an open seminar attempt's shared result panel."""
    attempt = models.ForeignKey(OpenSeminarAttempt, related_name='consents', on_delete=models.CASCADE)
    member = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    consented = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('attempt', 'member')


class OpenSeminarRPCComment(models.Model):
    """RPC member's personal comment on an open seminar attempt."""
    attempt = models.ForeignKey(OpenSeminarAttempt, related_name='rpc_comments', on_delete=models.CASCADE)
    member = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('attempt', 'member')
        ordering = ['-timestamp']


# ===========================================================================
# Teaching Credit
# ===========================================================================
# Workflow: [Precondition: ComprehensiveExam.status == 'passed'] -> Student
# submits 4 course choices for a semester -> HOD allocates one of the 4 (or
# sends it back with remarks, student edits and resubmits) -> [offline
# teaching] -> any student registered for the allocated course that semester
# submits one anonymous evaluation -> HOD reviews the aggregated (anonymized)
# evaluations and marks the registration completed with a satisfactory/
# not_satisfactory result (satisfactory awards the credit; not_satisfactory
# is terminal -- no retry, a fresh attempt would just be a new semester's
# registration).

class TeachingCreditAllocation(models.Model):
    """PhD student's teaching-credit registration for a semester."""
    STATUS_CHOICES = [
        ('pending', 'Pending HOD Decision'),
        ('sent_back', 'Sent Back by HOD'),
        ('allocated', 'Course Allocated'),
        ('completed', 'Completed'),
    ]
    RESULT_CHOICES = [('satisfactory', 'Satisfactory'), ('not_satisfactory', 'Not Satisfactory')]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='teaching_credit_allocations')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    choice_1 = models.ForeignKey(Courses, on_delete=models.CASCADE, related_name='teaching_credit_choice1')
    choice_2 = models.ForeignKey(Courses, on_delete=models.CASCADE, related_name='teaching_credit_choice2', null=True, blank=True)
    choice_3 = models.ForeignKey(Courses, on_delete=models.CASCADE, related_name='teaching_credit_choice3', null=True, blank=True)
    choice_4 = models.ForeignKey(Courses, on_delete=models.CASCADE, related_name='teaching_credit_choice4', null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    allocated_course = models.ForeignKey(
        Courses, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='teaching_credit_allocations',
    )
    hod_remarks = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='teaching_credit_decisions',
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    result = models.CharField(max_length=20, choices=RESULT_CHOICES, null=True, blank=True)
    completed_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='teaching_credit_completions',
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'semester')

    def __str__(self):
        return f"Teaching Credit — {self.student.id.user.get_full_name()} ({self.semester})"


class TeachingCreditEvaluationResponse(models.Model):
    """One class-student's anonymous evaluation of the Research Scholar's teaching.

    respondent is stored only to enforce one submission per student; it is
    never exposed via the API -- only aggregated stats and anonymized
    comments are shown to HOD/anyone else.
    """
    BAND_CHOICES = [
        ('<80', '<80%'), ('80-90', '80%-90%'), ('90-95', '90%-95%'), ('95-100', '95%-100%'),
    ]
    QUALITY_CHOICES = [
        ('Poor', 'Poor'), ('Average', 'Average'), ('Good', 'Good'), ('Excellent', 'Excellent'),
    ]

    registration = models.ForeignKey(TeachingCreditAllocation, related_name='evaluations', on_delete=models.CASCADE)
    respondent = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='teaching_credit_evaluations_given')

    punctuality_band = models.CharField(max_length=10, choices=BAND_CHOICES, blank=True)
    schedule_adherence_band = models.CharField(max_length=10, choices=BAND_CHOICES, blank=True)
    topics_sequence = models.CharField(max_length=10, choices=QUALITY_CHOICES, blank=True)
    teaching_aids = models.CharField(max_length=10, choices=QUALITY_CHOICES, blank=True)
    questions_answered = models.CharField(max_length=10, choices=QUALITY_CHOICES, blank=True)
    overall_effectiveness = models.CharField(max_length=10, choices=QUALITY_CHOICES, blank=True)
    strengths_weaknesses = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('registration', 'respondent')

    def __str__(self):
        return f"Evaluation for {self.registration} by respondent #{self.respondent_id}"
