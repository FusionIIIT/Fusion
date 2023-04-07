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

@api_view(['GET'])
def references(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    reference=Reference.objects.filter(unique_id=username)
    reference_details=serializers.ReferenceSerializer(reference,many=True).data
    resp={
        "references":reference_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def coauthor(request):
    coauthor=Coauthor.objects.all()
    coauthor_details=serializers.CoauthorSerializer(coauthor,many=True).data
    resp={
        "coauthor":coauthor_details,
    }
    
    return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
def patent(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    patent=Patent.objects.filter(unique_id=username)
    patent_details=serializers.PatentSerializer(patent,many=True).data
    resp={
        "patent":patent_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def coinventor(request):
    coinventor=Coinventor.objects.all()
    coinventor_details=serializers.CoinventorSerializer(coinventor,many=True).data
    resp={
        "coinventor":coinventor_details,
    }
    
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def interest(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    interest=Interest.objects.filter(unique_id=username)
    interest_details=serializers.InterestSerializer(interest,many=True).data
    resp={
        "interest":interest_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def achievement(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    achievement=Achievement.objects.filter(unique_id=username)
    achievement_details=serializers.AchievementSerializer(achievement,many=True).data
    resp={
        "achievement":achievement_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def extracurricular(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    extracurricular = Extracurricular.objects.filter(unique_id=username)
    extracurricular_details = serializers.ExtracurricularSerializer(extracurricular,many=True).data
    resp={
        "extracurricular":extracurricular_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def messageofficer(request):
    messageofficer=MessageOfficer.objects.all()
    messageofficer=serializers.MessageOfficerSerializer(messageofficer,many=True).data
    resp={
        "messageofficer":messageofficer,
    }

    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def notifystudent(request):
    notifystudent=NotifyStudent.objects.all()
    notifystudent=serializers.NotifyStudentSerializer(notifystudent,many=True).data
    resp={
        "notifystudent":notifystudent,
    }
    
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def role(request):
    role=Role.objects.all()
    role=serializers.RoleSerializer(role,many=True).data
    resp={
        "role":role,
    }
    
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def companydetails(request):
    companydetails=CompanyDetails.objects.all()
    companydetails=serializers.CompanyDetailsSerializer(companydetails,many=True).data
    resp={
        "companydetails":companydetails,
    }
    
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def placementstatus(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    placementstatus = PlacementStatus.objects.filter(unique_id=username)
    placementstatus_details = serializers.PlacementStatusSerializer(placementstatus,many=True).data
    resp={
        "placementstatus":placementstatus_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def placementrecord(request):
    print(list(PlacementRecord().__dict__.keys())[1:-2])
    placementrecord=PlacementRecord.objects.all()
    placementrecord=serializers.PlacementRecordSerializer(placementrecord,many=True).data
    resp={
        "placementrecord":placementrecord,
    }

    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def studentrecord(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    studentrecord = StudentRecord.objects.filter(unique_id=username)
    studentrecord_details = serializers.StudentRecordSerializer(studentrecord,many=True).data
    resp={
        "studentrecord":studentrecord_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def chairmanvisit(request):
    chairmanvisit=ChairmanVisit.objects.all()
    chairmanvisit=serializers.ChairmanVisitSerializer(chairmanvisit,many=True).data
    resp={
        "chairmanvisit":chairmanvisit,
    }

    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def placementschedule(request):
    placementschedule=PlacementSchedule.objects.all()
    placementschedule=serializers.PlacementScheduleSerializer(placementschedule,many=True).data
    resp={
        "placementschedule":placementschedule,
    }

    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def studentplacement(request):
    username=request.query_params.get("username")
    if not username:
        return Response({"messgae":"No Username Found"},status=status.HTTP_400_BAD_REQUEST)
    studentplacement = StudentPlacement.objects.filter(unique_id=username)
    studentplacement_details = serializers.StudentPlacementSerializer(studentplacement,many=True).data
    resp={
        "studentplacement":studentplacement_details
    }
    return Response(data=resp,status=status.HTTP_200_OK)