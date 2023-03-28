from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from applications.placement_cell.models import *
from . import serializers
from applications.globals.api.serializers import ExtraInfoSerializer
from applications.academic_information.api.serializers import StudentSerializers


@api_view(['GET'])
def projects(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"message":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    all_projects = Project.objects.filter(unique_id=username)
    project_details=serializers.ProjectSerializer(all_projects, many=True).data
    resp={
        "projects":project_details
    }
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['GET'])
def skills(request):
    skills=Skill.objects.all()
    skills_details=serializers.SkillSerializer(skills,many=True).data
    resp={
        "skills":skills_details,
    }
    
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def has(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    has=Has.objects.filter(unique_id=username)
    has_details=serializers.HasSerializer(has,many=True).data
    resp={
        "has_skills":has_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def education(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    education=Education.objects.filter(unique_id=username)
    education_details=serializers.EducationSerializer(education,many=True).data
    resp={
        "education_details":education_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def experiences(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    
    expriences=Experience.objects.filter(unique_id=username)
    experience_details=serializers.ExperienceSerializer(expriences,many=True).data
    resp={
        "experiences":experience_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def courses(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    
    courses=Course.objects.filter(unique_id=username)
    courses_details=serializers.CourseSerializer(courses,many=True).data
    resp={
        "experiences":courses_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def conference(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    
    conference=Conference.objects.filter(unique_id=username)
    conference_details=serializers.ConferenceSerializer(conference,many=True).data
    resp={
        "experiences":conference_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def publications(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    
    publications=Publication.objects.filter(unique_id=username)
    publications_details=serializers.PublicationSerializer(publications,many=True).data
    resp={
        "experiences":publications_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

