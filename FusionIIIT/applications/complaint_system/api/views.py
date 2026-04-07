from django.shortcuts import get_object_or_404
from django.db import transaction
from datetime import timedelta
import logging
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from django.utils import timezone
from applications.globals.models import User, ExtraInfo
from applications.complaint_system.models import (
    Caretaker,
    ComplaintEvent,
    ComplaintPriority,
    ComplaintStatus,
    StudentComplain,
    VerificationStatus,
    Supervisor,
    Workers,
)
from applications.complaint_system.escalation import escalate_complaint_record
from applications.complaint_system.assignment_policy import lookup_assignment_policy
from applications.complaint_system.notifications import (
    notify_complaint_created,
    notify_reopen_approved,
    notify_reopen_requested,
    notify_status_change,
    notify_verification_result,
)
from . import serializers


PRIORITY_SLA_HOURS = {
    ComplaintPriority.URGENT: 24,
    ComplaintPriority.STANDARD: 72,
    ComplaintPriority.LOW: 168,
}

REOPEN_WINDOW_DAYS = 7


logger = logging.getLogger(__name__)

ALLOWED_TRANSITIONS = {
    ComplaintStatus.PENDING: {ComplaintStatus.IN_PROGRESS, ComplaintStatus.ESCALATED},
    ComplaintStatus.IN_PROGRESS: {ComplaintStatus.RESOLVED, ComplaintStatus.ESCALATED},
    ComplaintStatus.RESOLVED: {ComplaintStatus.CLOSED, ComplaintStatus.REOPENED, ComplaintStatus.ESCALATED},
    ComplaintStatus.CLOSED: {ComplaintStatus.REOPENED},
    ComplaintStatus.ESCALATED: {ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED},
    ComplaintStatus.REOPENED: {ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED, ComplaintStatus.ESCALATED},
}


def _serialize_events(complaint):
    return serializers.ComplaintEventSerializer(complaint.events.select_related('actor', 'actor__user').all(), many=True).data


def _log_complaint_event(complaint, action, actor=None, from_status=None, to_status=None, note='', metadata=None):
    ComplaintEvent.objects.create(
        complaint=complaint,
        actor=actor,
        action=action,
        from_status=from_status,
        to_status=to_status,
        note=note,
        metadata=metadata or {},
    )


def _priority_to_deadline(priority):
    hours = PRIORITY_SLA_HOURS.get(priority, PRIORITY_SLA_HOURS[ComplaintPriority.STANDARD])
    return timezone.now() + timedelta(hours=hours)


def _resolution_reference_time(complaint):
    return complaint.closed_at or complaint.resolved_at or complaint.updated_at or complaint.complaint_date


def _reopen_deadline(complaint):
    reference_time = _resolution_reference_time(complaint)
    if reference_time is None:
        return None
    return reference_time + timedelta(days=REOPEN_WINDOW_DAYS)


def _resolve_assigned_worker(complaint):
    policy = lookup_assignment_policy(complaint.complaint_type, complaint.location)
    fallback_chain = policy.get('fallback_chain', ())

    caretaker = Caretaker.objects.filter(area=complaint.location).select_related('staff_id').first()

    for strategy in fallback_chain:
        worker = None
        if strategy == 'area_and_category' and caretaker is not None:
            worker = Workers.objects.filter(
                secincharge_id__staff_id=caretaker.staff_id,
                worker_type=complaint.complaint_type,
            ).select_related('secincharge_id').first()

        elif strategy == 'category_only':
            worker = Workers.objects.filter(
                worker_type=complaint.complaint_type,
            ).select_related('secincharge_id').first()

        elif strategy == 'any_worker':
            worker = Workers.objects.all().select_related('secincharge_id').first()

        if worker is not None:
            if strategy != 'area_and_category':
                logger.warning(
                    'Complaint assignment used fallback strategy',
                    extra={
                        'complaint_id': complaint.id,
                        'complaint_type': complaint.complaint_type,
                        'location': complaint.location,
                        'strategy': strategy,
                        'policy_source': policy.get('source'),
                    },
                )
            return worker, {
                'policy_source': policy.get('source'),
                'strategy': strategy,
                'team': policy.get('team', ''),
            }

    logger.warning(
        'Complaint assignment found no worker',
        extra={
            'complaint_id': complaint.id,
            'complaint_type': complaint.complaint_type,
            'location': complaint.location,
            'policy_source': policy.get('source'),
        },
    )
    return None, {
        'policy_source': policy.get('source'),
        'strategy': 'unassigned',
        'team': policy.get('team', ''),
    }


