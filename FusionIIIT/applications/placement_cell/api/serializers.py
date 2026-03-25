from rest_framework.authtoken.models import Token
from rest_framework import serializers

from applications.placement_cell.models import (
    Achievement, Course, Education, Experience, Has, Patent, Project,
    Publication, Skill, PlacementStatus, NotifyStudent, Reference,
    Conference, Extracurricular, Interest, Coauthor, Coinventor,
    PlacementSchedule, PlacementRecord, StudentRecord, ChairmanVisit,
    StudentPlacement, Role, CompanyDetails, MessageOfficer,
    Company, JobPosting, JobApplication, InterviewSchedule,
    InterviewPanel, JobOffer, Announcement, PlacementPolicy,
)


# =============================================
# Legacy Model Serializers (CV / Student Profile)
# =============================================

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
            has_obj = Has.objects.create(skill_id=skill_id, **validated_data)
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

class ReferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reference
        fields = '__all__'


class ConferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Conference
        fields = '__all__'


class ExtracurricularSerializer(serializers.ModelSerializer):

    class Meta:
        model = Extracurricular
        fields = '__all__'


class InterestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Interest
        fields = '__all__'


class CoauthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Coauthor
        fields = '__all__'


class CoinventorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Coinventor
        fields = '__all__'


# =============================================
# Placement Schedule / Status Serializers
# =============================================

class NotifyStudentSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotifyStudent
        fields = ('__all__')


class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = '__all__'


class CompanyDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CompanyDetails
        fields = '__all__'


class PlacementScheduleSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='notify_id.company_name', read_only=True)
    placement_type = serializers.CharField(source='notify_id.placement_type', read_only=True)
    ctc = serializers.DecimalField(source='notify_id.ctc', max_digits=10, decimal_places=4, read_only=True)
    role_st = serializers.CharField(source='get_role', read_only=True)
    notify_description = serializers.CharField(source='notify_id.description', read_only=True)
    jobID = serializers.IntegerField(source='notify_id.id', read_only=True)

    class Meta:
        model = PlacementSchedule
        fields = (
            'id', 'notify_id', 'title', 'placement_date', 'location',
            'description', 'time', 'role', 'attached_file', 'schedule_at',
            'company_name', 'placement_type', 'ctc', 'role_st',
            'notify_description', 'jobID',
        )
        read_only_fields = ('id',)


class PlacementStatusSerializer(serializers.ModelSerializer):
    notify_id = NotifyStudentSerializer()
    student_name = serializers.SerializerMethodField()
    student_roll = serializers.SerializerMethodField()

    class Meta:
        model = PlacementStatus
        fields = (
            'id', 'notify_id', 'unique_id', 'invitation', 'placed',
            'timestamp', 'no_of_days', 'student_name', 'student_roll',
        )

    def get_student_name(self, obj):
        try:
            user = obj.unique_id.id.user
            return '{} {}'.format(user.first_name, user.last_name)
        except Exception:
            return ''

    def get_student_roll(self, obj):
        try:
            return obj.unique_id.id.id
        except Exception:
            return ''


# =============================================
# Placement Records / Statistics Serializers
# =============================================

class PlacementRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlacementRecord
        fields = '__all__'


class StudentRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_roll = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='record_id.name', read_only=True)
    year = serializers.IntegerField(source='record_id.year', read_only=True)
    ctc = serializers.DecimalField(source='record_id.ctc', max_digits=5, decimal_places=2, read_only=True)
    placement_type = serializers.CharField(source='record_id.placement_type', read_only=True)
    department = serializers.SerializerMethodField()

    class Meta:
        model = StudentRecord
        fields = (
            'id', 'record_id', 'unique_id', 'student_name', 'student_roll',
            'company_name', 'year', 'ctc', 'placement_type', 'department',
        )

    def get_student_name(self, obj):
        try:
            user = obj.unique_id.id.user
            return '{} {}'.format(user.first_name, user.last_name)
        except Exception:
            return ''

    def get_student_roll(self, obj):
        try:
            return obj.unique_id.id.id
        except Exception:
            return ''

    def get_department(self, obj):
        try:
            return obj.unique_id.id.department.name
        except Exception:
            return ''


# =============================================
# Student Placement / Debar Serializers
# =============================================

class StudentPlacementSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_roll = serializers.SerializerMethodField()

    class Meta:
        model = StudentPlacement
        fields = '__all__'

    def get_student_name(self, obj):
        try:
            user = obj.unique_id.id.user
            return '{} {}'.format(user.first_name, user.last_name)
        except Exception:
            return ''

    def get_student_roll(self, obj):
        try:
            return obj.unique_id.id.id
        except Exception:
            return ''


# =============================================
# Chairman Visit Serializers
# =============================================

class ChairmanVisitSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChairmanVisit
        fields = '__all__'


class MessageOfficerSerializer(serializers.ModelSerializer):

    class Meta:
        model = MessageOfficer
        fields = '__all__'


# =============================================
# PCMS Serializers (Company, Jobs, Applications, etc.)
# =============================================

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
