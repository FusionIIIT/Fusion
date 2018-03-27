from django.db import models

from applications.academic_information.models import Course, Student
from applications.globals.models import ExtraInfo


class CourseDocuments(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    upload_time = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=100)
    document_name = models.CharField(max_length=40)
    document_url = models.CharField(max_length=100, null=True)

    def __str__(self):
        return '{} - {}'.format(self.course_id, self.document_name)


class CourseVideo(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    upload_time = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=100)
    video_name = models.CharField(max_length=40)
    video_url = models.CharField(max_length=100, null=True)

    def __str__(self):
        return '{} - {}'.format(self.course_id, self.video_name)


class Topics(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    topic_name = models.TextField(max_length=200)

    def __str__(self):
        return '{} - {} - {}'.format(self.pk, self.course_id, self.topic_name)


class QuestionBank(models.Model):
    instructor_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return '{} - {} - {}'.format(self.pk, self.instructor_id, self.name)


class Question(models.Model):
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topics, on_delete=models.CASCADE)
    question = models.TextField(max_length=1000)
    options1 = models.CharField(null=True, max_length=100)
    options2 = models.CharField(null=True, max_length=100)
    options3 = models.CharField(null=True, max_length=100)
    options4 = models.CharField(null=True, max_length=100)
    options5 = models.CharField(null=True, max_length=100)
    answer = models.IntegerField()
    image = models.TextField(max_length=1000, null=True)
    marks = models.IntegerField()

    # def __str__(self):
    #     return '{} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {}'.format(
    #         self.pk, self.question_bank, self.question, self.topic, self.options1,
    #         self.options2, self.options3, self.options4,
    #         self.options5, self.answer)


class Quiz(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    quiz_name = models.CharField(max_length=20)
    end_time = models.DateTimeField()
    start_time = models.DateTimeField()
    d_day = models.CharField(max_length=2)
    d_hour = models.CharField(max_length=2)
    d_minute = models.CharField(max_length=2)
    negative_marks = models.FloatField(default=0)
    number_of_question = models.IntegerField(default=0)
    description = models.TextField(max_length=1000)
    rules = models.TextField(max_length=2000)
    total_score = models.IntegerField(default=0)

    def __str__(self):
        return '{} - {} - {} - {} - {}'.format(
                self.pk, self.course_id,
                self.start_time, self.end_time,
                self.negative_marks)


class QuizQuestion(models.Model):
    quiz_id = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return '{} - {}'.format(
            self.pk, self.question)


class Practice(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    prac_quiz_name = models.CharField(max_length=20)
    negative_marks = models.FloatField(default=0)
    number_of_question = models.IntegerField(default=0)
    description = models.TextField(max_length=1000)
    total_score = models.IntegerField(default=0)

    def __str__(self):
        return '{} - {} - {} - {} - {}'.format(
                self.pk, self.course_id,
                self.negative_marks)


class PracticeQuestion(models.Model):
    prac_quiz_id = models.ForeignKey(Practice, on_delete=models.CASCADE)
    question = models.TextField(max_length=1000)
    options1 = models.CharField(null=True, max_length=100)
    options2 = models.CharField(null=True, max_length=100)
    options3 = models.CharField(null=True, max_length=100)
    options4 = models.CharField(null=True, max_length=100)
    options5 = models.CharField(null=True, max_length=100)
    answer = models.IntegerField()
    image = models.TextField(max_length=1000, null=True)

    def __str__(self):
        return '{} - {} - {} - {} - {} - {} - {} - {} - {}'.format(
            self.pk, self.quiz_id, self.options1,
            self.options2, self.options3, self.options4,
            self.options5, self.answer, self.announcement)


class StudentAnswer(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz_id = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question_id = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    choice = models.IntegerField()

    def __str__(self):
        return '{} - {} - {} - {} - {}'.format(
                self.pk, self.student_id,
                self.quiz_id, self.question_id,
                self.choice)


class Assignment(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    upload_time = models.DateTimeField(auto_now=True)
    submit_date = models.DateTimeField()
    assignment_name = models.CharField(max_length=100)
    assignment_url = models.CharField(max_length=100, null=True)

    def __str__(self):
        return '{} - {} - {}'.format(self.pk, self.course_id, self.assignment_name)


class StudentAssignment(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    assignment_id = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    upload_time = models.DateTimeField(auto_now=True)
    upload_url = models.TextField(max_length=200)
    score = models.IntegerField(null=True)
    feedback = models.CharField(max_length=100, null=True)
    assign_name = models.CharField(max_length=100)

    def __str__(self):
        return '{} - {} - {} - {} - {}'.format(
                self.pk, self.student_id,
                self.assignment_id, self.score,
                self.feedback)


class QuizResult(models.Model):
    quiz_id = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    score = models.IntegerField()
    finished = models.BooleanField(default=False)

    def __str__(self):
        return '{} - {} - {} - {} - {}'.format(
                self.pk, self.student_id,
                self.quiz_id, self.score,
                self.feedback)


class Forum(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    commenter_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    comment_time = models.DateTimeField(auto_now=True)
    comment = models.TextField(max_length=2000)

    def __str__(self):
        return '{} - {} - {} - {}'.format(
            self.pk, self.course_id,
            self.commenter_id,
            self.comment)


class ForumReply(models.Model):
    forum_ques = models.ForeignKey(Forum, on_delete=models.CASCADE,
                                   related_name='forum_ques')
    forum_reply = models.ForeignKey(Forum, on_delete=models.CASCADE,
                                    related_name='forum_reply')

    def __str__(self):
        return '{} - {} - {}'.format(self.pk, self.forum_ques, self.forum_reply)
