from rest_framework.authtoken.models import Token
from rest_framework import serializers


from applications.academic_procedures.models import (course_registration)

class CourseRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = course_registration
        fields = ('__all__')