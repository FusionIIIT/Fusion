from rest_framework import serializers
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo
from applications.scholarships.models import Award_and_scholarship,Previous_winner,Mcm,Director_silver,Director_gold,Notional_prize,Proficiency_dm

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





