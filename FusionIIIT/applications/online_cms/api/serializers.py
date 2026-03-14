# from rest_framework.authtoken.models import Token
# from rest_framework import serializers

# from applications.academic_procedures.models import course_registration


from rest_framework import serializers
from applications.academic_information.models import (Student,Student_attendance,Calendar, Timetable)
from applications.programme_curriculum.models import Course as Courses
from applications.programme_curriculum.models import CourseInstructor
from applications.academic_procedures.models import course_registration
from applications.globals.models import ExtraInfo
from applications.online_cms.models import *

class ExtraInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtraInfo
        fields = '__all__'  # Include all fields

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
        
    def create(self,validated_data):
        return Courses.objects.create(**validated_data)
class RegisteredCoursesSerializer(serializers.ModelSerializer):

    class Meta:
        model = course_registration
        fields = ('__all__')
class CourseRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = ('__all__')

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
        fields = '__all__'  # Include all fields for now (adjust as needed)

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'  # Include all fields for now (adjust as needed)

class ForumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forum
        fields = '__all__'  # Include all fields for now (adjust as needed)

class ForumReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumReply
        fields = '__all__'  # Include all fields for now (adjust as needed)

class GradingSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingScheme
        fields = '__all__'  # Include all fields for now (adjust as needed)

class GradingScheme_gradesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingScheme_grades
        fields = '__all__'  # Include all fields for now (adjust as needed)
class TopicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topics,
        fields = '__all__'
