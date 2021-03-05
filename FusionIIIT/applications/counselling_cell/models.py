from django.db import models

from applications.academic_information.models import Student
# Create your models here.


POSTIONS= (
    ('pos1', 'Student'),
    ('pos2', 'Student_Guide'),
    ('pos3', 'Student_Coordinator'),
)
STATUS= (
    ('status1', 'Unresolved'),
    ('status2', 'Resolved'),
    ('status3', 'InProgress'),
)

ISSUE_CATEGORY= (
    ('category1', 'Academics'),
    ('category2', 'Personal'),
    ('category3', 'Others'),
)

FAQ_CATEGORY= (
    ('category1', 'Academics'),
    ('category2', 'Personal'),
    ('category3', 'Others'),
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


class CounsellingInfo(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    student_position = models.CharField(max_length=50,choices=POSTIONS,default="pos1")

    class Meta:
        unique_together = (('student_id', 'student_position'),)

    def __str__(self):
        return f"{self.student_id} - {self.student_position}"
    

class Issues(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    issue_category = models.CharField(max_length=20, choices=ISSUE_CATEGORY,default="category1")
    issue = models.TextField(max_length=500,)
    status = models.CharField(max_length=20,choices=STATUS,default="status1")

class FAQ(models.Model):
    question = models.TextField(max_length=400)
    answer = models.TextField(max_length=1000)
    category = models.CharField(max_length=20,choices=FAQ_CATEGORY,default="category1")

class Counselling_meeting(models.Model):
    meet_date = models.DateField()
    agenda = models.TextField()
    venue = models.TextField()
    meeting_time = models.CharField(max_length=20, choices=TIME)

    def __str__(self):
        return '{} - {}'.format(self.meet_date, self.agenda)


class Counselling_minutes(models.Model):
    meeting_date = models.OneToOneField(Counselling_meeting, on_delete=models.CASCADE)
    counselling_minutes = models.FileField(upload_to='central_mess/')

    def __str__(self):
        return '{} - {}'.format(self.meeting_date.meet_date, self.mess_minutes)




