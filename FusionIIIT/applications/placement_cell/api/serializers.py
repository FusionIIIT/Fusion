from rest_framework.authtoken.models import Token
from rest_framework import serializers

from applications.placement_cell.models import *

class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = list(Project().__dict__.keys())[1:]
class SkillSerializer(serializers.ModelSerializer):

    class Meta:
        model = Skill
        fields = list(Skill().__dict__.keys())[1:]

class HasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Has
        fields = ('skill_id_id','skill_rating')

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
        fields = list(Education().__dict__.keys())[1:]

class ReferenceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Reference
        fields=list(Reference().__dict__.keys())[1:]

class CoauthorSerializer(serializers.ModelSerializer):

    class Meta:
        model=Coauthor
        fields=list(Coauthor().__dict__.keys())[1:]

class PatentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Patent
        fields=list(Patent().__dict__.keys())[1:]

class CoinventorSerializer(serializers.ModelSerializer):

    class Meta:
        model=Coinventor
        fields=list(Coinventor().__dict__.keys())[1:]

class InterestSerializer(serializers.ModelSerializer):

    class Meta:
        model=Interest
        fields=list(Interest().__dict__.keys())[1:]

class AchievementSerializer(serializers.ModelSerializer):

    class Meta:
        model=Achievement
        fields=list(Achievement().__dict__.keys())[1:]
        
class ExtracurricularSerializer(serializers.ModelSerializer):

    class Meta:
        model = Extracurricular
        fields=list(Extracurricular().__dict__.keys())[1:]

class MessageOfficerSerializer(serializers.ModelSerializer):

    class Meta:
        model = MessageOfficer
        fields=list(MessageOfficer().__dict__.keys())[1:]

class NotifyStudentSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotifyStudent
        fields = list(NotifyStudent().__dict__.keys())[1:]

class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = list(Role().__dict__.keys())[1:]
        
class CompanyDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CompanyDetails
        fields = list(CompanyDetails().__dict__.keys())[1:]

class PlacementStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlacementStatus
        fields = list(PlacementStatus().__dict__.keys())[1:]

class PlacementRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlacementRecord
        fields = list(PlacementRecord().__dict__.keys())[1:]

class StudentRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudentRecord
        fields = list(StudentRecord().__dict__.keys())[1:]

class ChairmanVisitSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChairmanVisit
        fields = list(ChairmanVisit().__dict__.keys())[1:]

class PlacementScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlacementSchedule
        fields = list(PlacementSchedule().__dict__.keys())[1:-1]

class StudentPlacementSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudentPlacement
        fields = list(StudentPlacement().__dict__.keys())[1:]

class ExperienceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Experience
        fields = list(Experience().__dict__.keys())[1:]

class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = list(Course().__dict__.keys())[1:]

class ConferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Conference
        fields = list(Conference().__dict__.keys())[1:]

class PublicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publication
        fields = list(Publication().__dict__.keys())[1:]