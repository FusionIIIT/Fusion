from django.db import models

from applications.academic_information.models import Student
# Create your models here.


POSTIONS= (
    ('student_guide', 'Student_Guide'),
    ('student_coordinator', 'Student_Coordinator'),
)
STATUS= (
    ('status_unresolved', 'Unresolved'),
    ('status_resolved', 'Resolved'),
    ('status_inprogress', 'InProgress'),
)

class CounsellingInfo(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    student_position = models.CharField(max_length=50,choices=POSTIONS,required=True)

    class Meta:
        unique_together = (('student_id', 'student_position'),)

    def __str__(self):
        return f"{self.student_id} - {self.student_position}"

class CounsellingCategory(models.Model):
    counselling_category_id = models.CharField(max_length=40)

class Issues(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    issue_category = models.ForeignKey(CounsellingCategory,on_delete=models.CASCADE)
    issue = models.TextField(max_length=500,)
    issue_status = models.CharField(max_length=20,choices=STATUS,default="status_unresolved")

class FAQ(models.Model):
    counselling_question = models.TextField(max_length=1000)
    counselling_answer = models.TextField(max_length=5000)
    counseliing_category = models.ForeignKey(CounsellingCategory,on_delete=models.CASCADE)

class CounsellingMeeting(models.Model):
    counselling_meeting_time = models.DateTimeField()
    counselling_agenda = models.TextField()
    counselling_venue = models.CharField(max_length=20)

    def __str__(self):
        return '{} - {}'.format(self.meeting, self.agenda)


class CounsellingMinutes(models.Model):
    counselling_meeting_time = models.ForeignKey(CounsellingMeeting, on_delete=models.CASCADE)
    counselling_minutes = models.FileField(upload_to='counselling_cell/')

    def __str__(self):
        return '{} - {}'.format(self.meeting_date.meet_date, self.mess_minutes)




