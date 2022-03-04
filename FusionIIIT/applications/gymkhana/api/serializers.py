from attr import fields
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from applications.gymkhana.models import Club_info,Club_member 

class Club_infoSerializer(serializers.ModelSerializer):

    class Meta:
        model=Club_info
        fields=['club_name']


class Club_DetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Club_info
        fields=['club_name',"co_ordinator","co_coordinator","activity_calender"]

class EmptySerializer(serializers.Serializer):
    pass