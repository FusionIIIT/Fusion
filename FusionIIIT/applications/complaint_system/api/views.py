from django.shortcuts import get_object_or_404
from django.db import transaction
from datetime import timedelta
from collections import Counter, defaultdict
import logging
from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
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
    notify_assignment_change,
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
MAX_REPORT_ROWS = 1000


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

    if complaint.is_draft:
        return False

    caretaker = Caretaker.objects.filter(staff_id=extra).first() if extra else None
    if caretaker and complaint.location == caretaker.area:
        return True

    if _has_supervisor_access(extra, complaint):
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


def _can_oversee_complaint(user, extra, complaint):
    if _is_superuser(user):
        return True

    if complaint.is_draft:
        return False

    return _has_supervisor_access(extra, complaint)


def _has_supervisor_access(extra, complaint):
    if extra is None or complaint is None:
        return False
    return Supervisor.objects.filter(
        sup_id=extra,
        type=complaint.complaint_type,
    ).filter(
        Q(area='') | Q(area=complaint.location)
    ).exists()


def _supervisor_scope_query(extra):
    if extra is None:
        return Q(pk__in=[])

    mappings = Supervisor.objects.filter(sup_id=extra).values_list('type', 'area')
    scope_query = Q(pk__in=[])
    for complaint_type, area in mappings:
        if area:
            scope_query |= Q(complaint_type=complaint_type, location=area, is_draft=False)
        else:
            scope_query |= Q(complaint_type=complaint_type, is_draft=False)
    return scope_query


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


