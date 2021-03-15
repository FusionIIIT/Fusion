from django.db import models
from applications.academic_information.models import Student
from applications.globals.models import Faculty
# Create your models here.

class CounsellingCellConstants :
    STUDENT_POSTIONS= (
        ('student_guide', 'Student_Guide'),
        ('student_coordinator', 'Student_Coordinator'),
    )
    FACULTY_POSTIONS= (
        ('head_counsellor', 'Head_Counsellor'),
        ('counsellor', 'Counsellor'),
    )
    
    STATUS= (
        ('status_unresolved', 'Unresolved'),
        ('status_resolved', 'Resolved'),
        ('status_inprogress', 'InProgress'),
    )

class FacultyCounsellingInfo(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    faculty_position = models.CharField(max_length=50,choices=CounsellingCellConstants.FACULTY_POSTIONS,required=True)

    class Meta:
        unique_together = (('faculty', 'faculty_position'))

    def __str__(self):
        return f"{self.student} - {self.student_position}"

class StudentCounsellingInfo(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    student_position = models.CharField(max_length=50,choices=CounsellingCellConstants.STUDENT_POSTIONS,required=True)

    class Meta:
        unique_together = (('student_id', 'student_position'))

    def __str__(self):
        return f"{self.student} - {self.student_position}"

class CounsellingTeam(models.Model):
    faculty = models.ForeignKey(FacultyCounsellingInfo ,on_delete=models.CASCADE)
    student_guide = models.ForeignKey(StudentCounsellingInfo,on_delete=models.CASCADE)
    student = models.ForeignKey(Student,on_delete=models.CASCADE)

    class Meta:
        unique_together = (('faculty', 'student_guide','student'))

    def __str__(self):
        return f"{self.faculty} - {self.student_guide} - {self.student}"

class CounsellingIssueCategory(models.Model):
    category = models.CharField(max_length=40)

    def __str__(self):
        return f"{self.category}"

class Issues(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    issue_category = models.ForeignKey(CounsellingCategory,on_delete=models.CASCADE)
    issue = models.TextField(max_length=500,)
    issue_status = models.CharField(max_length=20,choices=CounsellingCellConstants.STATUS,default="status_unresolved")

    def __str__(self):
        return f"{self.issue} - {student}"

class FAQ(models.Model):
    
    counselling_question = models.TextField(max_length=1000)
    counselling_answer = models.TextField(max_length=5000)
    counseliing_category = models.ForeignKey(CounsellingCategory,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.counselling_question}"

class CounsellingMeeting(models.Model):
    meeting_host_student =  models.ForeignKey(StudentCounsellingInfo,on_delete=models.CASCADE,default="Not Available")
    meeting_host_faculty = models.ForeignKey(FacultyCounsellingInfo,on_delete=models.CASCADE,default="Not Available")
    meeting_time = models.DateTimeField()
    agenda = models.TextField()
    venue = models.CharField(max_length=20)
    student_invities = models.ManyToManyField(Student)
    faculty_invities = models.ManyToManyField(FacultyCounsellingInfo)

    def __str__(self):
        return '{} - {}'.format(self.meeting, self.agenda)
    

class CounsellingMinutes(models.Model):
    counselling_meeting_time = models.ForeignKey(CounsellingMeeting, on_delete=models.CASCADE)
    counselling_minutes = models.FileField(upload_to='counselling_cell/')

    def __str__(self):
        return '{} - {}'.format(self.meeting_date.meet_date, self.mess_minutes)





