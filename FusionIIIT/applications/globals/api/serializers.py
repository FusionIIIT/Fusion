from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers

from notifications.models import Notification

from applications.globals.models import (ExtraInfo, HoldsDesignation, DepartmentInfo,
                                        Designation, Issue, IssueImage, Feedback)

from applications.placement_cell.api.serializers import (SkillSerializer, HasSerializer,
                                                        EducationSerializer, CourseSerializer, ExperienceSerializer,
                                                        ProjectSerializer, AchievementSerializer, PublicationSerializer,
                                                        PatentSerializer, PlacementStatusSerializer, NotifyStudentSerializer)

User = get_user_model()

class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30, required=True)
    password = serializers.CharField(required=True, write_only=True)


class AuthTokenSerializer(serializers.ModelSerializer):
    auth_token = serializers.SerializerMethodField()

    class Meta:
         model = User
         fields = ('auth_token',)

    def get_auth_token(self, obj):
        token, _ = Token.objects.get_or_create(user=obj)
        return token.key


class ProfileSkillCreateSerializer(serializers.Serializer):
    skill_name = serializers.CharField(max_length=255)
    skill_rating = serializers.IntegerField(min_value=1, max_value=5)


class ProfileSubmitSerializer(serializers.Serializer):
    about = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    age = serializers.DateField(required=True)
    address = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    contact = serializers.IntegerField(required=True, min_value=1000000000, max_value=999999999999)


class ProfileDeleteRequestSerializer(serializers.Serializer):
    deleteskill = serializers.CharField(required=False)
    deleteedu = serializers.CharField(required=False)
    deletecourse = serializers.CharField(required=False)
    deleteexp = serializers.CharField(required=False)
    deletepro = serializers.CharField(required=False)
    deleteach = serializers.CharField(required=False)
    deletepub = serializers.CharField(required=False)
    deletepat = serializers.CharField(required=False)

    def validate(self, attrs):
        delete_keys = [key for key, value in attrs.items() if value not in [None, ""]]
        if len(delete_keys) != 1:
            raise serializers.ValidationError("Exactly one delete action key is required.")
        attrs["delete_key"] = delete_keys[0]
        return attrs

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model=Notification
        fields = (
            'id', 'level', 'unread', 'verb', 'description', 'timestamp',
            'public', 'deleted', 'emailed', 'data',
            'actor_content_type', 'actor_object_id',
            'target_content_type', 'target_object_id',
            'action_object_content_type', 'action_object_object_id',
            'recipient'
        )

class DepartmentInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = DepartmentInfo
        fields = ('id', 'name')

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
        fields = ('id', 'name', 'full_name', 'type')

class HoldsDesignationSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    designation = DesignationSerializer()

    class Meta:
        model = HoldsDesignation
        fields = ('user','designation','held_at')


class IssueImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueImage
        fields = ("id", "image")


class IssueListSerializer(serializers.ModelSerializer):
    images = IssueImageSerializer(many=True, read_only=True)
    support_count = serializers.SerializerMethodField()
    is_supported = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = (
            "id",
            "title",
            "text",
            "module",
            "report_type",
            "closed",
            "timestamp",
            "added_on",
            "images",
            "support_count",
            "is_supported",
            "is_owner",
            "username",
        )

    def get_support_count(self, obj):
        return obj.support.count()

    def get_is_supported(self, obj):
        user = self.context.get("request").user
        return obj.support.filter(id=user.id).exists()

    def get_is_owner(self, obj):
        user = self.context.get("request").user
        return obj.user_id == user.id

    def get_username(self, obj):
        return obj.user.username


class IssueCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ("module", "report_type", "title", "text")


class FeedbackSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = ("id", "rating", "feedback", "timestamp", "username")

    def get_username(self, obj):
        return obj.user.username


class FeedbackCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ("rating", "feedback")


# Backward-compatible aliases used by existing views.
UserLoginSerializer = LoginRequestSerializer
AuthUserSerializer = AuthTokenSerializer