def _parse_datetime_input(value):
    if value in (None, ''):
        return None
    if hasattr(value, 'isoformat'):
        return value
    parsed = parse_datetime(str(value))
    return parsed or value


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _draft_submission_errors(payload):
    missing = []
    for field in ('complaint_type', 'location', 'details'):
        value = payload.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return missing


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

        scope_query = Q()
        caretaker = Caretaker.objects.filter(staff_id=extra).first()
        if caretaker:
            scope_query |= Q(location=caretaker.area, is_draft=False)

        supervisor_scope = _supervisor_scope_query(extra)
        if supervisor_scope.children:
            scope_query |= supervisor_scope

        if scope_query:
            complain = StudentComplain.objects.filter(scope_query)
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

    is_draft = str(request.data.get('is_draft', '')).lower() in ('1', 'true', 'yes')

    serializer = serializers.StudentComplainSerializers(data=request.data, context={'draft_mode': is_draft})
    if serializer.is_valid():
        with transaction.atomic():
            complaint = serializer.save(
                complainer=extra,
                is_draft=is_draft,
                submitted_at=None if is_draft else timezone.now(),
            )
            assignment_meta = {'policy_source': 'draft', 'strategy': 'draft', 'team': ''}
            if not is_draft:
                assignment_meta = _apply_create_defaults(complaint)
            complaint.save()
            _log_complaint_event(
                complaint,
                action='draft_saved' if is_draft else 'created',
                actor=extra,
                to_status=complaint.status,
                metadata={
                    'is_draft': complaint.is_draft,
                    'priority': complaint.priority,
                    'sla_deadline': complaint.sla_deadline.isoformat() if complaint.sla_deadline else None,
                    'assigned_to': complaint.assigned_to_id,
                    'assigned_team': complaint.assigned_team,
                    'assignment_policy_source': assignment_meta.get('policy_source'),
                    'assignment_strategy': assignment_meta.get('strategy'),
                },
            )
            if not is_draft:
                transaction.on_commit(lambda: notify_complaint_created(complaint, actor=extra))
        return Response(_complaint_payload(complaint), status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def submit_draft_api(request, c_id):
    user, extra = _get_request_extra_info(request)
    complaint = get_object_or_404(StudentComplain, id=c_id)

    if not complaint.is_draft:
        return Response({'message': 'Complaint is already submitted'}, status=status.HTTP_400_BAD_REQUEST)

    if not _is_complainant(extra, complaint) and not _is_superuser(user):
        return Response({'message': 'Only owner can submit this draft'}, status=status.HTTP_403_FORBIDDEN)

    incoming_data = request.data or {}
    serializer = serializers.StudentComplainSerializers(
        complaint,
        data=incoming_data,
        partial=True,
        context={'draft_mode': False},
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    pending_payload = {**{k: getattr(complaint, k) for k in ('complaint_type', 'location', 'details')}, **serializer.validated_data}
    missing_fields = _draft_submission_errors(pending_payload)
    if missing_fields:
        return Response(
            {'message': 'Draft is missing required fields', 'missing_fields': missing_fields},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        before_status = complaint.status
        complaint = serializer.save()
        complaint.is_draft = False
        complaint.submitted_at = timezone.now()
        if str(complaint.complaint_ref).startswith('DRF-'):
            complaint.complaint_ref = ''
        assignment_meta = _apply_create_defaults(complaint)
        complaint.save()

        _log_complaint_event(
            complaint,
            action='draft_submitted',
            actor=extra,
            from_status=before_status,
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

    return Response(_complaint_payload(complaint), status=status.HTTP_200_OK)

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

    if complain.is_draft and 'status' in request.data:
        return Response({'message': 'Draft complaints cannot change status'}, status=status.HTTP_400_BAD_REQUEST)

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

    if complaint.is_draft:
        return Response({'message': 'Draft complaints cannot be escalated'}, status=status.HTTP_400_BAD_REQUEST)
    
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

    if complaint.is_draft:
        return Response({'message': 'Draft complaints cannot be reopened'}, status=status.HTTP_400_BAD_REQUEST)

    if not _is_complainant(extra, complaint) and not _is_superuser(user):
        if not _has_supervisor_access(extra, complaint):
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
    if complaint.is_draft:
        return Response({'message': 'Draft complaints cannot be verified'}, status=status.HTTP_400_BAD_REQUEST)
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
        if not _has_supervisor_access(extra, complaint) and not _is_superuser(user):
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

    if complaint.is_draft:
        return Response({'message': 'Draft complaints cannot be updated by caretaker'}, status=status.HTTP_400_BAD_REQUEST)

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
        complaint.estimated_resolution_time = _parse_datetime_input(eta)

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def bulk_complaint_action_api(request):
    user, extra = _get_request_extra_info(request)
    action = str(request.data.get('action', '')).strip().lower()
    complaint_ids = request.data.get('complaint_ids', [])

    if isinstance(complaint_ids, str):
        complaint_ids = [item for item in complaint_ids.split(',') if item]

    if not isinstance(complaint_ids, (list, tuple)) or not complaint_ids:
        return Response({'message': 'complaint_ids are required'}, status=status.HTTP_400_BAD_REQUEST)

    complaints = list(StudentComplain.objects.filter(id__in=complaint_ids).select_related(
        'complainer',
        'complainer__user',
        'assigned_to',
        'assigned_to__secincharge_id',
        'assigned_to__secincharge_id__staff_id',
    ))
    complaints_by_id = {str(complaint.id): complaint for complaint in complaints}
    missing_ids = [str(complaint_id) for complaint_id in complaint_ids if str(complaint_id) not in complaints_by_id]
    if missing_ids:
        return Response(
            {'message': 'Some complaints were not found', 'missing_ids': missing_ids},
            status=status.HTTP_404_NOT_FOUND,
        )

    if action not in {'reassign', 'intervene'}:
        return Response({'message': 'Invalid bulk action'}, status=status.HTTP_400_BAD_REQUEST)

    if action == 'reassign':
        worker_id = request.data.get('assigned_to')
        if not worker_id:
            return Response({'message': 'assigned_to is required for bulk reassignment'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            worker = Workers.objects.select_related('secincharge_id', 'secincharge_id__staff_id').get(id=worker_id)
        except Workers.DoesNotExist:
            return Response({'message': 'Selected worker does not exist'}, status=status.HTTP_404_NOT_FOUND)

    else:
        worker = None

    updated = []
    with transaction.atomic():
        for complaint_id in complaint_ids:
            complaint = complaints_by_id[str(complaint_id)]

            if complaint.is_draft:
                return Response({'message': 'Draft complaints are not eligible for bulk action'}, status=status.HTTP_400_BAD_REQUEST)

            if not _can_oversee_complaint(user, extra, complaint):
                return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            if action == 'reassign':
                previous_worker = complaint.assigned_to
                complaint.assigned_to = worker
                complaint.worker_id = worker
                complaint.assigned_team = str(request.data.get('assigned_team', '')).strip() or complaint.assigned_team or ''

                reassignment_note = str(request.data.get('remarks', '')).strip()
                if reassignment_note:
                    complaint.remarks = reassignment_note
                    complaint.comment = reassignment_note[:100]

                complaint.save()
                _log_complaint_event(
                    complaint,
                    action='bulk_reassigned',
                    actor=extra,
                    note=reassignment_note,
                    metadata={
                        'previous_assigned_to': getattr(previous_worker, 'id', None),
                        'assigned_to': worker.id,
                        'assigned_team': complaint.assigned_team,
                    },
                )
                transaction.on_commit(
                    lambda complaint=complaint, previous_worker=previous_worker, reassignment_note=reassignment_note: notify_assignment_change(
                        complaint,
                        actor=extra,
                        previous_worker=previous_worker,
                        note=reassignment_note,
                    )
                )

            else:
                incoming_status = request.data.get('status')
                if incoming_status is None:
                    return Response({'message': 'status is required for bulk intervention'}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    incoming_status = int(incoming_status)
                except (TypeError, ValueError):
                    return Response({'message': 'Invalid complaint status'}, status=status.HTTP_400_BAD_REQUEST)

                if not _can_transition(complaint.status, incoming_status):
                    return Response({'message': 'Invalid complaint status transition'}, status=status.HTTP_400_BAD_REQUEST)

                remarks = str(request.data.get('remarks', '')).strip()
                if not remarks:
                    return Response({'message': 'remarks are required for bulk intervention'}, status=status.HTTP_400_BAD_REQUEST)

                before_status = complaint.status
                complaint.status = incoming_status
                complaint.remarks = remarks
                complaint.progress_notes = str(request.data.get('progress_notes', remarks))
                complaint.comment = remarks[:100]

                eta = request.data.get('estimated_resolution_time')
                if eta not in (None, ''):
                    complaint.estimated_resolution_time = _parse_datetime_input(eta)

                if incoming_status == ComplaintStatus.RESOLVED:
                    complaint.resolved_at = timezone.now()
                    complaint.closed_at = None
                    complaint.verification_status = VerificationStatus.PENDING
                elif incoming_status == ComplaintStatus.REOPENED:
                    complaint.reopened_at = timezone.now()
                    complaint.verification_status = VerificationStatus.PENDING

                complaint.save()
                _log_complaint_event(
                    complaint,
                    action='bulk_intervention',
                    actor=extra,
                    from_status=before_status,
                    to_status=incoming_status,
                    note=remarks,
                    metadata={
                        'estimated_resolution_time': complaint.estimated_resolution_time.isoformat() if complaint.estimated_resolution_time else None,
                    },
                )
                transaction.on_commit(
                    lambda complaint=complaint, before_status=before_status, incoming_status=incoming_status, remarks=remarks: notify_status_change(
                        complaint,
                        before_status,
                        incoming_status,
                        actor=extra,
                        remarks=remarks,
                    )
                )

            updated.append(_complaint_payload(complaint))

    return Response(
        {
            'action': action,
            'updated_count': len(updated),
            'complaints': updated,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def report_analytics_api(request):
    user, extra = _get_request_extra_info(request)
    if not _is_superuser(user):
        if not (extra and Supervisor.objects.filter(sup_id=extra).exists()):
            return Response({'message': 'Only admin/supervisor can generate reports'}, status=status.HTTP_403_FORBIDDEN)

    date_from = parse_date(str(request.query_params.get('date_from', '')).strip())
    date_to = parse_date(str(request.query_params.get('date_to', '')).strip())
    category = str(request.query_params.get('category', '')).strip()
    location = str(request.query_params.get('location', '')).strip()

    if date_from and date_to and date_from > date_to:
        return Response({'message': 'date_from cannot be after date_to'}, status=status.HTTP_400_BAD_REQUEST)

    queryset = StudentComplain.objects.filter(is_draft=False).order_by('-complaint_date')

    if date_from:
        queryset = queryset.filter(complaint_date__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(complaint_date__date__lte=date_to)
    if category:
        queryset = queryset.filter(complaint_type=category)
    if location:
        queryset = queryset.filter(location=location)

    if not _is_superuser(user):
        supervisor_scope = _supervisor_scope_query(extra)
        queryset = queryset.filter(supervisor_scope)

    total_matched = queryset.count()
    complaints = list(queryset[:MAX_REPORT_ROWS])
    is_truncated = total_matched > len(complaints)

    total_resolution_hours = 0.0
    resolved_count = 0
    compliant_count = 0
    reopen_count = 0
    feedback_count = 0

    for complaint in complaints:
        if str(getattr(complaint, 'feedback', '')).strip():
            feedback_count += 1

        if complaint.reopen_requested or complaint.reopened_at or complaint.status == ComplaintStatus.REOPENED:
            reopen_count += 1

        resolution_time = complaint.closed_at or complaint.resolved_at
        if resolution_time:
            resolved_count += 1
            total_resolution_hours += (resolution_time - complaint.complaint_date).total_seconds() / 3600.0
            if complaint.sla_deadline and resolution_time <= complaint.sla_deadline:
                compliant_count += 1

    average_resolution = (total_resolution_hours / resolved_count) if resolved_count else 0.0
    sla_compliance_rate = ((compliant_count * 100.0) / resolved_count) if resolved_count else 0.0
    reopen_rate = ((reopen_count * 100.0) / len(complaints)) if complaints else 0.0
    feedback_response_rate = ((feedback_count * 100.0) / len(complaints)) if complaints else 0.0

    status_logs = list(
        ComplaintEvent.objects.filter(complaint__in=complaints)
        .values('action')
        .annotate(count=Count('id'))
        .order_by('-count', 'action')[:10]
    )

    category_counter = Counter()
    location_counter = Counter()
    issue_cluster_counter = Counter()
    trend = defaultdict(lambda: {'created': 0, 'resolved': 0, 'closed': 0, 'escalated': 0})

    complaint_ids = [complaint.id for complaint in complaints]
    escalation_events = ComplaintEvent.objects.filter(
        complaint_id__in=complaint_ids,
        action__in=('escalated', 'auto_escalated'),
    ).values('created_at')

    for complaint in complaints:
        category_counter[complaint.complaint_type] += 1
        location_counter[complaint.location] += 1
        issue_cluster_counter[(complaint.complaint_type, complaint.location)] += 1

        created_day = complaint.complaint_date.date().isoformat()
        trend[created_day]['created'] += 1

        if complaint.resolved_at:
            resolved_day = complaint.resolved_at.date().isoformat()
            trend[resolved_day]['resolved'] += 1

        if complaint.closed_at:
            closed_day = complaint.closed_at.date().isoformat()
            trend[closed_day]['closed'] += 1

    for event in escalation_events:
        event_day = event['created_at'].date().isoformat()
        trend[event_day]['escalated'] += 1

    recurring_issue_clusters = [
        {
            'complaint_type': complaint_type,
            'location': issue_location,
            'count': count,
        }
        for (complaint_type, issue_location), count in issue_cluster_counter.most_common(10)
        if count > 1
    ]

    trend_series = [
        {
            'date': day,
            'created': values['created'],
            'resolved': values['resolved'],
            'closed': values['closed'],
            'escalated': values['escalated'],
        }
        for day, values in sorted(trend.items())
    ]

    return Response(
        {
            'report_generated_at': timezone.now().isoformat(),
            'filters': {
                'date_from': date_from.isoformat() if date_from else '',
                'date_to': date_to.isoformat() if date_to else '',
                'category': category,
                'location': location,
            },
            'totals': {
                'complaint_count': len(complaints),
                'total_matched_count': total_matched,
                'is_truncated': is_truncated,
                'resolved_count': resolved_count,
                'feedback_count': feedback_count,
            },
            'kpis': {
                'avg_resolution_time_hours': round(_to_float(average_resolution), 2),
                'sla_compliance_rate': round(_to_float(sla_compliance_rate), 2),
                'reopen_rate': round(_to_float(reopen_rate), 2),
                'feedback_response_rate': round(_to_float(feedback_response_rate), 2),
            },
            'status_logs': status_logs,
            'analytics': {
                'category_hotspots': [
                    {'category': category_name, 'count': count}
                    for category_name, count in category_counter.most_common(5)
                ],
                'location_hotspots': [
                    {'location': location_name, 'count': count}
                    for location_name, count in location_counter.most_common(5)
                ],
                'recurring_issue_clusters': recurring_issue_clusters,
                'time_series': trend_series,
            },
            'complaints': serializers.StudentComplainSerializers(complaints, many=True).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def submit_feedback_api(request, c_id):
    user, extra = _get_request_extra_info(request)
    complaint = get_object_or_404(StudentComplain, id=c_id)

    if complaint.is_draft:
        return Response({'message': 'Draft complaints cannot accept feedback'}, status=status.HTTP_400_BAD_REQUEST)

    if not _is_complainant(extra, complaint) and not _is_superuser(user):
        return Response({'message': 'Only complainant can submit feedback'}, status=status.HTTP_403_FORBIDDEN)

    if complaint.status != ComplaintStatus.CLOSED:
        return Response({'message': 'Feedback can only be submitted after closure'}, status=status.HTTP_400_BAD_REQUEST)

    feedback = str(request.data.get('feedback', '')).strip()
    if not feedback:
        return Response({'message': 'feedback is required'}, status=status.HTTP_400_BAD_REQUEST)

    if len(feedback) > 500:
        return Response({'message': 'feedback must be 500 characters or fewer'}, status=status.HTTP_400_BAD_REQUEST)

    rating = request.data.get('rating', None)
    if rating in (None, ''):
        rating = complaint.flag
    else:
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return Response({'message': 'rating must be a number between 1 and 5'}, status=status.HTTP_400_BAD_REQUEST)
        if rating < 1 or rating > 5:
            return Response({'message': 'rating must be between 1 and 5'}, status=status.HTTP_400_BAD_REQUEST)

    complaint.feedback = feedback
    complaint.flag = rating
    complaint.save(update_fields=['feedback', 'flag', 'updated_at'])

    _log_complaint_event(
        complaint,
        action='feedback_submitted',
        actor=extra,
        from_status=complaint.status,
        to_status=complaint.status,
        note=feedback[:120],
        metadata={'rating': rating},
    )

    return Response(_complaint_payload(complaint), status=status.HTTP_200_OK)
