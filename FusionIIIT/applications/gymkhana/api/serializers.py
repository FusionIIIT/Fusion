from attr import fields
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from applications.gymkhana.models import Club_info,Session_info,Event_info
from applications.gymkhana.models import Club_member,Core_team,Club_budget,Club_report,Fest_budget,Registration_form,Voting_polls

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
        fields=['club_name',"co_ordinator","co_coordinator","activity_calender"]

class Session_infoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session_info
        fields= ['venue','date','start_time','details']

class event_infoserializer(serializers.ModelSerializer):

    class Meta:
        model=Event_info
        fields=['club','event_name','incharge','date']

class club_budgetserializer(serializers.ModelSerializer):

    class Meta:
        model=Club_budget
        fields=['club','budget_for','budget_amt','budget_file']

class Club_reportSerializers(serializers.ModelSerializer):
    class Meta:
        model = Club_report
        fields = ['club', 'incharge' , 'event_name' , 'date' , 'event_details' ]

class Fest_budgerSerializer(serializers.ModelSerializer):
    class Meta:
        model=Fest_budget
        fields=['fest','budget_amt','budget_file','year','status']

class Registration_formSerializer(serializers.ModelSerializer):
    class Meta:
        model=Registration_form
        fields=['roll','user_name','branch','cpi','programme']

class Voting_pollSerializer(serializers.ModelSerializer):
    class Meta:
        model=Voting_polls
        fields=['title','pub_date','exp_date','created_by','groups']
