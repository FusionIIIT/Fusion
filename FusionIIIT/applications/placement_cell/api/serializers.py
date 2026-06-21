from rest_framework.authtoken.models import Token
from rest_framework import serializers

from applications.placement_cell.models import (Achievement, Course, Education,
                                                Experience, Has, Patent,
                                                Project, Publication, Skill,
                                                PlacementAppeal, PlacementStatus,
                                                NotifyStudent, PlacementAnnouncement,
                                                OffCampusPlacement,
                                                PlacementCalendarEvent)


class PlacementAppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacementAppeal
        fields = '__all__'

class SkillSerializer(serializers.ModelSerializer):

    class Meta:
        model = Skill
        fields = ('__all__')

class HasSerializer(serializers.ModelSerializer):
    skill_id = SkillSerializer()

    class Meta:
        model = Has
        fields = ('id', 'skill_id', 'skill_rating')

    def create(self, validated_data):
        skill = validated_data.pop('skill_id')
        skill_id, created = Skill.objects.get_or_create(**skill)
        try:
            has_obj = Has.objects.create(skill_id=skill_id,**validated_data)
        except:
            raise serializers.ValidationError({'skill': 'This skill is already present'})
        return has_obj

    def update(self, instance, validated_data):
        skill = validated_data.pop('skill_id', None)
        if skill:
            skill_id, _ = Skill.objects.get_or_create(**skill)
            duplicate = Has.objects.filter(
                unique_id=instance.unique_id,
                skill_id=skill_id,
            ).exclude(pk=instance.pk).exists()
            if duplicate:
                raise serializers.ValidationError({'skill': 'This skill is already present'})
            instance.skill_id = skill_id
        if 'skill_rating' in validated_data:
            instance.skill_rating = validated_data['skill_rating']
        instance.save()
        return instance

class EducationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Education
        fields = ('__all__')

class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = ('__all__')

class ExperienceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Experience
        fields = ('__all__')

class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ('__all__')

class AchievementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Achievement
        fields = ('__all__')

class PublicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publication
        fields = ('__all__')

class PatentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patent
        fields = ('__all__')

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
