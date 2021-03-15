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
from applications.academic_information.models import Student, Course, Curriculum, Curriculum_Instructor, Student_attendance, Meeting, Calendar, Holiday, Grades, Spi, Timetable, Exam_timetable
from . import serializers

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def student_api(request):

    if request.method == 'GET':
        student = Student.objects.all()
        student_serialized = serializers.StudentSerializers(student,many=True).data
        resp = {
            'students' : student_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def course_api(request):

    if request.method == 'GET':
        course = Course.objects.all()
        course_serialized = serializers.CourseSerializers(course,many=True).data
        resp = {
            'courses' : course_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
