from rest_framework import serializers
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo
from applications.scholarships.models import Award_and_scholarship,Previous_winner,Mcm,Director_silver,Director_gold,Notional_prize,Proficiency_dm,Release


class McmStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mcm
        fields = ['status']

    def validate_status(self, value):
        valid_statuses = ['ACCEPTED', 'REJECTED', 'UNDER_REVIEW']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of {valid_statuses}.")
        return value




class DirectorSilverDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director_silver
        fields = ['id', 'status']
        
    def validate_status(self, value):
        if value not in ['ACCEPTED', 'REJECTED']:
            raise serializers.ValidationError("Status must be either 'ACCEPTED' or 'REJECTED'.")
        return value




class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = '__all__'



# This serializer is used for editing the catalog by convenor and assistant
class AwardAndScholarshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award_and_scholarship
        fields = '_all_'


# this serializer is used for showing data on catalog form
class AwardAndScholarshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award_and_scholarship
        fields = ['id', 'award_name', 'catalog']
        extra_kwargs = {
            'catalog': {'required': True, 'allow_null': False}  # Make catalog optional
        }


class PreviousWinnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Previous_winner
        fields = ['student', 'programme', 'year', 'award_id'] 


class McmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mcm
        fields = '__all__'
class DirectorSilverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director_silver
        fields = '__all__'
class DirectorGoldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director_gold
        fields = '__all__'
class NotionalPrizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notional_prize
        fields = '__all__'
class ProficiencyDmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proficiency_dm
        fields = '__all__'





