from django.db import models
from applications.academic_information.models import Student, Curriculum
from applications.programme_curriculum.models import Course as Courses, CourseInstructor
from applications.globals.models import ExtraInfo

class Modules(models.Model):
    module_name = models.CharField(max_length=50)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, db_column='course_id_id')

    def __str__(self):
        return self.module_name

class CourseDocuments(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    module_id = models.ForeignKey(Modules, on_delete=models.CASCADE, default=1)
    upload_time = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=100)
    document_name = models.CharField(max_length=40)
    document_url = models.CharField(max_length=100, null=True)

    def __str__(self):
        return '{} - {}'.format(self.course_id, self.document_name)

class AttendanceFiles(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    upload_time = models.DateTimeField(auto_now=True)
    file_name = models.CharField(max_length=40)
    file_url = models.CharField(max_length=100, null=True)

    def __str__(self):
        return '{} - {}'.format(self.course_id, self.file_name)

class CourseVideo(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    upload_time = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=100)
    video_name = models.CharField(max_length=40)
    video_url = models.CharField(max_length=100, null=True)

    def __str__(self):
        return '{} - {}'.format(self.course_id, self.video_name)

class Topics(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    topic_name = models.TextField(max_length=200)

    def __str__(self):
        return '{} - {} - {}'.format(self.pk, self.course_id, self.topic_name)

class QuestionBank(models.Model):
    instructor_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
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

class Quiz(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
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
        return '{} - {} - {} - {} - {}'.format(self.pk, self.course_id, self.start_time, self.end_time, self.negative_marks)

class QuizQuestion(models.Model):
    quiz_id = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return '{} - {}'.format(self.pk, self.question)

class Practice(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    prac_quiz_name = models.CharField(max_length=20)
    negative_marks = models.FloatField(default=0)
    number_of_question = models.IntegerField(default=0)
    description = models.TextField(max_length=1000)
    total_score = models.IntegerField(default=0)

    def __str__(self):
        return '{} - {} - {} - {} - {}'.format(self.pk, self.course_id, self.negative_marks)

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
        return '{} - {} - {} - {} - {} - {} - {} - {} - {}'.format(self.pk, self.prac_quiz_id, self.options1, self.options2, self.options3, self.options4, self.options5, self.answer)

class StudentAnswer(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz_id = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question_id = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    choice = models.IntegerField()

    def __str__(self):
        return '{} - {} - {} - {} - {}'.format(self.pk, self.student_id, self.quiz_id, self.question_id, self.choice)

class Assignment(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
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
        return '{} - {} - {} - {} - {}'.format(self.pk, self.student_id, self.assignment_id, self.score, self.feedback)

class QuizResult(models.Model):
    quiz_id = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    score = models.IntegerField()
    finished = models.BooleanField(default=False)

    def __str__(self):
        return '{} - {} - {} - {} - {}'.format(self.pk, self.student_id, self.quiz_id, self.score, self.finished)

class Forum(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    commenter_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    comment_time = models.DateTimeField(auto_now=True)
    comment = models.TextField(max_length=2000)

    def __str__(self):
        return '{} - {} - {} - {}'.format(self.pk, self.course_id, self.commenter_id, self.comment)

class ForumReply(models.Model):
    forum_ques = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='forum_ques')
    forum_reply = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='forum_reply')

    def __str__(self):
        return '{} - {} - {}'.format(self.pk, self.forum_ques, self.forum_reply)

class GradingScheme(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    type_of_evaluation = models.CharField(max_length=100)
    weightage = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return '{} - {}'.format(self.pk, self.course_id)

class GradingScheme_grades(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    O_Lower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    O_Upper = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    A_plus_Lower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    A_plus_Upper = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    A_Lower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    A_Upper = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    B_plus_Lower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    B_plus_Upper = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    B_Lower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    B_Upper = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    C_plus_Lower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    C_plus_Upper = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    C_Lower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    C_Upper = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    D_plus_Lower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    D_plus_Upper = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    D_Lower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    D_Upper = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    F_Lower = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    F_Upper = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return '{} - {}'.format(self.pk, self.course_id)

class Student_grades(models.Model):
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    semester = models.IntegerField(default=1)
    year = models.IntegerField(default=2016)
    roll_no = models.TextField(max_length=2000)
    grade = models.TextField(max_length=2000)
    batch = models.IntegerField(default=2021)
    remarks = models.CharField(max_length=500, null=True)
    verified = models.BooleanField(default=False)
    reSubmit = models.BooleanField(default=True)

    def __str__(self):
        return '{} - {}'.format(self.pk, self.course_id)

class Attendance(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    instructor_id = models.ForeignKey(CourseInstructor, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.IntegerField(default=0)
    no_of_attendance = models.IntegerField(default=1)

    def __str__(self):
        return '{} - {} - {}'.format(self.pk, self.student_id, self.instructor_id)

class StudentEvaluation(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    evaluation_id = models.ForeignKey(GradingScheme, on_delete=models.CASCADE)
    marks = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total_marks = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return '{} - {} - {} - {}'.format(self.pk, self.student_id, self.evaluation_id, self.marks)