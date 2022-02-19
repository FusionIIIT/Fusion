from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status

from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import render
from applications.gymkhana.models import Club_info
from .serializers import Club_infoSerializer,Club_DetailsSerializer
from django.contrib.auth.models import User

def coordinator_club(request):
    club_info = []
    for i in Club_info.objects.all():
        co = (str(i.co_ordinator)).split(" ")
        co_co=(str(i.co_coordinator)).split(" ")
        if co[0]==str(request.user) or co_co[0] == str(request.user):
            club_info.append(serializers.ClubInfoSerializer(i).data)
	
    return club_info

class clubname(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        authentication_classes = [TokenAuthentication]
        clubname1 = Club_info.objects.all()
        serializer = Club_infoSerializer(clubname1, many = True)
        return Response(serializer.data)

class  Club_Details(APIView):

    def get(self,respect):
        clubdetail=Club_info.objects.all()
        serializer=Club_DetailsSerializer(clubdetail, many=True)
        return Response(serializer.data)
