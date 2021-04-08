from rest_framework.authtoken.models import Token
from rest_framework import serializers

from applications.academic_information.models import (Curriculum, Curriculum_Instructor,
                                                      Course)

from applications.globals.api.serializers import ExtraInfoSerializer

class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = ('__all__')

class CurriculumSerializer(serializers.ModelSerializer):
    course_id = CourseSerializer()

    class Meta:
        model = Curriculum
        fields = ('curriculum_id','course_code','course_id','credits','course_type',
                  'programme','branch','batch','sem','optional','floated')

class CurriculumInstructorSerializer(serializers.ModelSerializer):
    curriculum_id = CurriculumSerializer()

    class Meta:
        model = Curriculum_Instructor
        fields = ('curriculum_id', 'chief_inst')
