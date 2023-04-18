from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from applications.globals.models import (HoldsDesignation,Designation)
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from applications.globals.models import User,ExtraInfo
from applications.scholarships.models import Award_and_scholarship, Mcm, Notional_prize, Previous_winner,Release,Notification,Application,Director_silver,DM_Proficiency_gold,Director_gold
from . import serializers
from django.http import JsonResponse


@api_view(['GET'])
def browse_award_info(request):
    award = request.query_params.get('award')
    print(award)
    if not award:
        return Response({"message":"No Award Catalogue Found"},status=status.HTTP_400_BAD_REQUEST)
    award_catalogue = Award_and_scholarship.objects.filter(award_name=award)
    catalog=serializers.AwardAndScholarshipSerializers(award_catalogue, many=True).data
    resp={
        "Awards":catalog
    }
    return Response(data=resp, status=status.HTTP_200_OK)
  
@api_view(['GET'])
def get_previous_winner(request):
    award_name = request.query_params.get("award")
    programme = request.query_params.get("programme")
    year = request.query_params.get("year")
    award = Award_and_scholarship.objects.get(award_name=award_name)
    if not year and programme :
        return Response({"messgae":"No Previous Winner Found"},status=status.HTTP_400_BAD_REQUEST)
    winners = Previous_winner.objects.select_related('student','award_id').filter(year=year, award_id=award, programme=programme)
    studentrecord_details = serializers.PreviousWinnerSerializers(winners,many=True).data
    resp={
        "studentrecord":studentrecord_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['POST'])
def create_mcm(request):
    serializer = serializers.McmSerializers(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def apply_notional_prize(request):
    serializer = serializers.NationalPrizeSerializers(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)



@api_view(['POST'])
def apply_director_gold(request):
    serializer = serializers.DirectorGoldSerializers(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def apply_director_silver(request):
    serializer = serializers.DirectorSilverSerializers(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def apply_dm_proficiency_gold(request):
    serializer = serializers.DmProficiencyGoldSerializers(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def create_invitation(request):
    serializer = serializers.ReleaseSerializers(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def invitations(request):

    invitation = Release.objects.all()
    invitations = serializers.ReleaseSerializers(invitation,many=True).data
    resp = {
    'invitations' : invitations,
    }
    return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
def applications(request):

    application = Application.objects.all()
    applications = serializers.ApplicationSerializers(application,many=True).data
    resp = {
    'applications' : applications,
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def application_detail(request, application_id):
    try:
        application = Application.objects.get(application_id=application_id)
    except Application.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer =serializers. ApplicationSerializers(application)
        return Response(serializer.data)

@api_view(['PUT'])
def update_invitation(request,id):
    try: 
        invitation = Release.objects.get(id = id) 
    except Release.DoesNotExist: 
        return Response({'message': 'The Invitation does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'PUT':
        serializer = serializers.ReleaseSerializers(invitation,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)







# manage awards catalogue
@api_view(['PUT'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
def update_award_info(request, id):
    try:
        award = Award_and_scholarship.objects.get(id=id)
    except Award_and_scholarship.DoesNotExist:
        return Response({'message': 'Award not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = serializers.AwardAndScholarshipSerializers(award, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# rececnt invite application

#Getting details and Approving mcm application
@api_view(['GET', 'PUT'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
def mcm_detail(request, id):
    try:
        mcm = Mcm.objects.get(id=id)
    except Mcm.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = serializers.McmSerializers(mcm)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = serializers.McmSerializers(mcm, data=request.data)
        if serializer.is_valid():
            status_value = serializer.validated_data.get('status')
            if status_value in ('COMPLETE','INCOMPLETE','ACCEPT', 'REJECT', "Complete","Incomplete", "Reject", "Accept"):
                serializer.save()
                return Response(serializer.data)
            else:
                return Response({'status': 'Invalid value'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
def allmcms(request):

    mcm = Mcm.objects.all()
    mcms = serializers.McmSerializers(mcm,many=True).data
    resp = {
    'mcms' : mcms,
    }
    return Response(data=resp,status=status.HTTP_200_OK)

#getting details and approving for convocation medals
#1 Director's Gold medal
@api_view(['GET', 'PUT'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
def director_gold_detail(request, id):
    try:
        new_id = Director_gold.objects.get(id=id)
    except Director_gold.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = serializers.DirectorGoldSerializers(new_id)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = serializers.DirectorGoldSerializers(new_id, data=request.data)
        status_value = serializer.validated_data.get('status')
        if status_value in ('COMPLETE','INCOMPLETE','ACCEPT', 'REJECT', "Complete","Incomplete", "Reject", "Accept"):
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({'status': 'Invalid value'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#2 Director's Silver medal
@api_view(['GET', 'PUT'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
def director_silver_detail(request, id):
    try:
        director_silver = Director_silver.objects.get(id=id)
    except Director_silver.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = serializers.DirectorSilverSerializers(director_silver)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = serializers.DirectorSilverSerializers(director_silver, data=request.data)
        if serializer.is_valid():
            status_value = serializer.validated_data.get('status')
            if status_value in ('COMPLETE','INCOMPLETE','ACCEPT', 'REJECT', "Complete","Incomplete", "Reject", "Accept"):
                serializer.save()
                return Response(serializer.data)
            else:
                return Response({'status': 'Invalid value'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#3 D&M profieciency Gold
@api_view(['GET', 'PUT'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
def dm_proficiency_gold_detail(request, id):
    try:
        dm_proficiency_gold = DM_Proficiency_gold.objects.get(id=id)
    except DM_Proficiency_gold.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = serializers.DmProficiencyGoldSerializers(dm_proficiency_gold)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        serializer = serializers.DmProficiencyGoldSerializers(dm_proficiency_gold, data=request.data)
        if serializer.is_valid():
            status_value = serializer.validated_data.get('status')
            if status_value in ('COMPLETE','INCOMPLETE','ACCEPT', 'REJECT', "Complete","Incomplete", "Reject", "Accept"):
                serializer.save()
                return Response(serializer.data)
            else:
                return Response({'status': 'Invalid value'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    





    



