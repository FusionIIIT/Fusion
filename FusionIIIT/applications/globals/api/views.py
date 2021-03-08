from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from applications.globals.models import (HoldsDesignation,Designation)
from django.shortcuts import get_object_or_404
from applications.gymkhana.views import coordinator_club

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import serializers
from .utils import get_and_authenticate_user

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def dashboard(request):
    user=request.user
    notifs=request.user.notifications.all()
    name = request.user.first_name +"_"+ request.user.last_name
    desig = list(HoldsDesignation.objects.all().filter(working = request.user).values_list('designation'))
    b = [i for sub in desig for i in sub]
    roll_ = []
    for i in b :
        name_ = get_object_or_404(Designation, id = i)
        roll_.append(str(name_.name))
    
    notifsData=serializers.NotificationSerializer(notifs,many=True).data

    context={
        'notifications':notifsData,
        'Curr_desig' : roll_,
        'club_details' : coordinator_club(request)
    }

    return Response(data=context,status=status.HTTP_200_OK)
