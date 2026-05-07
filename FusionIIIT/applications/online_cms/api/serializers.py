from rest_framework import serializers
from ..models import *
from applications.academic_information.models import Course, Curriculum

class CourseSerializer(serializers.ModelSerializer):
    course_code = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'course_name', 'course_details', 'course_code']
        
    def get_course_code(self, obj):
        curr = Curriculum.objects.filter(course_id=obj).first()
        return curr.course_code if curr else None

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['id', 'assignment_name', 'submit_date', 'assignment_url', 'upload_time', 'course_id']

class StudentAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAssignment
        fields = ['id', 'assign_name', 'upload_url', 'score', 'feedback', 'upload_time', 'student_id', 'assignment_id']

class CourseDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseDocuments
        fields = ['id', 'document_name', 'description', 'document_url', 'upload_time', 'course_id']

class ForumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forum
        fields = ['id', 'comment', 'comment_time', 'commenter_id']


class ForumReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumReply
        fields = ['id', 'reply_dict', 'forum_ques_id']

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'quiz_name', 'start_time', 'end_time', 'd_day', 'd_hour', 'd_minute', 'negative_marks', 'number_of_question', 'description', 'rules', 'total_score']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question', 'options1', 'options2', 'options3', 'options4', 'options5', 'answer', 'image', 'marks', 'topic_id']

class QuizResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizResult
        fields = ['id', 'score', 'finished', 'quiz_id', 'student_id']

class QuestionBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionBank
        fields = ['id', 'name', 'course_id']

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topics
        fields = ['id', 'topic_name', 'course_id']

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        from applications.academic_information.models import Student_attendance
        model = Student_attendance
        fields = ['id', 'date', 'present', 'student_id', 'instructor_id']

