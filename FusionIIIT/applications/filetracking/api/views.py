import logging
import os
import base64
from django.db import transaction
from django.db.models import Q, OuterRef, Subquery

from django.contrib.auth import get_user_model
from django.core import serializers as django_serializers
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response

from applications.filetracking.models import (
    LegacyFile as File, LegacyTracking as Tracking,
    FileType, File as NewFile, FileMovement, FileAttachment, DraftFile, FileVersion,
    FTAccessPolicy, FTAdminAuditLog,
)
from applications.filetracking.services import (
    forward_file, approve_file, reject_file, close_file,
    return_file, amend_file_with_action, delete_draft, get_file_history,
    archive_file, unarchive_file,
    generate_file_number, get_initial_handler_for_file_type,
    get_next_required_designations,
)
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, DepartmentInfo

User = get_user_model()

logger = logging.getLogger(__name__)


ALLOWED_ATTACHMENT_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024
DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 500


def _validate_attachments(uploaded_files):
    for uploaded in uploaded_files:
        _, ext = os.path.splitext(uploaded.name or '')
        if ext.lower() not in ALLOWED_ATTACHMENT_EXTENSIONS:
            raise ValueError(
                f'Unsupported attachment type: {uploaded.name}. Allowed: PDF, JPG, JPEG, PNG'
            )
        if uploaded.size > MAX_ATTACHMENT_SIZE_BYTES:
            raise ValueError(f'Attachment too large: {uploaded.name}. Max size is 10MB')


def _is_ft_admin(user):
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    admin_tokens = ('admin', 'administrator', 'director', 'dean')
    designations = HoldsDesignation.objects.filter(working=user).select_related('designation')
    for holder in designations:
        name = (holder.designation.name or '').lower()
        full_name = (holder.designation.full_name or '').lower()
        if any(token in name or token in full_name for token in admin_tokens):
            return True

    return False


def _designation_tokens(user):
    designations = HoldsDesignation.objects.filter(working=user).select_related('designation')
    tokens = []
    for holder in designations:
        name = (holder.designation.name or '').lower()
        full_name = (holder.designation.full_name or '').lower()
        tokens.extend([name, full_name])
    return [token for token in tokens if token]


def _is_student_designation_token(token):
    normalized = (token or '').strip().lower().replace('_', ' ')
    student_exact = {'student', 'guest', 'research scholar', 'phd scholar'}
    if normalized in student_exact:
        return True
    if normalized.startswith('student '):
        return True
    if normalized.endswith(' student'):
        return True
    return False

def _get_user_designation_name(user):
    if not user:
        return ''

    hold = HoldsDesignation.objects.filter(working=user).select_related('designation').first()
    return hold.designation.name if hold and hold.designation else ''


def _safe_username(user_obj):
    return getattr(user_obj, 'username', '') if user_obj else ''


def _safe_holder_username(holder):
    return _safe_username(holder.user if holder and getattr(holder, 'user', None) else None)


def _safe_department_name(department):
    return department.name if department else ''


def _safe_designation_name(designation):
    return designation.name if designation else ''


def _forbid_if_not_ft_admin(request):
    if _is_ft_admin(request.user):
        return None
    return Response({'error': 'Admin privileges required'}, status=status.HTTP_403_FORBIDDEN)


def _has_valid_designation(user):
    """Check if user has any valid designation (faculty, staff, or student)."""
    if not user or not user.is_authenticated or not user.is_active:
        return False
    
    tokens = _designation_tokens(user)
    return bool(tokens)


def _forbid_if_no_valid_designation(request):
    """Permission check for reference data endpoints accessible to all designated users."""
    if _has_valid_designation(request.user):
        return None
    return Response(
        {'error': 'You must have a valid designation to access this resource'},
        status=status.HTTP_403_FORBIDDEN,
    )


def _is_ft_member(user):
    if not user or not user.is_authenticated or not user.is_active:
        return False

    extra = ExtraInfo.objects.filter(user=user).only('user_type').first()
    user_type = (extra.user_type or '').strip().lower() if extra else ''
    if user_type in {'faculty', 'staff'}:
        return True

    # Fallback for legacy profiles where user_type is incomplete.
    tokens = _designation_tokens(user)
    employee_markers = ('faculty', 'professor', 'staff', 'admin', 'administrator', 'dean', 'director')
    return any((not _is_student_designation_token(token)) and any(marker in token for marker in employee_markers) for token in tokens)


def _is_ft_student(user):
    if not user or not user.is_authenticated or not user.is_active:
        return False

    for token in _designation_tokens(user):
        if _is_student_designation_token(token):
            return True
    return False


def _is_ft_processor(user):
    if not user or not user.is_authenticated or not user.is_active:
        return False

    # Source of truth is designation. Any active non-student designation can process workflow actions.
    tokens = _designation_tokens(user)
    if not tokens:
        return False

    return any(not _is_student_designation_token(token) for token in tokens)


def _forbid_if_not_ft_member(request):
    if _is_ft_member(request.user):
        return None
    return Response(
        {'error': 'Only authenticated users with valid designations can use this endpoint'},
        status=status.HTTP_403_FORBIDDEN,
    )


def _forbid_if_not_ft_processor(request):
    if _is_ft_processor(request.user):
        return None
    return Response(
        {'error': 'Only faculty/administrative designations can process workflow actions'},
        status=status.HTTP_403_FORBIDDEN,
    )


def _get_sendable_file_types_queryset(user):
    """Return active file types available for compose/send flows."""
    return FileType.objects.filter(is_active=True).order_by('name')


