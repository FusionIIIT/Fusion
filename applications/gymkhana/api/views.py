from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import render
from applications.gymkhana.models import Club_info,Club_member,Core_team,Session_info,Event_info,Club_budget,Club_report,Fest_budget,Registration_form,Voting_polls
from .serializers import Club_memberSerializer,Core_teamSerializer,Club_infoSerializer,Club_DetailsSerializer,Session_infoSerializer,event_infoserializer,club_budgetserializer,Club_reportSerializers,Fest_budgerSerializer,Registration_formSerializer,Voting_pollSerializer
from django.contrib.auth.models import User

def coordinator_club(request):
    club_info = []
    for i in Club_info.objects.all():
        co = (str(i.co_ordinator)).split(" ")
        co_co=(str(i.co_coordinator)).split(" ")
        if co[0]==str(request.user) or co_co[0] == str(request.user):
            club_info.append(serializers.ClubInfoSerializer(i).data)
	
    return club_info

class core(APIView):
    def get(self,request):
        co=Core_team.objects.all()
        serializer=Core_teamSerializer(co, many=True)
        print(serializer.data)
        return Response(serializer.data)

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

class session_details(APIView):
    def get(self,respect):
        session = Session_info.objects.all()
        serializer = Session_infoSerializer(session, many = True)
        return Response(serializer.data)

class club_events(APIView):
    def get(self,respect):
        clubevents=Event_info.objects.all()
        serializer=event_infoserializer(clubevents, many = True)
        return Response(serializer.data)

class club_budgetinfo(APIView):
    def get(self,respect):
        clubbudget=Club_budget.objects.all()
        serializer=club_budgetserializer(clubbudget, many=True)
        return Response(serializer.data)

class club_report(APIView):
    def get(self,respect):
        clubreport = Club_report.objects.all()
        serializer = Club_reportSerializers(clubreport , many=True)
        return Response(serializer.data)

class Fest_Budget(APIView):

    def get(self,respect):
        festbudget=Fest_budget.objects.all()
        serializer=Fest_budgerSerializer(festbudget, many=True)
        return Response(serializer.data)

class Registraion_form(APIView):

    def get(self,respect):
        registration=Registration_form.objects.all()
        serializer=Registration_formSerializer(registration, many=True)
        return Response(serializer.data)


class Voting_Polls(APIView):

    def get(self,respect):
        votingpolls=Voting_polls.objects.all()
        serializer=Voting_pollSerializer(votingpolls, many=True)
        return Response(serializer.data)
