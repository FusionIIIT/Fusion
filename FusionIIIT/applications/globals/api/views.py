from django.contrib.auth import get_user_model
from applications.academic_information.models import Student
from applications.eis.api.views import profile as eis_profile
from applications.globals.models import (HoldsDesignation,Designation)
from applications.gymkhana.api.views import coordinator_club
from django.shortcuts import get_object_or_404, redirect

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
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
def logout(request):
    request.user.auth_token.delete()
    resp = {
        'message' : 'User logged out successfully'
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

@api_view(['GET'])
def profile(request, username=None):
    user = get_object_or_404(User, username=username) if username else request.user
    user_detail = serializers.UserSerializer(user).data
    profile = serializers.ExtraInfoSerializer(user.extrainfo).data
    if profile['user_type'] == 'student':
        student = user.extrainfo.student
        skills = serializers.HasSerializer(student.has_set.all(), many=True).data
        education = serializers.EducationSerializer(student.education_set.all(), many=True).data
        course = serializers.CourseSerializer(student.course_set.all(), many=True).data
        experience = serializers.ExperienceSerializer(student.experience_set.all(), many=True).data
        project = serializers.ProjectSerializer(student.project_set.all(), many=True).data
        achievement = serializers.AchievementSerializer(student.achievement_set.all(), many=True).data
        publication = serializers.PublicationSerializer(student.publication_set.all(), many=True).data
        patent = serializers.PatentSerializer(student.patent_set.all(), many=True).data
        current = serializers.HoldsDesignationSerializer(user.current_designation.all(), many=True).data
        resp = {
            'user' : user_detail,
            'profile' : profile,
            'skills' : skills,
            'education' : education,
            'course' : course,
            'experience' : experience,
            'project' : project,
            'achievement' : achievement,
            'publication' : publication,
            'patent' : patent,
            'current' : current
        }
        return Response(data=resp, status=status.HTTP_200_OK)
    elif profile['user_type'] == 'faculty':
        return redirect('/eis/api/profile/' + (username+'/' if username else ''))
