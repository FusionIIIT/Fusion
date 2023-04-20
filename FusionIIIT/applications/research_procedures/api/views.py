from rest_framework.viewsets import ModelViewSet
from applications.research_procedures.models import Patent
from .serializers import PatentSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly 
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
from applications.research_procedures.models import Patent, ResearchGroup, ResearchProject, ConsultancyProject, TechTransfer
from . import serializers
from applications.eis.models import *
from applications.eis.views import countries
from applications.globals.models import HoldsDesignation

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def consultant_api(request):
    # print(request.data)
    serializer = serializers.ConsultancyProjectSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        print('Successfully added consultant project.')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def research_api(request):
    # print(request.data)
    serializer = serializers.ResearchProjectSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        print('Successfully added research project.')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_research_project_api(request,username=None):
    user = get_object_or_404(User, username=username) if username else request.user
    user_detail = serializers.UserSerializer(user).data
    extra_info = serializers.ExtraInfoSerializer(user.extrainfo).data
    if extra_info['user_type'] != 'faculty':
        return Response(data={'message':'Not faculty'}, status=status.HTTP_400_BAD_REQUEST)
    pf = user.id
    projects = serializers.EmpResearchProjectsSerializer(emp_research_projects.objects.filter(pf_no=pf).order_by('-start_date'),many=True).data
    # print(projects)
    resp = {
            'projects' : projects,
    }
    return Response(data=resp, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_consultancy_project_api(request,username=None):
    user = get_object_or_404(User, username=username) if username else request.user
    user_detail = serializers.UserSerializer(user).data
    extra_info = serializers.ExtraInfoSerializer(user.extrainfo).data
    if extra_info['user_type'] != 'faculty':
        return Response(data={'message':'Not faculty'}, status=status.HTTP_400_BAD_REQUEST)
    pf = user.id
    consultancy = serializers.EmpConsultancyProjectsSerializer(emp_consultancy_projects.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
    # print(consultancy)
    resp = {
            'projects' : consultancy,
    }
    return Response(data=resp, status=status.HTTP_200_OK)
   

