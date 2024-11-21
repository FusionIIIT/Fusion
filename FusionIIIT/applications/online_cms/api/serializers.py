from rest_framework import serializers
from applications.academic_information.models import Student
from applications.programme_curriculum.models import Course as Courses, CourseInstructor
from applications.academic_procedures.models import course_registration
from applications.globals.models import ExtraInfo
from applications.online_cms.models import (
    Modules, 
    CourseDocuments, 
    Assignment, 
    Attendance, 
    Forum, 
    ForumReply, 
    GradingScheme, 
    GradingScheme_grades, 
    Topics,
    Student_grades
)



class ExtraInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtraInfo
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class CourseInstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseInstructor
        fields = '__all__'

class CoursesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = '__all__'

    def create(self, validated_data):
        return Courses.objects.create(**validated_data)

class RegisteredCoursesSerializer(serializers.ModelSerializer):
    class Meta:
        model = course_registration
        fields = '__all__'

class CourseRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = '__all__'

class ModulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modules
        fields = '__all__'

class CourseDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseDocuments
        fields = '__all__'

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'

class ForumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forum
        fields = '__all__'

class ForumReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumReply
        fields = '__all__'

class GradingSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingScheme
        fields = '__all__'

class GradingSchemeGradesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingScheme_grades
        fields = '__all__'

class TopicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topics
        fields = '__all__'
class StudentGradesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student_grades
        fields = '__all__'
