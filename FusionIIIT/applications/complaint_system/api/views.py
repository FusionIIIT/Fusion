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
from applications.globals.models import User,ExtraInfo
from applications.complaint_system.models import Caretaker, StudentComplain, Supervisor, Workers
from . import serializers


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def complaint_details_api(request,detailcomp_id1):
    complaint_detail = StudentComplain.objects.get(id=detailcomp_id1)
    complaint_detail_serialized = serializers.StudentComplainSerializers(instance=complaint_detail).data
    if complaint_detail.worker_id is None:
        worker_detail_serialized = {}
    else :
        worker_detail = Workers.objects.get(id=complaint_detail.worker_id.id)
        worker_detail_serialized = serializers.WorkersSerializers(instance=worker_detail).data
    complainer = User.objects.get(username=complaint_detail.complainer.user.username)
    complainer_serialized = serializers.UserSerializers(instance=complainer).data
    complainer_extra_info = ExtraInfo.objects.get(user = complainer)
    complainer_extra_info_serialized = serializers.ExtraInfoSerializers(instance=complainer_extra_info).data
    response = {
        'complainer' : complainer_serialized,
        'complainer_extra_info':complainer_extra_info_serialized,
        'complaint_details' : complaint_detail_serialized,
        'worker_details' : worker_detail_serialized
    }
    return Response(data=response,status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def student_complain_api(request):
    user = get_object_or_404(User,username = request.user.username)
    user = ExtraInfo.objects.all().filter(user = user).first()

    user_type = 'student'
    extra_info_id = ExtraInfo.objects.get(id=user.id)
    caretaker = Caretaker.objects.filter(staff_id=extra_info_id)
    supervisor = Supervisor.objects.filter(sup_id=extra_info_id)
    if caretaker.exists():
        complaints = StudentComplain.get_complaints_by_user(user, 'caretaker')
        user_type = 'caretaker'
    elif supervisor.exists():
        complaints = StudentComplain.get_complaints_by_user(user, 'supervisor')
        user_type = 'supervisor'
    else:
        complaints = StudentComplain.get_complaints_by_user(user, 'student')

    complaints = serializers.StudentComplainSerializers(complaints,many=True).data

    if user_type == 'caretaker' or user_type == 'student':
        for complaint in complaints:
            last_forwarded = StudentComplain.get_complaint_owner(complaint['id'])
            if last_forwarded.username != request.user.username:
                complaint['last_forwarded'] = {
                    'name': last_forwarded.first_name + ' ' + last_forwarded.last_name,
                    'username': last_forwarded.username,
                }

    resp = {
        'student_complain' : complaints,
        'user_type': user_type,
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def create_complain_api(request):
    serializer = serializers.StudentComplainSerializers(data=request.data)
    if serializer.is_valid():
        serializer.save()
        StudentComplain.create_file_for_complaint(serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELTE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_complain_api(request,c_id):
    try: 
        complain = StudentComplain.objects.get(id = c_id) 
    except StudentComplain.DoesNotExist: 
        return Response({'message': 'The Complain does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        complain.delete()
        return Response({'message': 'Complain deleted'},status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'PUT':
        serializer = serializers.StudentComplainSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def worker_api(request):

    if request.method == 'GET':
        worker = Workers.objects.all()
        workers = serializers.WorkersSerializers(worker,many=True).data
        resp = {
            'workers' : workers,
        }
        return Response(data=resp,status=status.HTTP_200_OK)

    elif request.method =='POST':
        user = get_object_or_404(User ,username=request.user.username)
        user = ExtraInfo.objects.all().filter(user = user).first()
        try :
            caretaker = Caretaker.objects.get(staff_id=user)
        except Caretaker.DoesNotExist:
            return Response({'message':'Logged in user does not have the permissions'},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        serializer = serializers.WorkersSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_worker_api(request,w_id):
    user = get_object_or_404(User ,username=request.user.username)
    user = ExtraInfo.objects.all().filter(user = user).first()
    try :
        caretaker = Caretaker.objects.get(staff_id=user)
    except Caretaker.DoesNotExist:
        return Response({'message':'Logged in user does not have the permissions'},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    try: 
        worker = Workers.objects.get(id = w_id) 
    except Workers.DoesNotExist: 
        return Response({'message': 'The worker does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        worker.delete()
        return Response({'message': 'Worker deleted'},status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'PUT':
        serializer = serializers.WorkersSerializers(worker,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def caretaker_api(request):
    if request.method == 'GET':
        caretakers = None
        user = get_object_or_404(User,username = request.user.username)
        user = ExtraInfo.objects.get(user = user)
        extra_info_id = ExtraInfo.objects.get(id=user.id)
        supervisor = Supervisor.objects.filter(sup_id=extra_info_id)
        if supervisor.exists():
            caretaker = Caretaker.objects.filter(area = supervisor.first().area)
        else:
            caretaker = Caretaker.objects.all()
        caretakers = serializers.CaretakerSerializers(caretaker,many=True).data
        resp = {
            'caretakers' : caretakers,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        user = get_object_or_404(User ,username=request.user.username)
        user = ExtraInfo.objects.all().filter(user = user).first()
        try :
            supervisor = Supervisor.objects.get(sup_id=user)
        except Supervisor.DoesNotExist:
            return Response({'message':'Logged in user does not have the permissions'},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        serializer = serializers.CaretakerSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST) 

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_caretaker_api(request,c_id):
    user = get_object_or_404(User ,username=request.user.username)
    user = ExtraInfo.objects.all().filter(user = user).first()
    try :
        supervisor = Supervisor.objects.get(sup_id=user)
    except Supervisor.DoesNotExist:
        return Response({'message':'Logged in user does not have the permissions'},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    try: 
        caretaker = Caretaker.objects.get(id = c_id) 
    except Caretaker.DoesNotExist: 
        return Response({'message': 'The Caretaker does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        caretaker.delete()
        return Response({'message': 'Caretaker deleted'},status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'PUT':
        serializer = serializers.CaretakerSerializers(caretaker,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def supervisor_api(request):

    if request.method == 'GET':
        supervisor = Supervisor.objects.all()
        supervisors = serializers.SupervisorSerializers(supervisor,many=True).data
        resp = {
            'supervisors' : supervisors,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        user = get_object_or_404(User,username=request.user.username)
        if user.is_superuser == False:
            return Response({'message':'Logged in user does not have permission'},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        serializer = serializers.SupervisorSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
   
@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_supervisor_api(request,s_id):
    user = get_object_or_404(User,username=request.user.username)
    if user.is_superuser == False:
        return Response({'message':'Logged in user does not have permission'},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    try: 
        supervisor = Supervisor.objects.get(id = s_id) 
    except Supervisor.DoesNotExist: 
        return Response({'message': 'The Caretaker does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        supervisor.delete()
        return Response({'message': 'Caretaker deleted'},status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'PUT':
        serializer = serializers.SupervisorSerializers(supervisor,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def forward_complaint_api(request):
    user = get_object_or_404(User, username=request.user.username) 
    user = ExtraInfo.objects.get(user=user)
    supervisor = Supervisor.objects.filter(sup_id=user)
    caretaker = Caretaker.objects.filter(staff_id=user)

    if supervisor.exists() or caretaker.exists():
        forward_supervisor = Supervisor.objects.get(id=request.data['forward_id'])
        StudentComplain.forward_complaint(forward_supervisor.sup_id, request.data['complaint_id'])
        return Response({'message':'Complaint forwarded'},status=status.HTTP_200_OK)
    else:
        return Response({'message':'Logged in user does not have permission'},status=status.HTTP_403_FORBIDDEN)
