from rest_framework.authtoken.models import Token
from rest_framework import serializers

from applications.placement_cell.models import (Achievement, Course, Education,
                                                Experience, Has, Patent,
                                                Project, Publication, Skill,
                                                PlacementStatus, NotifyStudent,
                                                Company, JobPosting, JobApplication,
                                                InterviewSchedule, InterviewPanel,
                                                JobOffer, Announcement, PlacementPolicy)

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


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('approval_status', 'approved_by', 'created_at', 'updated_at')


class CompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for company listings."""
    class Meta:
        model = Company
        fields = ('id', 'name', 'domain', 'website', 'approval_status')


class JobPostingSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    total_applications = serializers.IntegerField(read_only=True)
    is_deadline_passed = serializers.BooleanField(read_only=True)
    required_skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = JobPosting
        fields = '__all__'
        read_only_fields = ('posted_by', 'created_at', 'updated_at')


class JobPostingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job listing pages."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    total_applications = serializers.IntegerField(read_only=True)

    class Meta:
        model = JobPosting
        fields = ('id', 'title', 'company', 'company_name', 'job_type', 'ctc',
                  'location', 'application_deadline', 'is_active', 'total_applications')


class JobApplicationSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_roll = serializers.CharField(source='student.id.id', read_only=True)
    job_title = serializers.CharField(source='job_posting.title', read_only=True)
    company_name = serializers.CharField(source='job_posting.company.name', read_only=True)

    class Meta:
        model = JobApplication
        fields = '__all__'
        read_only_fields = ('applied_at', 'updated_at')

    def get_student_name(self, obj):
        user = obj.student.id.user
        return '{} {}'.format(user.first_name, user.last_name)


class InterviewScheduleSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job_posting.title', read_only=True)
    company_name = serializers.CharField(source='job_posting.company.name', read_only=True)

    class Meta:
        model = InterviewSchedule
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at')


class InterviewPanelSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = InterviewPanel
        fields = '__all__'

    def get_student_name(self, obj):
        user = obj.application.student.id.user
        return '{} {}'.format(user.first_name, user.last_name)


class JobOfferSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    company_name = serializers.CharField(
        source='application.job_posting.company.name', read_only=True
    )
    job_title = serializers.CharField(
        source='application.job_posting.title', read_only=True
    )
    is_deadline_passed = serializers.BooleanField(read_only=True)

    class Meta:
        model = JobOffer
        fields = '__all__'
        read_only_fields = ('extended_at', 'responded_at')

    def get_student_name(self, obj):
        user = obj.application.student.id.user
        return '{} {}'.format(user.first_name, user.last_name)


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')

    def get_created_by_name(self, obj):
        if obj.created_by:
            return '{} {}'.format(obj.created_by.first_name, obj.created_by.last_name)
        return ''


class PlacementPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacementPolicy
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

