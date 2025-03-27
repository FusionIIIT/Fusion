from django.db import models
from applications.academic_information.models import Student
from django.contrib.auth.models import User
from applications.globals.models import Faculty,ExtraInfo
from datetime import datetime,date

# Create your models here.

class CounsellingCellConstants :
    STUDENT_POSTIONS= (
        ('student_guide', 'Student Guide'),
        ('student_coordinator', 'Student Coordinator'),
    )
    FACULTY_POSTIONS= (
        ('head_counsellor', 'Head Counsellor'),
        ('faculty_counsellor', 'Faculty Counsellor'),
    )
    
    ISSUE_STATUS= (
        ('status_unresolved', 'Unresolved'),
        ('status_resolved', 'Resolved'),    
        ('status_inprogress', 'InProgress'),
    )
    TIME = (
        ('10', '10 a.m.'),
        ('11', '11 a.m.'),
        ('12', '12 p.m.'),
        ('13', '1 p.m.'),
        ('14', '2 p.m.'),
        ('15', '3 p.m.'),
        ('16', '4 p.m.'),
        ('17', '5 p.m.'),
        ('18', '6 p.m.'),
        ('19', '7 p.m.'),
        ('20', '8 p.m.'),
        ('21', '9 p.m.')
    )

    MEETING_STATUS = (
        ('status_accepted',"Accepted"),
        ('status_pending','Pending')
    )

class FacultyCounsellingTeam(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    faculty_position = models.CharField(max_length=50,choices=CounsellingCellConstants.FACULTY_POSTIONS)

    class Meta:
        unique_together = (('faculty', 'faculty_position'))

    def __str__(self):
        return f"{self.faculty} - {self.faculty_position}"

class StudentCounsellingTeam(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    student_position = models.CharField(max_length=50,choices=CounsellingCellConstants.STUDENT_POSTIONS)

    class Meta:
        unique_together = (('student_id', 'student_position'))

    def __str__(self):
        return f"{self.student} - {self.student_position}"

class StudentCounsellingInfo(models.Model):
    student_guide = models.ForeignKey(StudentCounsellingTeam,on_delete=models.CASCADE)
    student = models.OneToOneField(Student,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student_guide} - {self.student}"

class CounsellingIssueCategory(models.Model):
    category_id = models.CharField(max_length=40,unique=True)
    category = models.CharField(max_length=40)



    def __str__(self):
        return f"{self.category}"

class CounsellingIssue(models.Model):
    issue_raised_date = models.DateTimeField(default=datetime.now)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    issue_category = models.ForeignKey(CounsellingIssueCategory,on_delete=models.CASCADE)
    issue = models.TextField(max_length=500,)
    issue_status = models.CharField(max_length=20,choices=CounsellingCellConstants.ISSUE_STATUS,default="status_unresolved")
    response_remark = models.TextField(max_length=500,null=True)
    resolved_by = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE,null=True)
    
    def __str__(self):
        return f"{self.issue} - {self.student}"

class CounsellingFAQ(models.Model):
    
    counselling_question = models.TextField(max_length=1000)
    counselling_answer = models.TextField(max_length=5000)
    counselling_category = models.ForeignKey(CounsellingIssueCategory,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.counselling_question}"
class CounsellingMeeting(models.Model):
    meeting_host=  models.ForeignKey(ExtraInfo,on_delete=models.CASCADE,null=True, blank=True)
    meeting_date = models.DateField(default=date.today)
    meeting_time = models.CharField(max_length=20, choices=CounsellingCellConstants.TIME)
    agenda = models.TextField()
    venue = models.CharField(max_length=20)
    student_invities = models.TextField(max_length=500,default=None)

    def __str__(self):
        return '{} - {}'.format(self.meeting_time, self.agenda)

    

class CounsellingMinutes(models.Model):
    counselling_meeting = models.ForeignKey(CounsellingMeeting, on_delete=models.CASCADE)
    counselling_minutes = models.FileField(upload_to='counselling_cell/')

    def __str__(self):
        return '{} - {}'.format(self.counselling_meeting, self.counselling_minutes)
    
class StudentMeetingRequest(models.Model):
    requested_time = models.DateTimeField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    description = models.TextField(max_length=1000)
    requested_student_invitee = models.ForeignKey(StudentCounsellingTeam,on_delete=models.CASCADE,null=True, blank=True)
    requested_faculty_invitee = models.ForeignKey(FacultyCounsellingTeam,on_delete=models.CASCADE,null=True, blank=True)
    requested_meeting_status = models.CharField(max_length=20,choices=CounsellingCellConstants.MEETING_STATUS,default="status_pending")
    recipient_reply = models.TextField(max_length=1000)



    def __str__(self):
        return f"{self.student} - {self.requested_time}"