def _apply_create_defaults(complaint):
    assignment_meta = {'policy_source': 'global-default', 'strategy': 'unassigned', 'team': ''}

    if not complaint.sla_deadline:
        complaint.sla_deadline = _priority_to_deadline(complaint.priority)

    if not complaint.complaint_finish:
        complaint.complaint_finish = complaint.sla_deadline.date()

    if complaint.assigned_to is None:
        worker, assignment_meta = _resolve_assigned_worker(complaint)
        complaint.assigned_to = worker
    else:
        assignment_meta = {
            'policy_source': 'manual',
            'strategy': 'manual',
            'team': complaint.assigned_team or '',
        }

    if not complaint.assigned_team:
        complaint.assigned_team = assignment_meta.get('team', '')

    complaint.verification_status = VerificationStatus.PENDING

    return assignment_meta


def _can_transition(current_status, next_status):
    return next_status in ALLOWED_TRANSITIONS.get(current_status, set())


def _is_closed_status(status_value):
    return int(status_value) == ComplaintStatus.CLOSED


def _is_complainant(extra, complaint):
    return bool(extra and complaint.complainer_id == extra.id)


def _complaint_payload(complaint):
    complaint_data = serializers.StudentComplainSerializers(instance=complaint).data
    complaint_data['events'] = _serialize_events(complaint)
    return complaint_data


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


def _caretaker_for_user(extra):
    if extra is None:
        return None
    return Caretaker.objects.filter(staff_id=extra).first()