def _require_active_file_status(file_obj, allowed_statuses, operation_label='operation'):
    if file_obj.status not in allowed_statuses:
        return Response(
            {
                'error': (
                    f"File is not in an active state for {operation_label}. "
                    f"Current status: {file_obj.status}"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


def _require_existing_active_file(file_obj, operation_label='operation', allow_closed=False):
    inactive_statuses = {'ARCHIVED'}
    if not allow_closed:
        inactive_statuses.add('CLOSED')

    if file_obj.status in inactive_statuses:
        return Response(
            {
                'error': (
                    f"File is not active for {operation_label}. "
                    f"Current status: {file_obj.status}"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


def _get_file_department_context(file_obj, prefer_source=False):
    if prefer_source:
        return file_obj.source_department or file_obj.current_department
    return file_obj.current_department or file_obj.source_department


def _forbid_if_file_department_mismatch(file_obj, user_extra, operation_label='perform this action', prefer_source=False):
    department = _get_file_department_context(file_obj, prefer_source=prefer_source)
    if department and user_extra and user_extra.department_id != department.id:
        return Response(
            {'error': f'Only users from department {department.name} can {operation_label}'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def _legacy_api_guard():
    """Guard deprecated legacy endpoints behind an explicit feature flag."""
    return Response(
        {
            'error': 'Legacy filetracking API is deprecated. Use /filetracking/api/new/* endpoints.',
            'deprecated': True,
        },
        status=status.HTTP_410_GONE,
    )


def _get_pagination_params(request, default_limit=DEFAULT_LIST_LIMIT, max_limit=MAX_LIST_LIMIT):
    """Return optional pagination settings; None means preserve legacy full-list response."""
    raw_limit = request.query_params.get('limit')
    raw_offset = request.query_params.get('offset')

    if raw_limit is None and raw_offset is None:
        return None

    try:
        limit = int(raw_limit) if raw_limit is not None else default_limit
    except (TypeError, ValueError):
        limit = default_limit

    try:
        offset = int(raw_offset) if raw_offset is not None else 0
    except (TypeError, ValueError):
        offset = 0

    limit = max(1, min(limit, max_limit))
    offset = max(0, offset)

    return {
        'limit': limit,
        'offset': offset,
    }


def _paginate_payload(items, pagination):
    if not pagination:
        return items, None

    total = len(items)
    offset = min(pagination['offset'], total)
    limit = pagination['limit']
    end = min(offset + limit, total)

    meta = {
        'count': total,
        'limit': limit,
        'offset': offset,
        'has_next': end < total,
        'has_previous': offset > 0,
    }
    return items[offset:end], meta


def _primary_designation_map_for_users(user_ids):
    """Return a best-effort primary designation name keyed by user id."""
    if not user_ids:
        return {}

    mapping = {}
    designation_rows = HoldsDesignation.objects.filter(
        working_id__in=user_ids,
    ).select_related('designation').order_by('working_id', 'id')

    for row in designation_rows:
        if row.working_id not in mapping:
            mapping[row.working_id] = row.designation.name if row.designation else ''

    return mapping


def _server_error_response(error, user_message, log_context='filetracking_api'):
    logger.exception('%s failed: %s', log_context, str(error))
    return Response({'error': user_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _log_admin_action(actor, action, target_user=None, target_identifier='', details=None):
    FTAdminAuditLog.objects.create(
        actor=actor,
        action=action,
        target_user=target_user,
        target_identifier=target_identifier or (target_user.username if target_user else ''),
        details=details or {},
    )


def to_tracking_dict(track):
    file = track.file_id
    return {
        'id': file.id,
        'subject': file.subject,
        'description': file.description,
        'upload_date': file.upload_date,
        'branch': getattr(file, 'branch', 'FTS'),
        'uploader': file.uploader.user.username if file.uploader and file.uploader.user else '',
        'uploader_designation': file.designation.name if file.designation else '',
        'receiver': track.receiver_id.username if track.receiver_id else '',
        'receiver_designation': track.receive_design.name if track.receive_design else '',
        'sent_by_user': track.current_id.user.username if track.current_id and track.current_id.user else '',
        'sent_by_designation': track.current_design.designation.name if track.current_design and track.current_design.designation else '',
        'is_read': track.is_read,
        'file_extra_JSON': {
            'subject': file.subject or '',
            'description': file.description or '',
            'remarks': track.remarks or '',
        },
        'upload_file': file.upload_file.url if file.upload_file else '',
    }


def to_file_dict(file):
    return {
        'id': file.id,
        'subject': file.subject,
        'description': file.description,
        'upload_date': file.upload_date,
        'branch': getattr(file, 'branch', 'FTS'),
        'uploader': file.uploader.user.username if file.uploader and file.uploader.user else '',
        'uploader_designation': file.designation.name if file.designation else '',
        'is_read': file.is_read,
        'file_extra_JSON': {
            'subject': file.subject or '',
            'description': file.description or '',
            'remarks': '',
        },
        'upload_file': file.upload_file.url if file.upload_file else '',
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def designations_api(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'designations': []}, status=status.HTTP_200_OK)

    # Get all user's designations (no workflow-based filtering)
    raw_names = (
        HoldsDesignation.objects.filter(working=user)
        .select_related('designation')
        .values_list('designation__name', flat=True)
        .order_by('designation__name')
    )

    names = []
    seen = set()
    for name in raw_names:
        normalized = (name or '').strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        names.append(name.strip())
    
    return Response(
        {
            'designations': names,
            'required_designation': names[0] if names else '',
            'required_designations': names,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def dropdown_api(request):
    value = (request.data.get('value', '') or '').strip()

    # Get all users matching the search (no workflow-based filtering)
    users = User.objects.filter(username__icontains=value, is_active=True)

    users = users.distinct()[:20]
    users_json = django_serializers.serialize('json', list(users))
    return Response({'users': users_json}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def create_draft_api(request):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block

    current_user = request.user
    extrainfo = ExtraInfo.objects.filter(user=current_user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)

    subject = request.data.get('subject', '')
    description = request.data.get('description', '')

    designation_name = request.data.get('designation', '')
    designation = Designation.objects.filter(name=designation_name).first()
    src_module = request.data.get('src_module', '')

    f = File.objects.create(
        uploader=extrainfo,
        designation=designation,
        subject=subject,
        description=description,
        src_module=src_module,
    )

    return Response(to_file_dict(f), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def draft_api(request):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block

    current_user = request.user
    extrainfo = ExtraInfo.objects.filter(user=current_user).first()
    if not extrainfo:
        return Response([], status=status.HTTP_200_OK)

    tracked_file_ids = Tracking.objects.values_list('file_id_id', flat=True)
    drafts = File.objects.filter(uploader=extrainfo).exclude(id__in=tracked_file_ids).order_by('-upload_date')

    data = [to_file_dict(file) for file in drafts]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def file_api(request):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block
    return legacy_block


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def file_detail_api(request, file_id):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block

    f = get_object_or_404(File, id=file_id)

    if request.method == 'GET':
        return Response(to_file_dict(f), status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        f.delete()
        return Response({'message': 'File deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def inbox_api(request):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block

    current_user = request.user
    extra = ExtraInfo.objects.filter(user=current_user).first()
    if not extra:
        return Response([], status=status.HTTP_200_OK)

    tracks = Tracking.objects.filter(receiver_id=current_user).order_by('-receive_date')
    data = [to_tracking_dict(track) for track in tracks]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def outbox_api(request):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block

    current_user = request.user
    extra = ExtraInfo.objects.filter(user=current_user).first()
    if not extra:
        return Response([], status=status.HTTP_200_OK)

    tracks = Tracking.objects.filter(current_id=extra).order_by('-forward_date')
    data = [to_tracking_dict(track) for track in tracks]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def archive_list_api(request):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block

    files = File.objects.filter(is_read=True).order_by('-upload_date')
    data = [to_file_dict(file) for file in files]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def create_archive_api(request):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block

    file_id = request.data.get('file_id')
    f = get_object_or_404(File, id=file_id)
    f.is_read = True
    f.save()
    Tracking.objects.filter(file_id=f).update(is_read=True)
    return Response({'message': 'Archived'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def unarchive_api(request):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block

    file_id = request.data.get('file_id')
    f = get_object_or_404(File, id=file_id)
    f.is_read = False
    f.save()
    Tracking.objects.filter(file_id=f).update(is_read=False)
    return Response({'message': 'Unarchived'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def history_api(request, file_id):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block

    file_obj = get_object_or_404(File, id=file_id)
    tracks = Tracking.objects.filter(file_id=file_obj).order_by('forward_date')
    data = [
        {
            'id': t.id,
            'file_id': t.file_id.id,
            'current_id': t.current_id.user.username if t.current_id else '',
            'current_designation': t.current_design.designation.name if t.current_design and t.current_design.designation else '',
            'receiver_id': t.receiver_id.username if t.receiver_id else '',
            'receive_design': t.receive_design.name if t.receive_design else '',
            'remarks': t.remarks,
            'forward_date': t.forward_date,
            'upload_file': t.upload_file.url if t.upload_file else '',
        }
        for t in tracks
    ]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def forward_file_api(request, file_id):
    legacy_block = _legacy_api_guard()
    if legacy_block:
        return legacy_block
    return legacy_block


# New comprehensive FTS API endpoints

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_files_api(request):
    """List/Create new comprehensive files"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    if request.method == 'GET':
        pagination = _get_pagination_params(request)
        files = NewFile.objects.filter(created_by__user=request.user).select_related(
            'file_type', 'created_by', 'source_department', 'current_holder',
            'current_designation', 'current_department'
        )

        status_filter = (request.GET.get('status', '') or '').strip().upper()
        if status_filter:
            files = files.filter(status=status_filter)

        files = files.order_by('-created_at')

        data = [{
            'id': f.id,
            'file_number': f.file_number,
            'file_type': f.file_type.name if f.file_type else '',
            'subject': f.subject,
            'description': f.description,
            'status': f.status,
            'priority': f.priority,
            'created_at': f.created_at,
            'current_holder': _safe_holder_username(f.current_holder),
            'current_designation': _safe_designation_name(f.current_designation),
        } for f in files]

        paged_data, meta = _paginate_payload(data, pagination)
        if meta:
            return Response({'results': paged_data, 'meta': meta}, status=status.HTTP_200_OK)
        return Response(paged_data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        try:
            current_user = request.user
            extrainfo = ExtraInfo.objects.filter(user=current_user).first()
            if not extrainfo:
                return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)

            if not extrainfo.department:
                return Response(
                    {'error': 'Your profile has no department assigned. Please contact admin.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get required fields
            file_type_id = request.data.get('file_type_id')
            subject = request.data.get('subject', '')
            description = request.data.get('description', '')
            priority = request.data.get('priority', 'NORMAL')
            remarks = (request.data.get('remarks', '') or '').strip()
            action = (request.data.get('action', 'create') or 'create').lower()
            uploaded_files = request.FILES.getlist('files')
            if action == 'submit':
                action = 'create'
            if action not in ('draft', 'create'):
                return Response({'error': "action must be either 'draft' or 'create'"}, status=status.HTTP_400_BAD_REQUEST)

            forbidden_route_keys = {'receiver', 'receiver_username', 'receiver_designation', 'receiver_department_id', 'receiver_id'}
            if any(key in request.data for key in forbidden_route_keys):
                return Response(
                    {'error': 'Manual receiver selection is deprecated. Routing is automatically resolved from FileWorkflow.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not remarks or len(remarks) < 5:
                return Response(
                    {'error': 'Comment is mandatory (minimum 5 characters)'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                _validate_attachments(uploaded_files)
            except ValueError as err:
                return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)

            if not file_type_id or not subject:
                return Response({'error': 'file_type_id and subject are required'}, status=status.HTTP_400_BAD_REQUEST)

            file_type = _get_sendable_file_types_queryset(request.user).filter(id=file_type_id).first()
            if not file_type:
                return Response(
                    {'error': 'Invalid file type for your role or workflow is not configured'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if action == 'draft':
                attachment_payload = []
                for uploaded in uploaded_files:
                    attachment_payload.append({
                        'name': uploaded.name,
                        'content_type': getattr(uploaded, 'content_type', ''),
                        'content_b64': base64.b64encode(uploaded.read()).decode('ascii'),
                    })
                draft_payload = {
                    'description': description,
                    'priority': priority,
                    'remarks': remarks,
                    'attachments': attachment_payload,
                }
                draft = DraftFile.objects.create(
                    created_by=extrainfo,
                    file_type=file_type,
                    subject=subject,
                    description=description,
                    draft_data=draft_payload,
                )
                return Response(
                    {
                        'id': draft.id,
                        'message': 'Draft saved successfully',
                    },
                    status=status.HTTP_201_CREATED,
                )

            duplicate_subject = NewFile.objects.filter(
                created_by=extrainfo,
                subject__iexact=subject.strip(),
            ).exclude(status='ARCHIVED').exists()
            if duplicate_subject:
                return Response(
                    {'error': 'A file with the same subject already exists'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generate file number
            file_number = generate_file_number('FTS', extrainfo.department)

            sender_hd = HoldsDesignation.objects.filter(working=current_user).first()
            if not sender_hd or not sender_hd.designation:
                return Response(
                    {'error': 'Your profile has no active designation. Please contact admin.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            initial_holder = {
                'user': extrainfo,
                'designation': sender_hd.designation,
                'department': extrainfo.department,
            }

            initial_status = 'CREATED'

            with transaction.atomic():
                # Create the file in outbox first; explicit Send will advance workflow status.
                file = NewFile.objects.create(
                    file_number=file_number,
                    file_type=file_type,
                    subject=subject,
                    description=description,
                    created_by=extrainfo,
                    source_department=extrainfo.department,
                    current_holder=initial_holder['user'],
                    current_designation=initial_holder['designation'],
                    current_department=initial_holder['department'],
                    priority=priority,
                    status=initial_status,
                    source_module='FTS',
                )

                # Create initial movement
                FileMovement.objects.create(
                    file=file,
                    action='CREATE',
                    sender=extrainfo,
                    sender_designation=sender_hd.designation if sender_hd else initial_holder['designation'],
                    sender_department=extrainfo.department,
                    receiver=initial_holder['user'],
                    receiver_designation=initial_holder['designation'],
                    receiver_department=initial_holder['department'],
                    remarks=remarks or 'File created',
                )

                for uploaded in uploaded_files:
                    FileAttachment.objects.create(
                        file=file,
                        name=uploaded.name,
                        document=uploaded,
                        uploaded_by=extrainfo,
                        description='Uploaded during file creation',
                    )

            return Response({
                'id': file.id,
                'file_number': file.file_number,
                'status': file.status,
                'current_holder': _safe_holder_username(file.current_holder),
                'current_designation': _safe_designation_name(file.current_designation),
                'message': 'Draft saved successfully' if action == 'draft' else 'File created successfully',
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return _server_error_response(
                e,
                'Unable to create file right now. Please try again.',
                log_context='new_files_api.create',
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_send_file_api(request, file_id):
    """
    ✅ NEW ENDPOINT: Send file to next workflow handler
    
    This endpoint is called after user creates a file and explicitly chooses
    receiver username + receiver designation and sends it.
    
    This separates Create (Save) from Send (Forward to receiver).
    """
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        file = NewFile.objects.get(id=file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    # Only creator can send their own file (compare Django user identity, not designation/profile object)
    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)
    if not file.created_by or file.created_by.user_id != request.user.id:
        return Response({'error': 'Only file creator can send this file'}, status=status.HTTP_403_FORBIDDEN)

    department_error = _forbid_if_file_department_mismatch(file, extrainfo, 'send this file', prefer_source=True)
    if department_error:
        return department_error

    # File must be in CREATED state to send
    if file.status != 'CREATED':
        return Response(
            {'error': f'File must be in CREATED state. Current status: {file.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    remarks = request.data.get('remarks', '').strip()

    receiver_username = (
        request.data.get('receiver')
        or request.data.get('receiver_username')
        or ''
    ).strip()
    receiver_designation = (
        request.data.get('receiver_designation')
        or request.data.get('designation')
        or ''
    ).strip()

    if not receiver_username:
        return Response({'error': 'Receiver username is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not receiver_designation:
        return Response({'error': 'Receiver designation is required'}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ VALIDATION: Sending remarks are mandatory
    if not remarks or len(remarks) < 5:
        return Response(
            {'error': 'Sending remarks are mandatory (minimum 5 characters)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Forward file to next workflow step
        sent_file = forward_file(
            file_id,
            request.user,
            remarks=remarks,
            receiver_username=receiver_username,
            receiver_designation_name=receiver_designation,
        )

        return Response({
            'message': 'File sent successfully',
            'file_id': sent_file.id,
            'file_number': sent_file.file_number,
            'status': sent_file.status,
            'new_holder': _safe_holder_username(sent_file.current_holder),
            'receiver': _safe_holder_username(sent_file.current_holder),
            'receiver_designation': _safe_designation_name(sent_file.current_designation),
        }, status=status.HTTP_200_OK)

    except (ValueError, PermissionError, Designation.DoesNotExist) as e:
        logger.warning('new_send_file_api validation failed for file_id=%s user=%s: %s', file_id, request.user.username, str(e))
        return Response(
            {'error': 'Unable to send file with the provided details. Please verify inputs and try again.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication, TokenAuthentication])
def new_file_detail_api(request, file_id):
    """File details and updates"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        file = NewFile.objects.select_related(
            'file_type', 'created_by', 'source_department',
            'current_holder', 'current_designation', 'current_department'
        ).get(id=file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        extrainfo = ExtraInfo.objects.filter(user=request.user).first()
        is_creator = bool(file.created_by and file.created_by.user_id == request.user.id)
        is_current_holder = bool(file.current_holder and file.current_holder.user_id == request.user.id)
        is_participant = bool(
            extrainfo and (
                FileMovement.objects.filter(file=file).filter(
                    Q(sender=extrainfo) | Q(receiver=extrainfo)
                ).exists()
            )
        )
        if not (is_creator or is_current_holder or is_participant):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        active_error = _require_existing_active_file(file, operation_label='view this file', allow_closed=True)
        if active_error:
            return active_error

        # Pending means assigned and waiting. Once current holder opens it, mark as in-progress.
        if is_current_holder and file.status in ['PENDING', 'SUBMITTED']:
            file.status = 'IN_PROGRESS'
            file.save(update_fields=['status'])

        file_attachments = list(file.attachments.all().order_by('-uploaded_at'))
        is_active_status = file.status not in ['CLOSED', 'ARCHIVED']
        is_processing_status = file.status in ['PENDING', 'SUBMITTED', 'IN_PROGRESS', 'FORWARDED']
        is_created_status = file.status == 'CREATED'
        can_close_transition = file.status in ['APPROVED', 'REJECTED']

        can_send = is_creator and is_created_status
        can_approve = is_current_holder and is_processing_status
        can_forward = is_current_holder and is_processing_status
        can_return = is_current_holder and is_processing_status
        can_amend = is_current_holder and is_processing_status
        can_close = is_creator and can_close_transition

        data = {
            'id': file.id,
            'file_number': file.file_number,
            'file_type': {
                'id': file.file_type.id if file.file_type else None,
                'name': file.file_type.name if file.file_type else '',
                'category': file.file_type.category if file.file_type else '',
            },
            'subject': file.subject,
            'description': file.description,
            'status': file.status,
            'priority': file.priority,
            'created_at': file.created_at,
            'created_by': _safe_holder_username(file.created_by),
            'source_department': _safe_department_name(file.source_department),
            'current_holder': _safe_holder_username(file.current_holder),
            'current_designation': _safe_designation_name(file.current_designation),
            'current_department': _safe_department_name(file.current_department),
            'is_current_handler': is_current_holder,
            'is_view_only': not (is_processing_status and is_current_holder),
            'can_send': can_send,
            'can_approve': can_approve,
            'can_forward': can_forward,
            'can_return': can_return,
            'can_amend': can_amend,
            'can_close': can_close,
            # CamelCase aliases for frontend compatibility.
            'canSend': can_send,
            'canAccept': can_approve,
            'canApprove': can_approve,
            'canForward': can_forward,
            'canReturn': can_return,
            'canAmend': can_amend,
            'canClose': can_close,
            'isCurrentHandler': is_current_holder,
            'isViewOnly': not (is_processing_status and is_current_holder),
            'upload_file': file_attachments[0].document.url if file_attachments else '',
            'attachments': [{
                'id': att.id,
                'name': att.name,
                'document': att.document.url if att.document else '',
                'uploaded_at': att.uploaded_at,
                'uploaded_by': _safe_holder_username(att.uploaded_by),
            } for att in file.attachments.all()],
        }
        return Response(data, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        # Update file details (admin only or creator)
        if not file.created_by or file.created_by.user_id != request.user.id:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        active_error = _require_existing_active_file(file, operation_label='modify this file')
        if active_error:
            return active_error

        file_type_id = request.data.get('file_type_id')
        remarks = (request.data.get('remarks', '') or '').strip()
        uploaded_files = request.FILES.getlist('files')
        remove_attachment_ids = request.data.getlist('remove_attachment_ids') if hasattr(request.data, 'getlist') else request.data.get('remove_attachment_ids', [])

        if isinstance(remove_attachment_ids, str):
            remove_attachment_ids = [remove_attachment_ids]

        normalized_attachment_ids = []
        for attachment_id in remove_attachment_ids or []:
            if attachment_id in (None, '', 'null'):
                continue
            try:
                normalized_attachment_ids.append(int(attachment_id))
            except (TypeError, ValueError):
                return Response({'error': 'Invalid attachment selection'}, status=status.HTTP_400_BAD_REQUEST)

        if file_type_id:
            file_type = _get_sendable_file_types_queryset(request.user).filter(id=file_type_id).first()
            if not file_type:
                return Response({'error': 'Invalid file type for your role or workflow is not configured'}, status=status.HTTP_400_BAD_REQUEST)
            file.file_type = file_type

        file.subject = request.data.get('subject', file.subject)
        file.description = request.data.get('description', file.description)
        file.priority = request.data.get('priority', file.priority)

        try:
            _validate_attachments(uploaded_files)
        except ValueError as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            file.save()

            if normalized_attachment_ids:
                FileAttachment.objects.filter(file=file, id__in=normalized_attachment_ids).delete()

            if remarks:
                sender_hd = HoldsDesignation.objects.filter(working=request.user).select_related('designation').first()
                sender_designation = sender_hd.designation if sender_hd and sender_hd.designation else file.current_designation
                FileMovement.objects.create(
                    file=file,
                    action='COMMENT',
                    sender=file.created_by,
                    sender_designation=sender_designation,
                    sender_department=file.created_by.department if file.created_by and file.created_by.department else file.source_department,
                    receiver=file.current_holder,
                    receiver_designation=file.current_designation,
                    receiver_department=file.current_department,
                    remarks=remarks,
                )

            for uploaded in uploaded_files:
                FileAttachment.objects.create(
                    file=file,
                    name=uploaded.name,
                    document=uploaded,
                    uploaded_by=file.created_by,
                    description='Uploaded during file update',
                )

        return Response({'message': 'File updated successfully'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication, TokenAuthentication])
def new_forward_file_api(request, file_id):
    """Forward file to next handler"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        file = NewFile.objects.get(id=file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if user can forward this file
    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)
    if file.current_holder != extrainfo:
        return Response({'error': 'You are not the current holder of this file'}, status=status.HTTP_403_FORBIDDEN)

    department_error = _forbid_if_file_department_mismatch(file, extrainfo, 'forward this file')
    if department_error:
        return department_error

    status_error = _require_active_file_status(
        file,
        ['PENDING', 'SUBMITTED', 'IN_PROGRESS', 'FORWARDED', 'REJECTED'],
        'forward',
    )
    if status_error:
        return status_error

    remarks = request.data.get('remarks', '')
    uploaded_files = request.FILES.getlist('files')

    receiver_username = (
        request.data.get('receiver')
        or request.data.get('receiver_username')
        or ''
    ).strip()
    receiver_designation = (
        request.data.get('receiver_designation')
        or request.data.get('designation')
        or ''
    ).strip()

    if not receiver_username:
        return Response({'error': 'Receiver username is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not receiver_designation:
        return Response({'error': 'Receiver designation is required'}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ VALIDATION: Remarks/comments are mandatory
    if not remarks or len(remarks.strip()) < 5:
        return Response({'error': 'Remarks are mandatory (minimum 5 characters)'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        _validate_attachments(uploaded_files)
    except ValueError as err:
        return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            forwarded_file = forward_file(
                file_id,
                request.user,
                remarks=remarks,
                receiver_username=receiver_username,
                receiver_designation_name=receiver_designation,
            )

            for uploaded in uploaded_files:
                FileAttachment.objects.create(
                    file=forwarded_file,
                    name=uploaded.name,
                    document=uploaded,
                    uploaded_by=extrainfo,
                    description='Uploaded during forwarding',
                )

        return Response({
            'message': 'File forwarded successfully',
            'file_id': forwarded_file.id,
            'new_holder': _safe_holder_username(forwarded_file.current_holder),
            'receiver': _safe_holder_username(forwarded_file.current_holder),
            'receiver_designation': _safe_designation_name(forwarded_file.current_designation),
        }, status=status.HTTP_200_OK)
    except (ValueError, PermissionError, Designation.DoesNotExist, DepartmentInfo.DoesNotExist) as e:
        logger.warning('new_forward_file_api validation failed for file_id=%s user=%s: %s', file_id, request.user.username, str(e))
        return Response(
            {'error': 'Unable to forward file with the provided details. Please verify inputs and try again.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication, TokenAuthentication])
def new_approve_file_api(request, file_id):
    """Approve a file"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        file = NewFile.objects.get(id=file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if user can approve this file
    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)
    if file.current_holder != extrainfo:
        return Response({'error': 'You are not authorized to approve this file'}, status=status.HTTP_403_FORBIDDEN)

    department_error = _forbid_if_file_department_mismatch(file, extrainfo, 'approve this file')
    if department_error:
        return department_error

    status_error = _require_active_file_status(
        file,
        ['PENDING', 'SUBMITTED', 'IN_PROGRESS', 'FORWARDED'],
        'approve',
    )
    if status_error:
        return status_error

    remarks = request.data.get('remarks', '')

    # ✅ VALIDATION: Remarks/comments are mandatory
    if not remarks or len(remarks.strip()) < 5:
        return Response({'error': 'Approval remarks are mandatory (minimum 5 characters)'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        approved_file = approve_file(file_id, request.user, remarks)
        return Response({
            'message': 'File approved successfully',
            'file_id': approved_file.id,
            'status': approved_file.status,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return _server_error_response(
            e,
            'Unable to approve the file right now. Please try again.',
            log_context='new_approve_file_api',
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_reject_file_api(request, file_id):
    """Reject a file"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        file = NewFile.objects.get(id=file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if user can reject this file
    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)
    if file.current_holder != extrainfo:
        return Response({'error': 'You are not authorized to reject this file'}, status=status.HTTP_403_FORBIDDEN)

    department_error = _forbid_if_file_department_mismatch(file, extrainfo, 'reject this file')
    if department_error:
        return department_error

    status_error = _require_active_file_status(
        file,
        ['PENDING', 'SUBMITTED', 'IN_PROGRESS', 'FORWARDED'],
        'reject',
    )
    if status_error:
        return status_error

    remarks = request.data.get('remarks', '')

    # ✅ VALIDATION: Remarks/comments are mandatory
    if not remarks or len(remarks.strip()) < 5:
        return Response({'error': 'Rejection reason is mandatory (minimum 5 characters)'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        rejected_file = reject_file(file_id, request.user, remarks)
        return Response({
            'message': 'File rejected successfully',
            'file_id': rejected_file.id,
            'status': rejected_file.status,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return _server_error_response(
            e,
            'Unable to reject the file right now. Please try again.',
            log_context='new_reject_file_api',
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_close_file_api(request, file_id):
    """Close a file - only creator can close"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        file = NewFile.objects.get(id=file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if user is the creator (file owner) using Django user identity
    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)
    if not file.created_by or file.created_by.user_id != request.user.id:
        return Response({'error': 'Only file creator can close/archive this file'}, status=status.HTTP_403_FORBIDDEN)

    department_error = _forbid_if_file_department_mismatch(file, extrainfo, 'close this file', prefer_source=True)
    if department_error:
        return department_error

    remarks = request.data.get('remarks', '')

    # ✅ VALIDATION: Remarks/comments are mandatory
    if not remarks or len(remarks.strip()) < 5:
        return Response({'error': 'Closure remarks are mandatory (minimum 5 characters)'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        closed_file = close_file(file_id, request.user, remarks)
        return Response({
            'message': 'File closed successfully',
            'file_id': closed_file.id,
            'status': closed_file.status,
        }, status=status.HTTP_200_OK)
    except PermissionError as e:
        logger.warning('new_close_file_api permission denied for file_id=%s user=%s: %s', file_id, request.user.username, str(e))
        return Response({'error': 'You are not authorized to close this file.'}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return _server_error_response(
            e,
            'Unable to close the file right now. Please try again.',
            log_context='new_close_file_api',
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_archive_file_api(request, file_id):
    """Archive a closed file - only creator can archive."""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        file = NewFile.objects.get(id=file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)
    if not file.created_by or file.created_by.user_id != request.user.id:
        return Response({'error': 'Only file owner can archive this file'}, status=status.HTTP_403_FORBIDDEN)

    active_error = _require_existing_active_file(file, operation_label='archive this file', allow_closed=True)
    if active_error:
        return active_error

    remarks = (request.data.get('remarks', '') or 'File archived').strip()

    try:
        archived_file = archive_file(file_id, request.user, remarks)
        return Response(
            {
                'message': 'File archived successfully',
                'file_id': archived_file.id,
                'status': archived_file.status,
            },
            status=status.HTTP_200_OK,
        )
    except ValueError as e:
        if 'Invalid status transition for archive' in str(e):
            return Response(
                {'error': 'File must be in closed/completed state before archive'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.warning('new_archive_file_api business rule failed for file_id=%s user=%s: %s', file_id, request.user.username, str(e))
        return Response({'error': 'Unable to archive this file in its current state.'}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionError as e:
        logger.warning('new_archive_file_api permission denied for file_id=%s user=%s: %s', file_id, request.user.username, str(e))
        return Response({'error': 'You are not authorized to archive this file.'}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return _server_error_response(
            e,
            'Unable to archive the file right now. Please try again.',
            log_context='new_archive_file_api',
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_archive_list_api(request):
    """Get archived files for current user in new FTS system."""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response([], status=status.HTTP_200_OK)

    archived_files = NewFile.objects.filter(
        status='ARCHIVED',
    ).filter(
        Q(created_by__user=request.user)
        | Q(movements__sender=extrainfo)
        | Q(movements__receiver=extrainfo)
    ).select_related('created_by__user').distinct().order_by('-created_at')

    pagination = _get_pagination_params(request)
    data = []
    for f in archived_files:
        data.append({
            'id': f.id,
            'file_number': f.file_number,
            'subject': f.subject,
            'description': f.description,
            'status': f.status,
            'created_at': f.created_at,
            'upload_date': f.created_at,
            'uploader': _safe_holder_username(f.created_by),
            'uploader_designation': _get_user_designation_name(f.created_by.user) if f.created_by and f.created_by.user else '',
            'branch': 'FTS',
        })

    paged_data, meta = _paginate_payload(data, pagination)
    if meta:
        return Response({'results': paged_data, 'meta': meta}, status=status.HTTP_200_OK)
    return Response(paged_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_unarchive_file_api(request, file_id):
    """Unarchive file in new FTS system - only owner can unarchive."""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        file = NewFile.objects.get(id=file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)
    if not file.created_by or file.created_by.user_id != request.user.id:
        return Response({'error': 'Only file owner can unarchive this file'}, status=status.HTTP_403_FORBIDDEN)

    remarks = (request.data.get('remarks', '') or 'File unarchived').strip()

    try:
        unarchived_file = unarchive_file(file_id, request.user, remarks)
        return Response(
            {
                'message': 'File unarchived successfully',
                'file_id': unarchived_file.id,
                'status': unarchived_file.status,
            },
            status=status.HTTP_200_OK,
        )
    except PermissionError as e:
        logger.warning('new_unarchive_file_api permission denied for file_id=%s user=%s: %s', file_id, request.user.username, str(e))
        return Response({'error': 'You are not authorized to unarchive this file.'}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return _server_error_response(
            e,
            'Unable to unarchive the file right now. Please try again.',
            log_context='new_unarchive_file_api',
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_file_history_api(request, file_id):
    """Get file movement history - only creator and participants can view"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        history = get_file_history(file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    file_obj = history['file']
    user_extra = ExtraInfo.objects.filter(user=request.user).first()

    # ✅ SECURITY CHECK: Only creator and participants can view history
    is_creator = file_obj.created_by == user_extra
    is_current_holder = file_obj.current_holder == user_extra
    is_participant = FileMovement.objects.filter(file=file_obj).filter(
        Q(sender=user_extra) | Q(receiver=user_extra)
    ).exists()
    
    if not (is_creator or is_current_holder or is_participant):
        return Response({'error': 'You do not have permission to view this file history'}, status=status.HTTP_403_FORBIDDEN)

    active_error = _require_existing_active_file(file_obj, operation_label='track this file', allow_closed=True)
    if active_error:
        return active_error

    file_attachments = list(file_obj.attachments.all().order_by('-uploaded_at'))
    # ✅ NOTE: All movements reference the same file attachments (cumulative). Per-movement attachment
    # tracking would require schema redesign. Current behavior shows primary file attachment in history.
    first_attachment_url = file_attachments[0].document.url if file_attachments else ''

    data = {
        'file': {
            'id': file_obj.id,
            'file_number': file_obj.file_number,
            'subject': file_obj.subject,
            'status': file_obj.status,
            'upload_file': first_attachment_url,
        },
        'movements': [{
            'id': m.id,
            'action': m.action,
            'sender': _safe_holder_username(m.sender),
            'receiver': _safe_holder_username(m.receiver),
            'remarks': m.remarks,
            'timestamp': m.timestamp,
            'upload_file': first_attachment_url,
        } for m in history['movements']],
        'versions': [{
            'id': version.id,
            'version_number': version.version_number,
            'action': version.action,
            'comment': version.comment,
            'changed_by': version.changed_by.user.username if version.changed_by and version.changed_by.user else None,
            'created_at': version.created_at,
        } for version in FileVersion.objects.filter(file=file_obj).select_related('changed_by__user').order_by('-version_number')],
        'total_movements': history['total_movements'],
        'days_open': history['days_open'],
    }

    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_inbox_api(request):
    """Get user's inbox for new FTS system"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response([], status=status.HTTP_200_OK)

    pagination = _get_pagination_params(request)
    latest_movement_qs = FileMovement.objects.filter(file_id=OuterRef('pk')).order_by('-timestamp')

    files = NewFile.objects.filter(
        current_holder=extrainfo,
        status__in=['CREATED', 'PENDING', 'SUBMITTED', 'IN_PROGRESS', 'FORWARDED']
    ).select_related(
        'file_type', 'created_by__user', 'source_department', 'current_holder__user', 'current_designation'
    ).annotate(
        latest_sender_username=Subquery(latest_movement_qs.values('sender__user__username')[:1]),
        latest_sender_designation=Subquery(latest_movement_qs.values('sender_designation__name')[:1]),
    ).order_by('-received_at')

    designation_map = _primary_designation_map_for_users(
        [f.created_by.user_id for f in files if f.created_by and f.created_by.user_id]
    )

    data = []
    for f in files:
        data.append({
            'id': f.id,
            'file_number': f.file_number,
            'file_type': f.file_type.name if f.file_type else '',
            'subject': f.subject,
            'description': f.description,
            'status': f.status,
            'priority': f.priority,
            'created_at': f.created_at,
            'created_by': _safe_holder_username(f.created_by),
            'uploader': _safe_holder_username(f.created_by),
            'uploader_designation': designation_map.get(f.created_by.user_id, '') if f.created_by and f.created_by.user_id else '',
            'source_department': _safe_department_name(f.source_department),
            'current_holder': _safe_holder_username(f.current_holder),
            'current_designation': _safe_designation_name(f.current_designation),
            'sent_by_user': f.latest_sender_username or '',
            'sent_by_designation': f.latest_sender_designation or '',
        })

    paged_data, meta = _paginate_payload(data, pagination)
    if meta:
        return Response({'results': paged_data, 'meta': meta}, status=status.HTTP_200_OK)
    return Response(paged_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_outbox_api(request):
    """Get user's outbox for new FTS system"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response([], status=status.HTTP_200_OK)

    pagination = _get_pagination_params(request)

    sent_movements = FileMovement.objects.filter(
        sender=extrainfo,
        action='FORWARD'
    ).values_list('file_id', flat=True).distinct()

    latest_movement_qs = FileMovement.objects.filter(file_id=OuterRef('pk')).order_by('-timestamp')

    unique_files = NewFile.objects.filter(
        id__in=sent_movements
    ).exclude(status='ARCHIVED').select_related(
        'file_type', 'created_by__user', 'current_holder__user', 'current_designation'
    ).annotate(
        latest_sender_username=Subquery(latest_movement_qs.values('sender__user__username')[:1]),
        latest_sender_designation=Subquery(latest_movement_qs.values('sender_designation__name')[:1]),
        latest_receiver_username=Subquery(latest_movement_qs.values('receiver__user__username')[:1]),
        latest_receiver_designation=Subquery(latest_movement_qs.values('receiver_designation__name')[:1]),
    ).distinct().order_by('-created_at')

    designation_map = _primary_designation_map_for_users(
        [f.created_by.user_id for f in unique_files if f.created_by and f.created_by.user_id]
    )

    data = []
    for f in unique_files:
        data.append({
            'id': f.id,
            'file_number': f.file_number,
            'file_type': f.file_type.name if f.file_type else '',
            'subject': f.subject,
            'description': f.description,
            'status': f.status,
            'created_at': f.created_at,
            'created_by': _safe_holder_username(f.created_by),
            'uploader': _safe_holder_username(f.created_by),
            'can_send': bool(f.created_by and f.created_by.user_id == request.user.id and f.status == 'CREATED'),
            'can_archive': bool(f.created_by and f.created_by.user_id == request.user.id and f.status == 'CLOSED'),
            'uploader_designation': designation_map.get(f.created_by.user_id, '') if f.created_by and f.created_by.user_id else '',
            'current_holder': _safe_holder_username(f.current_holder),
            'current_designation': _safe_designation_name(f.current_designation),
            'receiver': f.latest_receiver_username or _safe_holder_username(f.current_holder),
            'receiver_designation': f.latest_receiver_designation or _safe_designation_name(f.current_designation),
            'sent_by_user': f.latest_sender_username or '',
            'sent_by_designation': f.latest_sender_designation or '',
        })

    paged_data, meta = _paginate_payload(data, pagination)
    if meta:
        return Response({'results': paged_data, 'meta': meta}, status=status.HTTP_200_OK)
    return Response(paged_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_pending_api(request):
    """Get pending actions for user"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response([], status=status.HTTP_200_OK)

    pagination = _get_pagination_params(request)
    files = NewFile.objects.filter(
        current_holder=extrainfo,
        status__in=['PENDING', 'SUBMITTED']
    ).select_related('file_type', 'created_by').order_by('-received_at')

    data = [{
        'id': f.id,
        'file_number': f.file_number,
        'file_type': f.file_type.name if f.file_type else '',
        'subject': f.subject,
        'priority': f.priority,
        'received_at': f.received_at,
    } for f in files]

    paged_data, meta = _paginate_payload(data, pagination)
    if meta:
        return Response({'results': paged_data, 'meta': meta}, status=status.HTTP_200_OK)
    return Response(paged_data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_drafts_api(request):
    """Manage draft files"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        pagination = _get_pagination_params(request)
        drafts = DraftFile.objects.filter(created_by=extrainfo).select_related('file_type').order_by('-created_at')
        data = [{
            'id': d.id,
            'file_type_id': d.file_type.id if d.file_type else None,
            'file_type': d.file_type.name if d.file_type else '',
            'subject': d.subject,
            'description': d.description,
            'draft_data': d.draft_data,
            'attachments': (d.draft_data or {}).get('attachments', []),
            'created_at': d.created_at,
            'updated_at': d.updated_at,
        } for d in drafts]
        paged_data, meta = _paginate_payload(data, pagination)
        if meta:
            return Response({'results': paged_data, 'meta': meta}, status=status.HTTP_200_OK)
        return Response(paged_data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        file_type_id = request.data.get('file_type_id')
        subject = (request.data.get('subject', '') or '').strip()
        description = request.data.get('description', '')
        remarks = (request.data.get('remarks', '') or '').strip()
        priority = (request.data.get('priority', 'NORMAL') or 'NORMAL').strip()

        if not file_type_id:
            return Response({'error': 'file_type_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not subject:
            return Response({'error': 'subject is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not remarks or len(remarks) < 5:
            return Response(
                {'error': 'Comment is mandatory (minimum 5 characters)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            file_type = FileType.objects.get(id=file_type_id)
        except FileType.DoesNotExist:
            return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_files = request.FILES.getlist('files')
        try:
            _validate_attachments(uploaded_files)
        except ValueError as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)

        duplicate_subject = NewFile.objects.filter(
            created_by=extrainfo,
            subject__iexact=subject,
        ).exclude(status='ARCHIVED').exists()
        if duplicate_subject:
            return Response(
                {'error': 'A file with the same subject already exists'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attachment_payload = []
        for uploaded in uploaded_files:
            attachment_payload.append({
                'name': uploaded.name,
                'content_type': getattr(uploaded, 'content_type', ''),
                'content_b64': base64.b64encode(uploaded.read()).decode('ascii'),
            })

        draft = DraftFile.objects.create(
            created_by=extrainfo,
            file_type=file_type,
            subject=subject,
            description=description,
            draft_data={
                'remarks': remarks,
                'priority': priority,
                'attachments': attachment_payload,
            },
        )

        return Response({
            'id': draft.id,
            'message': 'Draft saved successfully',
        }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_file_types_api(request):
    """Get available file types"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    file_types = _get_sendable_file_types_queryset(request.user)
    data = [{
        'id': ft.id,
        'name': ft.name,
        'category': ft.category,
        'description': ft.description,
        'requires_attachments': ft.requires_attachments,
    } for ft in file_types]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_designations_api(request):
    """Get available designations for routing"""
    forbidden = _forbid_if_not_ft_processor(request)
    if forbidden:
        return forbidden

    designations = Designation.objects.all().order_by('name', 'id')
    seen_names = set()
    data = []
    for designation in designations:
        if not designation.name or designation.name in seen_names:
            continue
        seen_names.add(designation.name)
        data.append({
            'id': designation.id,
            'name': designation.name,
            'full_name': designation.full_name,
            'type': designation.type,
        })
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication, TokenAuthentication])
def new_return_file_api(request, file_id):
    """Return file to sender/creator"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        file = NewFile.objects.get(id=file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if user can return this file (must be current holder)
    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)
    if file.current_holder != extrainfo:
        return Response({'error': 'You are not the current holder of this file'}, status=status.HTTP_403_FORBIDDEN)

    department_error = _forbid_if_file_department_mismatch(file, extrainfo, 'return this file')
    if department_error:
        return department_error

    status_error = _require_active_file_status(
        file,
        ['PENDING', 'SUBMITTED', 'IN_PROGRESS', 'FORWARDED', 'REJECTED'],
        'return',
    )
    if status_error:
        return status_error

    remarks = request.data.get('remarks', '')

    # ✅ VALIDATION: Remarks/return reason are mandatory
    if not remarks or len(remarks.strip()) < 5:
        return Response({'error': 'Return reason is mandatory (minimum 5 characters)'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        returned_file = return_file(file_id, request.user, remarks)
        return Response({
            'message': 'File returned successfully',
            'file_id': returned_file.id,
            'status': returned_file.status,
            'new_holder': _safe_holder_username(returned_file.current_holder),
        }, status=status.HTTP_200_OK)
    except (ValueError, PermissionError) as e:
        logger.warning('new_return_file_api validation failed for file_id=%s user=%s: %s', file_id, request.user.username, str(e))
        return Response(
            {'error': 'Unable to return file with the provided details. Please verify inputs and try again.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication, TokenAuthentication])
def new_amend_file_api(request, file_id):
    """Amend file: save in inbox or amend-and-forward."""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    try:
        file = NewFile.objects.get(id=file_id)
    except NewFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    # UC-003 precondition: file must be in current user's inbox and active.
    extrainfo = ExtraInfo.objects.filter(user=request.user).first()
    if not extrainfo:
        return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)

    if file.current_holder != extrainfo:
        return Response({'error': 'You can only amend files currently in your inbox'}, status=status.HTTP_403_FORBIDDEN)

    department_error = _forbid_if_file_department_mismatch(file, extrainfo, 'amend this file')
    if department_error:
        return department_error

    status_error = _require_active_file_status(
        file,
        ['PENDING', 'SUBMITTED', 'IN_PROGRESS', 'FORWARDED', 'REJECTED'],
        'amend',
    )
    if status_error:
        return status_error

    action = (request.data.get('action', 'SAVE') or 'SAVE').upper()
    comment = (request.data.get('comment', '') or '').strip()
    uploaded_files = request.FILES.getlist('files')
    if action not in ['SAVE', 'FORWARD']:
        return Response({'error': 'Invalid amendment action. Allowed values: SAVE, FORWARD'}, status=status.HTTP_400_BAD_REQUEST)

    # UC-003: At least comment or attachment should be supplied for amendment.
    if not comment and len(uploaded_files) == 0:
        return Response({'error': 'Provide amendment comment or at least one attachment'}, status=status.HTTP_400_BAD_REQUEST)

    receiver_username = ''
    receiver_designation = ''
    if action == 'FORWARD':
        receiver_username = (
            request.data.get('receiver')
            or request.data.get('receiver_username')
            or ''
        ).strip()
        receiver_designation = (
            request.data.get('receiver_designation')
            or request.data.get('designation')
            or ''
        ).strip()

        if not receiver_username:
            return Response({'error': 'Receiver username is required for amend-and-forward'}, status=status.HTTP_400_BAD_REQUEST)

        if not receiver_designation:
            return Response({'error': 'Receiver designation is required for amend-and-forward'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        _validate_attachments(uploaded_files)
    except ValueError as err:
        return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            amended_file, version = amend_file_with_action(
                file_id,
                request.user,
                action=action,
                comment=comment,
                receiver_username=receiver_username,
                receiver_designation_name=receiver_designation,
            )

            for uploaded in uploaded_files:
                FileAttachment.objects.create(
                    file=amended_file,
                    name=uploaded.name,
                    document=uploaded,
                    uploaded_by=extrainfo,
                    description='Uploaded during amendment' if action == 'SAVE' else 'Uploaded during amend-and-forward',
                )

        return Response({
            'message': 'Amendment saved successfully' if action == 'SAVE' else 'Amendment forwarded successfully',
            'file_id': amended_file.id,
            'status': amended_file.status,
            'version_number': version.version_number if version else None,
            'version_action': version.action if version else None,
            'new_holder': amended_file.current_holder.user.username if amended_file.current_holder and amended_file.current_holder.user else None,
        }, status=status.HTTP_200_OK)
    except (ValueError, PermissionError, Designation.DoesNotExist, DepartmentInfo.DoesNotExist) as e:
        logger.warning('new_amend_file_api validation failed for file_id=%s user=%s action=%s: %s', file_id, request.user.username, action, str(e))
        return Response(
            {'error': 'Unable to process amendment with the provided details. Please verify inputs and try again.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_delete_draft_api(request, draft_id):
    """Delete a draft file"""
    forbidden = _forbid_if_no_valid_designation(request)
    if forbidden:
        return forbidden

    confirm = str(request.query_params.get('confirm', 'false')).lower()
    if confirm not in ('1', 'true', 'yes'):
        return Response(
            {'error': 'Confirmation required. Pass confirm=true to permanently discard draft.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        draft = DraftFile.objects.get(id=draft_id)
    except DraftFile.DoesNotExist:
        return Response({'error': 'Draft not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        delete_draft(draft_id, request.user)
        return Response({
            'message': 'Draft deleted successfully',
        }, status=status.HTTP_200_OK)
    except PermissionError as e:
        logger.warning('new_delete_draft_api permission denied for draft_id=%s user=%s: %s', draft_id, request.user.username, str(e))
        return Response({'error': 'You are not authorized to delete this draft.'}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return _server_error_response(
            e,
            'Unable to delete draft right now. Please try again.',
            log_context='new_delete_draft_api',
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_admin_users_api(request):
    """FT Admin Console: create users, view users, and assign role designations."""
    forbidden = _forbid_if_not_ft_admin(request)
    if forbidden:
        return forbidden

    if request.method == 'GET':
        pagination = _get_pagination_params(request, default_limit=100, max_limit=1000)
        query = (request.query_params.get('q', '') or '').strip().lower()
        users = User.objects.all().order_by('username')
        if query:
            users = users.filter(username__icontains=query)

        users = list(users)
        extra_map = {
            extra.user_id: extra
            for extra in ExtraInfo.objects.filter(user_id__in=[u.id for u in users]).select_related('department')
        }
        roles_map = {}
        for row in HoldsDesignation.objects.filter(working_id__in=[u.id for u in users]).select_related('designation'):
            roles_map.setdefault(row.working_id, []).append(row.designation.name if row.designation else '')

        data = []
        for user in users:
            extra = extra_map.get(user.id)
            roles = [r for r in roles_map.get(user.id, []) if r]
            data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'roles': roles,
                'profile': {
                    'extra_id': extra.id if extra else None,
                    'user_type': extra.user_type if extra else None,
                    'department': extra.department.name if extra and extra.department else None,
                    'phone_no': extra.phone_no if extra else None,
                }
            })

        paged_data, meta = _paginate_payload(data, pagination)
        if meta:
            return Response({'results': paged_data, 'meta': meta}, status=status.HTTP_200_OK)
        return Response(paged_data, status=status.HTTP_200_OK)

    # POST create user and assign roles
    username = (request.data.get('username', '') or '').strip()
    password = request.data.get('password', '')
    if not username or not password:
        return Response({'error': 'username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=(request.data.get('first_name', '') or '').strip(),
        last_name=(request.data.get('last_name', '') or '').strip(),
        email=(request.data.get('email', '') or '').strip(),
    )

    department = None
    department_id = request.data.get('department_id')
    if department_id:
        department = DepartmentInfo.objects.filter(id=department_id).first()

    extra_id = (request.data.get('extra_id', '') or '').strip()
    if extra_id:
        ExtraInfo.objects.create(
            id=extra_id,
            user=user,
            title=(request.data.get('title', 'Mr.') or 'Mr.'),
            sex=(request.data.get('sex', 'M') or 'M'),
            user_type=(request.data.get('user_type', 'staff') or 'staff'),
            department=department,
            phone_no=request.data.get('phone_no') or 9999999999,
            address=(request.data.get('address', '') or ''),
        )

    assigned_roles = []
    designation_names = request.data.get('designation_names', []) or []
    for designation_name in designation_names:
        designation = Designation.objects.filter(name=designation_name).first()
        if designation:
            HoldsDesignation.objects.get_or_create(
                user=user,
                working=user,
                designation=designation,
            )
            assigned_roles.append(designation.name)

    _log_admin_action(
        actor=request.user,
        action='CREATE_USER',
        target_user=user,
        details={
            'assigned_roles': assigned_roles,
            'extra_profile_created': bool(extra_id),
        },
    )

    return Response(
        {
            'id': user.id,
            'username': user.username,
            'assigned_roles': assigned_roles,
            'message': 'User created successfully',
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_admin_user_detail_api(request, user_id):
    """FT Admin Console: update/deactivate users and manage role mappings."""
    forbidden = _forbid_if_not_ft_admin(request)
    if forbidden:
        return forbidden

    target_user = get_object_or_404(User, id=user_id)

    if request.method == 'GET':
        extra = ExtraInfo.objects.filter(user=target_user).first()
        roles = list(
            HoldsDesignation.objects.filter(working=target_user).select_related('designation').values_list('designation__name', flat=True)
        )
        return Response(
            {
                'id': target_user.id,
                'username': target_user.username,
                'first_name': target_user.first_name,
                'last_name': target_user.last_name,
                'email': target_user.email,
                'is_active': target_user.is_active,
                'is_staff': target_user.is_staff,
                'roles': roles,
                'profile': {
                    'extra_id': extra.id if extra else None,
                    'user_type': extra.user_type if extra else None,
                    'department_id': extra.department_id if extra else None,
                    'phone_no': extra.phone_no if extra else None,
                },
            },
            status=status.HTTP_200_OK,
        )

    if request.method == 'PUT':
        target_user.first_name = request.data.get('first_name', target_user.first_name)
        target_user.last_name = request.data.get('last_name', target_user.last_name)
        target_user.email = request.data.get('email', target_user.email)
        if 'is_active' in request.data:
            target_user.is_active = bool(request.data.get('is_active'))
        if 'is_staff' in request.data:
            target_user.is_staff = bool(request.data.get('is_staff'))
        target_user.save()

        extra = ExtraInfo.objects.filter(user=target_user).first()
        if extra:
            if 'user_type' in request.data:
                extra.user_type = request.data.get('user_type')
            if 'phone_no' in request.data:
                extra.phone_no = request.data.get('phone_no')
            if 'address' in request.data:
                extra.address = request.data.get('address')
            department_id = request.data.get('department_id')
            if department_id is not None:
                extra.department = DepartmentInfo.objects.filter(id=department_id).first()
            extra.save()

        role_changes = {'added': [], 'removed': []}
        if 'designation_names' in request.data:
            desired = set(request.data.get('designation_names') or [])
            existing = set(
                HoldsDesignation.objects.filter(working=target_user).select_related('designation').values_list('designation__name', flat=True)
            )

            to_remove = existing - desired
            to_add = desired - existing

            if to_remove:
                removed_objects = HoldsDesignation.objects.filter(working=target_user, designation__name__in=to_remove)
                removed_objects.delete()
                role_changes['removed'] = list(to_remove)
                _log_admin_action(
                    actor=request.user,
                    action='REMOVE_ROLE',
                    target_user=target_user,
                    details={'roles': list(to_remove)},
                )

            for role_name in to_add:
                designation = Designation.objects.filter(name=role_name).first()
                if designation:
                    HoldsDesignation.objects.get_or_create(user=target_user, working=target_user, designation=designation)
                    role_changes['added'].append(role_name)

            if role_changes['added']:
                _log_admin_action(
                    actor=request.user,
                    action='ASSIGN_ROLE',
                    target_user=target_user,
                    details={'roles': role_changes['added']},
                )

        _log_admin_action(
            actor=request.user,
            action='UPDATE_USER',
            target_user=target_user,
            details={'role_changes': role_changes},
        )

        return Response({'message': 'User updated successfully', 'role_changes': role_changes}, status=status.HTTP_200_OK)

    # DELETE: soft-delete by default
    hard_delete = str(request.query_params.get('hard_delete', 'false')).lower() == 'true'
    if hard_delete:
        username = target_user.username
        target_user.delete()
        _log_admin_action(
            actor=request.user,
            action='DELETE_USER',
            target_user=None,
            target_identifier=username,
            details={'mode': 'hard_delete'},
        )
        return Response({'message': 'User deleted permanently'}, status=status.HTTP_200_OK)

    target_user.is_active = False
    target_user.save(update_fields=['is_active'])
    _log_admin_action(
        actor=request.user,
        action='DELETE_USER',
        target_user=target_user,
        details={'mode': 'deactivate'},
    )
    return Response({'message': 'User deactivated successfully'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_admin_policies_api(request):
    """FT Admin Console: read/update FT ACL and policy entries."""
    forbidden = _forbid_if_not_ft_admin(request)
    if forbidden:
        return forbidden

    if request.method == 'GET':
        policies = FTAccessPolicy.objects.all().order_by('key')
        data = [
            {
                'key': policy.key,
                'value': policy.value,
                'updated_by': policy.updated_by.username if policy.updated_by else None,
                'updated_at': policy.updated_at,
            }
            for policy in policies
        ]
        return Response(data, status=status.HTTP_200_OK)

    # PUT accepts either a single key/value pair or list of entries.
    updates = request.data.get('policies')
    if updates is None:
        key = (request.data.get('key', '') or '').strip()
        if not key:
            return Response({'error': 'key is required'}, status=status.HTTP_400_BAD_REQUEST)
        updates = [{'key': key, 'value': request.data.get('value', {})}]

    applied = []
    for entry in updates:
        key = (entry.get('key', '') or '').strip()
        if not key:
            continue

        policy, _ = FTAccessPolicy.objects.update_or_create(
            key=key,
            defaults={
                'value': entry.get('value', {}),
                'updated_by': request.user,
            },
        )
        applied.append({'key': policy.key, 'value': policy.value})

    _log_admin_action(
        actor=request.user,
        action='UPDATE_POLICY',
        target_identifier='FT_POLICY',
        details={'policies': applied},
    )

    return Response({'message': 'Policies updated successfully', 'updated': applied}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def new_admin_audit_logs_api(request):
    """FT Admin Console: list security audit records for admin actions."""
    forbidden = _forbid_if_not_ft_admin(request)
    if forbidden:
        return forbidden

    pagination = _get_pagination_params(request, default_limit=100, max_limit=500)
    if not pagination:
        pagination = {'limit': 100, 'offset': 0}

    offset = pagination['offset']
    limit = pagination['limit']
    logs = FTAdminAuditLog.objects.select_related('actor', 'target_user').order_by('-created_at')[offset:offset + limit]
    data = [
        {
            'id': row.id,
            'action': row.action,
            'actor': row.actor.username if row.actor else None,
            'target_user': row.target_user.username if row.target_user else None,
            'target_identifier': row.target_identifier,
            'details': row.details,
            'created_at': row.created_at,
        }
        for row in logs
    ]

    total_count = FTAdminAuditLog.objects.count()
    meta = {
        'count': total_count,
        'limit': limit,
        'offset': min(offset, total_count),
        'has_next': (offset + limit) < total_count,
        'has_previous': offset > 0,
    }

    if request.query_params.get('limit') is not None or request.query_params.get('offset') is not None:
        return Response({'results': data, 'meta': meta}, status=status.HTTP_200_OK)
    return Response(data, status=status.HTTP_200_OK)
