from rest_framework.authtoken.models import Token
from rest_framework import serializers
from applications.department.models import(Announcements)


from applications.academic_procedures.models import (course_registration)

class CourseRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = course_registration
        fields = ('__all__')


class AnnouncementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcements
        fields = ['maker_id', 'ann_date', 'message', 'batch', 'department', 'programme', 'upload_announcement']

class AuthenticationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcements
        fields = '__all__'