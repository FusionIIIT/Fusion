from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from rest_framework.permissions import *
from rest_framework.authentication import *
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from . import serializers 
from applications.hr2.models import *


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@login_required
def employee_details_api(request,*args,**kwargs):
    if request.method == 'GET':
        employee_details = Employee.objects.all()
        employee_details = serializers.EmployeeSerializer(employee_details,many=True).data
        resp = {
            'employee_details' : employee_details,
        }
        return Response(data=resp,status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = serializers.EmployeeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@login_required
def emp_confidential_details_api(request,*args,**kwargs):
    if request.method == 'GET':
        emp_confidential_details = EmpConfidentialDetails.objects.all()
        emp_confidential_details = serializers.EmpConfidentialDetailsSerializer(emp_confidential_details,many=True).data
        resp = {
            'emp_confidential_details' : emp_confidential_details,
        }
        return Response(data=resp,status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = serializers.EmpConfidentialDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@login_required
def emp_dependents_api(request,*args,**kwargs):
    if request.method == 'GET':
        emp_dependents_details = EmpDependents.objects.all()
        emp_dependents_details = serializers.EmpDependentsSerializer(emp_dependents_details,many=True).data
        resp = {
            'emp_dependents_details' : emp_dependents_details,
        }
        return Response(data=resp,status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = serializers.EmpDependentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@login_required
def foreign_service_api(request,*args,**kwargs):
    if request.method == 'GET':
        foreign_service_details = ForeignService.objects.all()
        foreign_service_details = serializers.ForeignServiceSerializer(foreign_service_details,many=True).data
        resp = {
            'foreign_service_details' : foreign_service_details,
        }
        return Response(data=resp,status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = serializers.ForeignServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@login_required
def emp_appraisal_form_api(request,*args,**kwargs):
    if request.method == 'GET':
        emp_appraisal_form_details = ForeignService.objects.all()
        emp_appraisal_form_details = serializers.EmpAppraisalFormSerializer(emp_appraisal_form_details,many=True).data
        resp = {
            'emp_appraisal_form_details' : emp_appraisal_form_details,
        }
        return Response(data=resp,status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = serializers.EmpAppraisalFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@login_required
def work_assignment_api(request,*args,**kwargs):
    if request.method == 'GET':
        work_assignment_details = ForeignService.objects.all()
        work_assignment_details = serializers.WorkAssignemntSerializer(work_assignment_details,many=True).data
        resp = {
            'work_assignment_details' : work_assignment_details,
        }
        return Response(data=resp,status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = serializers.WorkAssignemntSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