def _is_assigned_caretaker(extra, complaint):
    if extra is None or complaint.assigned_to is None:
        return False
    sec = complaint.assigned_to.secincharge_id
    if sec is None or sec.staff_id_id is None:
        return False
    return sec.staff_id_id == extra.id


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def complaint_details_api(request,detailcomp_id1):
    user, extra = _get_request_extra_info(request)
    complaint_detail = get_object_or_404(StudentComplain, id=detailcomp_id1)

    if not _can_manage_complaint(user, extra, complaint_detail):
        return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    complaint_detail_serialized = _complaint_payload(complaint_detail)
    if complaint_detail.worker_id is None:
        worker_detail_serialized = {}
    else:
        worker_detail = Workers.objects.get(id=complaint_detail.worker_id.id)
        worker_detail_serialized = serializers.WorkersSerializers(instance=worker_detail).data
    if complaint_detail.assigned_to is None:
        assigned_worker_serialized = {}
    else:
        assigned_worker_serialized = serializers.WorkersSerializers(instance=complaint_detail.assigned_to).data
    complainer = User.objects.get(username=complaint_detail.complainer.user.username)
    complainer_serialized = serializers.UserSerializers(instance=complainer).data
    complainer_extra_info = ExtraInfo.objects.get(user=complainer)
    complainer_extra_info_serialized = serializers.ExtraInfoSerializers(instance=complainer_extra_info).data
    response = {
        'complainer': complainer_serialized,
        'complainer_extra_info':complainer_extra_info_serialized,
        'complaint_details': complaint_detail_serialized,
        'worker_details' : worker_detail_serialized,
        'assigned_worker_details': assigned_worker_serialized,
        'status_timeline': complaint_detail_serialized.get('events', []),
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
        with transaction.atomic():
            complaint = serializer.save(complainer=extra)
            assignment_meta = _apply_create_defaults(complaint)
            complaint.save()
            _log_complaint_event(
                complaint,
                action='created',
                actor=extra,
                to_status=complaint.status,
                metadata={
                    'priority': complaint.priority,
                    'sla_deadline': complaint.sla_deadline.isoformat() if complaint.sla_deadline else None,
                    'assigned_to': complaint.assigned_to_id,
                    'assigned_team': complaint.assigned_team,
                    'assignment_policy_source': assignment_meta.get('policy_source'),
                    'assignment_strategy': assignment_meta.get('strategy'),
                },
            )
            transaction.on_commit(lambda: notify_complaint_created(complaint, actor=extra))
        return Response(_complaint_payload(complaint), status=status.HTTP_201_CREATED)
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

    incoming_status = request.data.get('status')
    if incoming_status is not None:
        try:
            incoming_status = int(incoming_status)
        except (TypeError, ValueError):
            return Response({'message': 'Invalid complaint status'}, status=status.HTTP_400_BAD_REQUEST)

        if not _can_transition(complain.status, incoming_status):
            return Response({'message': 'Invalid complaint status transition'}, status=status.HTTP_400_BAD_REQUEST)

        if _is_closed_status(incoming_status):
            return Response(
                {'message': 'Use /verify/<complaint_id> to close after verification'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if incoming_status in (ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED):
            remarks = request.data.get('remarks', '')
            if not str(remarks).strip():
                return Response(
                    {'message': 'remarks are required when updating complaint progress'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    before_status = complain.status

    serializer = serializers.StudentComplainSerializers(complain, data=request.data, partial=True)
    if serializer.is_valid():
        with transaction.atomic():
            complaint = serializer.save()
            if incoming_status == ComplaintStatus.RESOLVED:
                complaint.resolved_at = timezone.now()
                complaint.closed_at = None
                complaint.verification_status = VerificationStatus.PENDING
            elif incoming_status == ComplaintStatus.REOPENED:
                complaint.reopened_at = timezone.now()
                complaint.verification_status = VerificationStatus.PENDING
            if complaint.sla_deadline and not complaint.complaint_finish:
                complaint.complaint_finish = complaint.sla_deadline.date()
            complaint.save()
            if incoming_status is not None and incoming_status != before_status:
                _log_complaint_event(
                    complaint,
                    action='status_updated',
                    actor=extra,
                    from_status=before_status,
                    to_status=incoming_status,
                    note=request.data.get('remarks', ''),
                    metadata={'verification_source': request.data.get('verification_source', '')},
                )
                remarks = request.data.get('remarks', '')
                transaction.on_commit(
                    lambda: notify_status_change(
                        complaint,
                        before_status,
                        incoming_status,
                        actor=extra,
                        remarks=remarks,
                    )
                )
        return Response(_complaint_payload(complaint), status=status.HTTP_200_OK)
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
    
    escalation_reason = request.data.get('escalation_reason', '')
    if not str(escalation_reason).strip():
        return Response({'message': 'escalation_reason is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not _can_transition(complaint.status, ComplaintStatus.ESCALATED):
        return Response({'message': 'Invalid complaint status transition'}, status=status.HTTP_400_BAD_REQUEST)

    escalate_complaint_record(complaint, escalation_reason, actor=extra, automatic=False)

    return Response(_complaint_payload(complaint), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def complaint_history_api(request, c_id):
    user, extra = _get_request_extra_info(request)
    complaint = get_object_or_404(StudentComplain, id=c_id)
    if not _can_manage_complaint(user, extra, complaint):
        return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    return Response({'events': _serialize_events(complaint)}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def reopen_complaint_api(request, c_id):
    user, extra = _get_request_extra_info(request)
    complaint = get_object_or_404(StudentComplain, id=c_id)

    if not _is_complainant(extra, complaint) and not _is_superuser(user):
        supervisor = Supervisor.objects.filter(sup_id=extra).first() if extra else None
        if supervisor is None:
            return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    reopen_reason = request.data.get('reopen_reason', '')
    if not str(reopen_reason).strip():
        return Response({'message': 'reopen_reason is required'}, status=status.HTTP_400_BAD_REQUEST)

    if complaint.status not in (ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED):
        return Response({'message': 'Only resolved or closed complaints can be reopened'}, status=status.HTTP_400_BAD_REQUEST)

    reopen_deadline = _reopen_deadline(complaint)
    if reopen_deadline is not None and timezone.now() > reopen_deadline and not _is_superuser(user):
        return Response({'message': 'Reopen request window has expired'}, status=status.HTTP_400_BAD_REQUEST)

    complaint.reopen_requested = True
    complaint.reopen_reason = reopen_reason
    complaint.reopen_requested_at = timezone.now()

    approve = str(request.data.get('approve', '')).lower() in ('1', 'true', 'yes')
    if approve:
        before_status = complaint.status
        complaint.status = ComplaintStatus.REOPENED
        complaint.reopened_at = timezone.now()
        complaint.verification_status = VerificationStatus.PENDING
        if complaint.assigned_to is None:
            assigned_worker, assignment_meta = _resolve_assigned_worker(complaint)
            complaint.assigned_to = assigned_worker
            complaint.assigned_team = assignment_meta.get('team', complaint.assigned_team or '')
        complaint.save()
        _log_complaint_event(
            complaint,
            action='reopen_approved',
            actor=extra,
            from_status=before_status,
            to_status=ComplaintStatus.REOPENED,
            note=reopen_reason,
        )
        transaction.on_commit(lambda: notify_reopen_approved(complaint, actor=extra, reason=reopen_reason))
    else:
        complaint.save()
        _log_complaint_event(
            complaint,
            action='reopen_requested',
            actor=extra,
            from_status=complaint.status,
            note=reopen_reason,
        )
        transaction.on_commit(lambda: notify_reopen_requested(complaint, actor=extra, reason=reopen_reason))

    return Response(_complaint_payload(complaint), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def verify_complaint_api(request, c_id):
    user, extra = _get_request_extra_info(request)
    complaint = get_object_or_404(StudentComplain, id=c_id)
    if not _can_manage_complaint(user, extra, complaint) and not _is_complainant(extra, complaint):
        return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    verification_source = str(request.data.get('verification_source', '')).strip().lower()
    if not verification_source:
        return Response({'message': 'verification_source is required'}, status=status.HTTP_400_BAD_REQUEST)

    valid_sources = {'complainant', 'supervisor'}
    if verification_source not in valid_sources:
        return Response({'message': 'verification_source must be complainant or supervisor'}, status=status.HTTP_400_BAD_REQUEST)

    if complaint.status != ComplaintStatus.RESOLVED:
        return Response({'message': 'Only resolved complaints can be verified and closed'}, status=status.HTTP_400_BAD_REQUEST)

    reopen_deadline = _reopen_deadline(complaint)
    if reopen_deadline is not None and timezone.now() > reopen_deadline and not _is_superuser(user):
        return Response({'message': 'Verification window has expired'}, status=status.HTTP_400_BAD_REQUEST)

    verification_decision = str(request.data.get('verification_decision', 'approve')).strip().lower()
    if verification_decision not in {'approve', 'reject'}:
        return Response({'message': 'verification_decision must be approve or reject'}, status=status.HTTP_400_BAD_REQUEST)

    notes = request.data.get('verification_notes', request.data.get('remarks', ''))
    if verification_decision == 'reject' and not str(notes).strip():
        return Response({'message': 'verification_notes are required when rejecting resolution'}, status=status.HTTP_400_BAD_REQUEST)

    if verification_source == 'complainant' and not _is_complainant(extra, complaint):
        return Response({'message': 'Only the complainant can verify as complainant'}, status=status.HTTP_403_FORBIDDEN)

    if verification_source == 'supervisor':
        supervisor = Supervisor.objects.filter(sup_id=extra, type=complaint.complaint_type).first() if extra else None
        if supervisor is None and not _is_superuser(user):
            return Response({'message': 'Only matching supervisor can verify as supervisor'}, status=status.HTTP_403_FORBIDDEN)

    before_status = complaint.status

    complaint.verification_source = verification_source
    complaint.verification_notes = notes

    if verification_decision == 'approve':
        complaint.verification_status = VerificationStatus.APPROVED
        complaint.status = ComplaintStatus.CLOSED
        complaint.closed_at = timezone.now()
        complaint.reopen_requested = False
        complaint.reopen_reason = ''
        complaint.reopen_requested_at = None
        action = 'verified_and_closed'
        to_status = ComplaintStatus.CLOSED
    else:
        complaint.verification_status = VerificationStatus.REJECTED
        complaint.status = ComplaintStatus.REOPENED
        complaint.reopened_at = timezone.now()
        complaint.reopen_requested = True
        complaint.reopen_reason = notes or 'Resolution rejected during verification'
        complaint.reopen_requested_at = timezone.now()
        complaint.closed_at = None
        action = 'verification_rejected'
        to_status = ComplaintStatus.REOPENED

    complaint.save()
    _log_complaint_event(
        complaint,
        action=action,
        actor=extra,
        from_status=before_status,
        to_status=to_status,
        note=notes,
        metadata={
            'verification_source': verification_source,
            'verification_decision': verification_decision,
        },
    )
    transaction.on_commit(
        lambda: notify_verification_result(
            complaint,
            actor=extra,
            decision=verification_decision,
            notes=notes,
        )
    )
    return Response(_complaint_payload(complaint), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def caretaker_action_api(request, c_id):
    user, extra = _get_request_extra_info(request)
    complaint = get_object_or_404(StudentComplain, id=c_id)

    caretaker = _caretaker_for_user(extra)
    if caretaker is None and not _is_superuser(user):
        return Response({'message': 'Only caretakers can update complaint progress'}, status=status.HTTP_403_FORBIDDEN)

    if not _is_superuser(user) and not _is_assigned_caretaker(extra, complaint):
        return Response({'message': 'Only assigned caretaker can update this complaint'}, status=status.HTTP_403_FORBIDDEN)

    incoming_status = request.data.get('status')
    if incoming_status is None:
        return Response({'message': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        incoming_status = int(incoming_status)
    except (TypeError, ValueError):
        return Response({'message': 'Invalid complaint status'}, status=status.HTTP_400_BAD_REQUEST)

    if incoming_status not in (ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED):
        return Response({'message': 'Caretaker can only set status to In Progress or Resolved'}, status=status.HTTP_400_BAD_REQUEST)

    if not _can_transition(complaint.status, incoming_status):
        return Response({'message': 'Invalid complaint status transition'}, status=status.HTTP_400_BAD_REQUEST)

    notes = request.data.get('remarks', '')
    if not str(notes).strip():
        return Response({'message': 'remarks are required'}, status=status.HTTP_400_BAD_REQUEST)

    before_status = complaint.status
    complaint.status = incoming_status
    complaint.remarks = notes
    complaint.progress_notes = request.data.get('progress_notes', notes)
    complaint.comment = str(notes)[:100]

    eta = request.data.get('estimated_resolution_time')
    if eta not in (None, ''):
        complaint.estimated_resolution_time = eta

    attachment = request.FILES.get('progress_attachment')
    if attachment is not None:
        complaint.progress_attachment = attachment

    complaint.save()

    _log_complaint_event(
        complaint,
        action='caretaker_progress_update',
        actor=extra,
        from_status=before_status,
        to_status=incoming_status,
        note=notes,
        metadata={
            'estimated_resolution_time': complaint.estimated_resolution_time.isoformat() if complaint.estimated_resolution_time else None,
            'has_progress_attachment': bool(attachment),
        },
    )

    transaction.on_commit(
        lambda: notify_status_change(
            complaint,
            before_status,
            incoming_status,
            actor=extra,
            remarks=notes,
        )
    )

    return Response(_complaint_payload(complaint), status=status.HTTP_200_OK)
