from rest_framework.authtoken.models import Token
from rest_framework import serializers

from applications.globals.api.serializers_profile import (  # noqa: F401
    AchievementSerializer, CourseSerializer, EducationSerializer, ExperienceSerializer,
    HasSerializer, PatentSerializer, ProjectSerializer, PublicationSerializer,
    SkillSerializer, StudentBankDetailsSerializer,
)
from applications.placement_cell.models import (Achievement, Course, Education,
                                                Experience, Has, Patent,
                                                Project, Publication, Skill,
                                                StudentBankDetails,
                                                PlacementAppeal, PlacementStatus,
                                                NotifyStudent, PlacementAnnouncement,
                                                OffCampusPlacement,
                                                PlacementCalendarEvent)


class PlacementAppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacementAppeal
        fields = '__all__'

class NotifyStudentSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotifyStudent
        fields = ('__all__')

class PlacementStatusSerializer(serializers.ModelSerializer):
    notify_id = NotifyStudentSerializer()

    class Meta:
        model = PlacementStatus
        fields = ('notify_id', 'invitation', 'placed', 'timestamp', 'no_of_days')


class PlacementAnnouncementSerializer(serializers.ModelSerializer):
    posted_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PlacementAnnouncement
        fields = ('id', 'title', 'body', 'posted_by_name', 'posted_at', 'is_pinned')
        read_only_fields = ('id', 'posted_at')

    def get_posted_by_name(self, obj):
        if obj.posted_by:
            full_name = '{} {}'.format(
                obj.posted_by.first_name, obj.posted_by.last_name
            ).strip()
            return full_name or obj.posted_by.username
        return None


class PlacementAnnouncementWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlacementAnnouncement
        fields = ('title', 'body', 'is_pinned')


class OffCampusPlacementSerializer(serializers.ModelSerializer):
    roll_no = serializers.CharField(source='student.user.username', read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = OffCampusPlacement
        fields = ('id', 'roll_no', 'student_name', 'company_name', 'role',
                  'offer_type', 'ctc', 'stipend', 'offer_date', 'notes', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_student_name(self, obj):
        user = obj.student.user
        return '{} {}'.format(user.first_name, user.last_name).strip()


class OffCampusPlacementWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = OffCampusPlacement
        fields = ('student', 'company_name', 'role', 'offer_type',
                  'ctc', 'stipend', 'offer_date', 'notes')


class PlacementCalendarEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlacementCalendarEvent
        fields = ('id', 'title', 'description', 'start', 'end', 'all_day',
                  'category', 'location', 'created_at')
        read_only_fields = ('id', 'created_at')
