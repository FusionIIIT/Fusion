from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from applications.globals.models import (HoldsDesignation,Designation)
from applications.gymkhana.api.views import coordinator_club
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


from . import serializers
from .utils import get_and_authenticate_user
from notifications.models import Notification

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = serializers.UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_and_authenticate_user(**serializer.validated_data)
    data = serializers.AuthUserSerializer(user).data
    resp = {
        'success' : 'True',
        'message' : 'User logged in successfully',
        'token' : data['auth_token']
    }
    return Response(data=resp, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def dashboard(request):
    user=request.user
    
    name = request.user.first_name +"_"+ request.user.last_name

    designation_list = list(HoldsDesignation.objects.all().filter(working = request.user).values_list('designation'))
    designation_id = [designation for designations in designation_list for designation in designations]
    designation_info = []
    for id in designation_id :
        name_ = get_object_or_404(Designation, id = id)
        designation_info.append(str(name_.name))
    
    notifications=serializers.NotificationSerializer(request.user.notifications.all(),many=True).data
    club_details= coordinator_club(request)

    resp={
        'notifications':notifications,
        'desgination_info' :  designation_info,
        'club_details' : club_details
    }

    return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def NotificationRead(request):
    try:
        notifId=int(request.data['id'])
        user=request.user
        notification = get_object_or_404(Notification, recipient=request.user, id=notifId)
        notification.mark_as_read()
        response ={
            'message':'notfication successfully marked as seen.'
        }
        return Response(response,status=status.HTTP_200_OK)
    except:
        response ={
            'error':'Failed, notification is not marked as seen.'
        }
        return Response(response,status=status.HTTP_404_NOT_FOUND)
        

