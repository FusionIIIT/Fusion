from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers

from notifications.models import Notification

from applications.globals.models import (ExtraInfo, HoldsDesignation, DepartmentInfo,
                                        Designation)

from applications.placement_cell.api.serializers import (SkillSerializer, HasSerializer,
                                                        EducationSerializer, CourseSerializer, ExperienceSerializer,
                                                        ProjectSerializer, AchievementSerializer, PublicationSerializer,
                                                        PatentSerializer, PlacementStatusSerializer, NotifyStudentSerializer)

User = get_user_model()

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class AuthUserSerializer(serializers.ModelSerializer):
    auth_token = serializers.SerializerMethodField()

    class Meta:
         model = User
         fields = ('auth_token',)

    def get_auth_token(self, obj):
        token, _ = Token.objects.get_or_create(user=obj)
        return token.key

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model=Notification
        fields=('__all__')

class DepartmentInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = DepartmentInfo
        fields = ('__all__')

class ExtraInfoSerializer(serializers.ModelSerializer):
    department = DepartmentInfoSerializer()

    def validate_phone_no(self, value):
        if value in [None, ""]:
            return value

        phone_no = str(value).strip()
        if not phone_no.isdigit() or len(phone_no) != 10:
            raise serializers.ValidationError("Phone number must contain exactly 10 digits.")
        return int(phone_no)

    class Meta:
        model = ExtraInfo
        fields = ('department','id','title','sex','date_of_birth',
                'address','phone_no','user_type','user_status','about_me')

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        exclude = ('password',)

class DesignationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Designation
        fields = ('__all__')

class HoldsDesignationSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    designation = DesignationSerializer()

    class Meta:
        model = HoldsDesignation
        fields = ('user','designation','held_at')
