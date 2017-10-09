# imports
from django.contrib.auth.models import User
from django.db import models
from applications.globals.models import *
from applications.academic.models import *

class CourseDocuments(models.Model):
    course_id=models.ForeignKey(Course, on_delete=models.CASCADE)
    upload_time=models.DateTimeField()
    description=models.CharField(max_length=100)
    document_name=models.CharField(max_length=40)

class CourseVideo(models.Model):
    course_id=models.ForeignKey(Course, on_delete=models.CASCADE)
    upload_time=models.DateTimeField()
    description=models.CharField(max_length=100)
    video_name=models.CharField(max_length=40)


class Quiz(models.Model):
    course_id=models.ForeignKey(Course, on_delete=models.CASCADE)
    end_time=models.DateTimeField()
    start_time=models.DateTimeField()
    d_day=models.CharField(max_length=2)
    d_hour=models.CharField(max_length=2)
    d_minute=models.CharField(max_length=2)
    negative_marks=models.FloatField(default=0)

class QuizQuestion(models.Model):
    qid=models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question=models.CharField(max_length=1000)
    options1=models.CharField(null=True,max_length=100)
    options2=models.CharField(null=True,max_length=100)
    options3=models.CharField(null=True,max_length=100)
    options4=models.CharField(null=True,max_length=100)
    options5=models.CharField(null=True,max_length=100)
    answer=models.CharField(max_length=100)
    announcement=models.CharField(max_length=2000)
    image=models.CharField(max_length=1000,null=True)
    marks=models.IntegerField()

class StudentAnswer(models.Model):
    student_id=models.ForeignKey(Student,on_delete=models.CASCADE)
    qid=models.ForeignKey(Quiz,on_delete=models.CASCADE)
    qqid=models.ForeignKey(QuizQuestion,on_delete=models.CASCADE)
    choice=models.CharField(max_length=100)

class Assignment(models.Model):
    course_id=models.ForeignKey(Course, on_delete=models.CASCADE)
    upload_time=models.DateTimeField()
    submit_date=models.DateTimeField()
    assignment_name=models.CharField(max_length=100)

class StudentAssignment(models.Model):
    student_id=models.ForeignKey(Student,on_delete=models.CASCADE)
    assignment_id=models.ForeignKey(Assignment,on_delete=models.CASCADE)
    upload_time=models.DateTimeField()
    upload_url=models.CharField(max_length=200)
    score=models.IntegerField()
    feedback=models.CharField(max_length=100)

class QuizResult(models.Model):
    qid=models.ForeignKey(Quiz,on_delete=models.CASCADE)
    student_id=models.ForeignKey(Student,on_delete=models.CASCADE)
    score=models.IntegerField()
    feedback=models.CharField(max_length=100)

class Forum(models.Model):
    course_id=models.ForeignKey(Course, on_delete=models.CASCADE)
    commenter_id=models.ForeignKey(ExtraInfo,on_delete=models.CASCADE)
    comment_time=models.DateTimeField()
    comment=models.CharField(max_length=2000)

class ForumReply(models.Model):
    forum_ques=models.ForeignKey(Forum, on_delete=models.CASCADE,related_name='forum_ques')
    forum_reply=models.ForeignKey(Forum, on_delete=models.CASCADE,related_name='forum_reply')
