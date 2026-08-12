from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers

from notifications.models import Notification

from applications.globals.models import (ExtraInfo, HoldsDesignation, DepartmentInfo,
                                        Designation, Announcement)

from applications.placement_cell.api.serializers import (SkillSerializer, HasSerializer,
                                                        EducationSerializer, CourseSerializer, ExperienceSerializer,
                                                        ProjectSerializer, AchievementSerializer, PublicationSerializer,
                                                        PatentSerializer, PlacementStatusSerializer, NotifyStudentSerializer)

User = get_user_model()

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30, required=True)
    password = serializers.CharField(required=True, write_only=True)


class AuthUserSerializer(serializers.ModelSerializer):
    auth_token = serializers.SerializerMethodField()

    class Meta:
         model = User
         fields = ('auth_token',)

    def get_auth_token(self, obj):
        Token.objects.filter(user=obj).delete()
        token = Token.objects.create(user=obj)
        return token.key

class NotificationSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model=Notification
        fields=('__all__')

    def get_data(self, obj):
        import json, ast
        payload = obj.data
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                try:
                    payload = ast.literal_eval(payload)
                except Exception:
                    payload = {}
        return json.dumps(payload if isinstance(payload, dict) else {})

class DepartmentInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = DepartmentInfo
        fields = ('__all__')

class ExtraInfoSerializer(serializers.ModelSerializer):
    department = DepartmentInfoSerializer()
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

class AnnouncementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Announcement
        fields = ('id', 'title', 'message', 'audience_type', 'target_role',
                'target_department', 'target_batch', 'target_users', 'created_at')
        extra_kwargs = {
            'target_role': {'required': False, 'allow_null': True},
            'target_department': {'required': False, 'allow_null': True},
            'target_batch': {'required': False, 'allow_null': True},
            'target_users': {'required': False},
        }

    def validate(self, attrs):
        audience_type = attrs.get('audience_type')
        required_field = {
            'role': 'target_role',
            'department': 'target_department',
            'batch': 'target_batch',
        }.get(audience_type)
        if required_field and not attrs.get(required_field):
            raise serializers.ValidationError(
                {required_field: f"This field is required when audience_type is '{audience_type}'."})
        if audience_type == 'individual' and not attrs.get('target_users'):
            raise serializers.ValidationError(
                {'target_users': "This field is required when audience_type is 'individual'."})
        return attrs
