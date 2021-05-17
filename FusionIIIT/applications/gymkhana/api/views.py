from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from applications.gymkhana.models import Club_info
from . import serializers

def coordinator_club(request):
    club_info = []
    for i in Club_info.objects.all():
        co = (str(i.co_ordinator)).split(" ")
        co_co=(str(i.co_coordinator)).split(" ")
        if co[0]==str(request.user) or co_co[0] == str(request.user):
            club_info.append(serializers.ClubInfoSerializer(i).data)
	
    return club_info