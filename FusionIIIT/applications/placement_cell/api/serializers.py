from rest_framework.authtoken.models import Token
from rest_framework import serializers

from applications.placement_cell.models import (Achievement, Course, Education,
                                                Experience, Has, Patent,
                                                Project, Publication, Skill,
                                                PlacementStatus, NotifyStudent)

class SkillSerializer(serializers.ModelSerializer):

    class Meta:
        model = Skill
        fields = ('__all__')

class HasSerializer(serializers.ModelSerializer):
    skill_id = SkillSerializer()

    class Meta:
        model = Has
        fields = ('skill_id','skill_rating')

    def create(self, validated_data):
        skill = validated_data.pop('skill_id')
        skill_id, created = Skill.objects.get_or_create(**skill)
        try:
            has_obj = Has.objects.create(skill_id=skill_id,**validated_data)
        except:
            raise serializers.ValidationError({'skill': 'This skill is already present'})
        return has_obj

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
