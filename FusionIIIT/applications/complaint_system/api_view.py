from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from applications.globals.models import (HoldsDesignation,Designation)
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from applications.globals.models import User
from .models import StudentComplain,ExtraInfo,Workers,Caretaker,Supervisor
from . import serializers


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def complaint_details(request,detailcomp_id1):
    detail = StudentComplain.objects.get(id=detailcomp_id1)
    if(detail.worker_id is None):
        worker_name = None
        worker_id = detail.worker_id  
    else:
        worker_id = detail.worker_id.id
        worker = Workers.objects.get(id=worker_id)
        worker_name = worker.name
    a=User.objects.get(username=detail.complainer.user.username)           
    y=ExtraInfo.objects.get(user=a)
    temp=StudentComplain.objects.filter(complainer=y).first()                                                                  
    comp_id=temp.id

    complainer_name = detail.complainer.user.first_name + ' ' + detail.complainer.user.last_name
    complainer_id = detail.complainer.id
    complaint_details = comp_id
    complaint_id = detail.details
    if detail.upload_complaint != "":
        image = detail.upload_complaint
    else :
        image = ""

    response = {
        "complainer_name": complainer_name, 
        "complainer_id": complainer_id,
        "complaint_details":complaint_details,
        "complaint_id":complaint_id,
        "worker_name":worker_name,
        "image":image
    }
    return Response(data=response,status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def StudentComplainApi(request):
    user = get_object_or_404(User,username = request.user.username)
    user = ExtraInfo.objects.all().filter(user = user).first()
    if user.user_type == 'student':
        complain = StudentComplain.objects.filter(complainer = user)
    elif user.user_type == 'staff':
        staff = ExtraInfo.objects.get(id=user.id)
        staff = Caretaker.objects.get(staff_id=staff)
        complain = StudentComplain.objects.filter(location = staff.area)
    elif user.user_type == 'faculty':
        faculty = ExtraInfo.objects.get(id=user.id)
        faculty = Supervisor.objects.get(sup_id=faculty)
        complain = StudentComplain.objects.filter(location = faculty.area)
    complains = serializers.StudentComplainSerializers(complain,many=True).data
    resp = {
        'StudentComplain' : complains,
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def WorkerApi(request):
    worker = Workers.objects.all()
    workers = serializers.WorkersSerializers(worker,many=True).data

    resp = {
        'Workers' : workers,
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def CaretakerApi(request):
    caretaker = Caretaker.objects.all()
    caretakers = serializers.CaretakerSerializers(caretaker,many=True).data
    resp = {
        'Caretakers' : caretakers,
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def SupervisorApi(request):
    supervisor = Supervisor.objects.all()
    supervisors = serializers.SupervisorSerializers(supervisor,many=True).data

    resp = {
        'Supervisors' : supervisors,
    }
    return Response(data=resp,status=status.HTTP_200_OK)

