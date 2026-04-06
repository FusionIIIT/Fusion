from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from django.utils import timezone
from applications.globals.models import User, ExtraInfo
from applications.complaint_system.models import Caretaker, StudentComplain, Supervisor, Workers
from . import serializers


def _get_request_extra_info(request):
    user = get_object_or_404(User, username=request.user.username)
    extra = ExtraInfo.objects.filter(user=user).first()
    return user, extra


def _is_superuser(user):
    return bool(user and user.is_superuser)


def _can_manage_complaint(user, extra, complaint):
    # Owner can always access their own complaint.
    if extra and complaint.complainer_id == extra.id:
        return True

    if _is_superuser(user):
        return True

    caretaker = Caretaker.objects.filter(staff_id=extra).first() if extra else None
    if caretaker and complaint.location == caretaker.area:
        return True

    supervisor = Supervisor.objects.filter(sup_id=extra).first() if extra else None
    if supervisor and complaint.complaint_type == supervisor.type:
        return True

    return False


def _can_change_status(user, extra):
    if _is_superuser(user):
        return True

    if extra is None:
        return False

    if Caretaker.objects.filter(staff_id=extra).exists():
        return True

    if Supervisor.objects.filter(sup_id=extra).exists():
        return True

    return False


def _can_escalate_complaint(user, extra):
    """Only caretakers can escalate complaints"""
    if _is_superuser(user):
        return True

    if extra is None:
        return False

    if Caretaker.objects.filter(staff_id=extra).exists():
        return True

    return False


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def complaint_details_api(request,detailcomp_id1):
    user, extra = _get_request_extra_info(request)
    complaint_detail = get_object_or_404(StudentComplain, id=detailcomp_id1)

    if not _can_manage_complaint(user, extra, complaint_detail):
        return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    complaint_detail_serialized = serializers.StudentComplainSerializers(instance=complaint_detail).data
    if complaint_detail.worker_id is None:
        worker_detail_serialized = {}
    else:
        worker_detail = Workers.objects.get(id=complaint_detail.worker_id.id)
        worker_detail_serialized = serializers.WorkersSerializers(instance=worker_detail).data
    complainer = User.objects.get(username=complaint_detail.complainer.user.username)
    complainer_serialized = serializers.UserSerializers(instance=complainer).data
    complainer_extra_info = ExtraInfo.objects.get(user=complainer)
    complainer_extra_info_serialized = serializers.ExtraInfoSerializers(instance=complainer_extra_info).data
    response = {
        'complainer': complainer_serialized,
        'complainer_extra_info':complainer_extra_info_serialized,
        'complaint_details': complaint_detail_serialized,
        'worker_details' : worker_detail_serialized
    }
    return Response(data=response, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def student_complain_api(request):
    user, extra = _get_request_extra_info(request)
    if extra is None:
        return Response({'student_complain': []}, status=status.HTTP_200_OK)

    if _is_superuser(user):
        complain = StudentComplain.objects.all().order_by('-complaint_date')
    elif extra.user_type in ('student', 'staff', 'faculty'):
        # Default to own complaints; role-specific expanded access below.
        complain = StudentComplain.objects.filter(complainer=extra)

        caretaker = Caretaker.objects.filter(staff_id=extra).first()
        if caretaker:
            complain = StudentComplain.objects.filter(location=caretaker.area)

        supervisor = Supervisor.objects.filter(sup_id=extra).first()
        if supervisor:
            complain = StudentComplain.objects.filter(complaint_type=supervisor.type)
    else:
        complain = StudentComplain.objects.none()

    complains = serializers.StudentComplainSerializers(complain.order_by('-complaint_date'), many=True).data
    resp = {
        'student_complain': complains,
    }
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def create_complain_api(request):
    _, extra = _get_request_extra_info(request)
    if extra is None:
        return Response({'message': 'User profile not found'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = serializers.StudentComplainSerializers(data=request.data)
    if serializer.is_valid():
        serializer.save(complainer=extra)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_complain_api(request,c_id):
    user, extra = _get_request_extra_info(request)
    try:
        complain = StudentComplain.objects.get(id=c_id)
    except StudentComplain.DoesNotExist:
        return Response({'message': 'The complaint does not exist'}, status=status.HTTP_404_NOT_FOUND)

    if not _can_manage_complaint(user, extra, complain):
        return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        complain.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if 'status' in request.data and not _can_change_status(user, extra):
        return Response(
            {'message': 'Only caretaker/supervisor can change complaint status'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = serializers.StudentComplainSerializers(complain, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def worker_api(request):

    if request.method == 'GET':
        worker = Workers.objects.all()
        workers = serializers.WorkersSerializers(worker, many=True).data
        resp = {
            'workers': workers,
        }
        return Response(data=resp, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        _, extra = _get_request_extra_info(request)
        try:
            caretaker = Caretaker.objects.get(staff_id=extra)
        except Caretaker.DoesNotExist:
            return Response({'message': 'Logged in user does not have permission'}, status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.WorkersSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_worker_api(request,w_id):
    _, extra = _get_request_extra_info(request)
    try:
        caretaker = Caretaker.objects.get(staff_id=extra)
    except Caretaker.DoesNotExist:
        return Response({'message': 'Logged in user does not have permission'}, status=status.HTTP_403_FORBIDDEN)
    try:
        worker = Workers.objects.get(id=w_id)
    except Workers.DoesNotExist:
        return Response({'message': 'The worker does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        worker.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = serializers.WorkersSerializers(worker, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def caretaker_api(request):

    if request.method == 'GET':
        caretaker = Caretaker.objects.all()
        caretakers = serializers.CaretakerSerializers(caretaker, many=True).data
        resp = {
            'caretakers': caretakers,
        }
        return Response(data=resp, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        _, extra = _get_request_extra_info(request)
        try:
            supervisor = Supervisor.objects.get(sup_id=extra)
        except Supervisor.DoesNotExist:
            return Response({'message': 'Logged in user does not have permission'}, status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.CaretakerSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_caretaker_api(request,c_id):
    _, extra = _get_request_extra_info(request)
    try:
        supervisor = Supervisor.objects.get(sup_id=extra)
    except Supervisor.DoesNotExist:
        return Response({'message': 'Logged in user does not have permission'}, status=status.HTTP_403_FORBIDDEN)
    try:
        caretaker = Caretaker.objects.get(id=c_id)
    except Caretaker.DoesNotExist:
        return Response({'message': 'The Caretaker does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        caretaker.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = serializers.CaretakerSerializers(caretaker, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def supervisor_api(request):

    if request.method == 'GET':
        supervisor = Supervisor.objects.all()
        supervisors = serializers.SupervisorSerializers(supervisor, many=True).data
        resp = {
            'supervisors': supervisors,
        }
        return Response(data=resp, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        user, _ = _get_request_extra_info(request)
        if not _is_superuser(user):
            return Response({'message': 'Logged in user does not have permission'}, status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.SupervisorSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_supervisor_api(request,s_id):
    user, _ = _get_request_extra_info(request)
    if not _is_superuser(user):
        return Response({'message': 'Logged in user does not have permission'}, status=status.HTTP_403_FORBIDDEN)
    try:
        supervisor = Supervisor.objects.get(id=s_id)
    except Supervisor.DoesNotExist:
        return Response({'message': 'The Supervisor does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        supervisor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = serializers.SupervisorSerializers(supervisor, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def escalate_complaint_api(request, c_id):
    """Escalate a complaint to supervisor"""
    user, extra = _get_request_extra_info(request)
    
    # Check if user can escalate
    if not _can_escalate_complaint(user, extra):
        return Response(
            {'message': 'Only caretaker can escalate complaints'},
            status=status.HTTP_403_FORBIDDEN,
        )
    
    try:
        complaint = StudentComplain.objects.get(id=c_id)
    except StudentComplain.DoesNotExist:
        return Response({'message': 'The complaint does not exist'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if user can manage this complaint
    if not _can_manage_complaint(user, extra, complaint):
        return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Update complaint with escalation info
    escalation_reason = request.data.get('escalation_reason', '')
    complaint.is_escalated = 1
    complaint.escalation_reason = escalation_reason
    complaint.escalated_date = timezone.now()
    complaint.save()
    
    serializer = serializers.StudentComplainSerializers(complaint)
    return Response(serializer.data, status=status.HTTP_200_OK)
