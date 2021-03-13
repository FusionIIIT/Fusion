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
from applications.complaint_system.models import Caretaker, StudentComplain, Supervisor, Workers
from . import serializers


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def ComplaintDetailsApi(request,detailcomp_id1):
    ComplaintDetail = StudentComplain.objects.get(id=detailcomp_id1)
    ComplaintDetailSerialized = serializers.StudentComplainSerializers(instance=ComplaintDetail).data
    if ComplaintDetail.worker_id is None:
        WorkerDetailSerialized = {}
    else :
        WorkerDetail = WorkerDetail.objects.get(id=ComplaintDetail.worker_id)
        WorkerDetailSerialized = serializers.WorkersSerializers(instance=WorkerDetail).data
    Complainer = User.objects.get(username=ComplaintDetail.complainer.user.username)
    ComplainerSerialized = serializers.UserSerializers(instance=Complainer).data
    ComplainerExtraInfo = ExtraInfo.objects.get(user = Complainer)
    ComplainerExtraInfoSerialized = serializers.ExtraInfoSerializers(instance=ComplainerExtraInfo).data
    response = {
        'Complainer' : ComplainerSerialized,
        'ComplainerExtraInfo':ComplainerExtraInfoSerialized,
        'ComplaintDetails' : ComplaintDetailSerialized,
        'WorkerDetails' : WorkerDetailSerialized
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

