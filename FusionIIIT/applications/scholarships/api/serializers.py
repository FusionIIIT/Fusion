from django.contrib.auth import get_user_model
from rest_framework import serializers
from applications.scholarships.models import Award_and_scholarship, Mcm, Notional_prize, Previous_winner,Release,Notification,Application,Director_silver,DM_Proficiency_gold,Director_gold
from applications.globals.models import ExtraInfo,User

class AwardAndScholarshipSerializers(serializers.ModelSerializer):

    class Meta:
        model = Award_and_scholarship
        fields = list(Award_and_scholarship().__dict__.keys())[1:]

class McmSerializers(serializers.ModelSerializer):

    class Meta:
        model=Mcm
        fields=('__all__')

class NationalPrizeSerializers(serializers.ModelSerializer):

    class Meta:
        model=Notional_prize
        fields=('__all__')

class PreviousWinnerSerializers(serializers.ModelSerializer):

    class Meta:
        model = Previous_winner
        fields = list(Previous_winner().__dict__.keys())[1:]


class ReleaseSerializers(serializers.ModelSerializer):

    class Meta:
        model=Release
        fields=('__all__')

class NotificationSerializers(serializers.ModelSerializer):

    class Meta:
        model=Notification
        fields=('__all__')

class ApplicationSerializers(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'
        
class DirectorSilverSerializers(serializers.ModelSerializer):

    class Meta:
        model=Director_silver
        fields=('__all__')

class DmProficiencyGoldSerializers(serializers.ModelSerializer):

    class Meta:
        model=DM_Proficiency_gold
        fields=('__all__')


class DirectorGoldSerializers(serializers.ModelSerializer):

    class Meta:
        model=Director_gold
        fields=('__all__')

class UserSerializers(serializers.ModelSerializer):

    class Meta:
        model=User
        fields=('__all__')

class ExtraInfoSerializers(serializers.ModelSerializer):

    class Meta:
        model=ExtraInfo
        fields=('__all__')





   