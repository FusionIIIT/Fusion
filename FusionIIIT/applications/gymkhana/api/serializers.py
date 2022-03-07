from attr import fields
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from applications.gymkhana.models import Club_info,Session_info,Event_info
from applications.gymkhana.models import Club_member,Core_team,Club_budget

class Club_infoSerializer(serializers.ModelSerializer):

    class Meta:
        model=Club_info
        fields=['club_name']


class EmptySerializer(serializers.Serializer):
    pass

class Club_memberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club_member
        fields = ['member','club']
    

class Core_teamSerializer(serializers.ModelSerializer):

    class Meta:
        model=Core_team
        fields=('_all_')

class Club_DetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Club_info
        fields=('club_name',"co_ordinator","co_coordinator","activity_calender")

class Session_infoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session_info
        fields= ['venue','date','start_time','details']

class event_infoserializer(serializers.Serializer):

    class Meta:
        model=Event_info
        fields=('club','event_name','incharge','date')

class club_budgetserializer(serializers.Serializer):

    class Meta:
        model=Club_budget
        fields=('club','budget_for','budget_amt','budget_file')
